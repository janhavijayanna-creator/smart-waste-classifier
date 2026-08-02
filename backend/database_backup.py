import json
import sqlite3
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "backend"
    / "waste_classifier.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                confidence REAL NOT NULL,
                recommendation TEXT NOT NULL,
                top_predictions TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def save_prediction(
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
                file_name,
                predicted_class,
                confidence,
                recommendation,
                top_predictions,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
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


def get_prediction_history():
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
            ORDER BY id DESC
            """
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

def get_statistics():
    connection = get_connection()

    try:
        valid_classes = [
            "broken_toys",
            "cardboard",
            "glass",
            "human",
            "metal",
            "paper",
            "plastic",
            "trash",
        ]

        total_scans = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM predictions
            """
        ).fetchone()["total"]

        class_rows = connection.execute(
            """
            SELECT
                predicted_class,
                COUNT(*) AS count
            FROM predictions
            WHERE predicted_class != 'uncertain'
            GROUP BY predicted_class
            ORDER BY count DESC
            """
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
            WHERE predicted_class = 'uncertain'
            """
        ).fetchone()["total"]

        average_confidence_row = connection.execute(
            """
            SELECT AVG(confidence) AS average
            FROM predictions
            """
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


def delete_prediction(prediction_id: int):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM predictions
            WHERE id = ?
            """,
            (prediction_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


def clear_prediction_history():
    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM predictions
            """
        )

        connection.commit()

    finally:
        connection.close()