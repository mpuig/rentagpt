import logging
import os
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
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import VectorStore, Chroma

from src.callback import StreamingLLMCallbackHandler
from src.config import templates, cfg
from src.prompts import PROMPT_TEMPLATE, YAML_DOCUMENT_TEMPLATE
from src.schemas import ChatResponse

app = FastAPI(debug=True, version="0.0.1", title="RentaGPT API")

docsearch: Optional[VectorStore] = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    pickle_docs_file = f"{cfg.chroma.persist_directory}/documents.pkl"
    if not Path(pickle_docs_file).exists():
        raise ValueError(
            f"{pickle_docs_file} does not exist, please run ingest.py first"
        )
    with open(pickle_docs_file, "rb") as f:
        documents = pickle.load(f)

    if not os.path.exists(embeddings_file):
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=250,
            chunk_overlap=0,
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


def build_yaml_documents(query_results) -> str:
    documents = [
        {"text": doc.page_content, "URL": doc.metadata["source"]}
        for doc in query_results
    ]
    yaml_products = [
        YAML_DOCUMENT_TEMPLATE.format(yaml_document=yaml.safe_dump(info))
        for info in documents
    ]
    return "\n".join(yaml_products)


def get_chain(stream_handler):
    manager = AsyncCallbackManager([])
    stream_manager = AsyncCallbackManager([stream_handler])
    streaming_llm = OpenAI(
        openai_api_key=cfg.providers.openai.api_key,
        streaming=True,
        callback_manager=stream_manager,
        verbose=True,
        temperature=0.0,
        max_tokens=1000,
    )
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE, input_variables=["documents", "question"]
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
    qa_chain = get_chain(stream_handler)

    chat_history = []
    while True:
        try:
            # Receive and send back the client message
            question = await websocket.receive_text()
            resp = ChatResponse(sender="you", message=question, type="stream")
            await websocket.send_json(resp.dict())

            # Construct a response
            start_resp = ChatResponse(sender="bot", message="", type="start")
            await websocket.send_json(start_resp.dict())

            query_results = docsearch.max_marginal_relevance_search(
                query=question,
                k=5,
            )
            yaml_documents = build_yaml_documents(query_results)
            result = await qa_chain.acall(
                {"documents": yaml_documents, "question": question}
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=cfg.api.host,
        port=cfg.api.port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
