import io

import matplotlib
import pandas as pd
import requests
from flask import flash, redirect, render_template, request, send_file, session, url_for

from lib import ai, storage
from lib.database import sql
from lib.enums import TransactionType
from lib.models import Product, Task, Transaction, User
from main import app
from utils import require_login

matplotlib.use("Agg")
import base64

import matplotlib.pyplot as plt


@app.route("/engagement/tasks")
@require_login
def tasks():
    user_id = session.get("user_id")
    user = sql.session.query(User).filter_by(id=user_id).first()
    tasks = sql.session.query(Task).all()

    return render_template("tasks.html", user=user, tasks=tasks)


@app.route("/engagement/tasks/<id>", methods=["GET", "POST"])
@require_login
def tasks_verify(id):
    task = sql.session.query(Task).filter_by(id=id).first()
    user_id = session.get("user_id")
    user = sql.session.query(User).filter_by(id=user_id).first()

    if request.method == "POST":
        # Collect data from the form
        image = request.files.get("image")

        # Validate data provided
        if not image:
            return "No image provided.", 400

        # Save the image to a file
        path = storage.save_file(image)

        # Get prompt
        with open("src/static/prompts/verify.txt", "r") as file:
            prompt = file.read().format(criteria=task.criteria)

        # Perform verification
        result = ai.analyze_image(prompt, path, return_json=True)
        
        print("Verification Result:", result)
        print("Answer: " + str(result["answer"]))
        print("Confidence: " + result["reasoning"])
        
        if result["answer"]:
            # Check if verification is successful
            if not user:
                print("User not found!")  # Debugging
                flash("User not found!", "danger")
                return redirect(url_for("tasks_verify", id=id))

            print("User Object:", user)  # Debugging
            print("Task Points:", task.points)  # Debugging

            task_points = task.points  # Get points from task model
            task_name = task.name      # Get task name from task model

            try:
                user.points += task_points
                sql.session.commit()
                sql.session.refresh(user)  # Ensure changes are applied

                # Log the transaction
                new_transaction = Transaction(
                    user_id=user_id,
                    type=TransactionType.EARNED,
                    amount=task_points,
                    description=f"Points rewarded for verifying task: {task_name}.",
                )
                sql.session.add(new_transaction)
                sql.session.commit()
                sql.session.refresh(user)  # Ensure changes are applied

                print(f"Points updated successfully! User now has {user.points} points.")  # Debugging
                flash(f"Congratulations! You've earned {task_points} points for {task_name}.", "success")

            except Exception as e:
                sql.session.rollback()
                print("Error while processing points:", str(e))  # Debugging
                flash(f"An error occurred while processing points: {str(e)}", "danger")

        return render_template("tasks-verify-status.html", task=task, result=result)

    return render_template("tasks-verify.html", task=task)



@app.route("/engagement/rewards")
@require_login
def rewards():
    user_id = session.get("user_id")
    user = sql.session.query(User).filter_by(id=user_id).first()
    products = sql.session.query(Product).all()
    return render_template("rewards.html", user=user, products=products)


@app.route("/engagement/points")
@require_login
def points():
    user_id = session.get("user_id")
    user = sql.session.query(User).filter_by(id=user_id).first()
    return render_template("points.html", user=user)


@app.route("/engagement/points/add", methods=["POST"])
@require_login
def add_points():
    user_id = session.get("user_id")
    task_points = request.form.get("task_points", type=int)  # Get task points from the form
    task_name = request.form.get("task_name")  # Get task name from the form

    if not task_points or not task_name:
        flash("Invalid task details provided.", "danger")
        return redirect(url_for("rewards"))

    user = sql.session.query(User).filter_by(id=user_id).first()

    if user:
        try:
            user.points += task_points

            # Log the transaction
            new_transaction = Transaction(
                user_id=user_id,
                type=TransactionType.EARNED,
                amount=task_points,
                description=f"Points rewarded to user by completing task {task_name}.",
            )
            sql.session.add(new_transaction)
            sql.session.commit()

            flash(f"Congratulations! You've earned {task_points} points for {task_name}.", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred while processing points: {str(e)}", "danger")
    else:
        flash("User not found!", "danger")

    return redirect(url_for("rewards"))


RECAPTCHA_SECRET_KEY = "6Ldk8skqAAAAAPZgQrYfsfwoOGHQJ5z0q5ZNC4l5"


@app.route("/engagement/redeem", methods=["POST"])
@require_login
def redeem_reward():
    user_id = session.get("user_id")
    reward_name = request.form.get("reward_name")
    reward_cost = int(request.form.get("reward_cost"))

    # Verify reCAPTCHA
    recaptcha_response = request.form.get("g-recaptcha-response")  # Get response from form
    recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"

    payload = {
        "secret": RECAPTCHA_SECRET_KEY,  # Your Google reCAPTCHA secret key
        "response": recaptcha_response,
    }

    response = requests.post(recaptcha_verify_url, data=payload)
    result = response.json()

    if not result.get("success"):
        flash("reCAPTCHA verification failed. Please try again.", "danger")
        return redirect(url_for("rewards"))

    # Fetch the user
    user = sql.session.query(User).filter_by(id=user_id).first()

    if user and user.points >= reward_cost:
        try:
            # Deduct points from user
            user.points -= reward_cost

            # Log the transaction
            new_transaction = Transaction(
                user_id=user_id,
                type=TransactionType.REDEMPTION,
                amount=reward_cost,
                description=f"Points deducted by redeeming reward {reward_name}.",
            )
            sql.session.add(new_transaction)
            sql.session.commit()

            flash(f"Reward '{reward_name}' claimed successfully!", "success")
        except Exception as e:
            sql.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
    else:
        flash("You do not have enough points to claim this reward!", "danger")

    return redirect(url_for("rewards"))


@app.route("/engagement/transactions")
@require_login
def transactions():
    user_id = session.get("user_id")

    # Fetch all transactions for the user
    user_transactions = (
        sql.session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    )

    return render_template("transactions.html", transactions=user_transactions)

#excel file as database
@app.route("/transactions/export")
def export_transactions():
    user_id = session.get("user_id")

    # Fetch user transactions
    user_transactions = (
        sql.session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc()).all()
    )

    if not user_transactions:
        return "No transactions found.", 404

    # Convert transactions to a list of dictionaries
    transactions_data = [
        {
            "Date": transaction.created_at.strftime("%d/%m/%Y"),
            "Description": transaction.description,
            "Points": transaction.amount,
            "Type": transaction.type.value,  # Assuming transaction.type is an Enum
        }
        for transaction in user_transactions
    ]

    # Convert to Pandas DataFrame
    df = pd.DataFrame(transactions_data)

    # Save to an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")

    output.seek(0)

    # Send file as downloadable attachment
    return send_file(
        output,
        as_attachment=True,
        download_name="transactions.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

#dashboard at view transaction page
@app.route("/transactions/dashboard")
def dashboard():
    user_id = session.get("user_id")

    # Fetch user transactions
    transactions = (
        sql.session.query(Transaction)
        .filter_by(user_id=user_id)
        .order_by(Transaction.created_at.asc())  # Ascending order for line graph
        .all()
    )

    # Check if there are transactions
    # has_transactions = bool(transactions)  # True if transactions exist, False if empty
    # If no transactions, just render the message without graphs
    # if not has_transactions:
    # return render_template("dashboard.html", has_transactions=False)
    # Convert transactions to DataFrame

    df = pd.DataFrame(
        [
            {
                "Date": transaction.created_at.strftime("%Y-%m-%d"),
                "Type": transaction.type.value,
                "Amount": transaction.amount,
            }
            for transaction in transactions
        ]
    )

    # Ensure DataFrame is not empty
    if df.empty:
        return "No data available for visualization.", 404

    # Group data for graphs
    daily_points = df.groupby("Date")["Amount"].sum()  # Line Graph
    transaction_counts = df["Type"].value_counts()  # Bar Graph

    # KPI
    total_earned = df[df["Type"] == "earned"]["Amount"].sum()
    total_redeemed = abs(df[df["Type"] == "redemption"]["Amount"].sum())  # Convert to positive
    net_transactions = total_earned - total_redeemed

    # bar graph
    bar_chart = io.BytesIO()
    plt.figure(figsize=(7, 5))
    transaction_counts.plot(kind="bar", color=["green", "red"])
    plt.title("Most Used Transaction Types")
    plt.xlabel("Transaction Type")
    plt.ylabel("Frequency")
    plt.savefig(bar_chart, format="jpeg")
    plt.close()
    bar_chart.seek(0)
    bar_chart_url = base64.b64encode(bar_chart.getvalue()).decode("utf-8")

    # line graph
    line_chart = io.BytesIO()
    plt.figure(figsize=(7, 5))
    daily_points.plot(kind="line", marker="o", color="blue")
    plt.title("Daily Points Usage")
    plt.xlabel("Date")
    plt.ylabel("Points")
    plt.grid(True)
    plt.savefig(line_chart, format="png")
    plt.close()
    line_chart.seek(0)
    line_chart_url = base64.b64encode(line_chart.getvalue()).decode("utf-8")

    return render_template(
        "dashboard.html",
        bar_chart_url=bar_chart_url,
        line_chart_url=line_chart_url,
        total_earned=total_earned,
        total_redeemed=total_redeemed,
        net_transactions=net_transactions,
    )