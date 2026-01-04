"""
Configuration management for DHCS BHT Multi-Agent System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    openai_api_key: str
    agent_model: str = "gpt-4o-mini"
    agent_temperature: float = 0.7
    agent_max_iterations: int = 5

    # Pinot Configuration
    pinot_broker_url: str = "http://localhost:8099"
    pinot_table_name: str = "dhcs_crisis_intake"

    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_topic: str = "dhcs_crisis_intake"

    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_data"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
