"""
Configuration Module - The Divine Settings
Centralized configuration following Pulchritudo in Simplicitate principle
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict
from typing import Optional
from pathlib import Path
import os

# Base directory of the project (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Central configuration for Mozart RAG
    
    Philosophy:
    - All paths absolute and explicit (using BASE_DIR)
    - Environment variables override defaults
    - No magic values scattered across codebase
    - Folder-based knowledge architecture
    """
    
    # === Google Cloud / Vertex AI ===
    PROJECT_ID: str = "your-project-id"
    LOCATION: str = "us-central1"
    
    # === Google AI API (Alternative to Vertex AI) ===
    # If GOOGLE_API_KEY is set, use Google AI instead of Vertex AI
    GOOGLE_API_KEY: Optional[str] = None
    USE_GOOGLE_AI: bool = False  # Auto-detected if API key is present
    
    # === Model Configuration ===
    MODEL_NAME_ANSWER: str = "gemini-2.5-pro-preview-05-06"
    MODEL_NAME_JUDGE: str = "gemini-2.5-pro-preview-05-06"

    
    # === Vector Database ===
    VECTOR_DB_PATH: str = str(BASE_DIR / "vector_db")
    EMBEDDING_MODEL: str = "textembedding-gecko@003"
    
    # === Knowledge Base (FOLDER-BASED) ===
    KNOWLEDGE_ROOT: str = str(BASE_DIR / "rag_knowledge")
    KNOWLEDGE_DIR_DB: str = str(BASE_DIR / "rag_knowledge" / "db")
    KNOWLEDGE_DIR_EXAMPLE: str = str(BASE_DIR / "rag_knowledge" / "example")
    KNOWLEDGE_DIR_MCP: str = str(BASE_DIR / "rag_knowledge" / "mcp")
    KNOWLEDGE_DIR_STANDARD: str = str(BASE_DIR / "rag_knowledge" / "standard")
    KNOWLEDGE_INDEX_PATH: str = str(BASE_DIR / "rag_knowledge" / "knowledge_index.json")
    
    # === Trust Log ===
    TRUST_LOG_DIR: str = "./logs/mcp_spec"
    TRUST_LOG_RETENTION_DAYS: int = 90
    
    # === RAG Parameters ===
    MAX_CONTEXT_CHARS: int = 300000
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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


# Global settings instance
settings = Settings()
