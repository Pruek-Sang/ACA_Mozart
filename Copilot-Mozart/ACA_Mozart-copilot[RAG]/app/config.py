"""
Configuration Module - The Divine Settings
Centralized configuration following Pulchritudo in Simplicitate principle
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Central configuration for Mozart RAG
    
    Philosophy:
    - All paths absolute and explicit
    - Environment variables override defaults
    - No magic values scattered across codebase
    """
    
    # === Google Cloud / Vertex AI ===
    PROJECT_ID: str = "your-project-id"
    LOCATION: str = "us-central1"
    
    # === Model Configuration ===
    MODEL_NAME_ANSWER: str = "gemini-2.0-flash-exp"
    MODEL_NAME_JUDGE: str = "gemini-2.0-flash-exp"

    
    # === Vector Database ===
    VECTOR_DB_PATH: str = "./vector_db"
    EMBEDDING_MODEL: str = "textembedding-gecko@003"
    
    # === Knowledge Base ===
    KNOWLEDGE_ROOT: str = "./rag_knowledge"
    KNOWLEDGE_INDEX_PATH: str = "./rag_knowledge/knowledge_index.json"
    
    # === Trust Log ===
    TRUST_LOG_DIR: str = "./logs/mcp_spec"
    TRUST_LOG_RETENTION_DAYS: int = 90
    
    # === RAG Parameters ===
    MAX_CONTEXT_CHARS: int = 20000
    DEFAULT_TOP_K: int = 5
    MAX_RETRIEVAL_DOCS: int = 10
    
    # === LLM Generation ===
    GENERATION_TEMPERATURE: float = 0.0
    MAX_OUTPUT_TOKENS: int = 8192
    RETRY_MAX_ATTEMPTS: int = 2
    
    # === API ===
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_TITLE: str = "Amadeus RAG (Aura v3.2)"
    API_VERSION: str = "3.2.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
