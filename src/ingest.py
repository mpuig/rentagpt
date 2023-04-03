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


def fix_document(doc: Document) -> Document:
    return Document(
        page_content=ftfy.fix_text(doc.page_content).replace(TEXT_TO_REMOVE, ""),
        metadata=doc.metadata,
    )


def ingest_docs(links: List[str]) -> None:
    """Get documents from web pages."""
    pickle_docs_file = f"{cfg.chroma.persist_directory}/documents.pkl"
    embeddings_file = f"{cfg.chroma.persist_directory}/chroma-embeddings.parquet"

    if os.path.exists(pickle_docs_file):
        with open(pickle_docs_file, "rb") as fp:
            documents = pickle.load(fp)
    else:
        loader = UnstructuredURLLoader(urls=links)
        downloaded_docs = loader.load()
        documents = [fix_document(doc) for doc in downloaded_docs]
        with open(pickle_docs_file, "wb") as fp:
            pickle.dump(documents, fp)

    print(f"Num of downloaded documents: {len(documents)}")

    embeddings = OpenAIEmbeddings(
        openai_api_key=cfg.providers.openai.api_key,
        model="text-embedding-ada-002",
    )

    if not os.path.exists(embeddings_file):
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=250, chunk_overlap=0
        )
        client = Chroma.from_documents(
            documents=text_splitter.split_documents(documents),
            embedding=embeddings,
            collection_name=cfg.chroma.collection_name,
            persist_directory=cfg.chroma.persist_directory,
        )
        client.persist()


if __name__ == "__main__":
    # Crawl AEAT docs about Renta 2022
    starting_url = "https://sede.agenciatributaria.gob.es/Sede/Ayuda/22Manual/100.html"
    url_prefix = "https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/irpf-2022"
    links = get_all_links(starting_url, url_prefix)
    print(f"Links: {len(links)}")

    ingest_docs(links)
