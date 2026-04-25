from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    base_api_url: str = "http://192.168.0.50:30181"


settings = Settings()
