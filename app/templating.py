"""Shared Jinja2 templates instance."""

from __future__ import annotations

from fastapi.templating import Jinja2Templates

from .config import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
