#!/usr/bin/env python3
"""
filmsim_db.py — SQLite helpers for FilmSimBot

Stores:
- premium status (premium_until UTC)
- daily usage counters

Usage:
    from filmsim_db import FilmSimDB
    db = FilmSimDB("/path/to/filmsim.db")
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Tuple


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today_utc_iso() -> str:
    # Daily limit resets by UTC date.
    # If you prefer local time, change to date.today().isoformat()
    return utc_now().date().isoformat()


@dataclass
class PremiumInfo:
    is_premium: bool
    premium_until: Optional[datetime]


class FilmSimDB:
    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id   INTEGER PRIMARY KEY,
                    premium_until INTEGER  -- unix epoch seconds UTC, nullable
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS usage (
                    telegram_id INTEGER NOT NULL,
                    day         TEXT    NOT NULL,  -- YYYY-MM-DD
                    count       INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (telegram_id, day)
                )
                """
            )
            con.commit()

    # ---------- premium ----------

    def get_premium_info(self, telegram_id: int) -> PremiumInfo:
        with self._connect() as con:
            cur = con.execute(
                "SELECT premium_until FROM users WHERE telegram_id=?",
                (telegram_id,),
            )
            row = cur.fetchone()

        if not row or row[0] is None:
            return PremiumInfo(is_premium=False, premium_until=None)

        premium_until = datetime.fromtimestamp(int(row[0]), tz=timezone.utc)
        return PremiumInfo(is_premium=(premium_until > utc_now()), premium_until=premium_until)

    def is_premium(self, telegram_id: int) -> bool:
        return self.get_premium_info(telegram_id).is_premium

    def set_premium_until(self, telegram_id: int, premium_until: Optional[datetime]) -> None:
        ts = int(premium_until.timestamp()) if premium_until else None
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO users (telegram_id, premium_until)
                VALUES (?, ?)
                ON CONFLICT(telegram_id)
                DO UPDATE SET premium_until=excluded.premium_until
                """,
                (telegram_id, ts),
            )
            con.commit()

    def grant_premium_days(self, telegram_id: int, days: int) -> datetime:
        """
        Adds premium days from the later of (now) or (existing premium_until).
        Returns the new premium_until.
        """
        info = self.get_premium_info(telegram_id)
        base = info.premium_until if info.premium_until and info.premium_until > utc_now() else utc_now()
        new_until = base + timedelta(days=days)
        self.set_premium_until(telegram_id, new_until)
        return new_until

    # ---------- usage ----------

    def get_usage(self, telegram_id: int, day: Optional[str] = None) -> int:
        day = day or today_utc_iso()
        with self._connect() as con:
            cur = con.execute(
                "SELECT count FROM usage WHERE telegram_id=? AND day=?",
                (telegram_id, day),
            )
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def get_usage_today(self, telegram_id: int) -> int:
        return self.get_usage(telegram_id, today_utc_iso())

    def increment_usage(self, telegram_id: int, day: Optional[str] = None, amount: int = 1) -> int:
        """
        Increments usage for the day and returns the new count.
        Call this ONLY after a successful export.
        """
        day = day or today_utc_iso()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO usage (telegram_id, day, count)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id, day)
                DO UPDATE SET count = count + excluded.count
                """,
                (telegram_id, day, amount),
            )
            con.commit()

            cur = con.execute(
                "SELECT count FROM usage WHERE telegram_id=? AND day=?",
                (telegram_id, day),
            )
            row = cur.fetchone()
        return int(row[0]) if row else 0

    def can_process(self, telegram_id: int, free_daily_limit: int) -> Tuple[bool, int, int]:
        """
        Returns: (allowed, used_today, limit)
        Premium => allowed always, limit reported as free_daily_limit for UI consistency.
        """
        used = self.get_usage_today(telegram_id)
        if self.is_premium(telegram_id):
            return True, used, free_daily_limit
        return (used < free_daily_limit), used, free_daily_limit
