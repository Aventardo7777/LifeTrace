"""LifeTrace launcher.

Run the app with:

    python run.py

Then open http://127.0.0.1:8000 in your browser.
"""

from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
