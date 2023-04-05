import os.path

from pydantic import BaseSettings, BaseModel, Field

SRC_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(SRC_PATH, "..", "data")


class APIConfig(BaseModel):
    host: str = "localhost"
    port: int = Field(min=0, max=65535, default=8000)


class OpenAIConfig(BaseModel):
    api_key: str


class ProvidersConfig(BaseModel):
    openai: OpenAIConfig


class ChromaConfig(BaseModel):
    persist_directory: str = os.path.join(DATA_PATH, "chroma")
    collection_name: str = "renta22"


class Config(BaseSettings):
    api: APIConfig
    chroma: ChromaConfig
    data_directory: str = DATA_PATH
    prompt_template: str = 'SOURCES'
    providers: ProvidersConfig

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


cfg = Config()
