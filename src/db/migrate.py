from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from src.db.database import engine
from src.core.settings import settings


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "schema.sql"
MIGRATIONS_DIR = BASE_DIR / "migrations"


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_dollar_quote = False

    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue

        if "$$" in line:
            quote_count = line.count("$$")
            if quote_count % 2 == 1:
                in_dollar_quote = not in_dollar_quote

        current.append(line)

        if in_dollar_quote:
            continue

        single_quotes = line.count("'") - line.count("\\'")
        if single_quotes % 2 == 1:
            in_single_quote = not in_single_quote

        if not in_single_quote and stripped.endswith(";"):
            statement = "\n".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    trailing = "\n".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def _execute_sql_file(path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)
    if not statements:
        return
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def ensure_database_exists() -> bool:
    target_url = make_url(settings.DATABASE_URL)
    database_name = target_url.database
    if not database_name:
        raise ValueError("DATABASE_URL sem nome de banco.")

    admin_url = target_url.set(database="postgres")
    admin_engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name;"),
                {"name": database_name},
            ).scalar()
            if exists:
                return False
            conn.execute(text(f'CREATE DATABASE "{database_name}"'))
            return True
    finally:
        admin_engine.dispose()


def run_migrations(*, include_schema: bool = False) -> list[str]:
    applied: list[str] = []
    if include_schema and SCHEMA_FILE.exists():
        _execute_sql_file(SCHEMA_FILE)
        applied.append(SCHEMA_FILE.name)

    if MIGRATIONS_DIR.exists():
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            _execute_sql_file(migration_file)
            applied.append(f"migrations/{migration_file.name}")
    return applied


if __name__ == "__main__":
    if "--create-db" in sys.argv:
        created = ensure_database_exists()
        print(f"Database created: {created}")
    applied_files = run_migrations(include_schema="--bootstrap" in sys.argv)
    print("Applied:")
    for item in applied_files:
        print(f"- {item}")
