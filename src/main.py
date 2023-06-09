import json
import logging
import os
import os.path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import VectorStore, Chroma

from src.callback import StreamingLLMCallbackHandler
from src.chains import build_yaml_documents, get_streaming_chain, get_filter_documents_chain
from src.config import cfg, SRC_PATH
from src.schemas import BotResponse

app = FastAPI(
    title="Renta GPT API",
    description="A retrieval engine about Renta 2022 (Spanish Taxes).",
    version="0.9.0",
    servers=[{"url": "https://rentagpt.com"}],
)

app.mount("/public", StaticFiles(directory=os.path.join(SRC_PATH, "public")), name="public")
app.mount("/.well-known", StaticFiles(directory=os.path.join(SRC_PATH, ".well-known")), name="well-known")
templates = Jinja2Templates(directory=os.path.join(SRC_PATH, "templates"))

docsearch: Optional[VectorStore] = None

origins = [
    "https://rentagpt.fly.dev",
    "https://rentagpt.com",
    "http://localhost:8000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logging.info("loading pickled documents")
    embeddings_file = f"{cfg.chroma.persist_directory}/chroma-embeddings.parquet"

    if not os.path.exists(embeddings_file):
        raise ValueError(
            f"{embeddings_file} does not exist, please run ingest.py first"
        )


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/legal-info")
async def get(request: Request):
    return templates.TemplateResponse("legal-info.html", {"request": request})


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(path=os.path.join(SRC_PATH, "public", "favicon.ico"))


@app.websocket("/query")
async def websocket_endpoint(websocket: WebSocket):
    global docsearch

    await websocket.accept()
    stream_handler = StreamingLLMCallbackHandler(websocket)

    try:
        # Receive and send back the client message
        question = await websocket.receive_text()
        data = json.loads(question)
        api_key = data["apiKey"]

        if docsearch is None and api_key:
            embedding = OpenAIEmbeddings(
                openai_api_key=api_key,
                model="text-embedding-ada-002",
            )
            docsearch = Chroma(
                embedding_function=embedding,
                collection_name=cfg.chroma.collection_name,
                persist_directory=cfg.chroma.persist_directory,
            )

        resp = BotResponse(sender="you", message=data["query"], type="stream")
        await websocket.send_json(resp.dict())

        start_resp = BotResponse(sender="bot", message="", type="start")
        await websocket.send_json(start_resp.dict())

        query_results = docsearch.max_marginal_relevance_search(
            query=question,
            k=4,
        )

        filter_documents_chain = get_filter_documents_chain(api_key)
        documents = build_yaml_documents(query_results)
        result = await filter_documents_chain.acall({
            "question": question,
            "documents": documents,
        })

        try:
            result_text = result['text'].replace("```json", "").replace("```", "")
            result_results = json.loads(result_text)["results"]
        except Exception as e:
            logging.error(e)
            result_results = []

        result_json = {"sources": result_results}
        links = BotResponse(sender="bot", message=json.dumps(result_json), type="info")
        await websocket.send_json(links.dict())

        sources = [source['source'] for source in result_results]
        filtered_query_results = list(filter(lambda x: x.metadata['source'] in sources, query_results))
        filtered_documents = build_yaml_documents(filtered_query_results)
        streaming_chain = get_streaming_chain(stream_handler, api_key)
        result = await streaming_chain.acall({
            "question": question,
            "documents": filtered_documents,
        })

        end_resp = BotResponse(sender="bot", message="", type="end")
        await websocket.send_json(end_resp.dict())
    except WebSocketDisconnect:
        logging.info("websocket disconnect")
        return
    except Exception as e:
        logging.error(e)
        resp = BotResponse(
            sender="bot",
            message="Sorry, something went wrong. Try again.",
            type="error",
        )
        await websocket.send_json(resp.dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=cfg.api.host, port=cfg.api.port, reload=True)
