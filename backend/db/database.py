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
                    issuer_name TEXT,
                    beneficiary_name TEXT,
                    beneficiary_iban TEXT,
                    amount REAL,
                    currency TEXT,
                    due_date TEXT,
                    payment_reference TEXT,
                    manual_payment_required INTEGER,
                    auto_debit_detected INTEGER,
                    recommended_action TEXT,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._ensure_columns(connection)

    def _ensure_columns(self, connection: sqlite3.Connection) -> None:
        existing_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(analysis_history)").fetchall()
        }
        required_columns = {
            "issuer_name": "TEXT",
            "beneficiary_name": "TEXT",
            "beneficiary_iban": "TEXT",
            "payment_reference": "TEXT",
            "manual_payment_required": "INTEGER DEFAULT 0",
            "auto_debit_detected": "INTEGER DEFAULT 0",
        }
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE analysis_history ADD COLUMN {column_name} {column_type}"
                )

    def save_analysis(self, analysis: AnalysisResponse) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO analysis_history (
                    document_type,
                    issuer_name,
                    beneficiary_name,
                    beneficiary_iban,
                    amount,
                    currency,
                    due_date,
                    payment_reference,
                    manual_payment_required,
                    auto_debit_detected,
                    recommended_action,
                    summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.document_type.value,
                    analysis.issuer_name,
                    analysis.beneficiary_name,
                    analysis.beneficiary_iban,
                    analysis.amount,
                    analysis.currency,
                    analysis.due_date,
                    analysis.payment_reference,
                    int(analysis.manual_payment_required),
                    int(analysis.auto_debit_detected),
                    analysis.recommended_action.value,
                    analysis.summary,
                ),
            )
