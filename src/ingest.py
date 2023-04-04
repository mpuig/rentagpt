import os
import pickle
from typing import List
from urllib.parse import urljoin

import ftfy
import requests
from bs4 import BeautifulSoup
from langchain.document_loaders import UnstructuredURLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

from src.config import cfg

TEXT_TO_REMOVE = """
Generar PDF

Cerrar

La generación del PDF puede tardar varios minutos dependiendo de la cantidad de información.

Seleccione la información que desee incluir en el PDF:

Página actual

Apartado actual y subapartados

Todo el documento

Puede cancelar la generación del PDF en cualquier momento."""


def fix_document(doc: Document) -> Document:
    return Document(
        page_content=ftfy.fix_text(doc.page_content).replace(TEXT_TO_REMOVE, ""),
        metadata=doc.metadata,
    )


def get_all_links(starting_url: str, url_prefix: str) -> List[str]:
    try:
        response = requests.get(starting_url)
        if response.status_code != 200:
            print(f"Failed to load the page. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        links = []

        for link in soup.find_all("a"):
            href = link.get("href")
            if href:
                absolute_url = urljoin(starting_url, href)
                if absolute_url.startswith(url_prefix):
                    links.append(absolute_url)

        return links

    except Exception as e:
        print(f"Error: {e}")
        return []


def crawl_aeat() -> List[str]:
    starting_url = "https://sede.agenciatributaria.gob.es/Sede/Ayuda/22Manual/100.html"
    url_prefix = "https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/irpf-2022"
    return get_all_links(starting_url, url_prefix)


def load_links(links: List[str]) -> List[Document]:
    """Get documents from web pages."""
    pickle_docs_file = f"{cfg.data_directory}/documents.pkl"

    if os.path.exists(pickle_docs_file):
        with open(pickle_docs_file, "rb") as fp:
            documents = pickle.load(fp)
    else:
        loader = UnstructuredURLLoader(urls=links)
        downloaded_docs = loader.load()
        documents = [fix_document(doc) for doc in downloaded_docs]
        with open(pickle_docs_file, "wb") as fp:
            pickle.dump(documents, fp)
    return documents


def create_embeddings(documents: List[Document]) -> List[Document]:
    split_documents = []

    embeddings_file = f"{cfg.chroma.persist_directory}/chroma-embeddings.parquet"
    embeddings = OpenAIEmbeddings(
        openai_api_key=cfg.providers.openai.api_key,
        model="text-embedding-ada-002",
    )

    if not os.path.exists(embeddings_file):
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=250,
            chunk_overlap=0
        )
        split_documents = text_splitter.split_documents(documents)
        client = Chroma.from_documents(
            documents=split_documents,
            embedding=embeddings,
            collection_name=cfg.chroma.collection_name,
            persist_directory=cfg.chroma.persist_directory,
        )
        client.persist()
    return split_documents


if __name__ == "__main__":
    links = crawl_aeat()
    print(f"Links: {len(links)}")

    documents = load_links(links)
    print(f"Num of downloaded documents: {len(documents)}")

    split_documents = create_embeddings(documents)
    print(f"Num of split documents: {len(split_documents)}")
