import hashlib
import json
import secrets
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_FOLDER = Path(
    os.environ.get(
        "DATA_DIRECTORY",
        PROJECT_ROOT / "backend"
    )
)

DATABASE_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = (
    DATABASE_FOLDER
    / "waste_classifier.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def initialize_database():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_name TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                confidence REAL NOT NULL,
                recommendation TEXT NOT NULL,
                top_predictions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        columns = connection.execute(
            "PRAGMA table_info(predictions)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "user_id" not in column_names:
            connection.execute(
                """
                ALTER TABLE predictions
                ADD COLUMN user_id INTEGER
                """
            )

        connection.commit()

    finally:
        connection.close()


def create_user(
    name: str,
    email: str,
    password: str
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                hash_password(password),
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            )
        )

        connection.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError as error:
        raise ValueError(
            "An account with this email already exists."
        ) from error

    finally:
        connection.close()


def authenticate_user(
    email: str,
    password: str
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash
            FROM users
            WHERE email = ?
            """,
            (
                email.strip().lower(),
            )
        ).fetchone()

        if row is None:
            return None

        if row["password_hash"] != hash_password(password):
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
        }

    finally:
        connection.close()


def create_session(user_id: int):
    connection = get_connection()

    try:
        token = secrets.token_urlsafe(32)

        expires_at = (
            datetime.now()
            + timedelta(days=7)
        ).isoformat(
            timespec="seconds"
        )

        connection.execute(
            """
            INSERT INTO sessions (
                token,
                user_id,
                expires_at,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                token,
                user_id,
                expires_at,
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            )
        )

        connection.commit()

        return token

    finally:
        connection.close()


def get_user_by_token(token: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                users.id,
                users.name,
                users.email,
                sessions.expires_at
            FROM sessions
            JOIN users
                ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,)
        ).fetchone()

        if row is None:
            return None

        expires_at = datetime.fromisoformat(
            row["expires_at"]
        )

        if expires_at < datetime.now():
            connection.execute(
                """
                DELETE FROM sessions
                WHERE token = ?
                """,
                (token,)
            )

            connection.commit()

            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
        }

    finally:
        connection.close()


def delete_session(token: str):
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM sessions
            WHERE token = ?
            """,
            (token,)
        )

        connection.commit()

    finally:
        connection.close()


def save_prediction(
    user_id: int,
    file_name: str,
    predicted_class: str,
    confidence: float,
    recommendation: str,
    top_predictions: list
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO predictions (
                user_id,
                file_name,
                predicted_class,
                confidence,
                recommendation,
                top_predictions,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file_name,
                predicted_class,
                confidence,
                recommendation,
                json.dumps(top_predictions),
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            )
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


def get_prediction_history(user_id: int):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                file_name,
                predicted_class,
                confidence,
                recommendation,
                top_predictions,
                created_at
            FROM predictions
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()

        history = []

        for row in rows:
            history.append(
                {
                    "id": row["id"],
                    "file_name": row["file_name"],
                    "predicted_class": row[
                        "predicted_class"
                    ],
                    "confidence": row["confidence"],
                    "recommendation": row[
                        "recommendation"
                    ],
                    "top_predictions": json.loads(
                        row["top_predictions"]
                    ),
                    "created_at": row["created_at"],
                }
            )

        return history

    finally:
        connection.close()


def get_statistics(user_id: int):
    connection = get_connection()

    try:
        [
    "broken_toys",
    "cardboard",
    "e_waste",
    "glass",
    "metal",
    "organic",
    "paper",
    "plastic",
]

        total_scans = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM predictions
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()["total"]

        class_rows = connection.execute(
            """
            SELECT
                predicted_class,
                COUNT(*) AS count
            FROM predictions
            WHERE
                user_id = ?
                AND predicted_class != 'uncertain'
            GROUP BY predicted_class
            ORDER BY count DESC
            """,
            (user_id,)
        ).fetchall()

        class_counts = {
            class_name: 0
            for class_name in valid_classes
        }

        for row in class_rows:
            predicted_class = row["predicted_class"]

            if predicted_class in class_counts:
                class_counts[predicted_class] = row["count"]

        most_detected_class = None

        if class_rows:
            most_detected_class = class_rows[0][
                "predicted_class"
            ]

        uncertain_count = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM predictions
            WHERE
                user_id = ?
                AND predicted_class = 'uncertain'
            """,
            (user_id,)
        ).fetchone()["total"]

        average_confidence_row = connection.execute(
            """
            SELECT AVG(confidence) AS average
            FROM predictions
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        average_confidence = (
            average_confidence_row["average"] or 0
        )

        return {
            "total_scans": total_scans,
            "most_detected_class": most_detected_class,
            "average_confidence": round(
                average_confidence,
                2
            ),
            "class_counts": class_counts,
            "waste_categories": len(valid_classes),
            "uncertain_count": uncertain_count,
        }

    finally:
        connection.close()


def delete_prediction(
    user_id: int,
    prediction_id: int
):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM predictions
            WHERE
                id = ?
                AND user_id = ?
            """,
            (
                prediction_id,
                user_id,
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def clear_prediction_history(user_id: int):
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM predictions
            WHERE user_id = ?
            """,
            (user_id,)
        )

        connection.commit()

    finally:
        connection.close()