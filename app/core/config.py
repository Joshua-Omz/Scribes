"""
Application configuration management using Pydantic Settings.
Loads environment variables from .env file and provides typed access.
"""

from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic v2 settings management.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="Scribes", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:bbjbbjbbj371419@localhost:5432/scribes_db",
        description="PostgreSQL async connection string"
    )
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    
    # SMTP Configuration
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(default="noreply@scribes.app", description="From email address")
    smtp_from_name: str = Field(default="Scribes App", description="From name")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed origins"
    )
    
    # Security
    password_min_length: int = Field(default=8, description="Minimum password length")
    verification_token_expire_hours: int = Field(default=24, description="Email verification token expiration")
    reset_token_expire_hours: int = Field(default=1, description="Password reset token expiration")
    
    # Pagination
    default_page_size: int = Field(default=20, description="Default pagination page size")
    max_page_size: int = Field(default=100, description="Maximum pagination page size")
    
    # AI/Embeddings (for future use)
    openai_api_key: str = Field(default="", description="OpenAI API key")
    huggingface_api_key: str = Field(
        default="",
        alias="HUGGINGFACE_API_KEY",
        description="Hugging Face API key"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model identifier"
    )
    
    # Redis & Background Tasks
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL for background tasks"
    )
    redis_max_connections: int = Field(default=10, description="Redis connection pool size")
    arq_job_timeout: int = Field(default=3600, description="ARQ job timeout in seconds (1 hour default)")
    arq_max_jobs: int = Field(default=10, description="Maximum concurrent ARQ jobs")
    arq_keep_result: int = Field(default=3600, description="How long to keep job results in seconds")
    
    # AI Assistant Configuration (Phase 6 - RAG with token awareness)
    # Token Budget Breakdown (Total: 2048 tokens):
    # - System prompt:  150 tokens (7%)  - Pastoral instructions & citation rules
    # - User query:     150 tokens (7%)  - User's question
    # - Context:       1200 tokens (59%) - Retrieved sermon chunks (3-4 chunks)
    # - Max output:     400 tokens (20%) - Generated pastoral answer
    # - Safety buffer:  148 tokens (7%)  - Formatting overhead & margin
    
    assistant_model_top_p: float = Field(
        default= 0.9
    )
    assistant_model_repition_penalty: float = Field(
        default= 1.1
    )
    
    assistant_model_temperature: float = Field(
        default=0.2,
        description = "this is the rate of creativity, we need to set this low"

    )
    assistant_model_context_window: int = Field(
        default=2048,
        description="Total context window for generation model (Llama-2/Llama-3.2)"
    )
    assistant_top_k: int = Field(
        default=50,
        description="Number of top chunks to retrieve from vector DB (retrieve many, use best)"
    )
    assistant_max_context_tokens: int = Field(
        default=1200,
        description="Maximum tokens for retrieved sermon context (59% of window, ~900 words)"
    )
    assistant_system_tokens: int = Field(
        default=150,
        description="Reserved for system instructions (pastoral tone, citation rules)"
    )
    assistant_user_query_tokens: int = Field(
        default=150,
        description="Maximum tokens allowed for user query (prevents overflow)"
    )
    assistant_max_output_tokens: int = Field(
        default=400,
        description="Maximum tokens for model output/answer (20% of window)"
    )
    assistant_embedding_dim: int = Field(
        default=384,
        description="Embedding dimension (must match sentence-transformers/all-MiniLM-L6-v2)"
    )
    assistant_chunk_size: int = Field(
        default=384,
        description="Target chunk size in tokens for note chunking (~288 words per chunk)"
    )
    assistant_chunk_overlap: int = Field(
        default=64,
        description="Token overlap between consecutive chunks (preserves context across boundaries)"
    )   
    # Hugging Face Models Configuration
    hf_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Hugging Face embedding model (384-dim)"
    )
    hf_generation_model: str = Field(
        default="meta-llama/Llama-3.2-3B-Instruct",
        description="Hugging Face generation model for assistant. Modern instruction-tuned models (Llama-3.x, Mistral-Instruct) use chat_completion endpoint."
    )
    hf_use_api: bool = Field(
        default=True,
        description="Use Hugging Face Inference API instead of local model"
    )
    hf_api_mode: str = Field(
        default="chat",
        description="API mode: 'chat' for chat_completion (instruction models) or 'text' for text_generation (completion models)"
    )
    hf_generation_temperature: float = Field(
        default=0.2,
        description="Temperature for text generation (lower = more deterministic)"
    )
    hf_generation_timeout: int = Field(
        default=30,
        description="Timeout for generation requests in seconds"
    )
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Convenience instance for imports
settings = get_settings()
