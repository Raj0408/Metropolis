from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # --- Application Settings ---
    ENVIRONMENT: str = "prod"

    # --- PostgreSQL Database ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # --- Redis Broker ---
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def database_url(self) -> str:
        """Asynchronously compatible database URL."""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()