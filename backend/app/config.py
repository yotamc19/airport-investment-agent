from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    model_name: str = "claude-sonnet-4-6"
    faa_api_base_url: str = "https://nasstatus.faa.gov/api/airport-status-information"

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
