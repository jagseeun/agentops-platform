from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


SAFE_DATABASE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def _render_url(url: URL) -> str:
    return url.render_as_string(hide_password=True)


def _assert_safe_test_database_url(test_database_url: str, database_url: str) -> URL:
    test_url = make_url(test_database_url)
    development_url = make_url(database_url)

    if _render_url(test_url) == _render_url(development_url):
        raise RuntimeError("TEST_DATABASE_URL must not be the same as DATABASE_URL")

    if not test_url.database:
        raise RuntimeError("TEST_DATABASE_URL must include a database name")

    if not test_url.database.endswith("_test"):
        raise RuntimeError(
            f"TEST_DATABASE_URL must point to a database ending with _test: {_render_url(test_url)}"
        )

    if not SAFE_DATABASE_NAME_PATTERN.fullmatch(test_url.database):
        raise RuntimeError(
            f"TEST_DATABASE_URL database name contains unsafe characters: {test_url.database}"
        )

    return test_url


def _database_admin_url(test_url: URL) -> URL:
    return test_url.set(database="postgres")


def _database_exists(admin_engine, database_name: str) -> bool:
    with admin_engine.connect() as connection:
        result = connection.execute(
            text("select 1 from pg_database where datname = :database_name"),
            {"database_name": database_name},
        ).scalar()

    return result == 1


def _create_database(admin_engine, database_name: str) -> None:
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))


def _drop_database(admin_engine, database_name: str) -> None:
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(
            text(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :database_name
                  AND pid <> pg_backend_pid()
                """
            ),
            {"database_name": database_name},
        )
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))


def _ensure_test_database(test_url: URL, *, recreate: bool) -> None:
    database_name = test_url.database
    if database_name is None:
        raise RuntimeError("TEST_DATABASE_URL must include a database name")

    admin_engine = create_engine(
        _database_admin_url(test_url),
        connect_args={"connect_timeout":5}
    )
    try:
        if recreate:
            print(f"Recreating test database: {database_name}")
            _drop_database(admin_engine, database_name)
            _create_database(admin_engine, database_name)
            return

        if _database_exists(admin_engine, database_name):
            print(f"Test database already exists: {database_name}")
            return

        print(f"Creating test database: {database_name}")
        _create_database(admin_engine, database_name)
    finally:
        admin_engine.dispose()


def _run_pytest(pytest_args: list[str]) -> int:
    command = [sys.executable, "-m", "pytest", *pytest_args]
    print("Running:", "python -m pytest", " ".join(pytest_args))
    return subprocess.call(command)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the local test database and run pytest.",
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        help="Drop and recreate TEST_DATABASE_URL. Only *_test databases are allowed.",
    )

    args, pytest_args = parser.parse_known_args()

    if settings.test_database_url is None:
        raise RuntimeError("TEST_DATABASE_URL is required")

    test_url = _assert_safe_test_database_url(
        settings.test_database_url,
        settings.database_url,
    )

    try:
        _ensure_test_database(test_url, recreate=args.recreate_db)
    except OperationalError as exc:
        print(
            "Could not connect to Postgres. Start it first with: docker compose up -d postgres",
            file=sys.stderr,
        )
        return 1
    except ProgrammingError as exc:
        raise RuntimeError("Could not prepare the test database") from exc

    return _run_pytest(pytest_args)


if __name__ == "__main__":
    raise SystemExit(main())
