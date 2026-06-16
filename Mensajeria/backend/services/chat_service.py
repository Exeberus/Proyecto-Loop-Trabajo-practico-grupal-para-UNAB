import sqlite3
from database import get_db
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_PATH = os.path.join(
    BASE_DIR,
    "database.db"
)


def get_db():

    return sqlite3.connect(DB_PATH)


def create_conversation(
    user1_id,
    user2_id
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM conversations
        WHERE
        (
            user1_id = ?
            AND user2_id = ?
        )
        OR
        (
            user1_id = ?
            AND user2_id = ?
        )
        """,
        (
            user1_id,
            user2_id,
            user2_id,
            user1_id
        )
    )

    existing = cursor.fetchone()

    if existing:

        conn.close()

        return {
            "id": existing[0]
        }

    cursor.execute(
        """
        INSERT INTO conversations
        (
            user1_id,
            user2_id
        )
        VALUES
        (
            ?,
            ?
        )
        """,
        (
            user1_id,
            user2_id
        )
    )

    conn.commit()

    conversation_id = cursor.lastrowid

    conn.close()

    return {
        "id": conversation_id
    }


def send_message(
    conversation_id,
    sender_id,
    content
):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (
            conversation_id,
            sender_id,
            content
        )
        VALUES
        (
            ?,
            ?,
            ?
        )
        """,
        (
            conversation_id,
            sender_id,
            content
        )
    )

    conn.commit()

    message_id = cursor.lastrowid

    conn.close()

    return {
        "id": message_id
    }


def get_messages(
    conversation_id
):

    conn = get_db()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (
            conversation_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    messages = []

    for row in rows:

        messages.append({
            "id": row["id"],
            "conversation_id": row["conversation_id"],
            "sender_id": row["sender_id"],
            "content": row["content"],
            "is_read": bool(row["is_read"]),
            "created_at": row["created_at"]
        })

    return messages


def mark_as_read(
    message_id
):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE messages
        SET is_read = 1
        WHERE id = ?
        """,
        (
            message_id,
        )
    )

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated > 0