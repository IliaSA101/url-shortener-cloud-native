from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    postgres_url: str
    redis_url: str
    
    # Говорим Pydantic искать переменные в файле .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Создаем глобальный объект настроек
settings = Settings()