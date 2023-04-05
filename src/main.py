import json
import logging
import os
import os.path
import pickle
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
from langchain import OpenAI, LLMChain
from langchain import PromptTemplate
from langchain.callbacks.base import AsyncCallbackManager
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import VectorStore, Chroma
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from src.callback import StreamingLLMCallbackHandler
from src.config import cfg, SRC_PATH
from src.prompts import (YAML_PROMPT_TEMPLATE, YAML_DOCUMENT_TEMPLATE,
                         SOURCES_PROMPT_TEMPLATE, SOURCES_DOCUMENT_TEMPLATE)
from src.schemas import ChatResponse

app = FastAPI(debug=True, version="0.0.1", title="Renta GPT API")

app.mount("/public", StaticFiles(directory=os.path.join(SRC_PATH, "public")), name="public")
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

embedding = OpenAIEmbeddings(
    openai_api_key=cfg.providers.openai.api_key,
    model="text-embedding-ada-002",
)


@app.on_event("startup")
async def startup_event():
    logging.info("loading pickled documents")
    embeddings_file = f"{cfg.chroma.persist_directory}/chroma-embeddings.parquet"
    pickle_docs_file = f"{cfg.data_directory}/documents.pkl"
    if not Path(pickle_docs_file).exists():
        raise ValueError(
            f"{pickle_docs_file} does not exist, please run ingest.py first"
        )
    with open(pickle_docs_file, "rb") as f:
        documents = pickle.load(f)

    if not os.path.exists(embeddings_file):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=50,
            length_function=len,
        )
        client = Chroma.from_documents(
            documents=text_splitter.split_documents(documents),
            embedding=embedding,
            collection_name=cfg.chroma.collection_name,
            persist_directory=cfg.chroma.persist_directory,
        )
        client.persist()

    global docsearch
    docsearch = Chroma(
        embedding_function=embedding,
        collection_name=cfg.chroma.collection_name,
        persist_directory=cfg.chroma.persist_directory,
    )


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    file_name = "favicon.ico"
    file_path = os.path.join(SRC_PATH, "public", file_name)
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})


def build_yaml_documents(query_results) -> str:
    documents = [
        {"id": idx, "text": doc.page_content, "URL": doc.metadata["source"]}
        for idx, doc in enumerate(query_results)
    ]
    yaml_documents = [
        YAML_DOCUMENT_TEMPLATE.format(yaml_document=yaml.safe_dump(info))
        for info in documents
    ]
    return "\n".join(yaml_documents)


def build_sources_documents(query_results) -> str:
    return "\n".join([
        SOURCES_DOCUMENT_TEMPLATE.format(
            idx=idx+1,
            text=doc.page_content,
            source=doc.metadata["source"]
        ) for idx, doc in enumerate(query_results)
    ])


def get_chain(stream_handler, api_key):
    manager = AsyncCallbackManager([])
    stream_manager = AsyncCallbackManager([stream_handler])
    if cfg.prompt_template == 'YAML':
        template = YAML_PROMPT_TEMPLATE
    else:
        template = SOURCES_PROMPT_TEMPLATE
    streaming_llm = OpenAI(
        # openai_api_key=cfg.providers.openai.api_key,
        openai_api_key=api_key,
        streaming=True,
        callback_manager=stream_manager,
        verbose=True,
        temperature=0.0,
        max_tokens=500,
    )
    prompt = PromptTemplate(
        template=template,
        input_variables=["documents", "question"]
    )
    return LLMChain(
        llm=streaming_llm,
        prompt=prompt,
        callback_manager=manager,
    )


@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    stream_handler = StreamingLLMCallbackHandler(websocket)

    chat_history = []
    while True:
        try:
            # Receive and send back the client message
            question = await websocket.receive_text()
            data = json.loads(question)

            resp = ChatResponse(sender="you", message=data["query"], type="stream")
            await websocket.send_json(resp.dict())

            # Construct a response
            start_resp = ChatResponse(sender="bot", message="", type="start")
            await websocket.send_json(start_resp.dict())

            query_results = docsearch.max_marginal_relevance_search(
                query=question,
                k=4,
            )
            message = {
                "sources": [
                    {"text": f"{idx+1}", "url": doc.metadata["source"]}
                    for idx, doc in enumerate(query_results)
                ]
            }
            links = ChatResponse(sender="bot", message=json.dumps(message), type="info")
            await websocket.send_json(links.dict())

            if cfg.prompt_template == 'YAML':
                documents = build_yaml_documents(query_results)
            else:
                documents = build_sources_documents(query_results)

            qa_chain = get_chain(stream_handler, data["apiKey"])
            result = await qa_chain.acall(
                {"documents": documents, "question": question}
            )

            chat_history.append((question, result["text"]))

            end_resp = ChatResponse(sender="bot", message="", type="end")
            await websocket.send_json(end_resp.dict())
        except WebSocketDisconnect:
            logging.info("websocket disconnect")
            break
        except Exception as e:
            logging.error(e)
            resp = ChatResponse(
                sender="bot",
                message="Sorry, something went wrong. Try again.",
                type="error",
            )
            await websocket.send_json(resp.dict())


@app.websocket("/chatfake")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            # Receive and send back the client message
            question = await websocket.receive_text()
            data = json.loads(question)
            resp = ChatResponse(sender="you", message=data["query"], type="stream")
            await websocket.send_json(resp.dict())

            # Send links
            message = {"sources": [
                {"text": "1", "url": "http://link1.com/page1/rtx"},
                {"text": "2", "url": "http://link2.com"},
                {"text": "3", "url": "http://link3.com"},
            ]}
            links = ChatResponse(sender="bot", message=json.dumps(message), type="info")
            await websocket.send_json(links.dict())

            # Construct a response
            start_resp = ChatResponse(sender="bot", message="", type="start")
            await websocket.send_json(start_resp.dict())

            import time
            message = "lorem ipsum [2]. Dolor sit amet [1]."
            for token in message.split(" "):
                stream_resp = ChatResponse(sender="bot", message=f"{token} ", type="stream")
                await websocket.send_json(stream_resp.dict())
                time.sleep(1)

            end_resp = ChatResponse(sender="bot", message=message, type="end")
            await websocket.send_json(end_resp.dict())
        except WebSocketDisconnect:
            logging.info("websocket disconnect")
            break
        except Exception as e:
            logging.error(e)
            resp = ChatResponse(
                sender="bot",
                message="Sorry, something went wrong. Try again.",
                type="error",
            )
            await websocket.send_json(resp.dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=cfg.api.host,
        port=cfg.api.port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
