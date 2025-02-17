from flask import redirect, render_template, request, session, url_for
from flask_socketio import join_room
from sqlalchemy import and_, or_

from lib.database import sql
from lib.models import Message, Rooms, User
from lib.socket import io as socketio
from main import app, socket
from utils import require_login


@socketio.on("join")
def on_join(data):
    room = sql.session.query(Rooms).filter(
    or_(
        and_(Rooms.user_1 == session["user_id"], Rooms.user_2 == data.get("receiver_id")),
        and_(Rooms.user_1 == data.get("receiver_id"), Rooms.user_2 == session["user_id"])
    )
    ).first()

    if not room:
        room = Rooms(user_1 = session["user_id"], user_2 = data.get("receiver_id"))

        sql.session.add(room)
        sql.session.commit()
        print(f"created room between {room.user_1} and {room.user_2}")

    join_room(room.id)

    print(f"joined room between {room.user_1} and {room.user_2}")

@app.route("/community/messages")
@app.route("/community/messages/<receiver_id>", methods=["GET", "POST"])
@require_login
def messaging(receiver_id=None):
    user_list = sql.session.query(User).all()

    return render_template(
        "messaging.html",
        users=user_list,
        sender_id=session["user_id"],
        receiver_id=receiver_id,
    )


@socketio.on("send_message")
def handle_send_message(data):
    print("running the send message python function")
    sender_id = session["user_id"]
    receiver_id = data.get("receiver_id")
    message_content = data.get("message")

    if len(message_content) == 0:
        return

    empty = True

    for char in message_content:
        if char != " ":
            empty = False
            break

        if empty:
            return

    # Save the message in the database
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=message_content,
        is_visible=True,
    )
    sql.session.add(message)
    sql.session.commit()

    # Find the room for these users
    room = sql.session.query(Rooms).filter(
        or_(
            and_(Rooms.user_1 == sender_id, Rooms.user_2 == receiver_id),
            and_(Rooms.user_1 == receiver_id, Rooms.user_2 == sender_id)
        )
    ).first()

    if room:
        # Emit to the room instead of individual receiver
        socket.io.emit("receive_message", message.to_dict(), room=room.id)
    else:
        print("No room found for these users")

@app.route("/community/search-results")
@app.route("/community/messages/<receiver_id>", methods=["GET", "POST"])
def search_messages():
    search_query = request.args.get("search_query")
    users = sql.session.query(User).all()
    valid_messages = (
    sql.session.query(Message)
    .filter(Message.is_visible == True)
    .filter(Message.message.like(f"%{search_query}%"))
    .filter(
        or_(
            Message.receiver_id == session["user_id"],
            Message.sender_id == session["user_id"]
        )
    )
    .order_by(Message.created_at)
    .limit(50)
    .all()
)

    return render_template("search-results.html", messages=valid_messages, users = users)

@app.route("/community/messages", methods=["GET"])
def edit_message(id):
    content = request.args.get("new_content")

@app.route("/community/messages/<receiver_id>/<message_id>", methods=["POST"])
def delete_message(receiver_id, message_id):
    print(receiver_id, message_id)

    message = sql.session.query(Message).filter(
        and_(Message.receiver_id == receiver_id, Message.id == message_id)
    ).first()

    if message:
        message.is_visible = False
        sql.session.commit()

    # Get the room before deleting the message
    room = sql.session.query(Rooms).filter(
        or_(
            and_(Rooms.user_1 == message.sender_id, Rooms.user_2 == message.receiver_id),
            and_(Rooms.user_1 == message.receiver_id, Rooms.user_2 == message.sender_id)
        )
    ).first()

    # Emit delete event to the room if found
    if room:
        socket.io.emit("message_deleted", {"message_id": message_id}, room=room.id)

    return redirect(url_for("messaging", receiver_id=receiver_id if receiver_id != session["user_id"] else message.sender_id))


@app.route("/community/messages/deleted")
def deleted_messages():
    messages = sql.session.query(Message).filter(and_(Message.sender_id == session["user_id"], Message.is_visible != True))
    for message in messages:
        print(message.message)
    return render_template("deleted_messages.html", messages = messages)


@app.route("/community/messages/deleted/restore")
def restore_message(methods=["POST"]):
    pass
