from flask import Blueprint
from flask import request

from backend.services.chat_service import (
    create_conversation,
    send_message,
    get_messages,
    mark_as_read
)

chat_bp = Blueprint(
    "chat",
    __name__
)


@chat_bp.route(
    "/conversation",
    methods=["POST"]
)
def create_conversation_route():

    data = request.get_json()

    conversation = create_conversation(
        data["user1_id"],
        data["user2_id"]
    )

    return {
        "conversation_id":
        conversation["id"]
    }, 201


@chat_bp.route(
    "/message",
    methods=["POST"]
)
def send_message_route():

    data = request.get_json()

    message = send_message(
        data["conversation_id"],
        data["sender_id"],
        data["content"]
    )

    return {
        "message_id":
        message["id"]
    }, 201


@chat_bp.route(
    "/conversation/<int:id>",
    methods=["GET"]
)
def get_messages_route(id):

    messages = get_messages(id)

    return messages


@chat_bp.route(
    "/message/read/<int:id>",
    methods=["PUT"]
)
def read_message(id):

    updated = mark_as_read(id)

    if not updated:
        return {
            "error": "Mensaje no encontrado"
        }, 404

    return {
        "message": "Leído"
    }