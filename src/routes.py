from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, Event
from database import session as db_session

from utils import admin_required

from main import app
from models import User


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/admin")
@admin_required
def admin():
    return render_template("admin-dashboard.html")


@app.route("/admin/events", methods=["GET", "POST"])
@admin_required
def admin_events():
    # Query all events from the database
    events = db_session.query(Event).all()

    if request.method == "POST" and request.form.get("delete_event"):
        # Handle deletion of event
        event_id = request.form['delete_event']
        event_to_delete = db_session.query(Event).filter_by(id=event_id).first()

        if event_to_delete:
            try:
                db_session.delete(event_to_delete)
                db_session.commit()
                flash("Event deleted successfully!", 'success')
            except Exception as e:
                db_session.rollback()  # Rollback in case of error
                flash(f"An error occurred while deleting the event: {str(e)}", 'error')

        return redirect(url_for('admin_events'))

    return render_template("admin-events.html", events=events)


@app.route("/admin/add/events", methods=["GET", "POST"])
@admin_required
def add_events():
    if request.method == "POST":
        # Collect data from the form
        event_name = request.form['eventName']
        event_description = request.form['eventDescription']
        event_location = request.form['eventLocation']
        event_date = request.form['eventDate']

        # Create an Event object and save it to the database
        new_event = Event(
            title=event_name,
            description=event_description,
            location=event_location,
            date=event_date
        )

        try:
            # Add the event to the session and commit it to the database
            db_session.add(new_event)
            db_session.commit()
            flash("Event added successfully!", 'success')
        except Exception as e:
            db_session.rollback()  # Rollback if there's an error
            flash(f"An error occurred while adding the event: {str(e)}", 'error')

        return redirect(url_for('admin_events'))
    
    return render_template("add-events.html")


@app.route("/admin/users")
@admin_required
def admin_users():
    return render_template("admin-users.html")


@app.route("/admin/transactions")
@admin_required
def admin_transactions():
    return render_template("admin-transactions.html")


@app.route("/community/messages")
def messaging_page():
    return render_template("messaging.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    # Check if the user is already logged in
    if 'user_id' in session:
        flash("You're already logged in!", 'error')
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Get the user from the database
        user = db_session.query(User).filter_by(email=email).first()

        # Check if user exists and password matches
        if user and check_password_hash(user.password, password):
            # Store user ID in session to keep the user logged in
            session['user_id'] = user.id
            session['user_email'] = user.email  # Store the email in the session


            # Check the email domain
            if user.email.endswith("@mymail.nyp.edu.sg"):
                flash("Admin login successful!", 'success')
                return redirect(url_for("admin"))
            else:
                flash("Login successful!", 'success')
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
        existing_user = (
            db_session.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )

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
            db_session.add(new_user)
            db_session.commit()
            flash("Sign up successful! You can now log in.", "success")
            return redirect("/login")
        except Exception as e:
            db_session.rollback()  # Rollback if there's an error
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()  # Clear all session data
    flash("You've been logged out successfully.", 'success')
    return redirect(url_for("home"))

@app.route("/events")
def events():
    # Query the database for all events
    events = db_session.query(Event).all()

    return render_template("events.html", events=events)