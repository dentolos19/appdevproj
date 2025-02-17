from datetime import datetime

from flask import flash, json, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from lib import ai, database, storage
from lib.database import sql
from lib.models import Event, EventAttendee, Product, Task, Transaction, User
from main import app
from utils import require_admin


@app.route("/admin")
@app.route("/admin/dashboard")
@require_admin
def admin():
    return render_template("admin/dashboard.html")


@app.route("/admin/events")
@require_admin
def admin_events():
    search = request.args.get("search", "")

    events = (
        sql.session.query(Event).filter(Event.title.ilike(f"%{search}%")).all()
        if search
        else sql.session.query(Event).all()
    )

    return render_template("admin/events.html", events=events, search=search)


@app.route("/admin/events/new", methods=["GET", "POST"])
@require_admin
def admin_events_new():
    if request.method == "POST":
        # Collect data from the form
        event_title = request.form["title"]
        event_description = request.form["description"]
        event_location = request.form["location"]
        event_date = request.form["date"]
        event_image = request.files["image"]

        if event_image and not storage.check_format(event_image, storage.image_extensions):
            flash("Invalid file type! Only images with extensions .png, .jpg, .jpeg, and .gif are allowed.", "danger")
            return redirect(request.url)

        image_url = storage.upload_file(event_image)

        new_event = Event(
            title=event_title,
            description=event_description,
            location=event_location,
            date=event_date,
            image_url=image_url,
        )

        try:
            sql.session.add(new_event)
            sql.session.commit()
            flash("Event added successfully!", "success")
        except Exception as e:
            sql.session.rollback()  # Rollback if there's an error
            flash(f"An error occurred while adding the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events-new.html")


@app.route("/admin/events/<id>", methods=["GET", "POST"])
def admin_events_manage(id):
    # Query the event from the database
    event = sql.session.query(Event).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        event_title = request.form["title"]
        event_description = request.form["description"]
        event_location = request.form["location"]
        event_date = request.form["date"]
        event_image = request.files["image"]

        image_url = event.image_url

        if event_image and not storage.check_format(event_image, storage.image_extensions):
            flash("Invalid file type! Only images with extensions .png, .jpg, .jpeg, and .gif are allowed.", "danger")
            return redirect(request.url)
        elif event_image:
            image_url = storage.upload_file(event_image)

        event.title = event_title
        event.description = event_description
        event.location = event_location
        event.date = event_date
        event.image_url = image_url

        try:
            sql.session.commit()
            flash("Event updated successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while updating the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events-manage.html", event=event)


@app.route("/admin/events/<id>/delete", methods=["GET", "POST"])
def admin_events_delete(id):
    # Query the event from the database
    event = sql.session.query(Event).filter_by(id=id).first()

    if request.method == "POST":
        event_title = request.form["title"]

        if event.title != event_title:
            flash("The event title does not match. Please try again.", "danger")
            return redirect(url_for("admin_events_delete", id=id))

        try:
            sql.session.delete(event)
            sql.session.commit()
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the event: {str(e)}", "danger")

        return redirect(url_for("admin_events"))

    return render_template("admin/events-delete.html", event=event)


@app.route("/admin/users")
@require_admin
def admin_users():
    search = request.args.get("search", "")

    users = (
        sql.session.query(User).filter(User.name.ilike(f"%{search}%")).all()
        if search
        else sql.session.query(User).all()
    )

    return render_template("admin/users.html", users=users, search=search)


@app.route("/admin/users/new", methods=["GET", "POST"])
@require_admin
def admin_users_new():
    if request.method == "POST":
        # Collect data from the form
        user_name = request.form["name"]
        user_email = request.form["email"]
        user_password = request.form["password"]
        user_bio = request.form["bio"]
        user_birthday = request.form["birthday"]

        user_hashed_password = generate_password_hash(user_password, method="pbkdf2:sha1")

        # Update the user object with the new data
        new_user = User(
            name=user_name,
            email=user_email,
            password=user_hashed_password,
            bio=user_bio,
            birthday=user_birthday,
        )

        try:
            # Commit the changes to the database
            sql.session.add(new_user)
            sql.session.commit()
            flash("User created successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while creating the user: {str(e)}", "danger")

        return redirect(url_for("admin_users"))

    return render_template("admin/users-new.html")


@app.route("/admin/users/<id>", methods=["GET", "POST"])
@require_admin
def admin_users_manage(id):
    # Query the user from the database
    user = sql.session.query(User).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        user_name = request.form["name"]
        user_email = request.form["email"]
        user_bio = request.form["bio"]
        user_birthday = request.form["birthday"]

        # Update the user object with the new data
        user.email = user_email
        user.name = user_name
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

    # Query other related data from the database
    attendings = sql.session.query(EventAttendee).filter_by(user_id=id).all()
    transactions = sql.session.query(Transaction).filter_by(user_id=id).all()

    return render_template("admin/users-manage.html", user=user, attendings=attendings, transactions=transactions)


@app.route("/admin/users/<id>/delete", methods=["GET", "POST"])
@require_admin
def admin_users_delete(id):
    # Query the user from the database
    user = sql.session.query(User).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        user_name = request.form["name"]

        if user.name != user_name:
            flash("The name does not match. Please try again.", "danger")
            return redirect(url_for("admin_users_delete", id=id))

        try:
            sql.session.delete(user)
            sql.session.commit()
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the user: {str(e)}", "danger")

        return redirect(url_for("admin_users"))

    return render_template("admin/users-delete.html", user=user)


@app.route("/admin/tasks")
@require_admin
def admin_tasks():
    search = request.args.get("search", "")

    tasks = (
        sql.session.query(Task).filter(Task.name.ilike(f"%{search}%")).all()
        if search
        else sql.session.query(Task).all()
    )

    return render_template("admin/tasks.html", tasks=tasks, search=search)


@app.route("/admin/tasks/new", methods=["GET", "POST"])
@require_admin
def admin_tasks_new():
    if request.method == "POST":
        # Collect data from the form
        name = request.form.get("name")
        description = request.form.get("description")
        criteria = request.form.get("criteria")
        points = request.form.get("points")
        image = request.files.get("image")

        image_url = None

        # Validate form data
        if image:
            if storage.check_format(image, storage.image_extensions):
                image_url = storage.upload_file(image)
            else:
                flash("The file format is not allowed.", "danger")
                return redirect(request.referrer)

        # Create new object
        task = Task(
            name=name,
            description=description,
            criteria=criteria,
            points=points,
            image_url=image_url,
        )

        try:
            # Commit changes to the database
            sql.session.add(task)
            sql.session.commit()
            flash("Task added successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while adding the task! {str(e)}", "danger")

        return redirect(url_for("admin_tasks"))

    return render_template("admin/tasks-new.html")


@app.route("/admin/tasks/<id>", methods=["GET", "POST"])
@require_admin
def admin_tasks_manage(id):
    # Query the task from the database
    task = sql.session.query(Task).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        name = request.form.get("name")
        description = request.form.get("description")
        criteria = request.form.get("criteria")
        points = request.form.get("points")
        image = request.files.get("image")

        image_url = task.image_url

        # Validate form data
        if image:
            if storage.check_format(image, storage.image_extensions):
                image_url = storage.upload_file(image)
            else:
                flash("The file format is not allowed.", "danger")
                return redirect(request.referrer)

        # Update the object with the new data
        task.name = name
        task.description = description
        task.criteria = criteria
        task.points = points
        task.image_url = image_url

        try:
            # Commit changes to the database
            sql.session.commit()
            flash("Task updated successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while updating the task! {str(e)}", "danger")

        return redirect(url_for("admin_tasks"))

    return render_template("admin/tasks-manage.html", task=task)


@app.route("/admin/tasks/<id>/delete", methods=["GET", "POST"])
@require_admin
def admin_tasks_delete(id):
    # Query the task from the database
    task = sql.session.query(Task).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        task_name = request.form["name"]

        # Validate form data
        if task.name != task_name:
            flash("The task name does not match. Please try again.", "danger")
            return redirect(url_for("admin_tasks_delete", id=id))

        try:
            # Commit changes to the database
            sql.session.delete(task)
            sql.session.commit()
            flash("Task deleted successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the task! {str(e)}", "danger")

        return redirect(url_for("admin_tasks"))

    return render_template("admin/tasks-delete.html", task=task)


@app.route("/admin/products")
@require_admin
def admin_products():
    search = request.args.get("search", "")

    products = (
        sql.session.query(Product).filter(Product.name.ilike(f"%{search}%")).all()
        if search
        else sql.session.query(Product).all()
    )

    return render_template("admin/products.html", products=products, search=search)


@app.route("/admin/products/new", methods=["GET", "POST"])
@require_admin
def admin_products_new():
    if request.method == "POST":
        # Collect data from the form
        product_name = request.form["name"]
        product_description = request.form["description"]
        product_points = request.form["points"]
        product_stock = request.form["stock"]
        product_image = request.files["image"]

        image_url = None

        if product_image:
            if storage.check_format(product_image, storage.image_extensions):
                image_url = storage.upload_file(product_image)
            else:
                flash("The file format is not allowed.", "danger")
                return redirect(request.referrer)

        # Create a Product object and save it to the database
        new_product = Product(
            name=product_name,
            description=product_description,
            points=product_points,
            stock=product_stock,
            image_url=image_url,
        )

        try:
            # Add the product to the session and commit it to the database
            sql.session.add(new_product)
            sql.session.commit()
            flash("Product added successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while adding the product: {str(e)}", "danger")

        return redirect(url_for("admin_products"))

    return render_template("admin/products-new.html")


@app.route("/admin/products/<id>", methods=["GET", "POST"])
@require_admin
def admin_products_manage(id):
    # Query the product from the database
    product = sql.session.query(Product).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        product_name = request.form["name"]
        product_description = request.form["description"]
        product_points = request.form["points"]
        product_stock = request.form["stock"]
        product_image = request.files["image"]

        image_url = product.image_url

        if product_image:
            if storage.check_format(product_image, storage.image_extensions):
                image_url = storage.upload_file(product_image)
            else:
                flash("The file format is not allowed.", "danger")
                return redirect(url_for("admin_products_manage", id=id))

        # Update the product object with the new data
        product.name = product_name
        product.description = product_description
        product.points = product_points
        product.stock = product_stock
        product.image_url = image_url

        try:
            # Commit the changes to the database
            sql.session.commit()
            flash("Product updated successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while updating the product: {str(e)}", "danger")

        return redirect(url_for("admin_products"))

    return render_template("admin/products-manage.html", product=product)


@app.route("/admin/products/<id>/delete", methods=["GET", "POST"])
@require_admin
def admin_products_delete(id):
    # Query the product from the database
    product = sql.session.query(Product).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        product_name = request.form["name"]

        if product.name != product_name:
            flash("The product name does not match. Please try again.", "danger")
            return redirect(url_for("admin_products_delete", id=id))

        try:
            sql.session.delete(product)
            sql.session.commit()
            flash("Product deleted successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the product: {str(e)}", "danger")

        return redirect(url_for("admin_products"))

    return render_template("admin/products-delete.html", product=product)


@app.route("/admin/transactions")
@require_admin
def admin_transactions():
    # Query all transactions from the database
    transactions = sql.session.query(Transaction).order_by(Transaction.created_at.desc()).all()

    return render_template("admin/transactions.html", transactions=transactions)


@app.route("/admin/transactions/<id>")
@require_admin
def admin_transactions_view(id):
    # Query the transaction and user from the database
    transaction = sql.session.query(Transaction).filter_by(id=id).first()
    user = sql.session.query(User).filter_by(id=transaction.user_id).first()

    return render_template("admin/transactions-view.html", transaction=transaction, user=user)


@app.route("/admin/transactions/<id>/delete", methods=["GET", "POST"])
@require_admin
def admin_transactions_delete(id):
    # Query the transaction from the database
    transaction = sql.session.query(Transaction).filter_by(id=id).first()

    if request.method == "POST":
        # Collect data from the form
        transaction_id = request.form["id"]

        if transaction.id != int(transaction_id):
            flash("The transaction ID does not match. Please try again.", "danger")
            return redirect(url_for("admin_transactions_delete", id=id))

        try:
            sql.session.delete(transaction)
            sql.session.commit()
            flash("Transaction deleted successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while deleting the transaction: {str(e)}", "danger")

        return redirect(url_for("admin_transactions"))

    return render_template("admin/transactions-delete.html", transaction=transaction)


@app.route("/admin/advanced")
def admin_advanced():
    return render_template("admin/advanced.html")


@app.route("/admin/advanced/database/reset", methods=["POST"])
def admin_advanced_reset_database():
    try:
        database.reset()
        flash("Resetted the database successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while resetting the database! {str(e)}", "danger")

    return redirect(url_for("admin_advanced"))


@app.route("/admin/advanced/database/setup", methods=["POST"])
def admin_advanced_setup_database():
    try:
        database.setup()
        flash("Set up the database successfully!", "success")
    except Exception as e:
        flash(f"An error occurred while setting up the database! {str(e)}", "danger")

    return redirect(url_for("admin_advanced"))


@app.route("/admin/advanced/generate/users", methods=["POST"])
def admin_advanced_generate_users():
    # Collect data from the form
    count = int(request.form["count"])

    # Get prompt
    with open("src/static/prompts/generate-users.txt", "r") as file:
        prompt = file.read().format(count=count, today=datetime.now().strftime("%Y-%m-%d"))

    # Generate response
    response = ai.generate_structured(prompt)
    data = json.loads(response)

    # Parse response
    users = data["users"]
    for user in users:
        user["created_at"] = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%S")

    try:
        # Add the users to the database
        sql.session.bulk_insert_mappings(User, users)
        sql.session.commit()
        flash("Users generated successfully!", "success")
    except Exception as e:
        sql.session.rollback()
        flash(f"An error occurred while generating users! {str(e)}", "danger")

    return redirect(url_for("admin_advanced"))


@app.route("/admin/advanced/generate/transactions", methods=["POST"])
def admin_advanced_generate_transactions():
    pass


@app.route("/admin/advanced/error")
def admin_advanced_error():
    raise Exception("An error occurred while generating transactions! Please try again.")