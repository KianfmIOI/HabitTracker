from flask import Flask, redirect, render_template, request, url_for
import habits

app = Flask(__name__)

@app.get("/")
def index():
    # Render the home page with the current user, habit rows, and any status message.
    data = habits.load_data()
    message = request.args.get("message")
    error = request.args.get("error")

    return render_template(
        "index.html",
        user=data.get("user"),
        habits= habits.get_habit_rows(data),
        message=message,
        error=error,
    )


@app.post("/set-user")
def set_user_route():
    # Handle user-name form submission and redirect back with success/error text.
    data = habits.load_data()
    ok, text = habits.set_user(data, request.form.get("name", ""))
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/add-habit")
def add_habit_route():
    # Handle add-habit form submission and redirect back with success/error text.
    data = habits.load_data()
    ok, text = habits.add_habit(data, request.form.get("habit_name", ""))
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/check-in/<habit_name>")
def check_in_route(habit_name):
    # Check in a single habit for today, then redirect back with result text.
    data = habits.load_data()
    ok, text = habits.check_in(data, habit_name)
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/delete/<habit_name>")
def delete_route(habit_name):
    # Delete a single habit, then redirect back with result text.
    data = habits.load_data()
    ok, text = habits.delete_habit(data, habit_name)
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/main/<habit_name>")
def toggle_main_route(habit_name):
    # Toggle the selected habit as main, then redirect back with result text.
    data = habits.load_data()
    ok, text = habits.toggle_main_habit(data, habit_name)
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


if __name__ == "__main__":
    # Run the Flask development server when this module is executed directly.
    app.run(debug=True)
