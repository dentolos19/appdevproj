from flask import flash, redirect, render_template, request, url_for

from database import sql
from main import app
from models import Event, Transaction, User
from utils import require_admin


@app.route("/admin")
@app.route("/admin/dashboard")
@require_admin
def admin():
    return render_template("admin/dashboard.html")


@app.route("/admin/events", methods=["GET", "POST"])
@require_admin
def admin_events():
    # Query all events from the database
    events = sql.session.query(Event).all()

    if request.method == "POST" and request.form.get("delete_event"):
        # Handle deletion of event
        event_id = request.form["delete_event"]
        event_to_delete = sql.session.query(Event).filter_by(id=event_id).first()

        if event_to_delete:
            try:
                sql.session.delete(event_to_delete)
                sql.session.commit()
                flash("Event deleted successfully!", "success")
            except Exception as e:
                sql.session.rollback()  # Rollback in case of error
                flash(f"An error occurred while deleting the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events.html", events=events)


@app.route("/admin/events/new", methods=["GET", "POST"])
@require_admin
def admin_events_new():
    if request.method == "POST":
        # Collect data from the form
        event_title = request.form["title"]
        event_description = request.form["description"]
        event_location = request.form["location"]
        event_date = request.form["date"]

        # Create an Event object and save it to the database
        new_event = Event(
            title=event_title,
            description=event_description,
            location=event_location,
            date=event_date,
        )

        try:
            # Add the event to the session and commit it to the database
            sql.session.add(new_event)
            sql.session.commit()
            flash("Event added successfully!", "success")
        except Exception as e:
            sql.session.rollback()  # Rollback if there's an error
            flash(f"An error occurred while adding the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events-new.html")


@app.route("/admin/events/<int:id>", methods=["GET", "POST"])
def admin_events_edit(id):
    # Query the event from the database
    event = sql.session.query(Event).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        event_title = request.form["title"]
        event_description = request.form["description"]
        event_location = request.form["location"]
        event_date = request.form["date"]

        # Update the event object with the new data
        event.title = event_title
        event.description = event_description
        event.location = event_location
        event.date = event_date

        try:
            # Commit the changes to the database
            sql.session.commit()
            flash("Event updated successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while updating the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events-edit.html", event=event)


@app.route("/admin/events/<int:id>/delete", methods=["GET", "POST"])
def admin_events_delete(id):
    # Query the event from the database
    event = sql.session.query(Event).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        event_title = request.form["title"]

        if event.title != event_title:
            flash("The event title does not match. Please try again.", "danger")
            return redirect(url_for("admin_events_delete", id=id))

        try:
            sql.session.delete(event)
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events-delete.html", event=event)


@app.route("/admin/users")
@require_admin
def admin_users():
    # Query all events from the database
    users = sql.session.query(User).all()

    return render_template("admin/users.html", users=users)


@app.route("/admin/users/<int:id>", methods=["GET", "POST"])
@require_admin
def admin_users_edit(id):
    # Query the user from the database
    user = sql.session.query(User).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        user_username = request.form["username"]
        user_email = request.form["email"]
        user_bio = request.form["bio"]
        user_birthday = request.form["birthday"]

        # Update the user object with the new data
        user.email = user_email
        user.username = user_username
        user.bio = user_bio
        user.birthday = user_birthday

        try:
            # Commit the changes to the database
            sql.session.commit()
            flash("User updated successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while updating the user: {str(e)}", "danger")

        return redirect(url_for("admin_users"))

    return render_template("admin/users-edit.html", user=user)


@app.route("/admin/users/<int:id>/delete", methods=["GET", "POST"])
@require_admin
def admin_users_delete(id):
    # Query the user from the database
    user = sql.session.query(User).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        user_username = request.form["username"]

        if user.username != user_username:
            flash("The username does not match. Please try again.", "danger")
            return redirect(url_for("admin_users_delete", id=id))

        try:
            sql.session.delete(user)
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the user: {str(e)}", "danger")

        return redirect(url_for("admin_users"))

    return render_template("admin/users-delete.html", user=user)


@app.route("/admin/transactions")
@require_admin
def admin_transactions():
    # Query all transactions from the database
    transactions = sql.session.query(Transaction).all()

    return render_template("admin/transactions.html", transactions=transactions)