import os
from dotenv import load_dotenv

load_dotenv()


def db_path() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./cloud_dashboard.db")
    return url.replace("sqlite:///", "", 1)


def use_mock() -> bool:
    """Mock mode is the default so the app runs with no cloud accounts."""
    return os.getenv("USE_MOCK", "true").lower() == "true"
