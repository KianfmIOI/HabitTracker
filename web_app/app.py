from flask import Flask, redirect, render_template, request, url_for

from habits import add_habit, check_in, delete_habit, get_habit_rows, load_data, set_user

app = Flask(__name__)


@app.get("/")
def index():
    data = load_data()
    message = request.args.get("message")
    error = request.args.get("error")

    return render_template(
        "index.html",
        user=data.get("user"),
        habits=get_habit_rows(data),
        message=message,
        error=error,
    )


@app.post("/set-user")
def set_user_route():
    data = load_data()
    ok, text = set_user(data, request.form.get("name", ""))
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/add-habit")
def add_habit_route():
    data = load_data()
    ok, text = add_habit(data, request.form.get("habit_name", ""))
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/check-in/<habit_name>")
def check_in_route(habit_name):
    data = load_data()
    ok, text = check_in(data, habit_name)
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


@app.post("/delete/<habit_name>")
def delete_route(habit_name):
    data = load_data()
    ok, text = delete_habit(data, habit_name)
    return redirect(url_for("index", **({"message": text} if ok else {"error": text})))


if __name__ == "__main__":
    app.run(debug=True)
