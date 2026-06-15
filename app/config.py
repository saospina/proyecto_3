from __future__ import annotations

import os


class Config:
    def __init__(self) -> None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")

        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

        self.SQLALCHEMY_DATABASE_URI = database_url
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
        self.OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        if not self.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        self.OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
