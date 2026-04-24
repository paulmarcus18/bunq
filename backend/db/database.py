from __future__ import annotations

import sqlite3
from pathlib import Path

from models.schemas import AnalysisResponse


class AnalysisHistoryStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_type TEXT,
                    sender TEXT,
                    recipient_name TEXT,
                    amount REAL,
                    currency TEXT,
                    due_date TEXT,
                    risk_level TEXT,
                    recommended_action TEXT,
                    summary TEXT,
                    confidence REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def save_analysis(self, analysis: AnalysisResponse) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO analysis_history (
                    document_type,
                    sender,
                    recipient_name,
                    amount,
                    currency,
                    due_date,
                    risk_level,
                    recommended_action,
                    summary,
                    confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.document_type.value,
                    analysis.sender,
                    analysis.recipient_name,
                    analysis.amount,
                    analysis.currency,
                    analysis.due_date,
                    analysis.risk_level.value,
                    analysis.recommended_action.value,
                    analysis.summary,
                    analysis.confidence,
                ),
            )
