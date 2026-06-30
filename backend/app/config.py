from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DATA_ROOT = Path(os.getenv("DATA_ROOT", PROJECT_ROOT / "data")).resolve()
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", PROJECT_ROOT / "config" / "demo_config.yaml")).resolve()


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}

CONFIG = load_config()

SERVER_HOST = CONFIG.get("server", {}).get("host", "127.0.0.1")
SERVER_PORT = int(CONFIG.get("server", {}).get("port", 8008))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", CONFIG.get("llm", {}).get("base_url", "https://api.deepseek.com"))
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", CONFIG.get("llm", {}).get("model", "deepseek-v4-flash"))
MOCK_LLM_WHEN_NO_KEY = os.getenv("MOCK_LLM_WHEN_NO_KEY", "true").lower() in {"true", "1", "yes"}
