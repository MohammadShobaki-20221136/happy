"""
Seeds the word_bank table from word_bank_seed.csv (derived from the AFINN-111
open sentiment lexicon: https://github.com/fnielsen/afinn).

Run with:
    python -m app.seed_word_bank
"""
import csv
import os

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import engine
from app.models import word_bank

CSV_PATH = os.path.join(os.path.dirname(__file__), "word_bank_seed.csv")


def load_seed_rows():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "word": r["word"],
                "category": r["category"],
                "weight": int(r["weight"]),
            })
    return rows


def seed_word_bank():
    rows = load_seed_rows()
    if not rows:
        print("No rows found in", CSV_PATH)
        return

    with engine.connect() as conn:
        try:
            # ON CONFLICT DO NOTHING so re-running this is safe and won't
            # error on the unique "word" constraint.
            stmt = pg_insert(word_bank).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=["word"])
            result = conn.execute(stmt)
            conn.commit()
            print(f"Seed complete. Attempted {len(rows)} words, "
                  f"{result.rowcount} newly inserted (rest already existed).")
        except SQLAlchemyError:
            conn.rollback()
            raise


def word_bank_count():
    with engine.connect() as conn:
        try:
            result = conn.execute(select(word_bank))
            return len(result.fetchall())
        except SQLAlchemyError:
            conn.rollback()
            raise


if __name__ == "__main__":
    seed_word_bank()
    print("word_bank now has", word_bank_count(), "rows")