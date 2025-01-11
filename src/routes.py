import stripe
from flask import flash, redirect, render_template, request, session, url_for
from flask_socketio import join_room
from werkzeug.security import check_password_hash, generate_password_hash

from database import sql
from main import app, socketio
from models import Event, Message, User
from utils import check_admin_status, check_logged_in, require_login


@app.context_processor
def init():
    is_logged_in = check_logged_in()
    is_admin_user = check_admin_status()
    return dict(is_logged_in=is_logged_in, is_admin_user=is_admin_user)


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    # Query the user from the database
    user = sql.session.query(User).filter(User.id == user_id).first()

    if not user:
        return "User not found", 404

    return render_template("profile.html", user=user)


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    user = sql.session.query(User).filter(User.id == user_id).first()

    if request.method == "POST":
        user.email = request.form["email"]
        user.username = request.form["username"]
        user.bio = request.form["bio"]
        user.birthday = request.form["birthday"]

        try:
            sql.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect("/profile")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("edit-profile.html", user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Check if the user is already logged in
    if "user_id" in session:
        flash("You're already logged in!", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Get the user from the database
        user = sql.session.query(User).filter_by(email=email).first()

        # Check if user exists and password matches
        if user and check_password_hash(user.password, password):
            # Store user ID in session to keep the user logged in
            session["user_id"] = user.id
            session["user_email"] = user.email  # Store the email in the session

            # Check the email domain
            if user.email.endswith("@mymail.nyp.edu.sg"):
                flash("Admin login successful!", "success")
                return redirect(url_for("admin"))
            else:
                flash("Login successful!", "success")
                return redirect(url_for("home"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        bio = request.form["bio"]
        birthday = request.form["birthday"]

        # Check if the username or email already exists in the database
        existing_user = sql.session.query(User).filter((User.email == email) | (User.username == username)).first()

        if existing_user:
            flash("Error! Username or email already exists.", "danger")
            return redirect("/signup")

        # Hash the password
        hashed_password = generate_password_hash(password, method="pbkdf2:sha1")

        # Create a new user
        new_user = User(
            email=email,
            username=username,
            password=hashed_password,
            bio=bio,
            birthday=birthday,
        )

        try:
            # Add the new user to the database
            sql.session.add(new_user)
            sql.session.commit()
            flash("Sign up successful! You can now log in.", "success")
            return redirect("/login")
        except Exception as e:
            sql.session.rollback()  # Rollback if there's an error
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()  # Clear all session data
    flash("You've been logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/events")
@require_login
def events():
    # Get filter values from the request
    from_date = request.args.get("fromDate")
    to_date = request.args.get("toDate")
    location = request.args.get("location")

    # Query the database for events based on filter values
    query = sql.session.query(Event)

    if from_date:
        query = query.filter(Event.date >= from_date)
    if to_date:
        query = query.filter(Event.date <= to_date)
    if location:
        query = query.filter(Event.location == location)

    events = query.all()

    return render_template("events.html", events=events)


@app.route("/donation", methods=["GET", "POST"])
@require_login
def donation():
    if request.method == "POST":
        try:
            amount = int(request.form["amount"]) * 100
            if amount < 50:
                return "Donation amount must be at least $0.50.", 400
        except ValueError:
            return "Invalid donation amount.", 400

        stripe_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "sgd",
                        "product_data": {
                            "name": "Donation",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=url_for("donation_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("donation", _external=True),
        )

        return redirect(stripe_session.url, code=303)

    return render_template("donation.html")


@app.route("/donation/success")
@require_login
def donation_success():
    flash("Donation successful! Thank you for your support.", "success")
    return redirect(url_for("donation"))


@app.route("/chat")
@require_login
def chat():
    return render_template("chat.html")


@app.route("/community/messages", methods=["GET", "POST"])
@app.route("/community/messages/<int:receiver_id>", methods=["GET", "POST"])
@require_login
def messaging(receiver_id=None):
    user_list = sql.session.query(User).all()

    if request.method == "POST":
        message_content = request.form.get("message")
        receiver_id = request.form.get("receiver-id")
        sender_id = request.form.get("sender-id")

        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message_content,
            is_read=False,
        )

        sql.session.add(message)
        sql.session.commit()

        # socketio.emit(
        #     "receive_message",
        #     message.to_dict(),
        #     room=receiver_id,
        # )

        return render_template(
            "messaging.html",
            users=user_list,
            sender_id=session["user_id"],
            receiver_id=receiver_id,
        )

    return render_template(
        "messaging.html",
        users=user_list,
        sender_id=session["user_id"],
        receiver_id=receiver_id,
    )


@app.route("/event/details")
def event_info():
    event_id = request.args.get("id")
    event = sql.session.query(Event).filter_by(id=event_id).first()

    return render_template("event-details.html", event=event)


from routing.admin import *


@socketio.on("join")
def on_join(data):
    room = data.get("recipient_id")
    if room:
        join_room(room)


@socketio.on("disconnect")
def on_disconnect():
    pass