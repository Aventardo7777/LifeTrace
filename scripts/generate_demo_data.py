"""Generate a realistic demo dataset and seed it into the database.

Usage:
    python scripts/generate_demo_data.py [--days 90] [--reset]

Options:
    --days N     number of days to generate (default 60)
    --reset      wipe existing data before seeding
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the project root importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db  # noqa: E402
from app.seed import seed_demo_data  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed LifeTrace demo data")
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        if args.reset:
            from app.models import DailyRecord

            db.query(DailyRecord).delete()
            db.commit()
        created = seed_demo_data(db, days=args.days)
        print(f"已生成 {created} 条 Demo 数据（目标 {args.days} 天）。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
