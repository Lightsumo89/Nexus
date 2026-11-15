from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+pymysql://pickup:pickup@127.0.0.1:3306/pickup?charset=utf8mb4"
    env: str = "dev"
    cookie_secure: bool = False
    session_days: int = 30
    upload_dir: str = "uploads"
    brevo_api_key: str = "api key"
    brevo_sender_email: str = "linkgallagher917@gmail.com"
    brevo_sender_name: str = "Sports Platform"


settings = Settings()
