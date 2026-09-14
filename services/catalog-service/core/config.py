from typing import Annotated
from enum import StrEnum
from functools import cached_property

from pydantic import Field, PostgresDsn, AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv


class ModelConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv('.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )
    

class EnvironmentEnum(str, StrEnum):
    PRODUCTION = "PRODUCTION"
    TEST = "TEST"
    LOCAL = "LOCAL"
    

class AppSettings(ModelConfig):
    project_name: Annotated[str, Field(..., alias='PROJECT_NAME')]
    environment: EnvironmentEnum = Field(EnvironmentEnum.LOCAL, alias='ENVIRONMENT')


class DbSettings(ModelConfig):
    host: Annotated[str, Field(..., alias='SQL_HOST')]
    port: Annotated[int, Field(..., alias='SQL_PORT')]
    db_name: Annotated[str, Field(..., alias='POSTGRES_DB')]
    user: Annotated[str, Field(..., alias='POSTGRES_USER')]
    password: Annotated[str, Field(..., alias='POSTGRES_PASSWORD')]
    echo: Annotated[bool, Field(..., alias='ECHO')]
    
    @cached_property
    def dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            path=self.db_name,
        )
    

class BrokerSettings(ModelConfig):
    broker_url: Annotated[AmqpDsn, Field(..., alias="BROKER_URL")]  # e.g. amqp://guest:guest@localhost:5672/

    publish_retries: Annotated[int, Field(3, alias="PUBLISH_RETRIES")]
    publish_retry_backoff: Annotated[float, Field(0.5, alias="PUBLISH_RETRY_BACKOFF")]
    

class CorsSettings(ModelConfig):
    cors_origins: Annotated[list[str], Field(
            default=["http://localhost:3000", "http://localhost:8080"],
            alias="CORS_ORIGINS",
        )
    ]
    cors_allow_credentials: Annotated[bool, Field(default=True, alias="CORS_ALLOW_CREDENTIALS")]
    cors_allow_methods: Annotated[list[str], Field(
            default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            alias="CORS_ALLOW_METHODS",
        )
    ]
    cors_allow_headers: Annotated[list[str], Field(default=["*"], alias="CORS_ALLOW_HEADERS")]
    

class Settings(BaseSettings):
    app: AppSettings
    db: DbSettings
    broker: BrokerSettings
    cors: CorsSettings
    

settings = Settings()
