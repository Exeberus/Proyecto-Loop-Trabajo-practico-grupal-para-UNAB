from backend.extensions import db

from backend.models.conversation import Conversation
from backend.models.message import Message


def create_conversation(user1_id, user2_id):

    existing = Conversation.query.filter(
        (
            (Conversation.user1_id == user1_id) &
            (Conversation.user2_id == user2_id)
        ) |
        (
            (Conversation.user1_id == user2_id) &
            (Conversation.user2_id == user1_id)
        )
    ).first()

    if existing:
        return existing

    conversation = Conversation(
        user1_id=user1_id,
        user2_id=user2_id
    )

    db.session.add(conversation)

    db.session.commit()

    return conversation


def send_message(
    conversation_id,
    sender_id,
    content
):

    message = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content
    )

    db.session.add(message)

    db.session.commit()

    return message


def get_messages(conversation_id):

    return Message.query.filter_by(
        conversation_id=conversation_id
    ).order_by(
        Message.created_at.asc()
    ).all()


def mark_as_read(message_id):

    message = Message.query.get(message_id)

    if not message:
        return None

    message.is_read = True

    db.session.commit()

    return message