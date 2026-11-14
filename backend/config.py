from zoneinfo import ZoneInfo
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    timezone: ZoneInfo = ZoneInfo("Asia/Tokyo")
    verify_token: str
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def tz(self) -> ZoneInfo:
        return self.timezone

@lru_cache
def get_settings() -> Config:
    return Config()

config = get_settings()