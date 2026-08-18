from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Offline Pharma Distribution"
    # .env.example and the docs both set APP_ENV; alias this field so
    # that variable actually reaches settings.environment (previously
    # pydantic-settings looked for ENVIRONMENT and silently ignored
    # APP_ENV, so switching APP_ENV=production did nothing).
    environment: str = Field(default="development", validation_alias="APP_ENV")

    # NOTE: names below are UPPERCASE to match settings.X usage in
    # app/api/auth.py and app/core/security.py, and to match the
    # variable names documented in .env.example. database_url stays
    # lowercase to match app/core/database.py.
    database_url: str = "sqlite:///./pharma.db"

    JWT_SECRET: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 30

    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    backup_key: str = "change-me"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def validate_production_secrets(self) -> None:
        """Refuse to run with placeholder secrets outside development."""
        if self.environment.lower() != "development":
            insecure_defaults = {
                "JWT_SECRET": "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET",
                "backup_key": "change-me",
            }
            for field, placeholder in insecure_defaults.items():
                if getattr(self, field) == placeholder:
                    raise RuntimeError(
                        f"Refusing to start: {field} is still set to its placeholder "
                        f"value. Set a real secret via the environment or .env file "
                        f"before running with APP_ENV != development."
                    )


settings = Settings()
