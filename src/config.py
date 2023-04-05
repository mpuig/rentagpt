import os.path

from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings, BaseModel, Field

src_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(src_path, "..")
templates = Jinja2Templates(directory=os.path.join(src_path, "templates"))


class APIConfig(BaseModel):
    host: str = "localhost"
    port: int = Field(min=0, max=65535, default=8000)


class OpenAIConfig(BaseModel):
    api_key: str


class ProvidersConfig(BaseModel):
    openai: OpenAIConfig


class ChromaConfig(BaseModel):
    persist_directory: str = os.path.join(data_path, "data", "chroma")
    collection_name: str = "renta22"


class Config(BaseSettings):
    api: APIConfig
    chroma: ChromaConfig
    data_directory: str = os.path.join(data_path, "data")
    prompt_template: str = 'SOURCES'
    providers: ProvidersConfig

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


cfg = Config()
