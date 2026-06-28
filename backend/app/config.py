"""Application configuration."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./epc_dev.db"
    groq_api_key: str = ""
    chroma_path: str = "./chroma_data"
    data_dir: str = str(PROJECT_ROOT / "data")
    cors_origins: str = "http://localhost:3000"
    chunk_size: int = 2000
    chunk_overlap: int = 320

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chroma_path_resolved(self) -> Path:
        path = Path(self.chroma_path)
        return path if path.is_absolute() else BACKEND_ROOT / path

    @property
    def data_dir_resolved(self) -> Path:
        path = Path(self.data_dir)
        return path if path.is_absolute() else PROJECT_ROOT / path


settings = Settings()
