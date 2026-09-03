"""Application configuration.

All paths are resolved relative to the project root so the app works
regardless of the current working directory.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root: app/config.py -> app -> project root
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Ensure the data directory always exists.
DATA_DIR.mkdir(parents=True, exist_ok=True)

# The SQLite database lives entirely on the local disk.
DEFAULT_DB_PATH = DATA_DIR / "lifetrace.db"
DATABASE_URL = os.environ.get(
    "LIFETRACE_DB_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
)

# Auto-seed demo data on first run if the database is empty.
AUTO_SEED_DEMO = os.environ.get("LIFETRACE_AUTO_SEED", "1") == "1"
DEMO_DAYS = int(os.environ.get("LIFETRACE_DEMO_DAYS", "60"))

# App metadata.
APP_NAME = "LifeTrace"
APP_SUBTITLE = "Personal Life Data Observatory"
APP_VERSION = "1.0.0"
