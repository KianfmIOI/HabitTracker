from flask import Flask, redirect, render_template, request,make_response, session, url_for,jsonify, abort,flash
from flask_sqlalchemy import SQLAlchemy 
from models import db, User, Habit, CheckIn
from datetime import datetime, date, timedelta
import secrets
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Asadi1385'

db.init_app(app)
with app.app_context():
    db.create_all()

def query_check_ins(habit_id,order='desc'):
    query = CheckIn.query.filter_by(habit_id = habit_id)
    if order == 'desc':
        query = query.order_by(CheckIn.check_in_date.desc())
    else:
        query = query.order_by(CheckIn.check_in_date.asc())
    return query.all()
app.add_template_filter(query_check_ins)

def details_date(dt):
    if not dt:
        return "—"
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt
        
    today = date.today()

    delta = (today - d).days

    if delta == 0:
        return "Today"
    elif delta == 1:
        return "Yesterday"
    elif delta < 7:
        return f"{delta} days ago"
    elif delta < 30:
        weeks = delta // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif delta < 365:
        months = delta // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = delta // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
app.add_template_filter(details_date)

def habit_completion(habit: Habit):
    if not habit.last_check_in_date:
        return 0
    expected = 30 // habit.interval
    if expected == 0:
        expected = 1

    actual_check_ins = len([ci for ci in habit.check_ins if ci.is_done])

    return f"{actual_check_ins}/{expected}"
app.add_template_filter(habit_completion)


def fill_missed_days(habit):
    if habit.is_archived or not habit.last_check_in_date:
        return
    
    today = date.today()
    # if already synced
    if habit.last_sync_date == today:
        return
    
    passed_days = (today - habit.last_check_in_date).days
    if passed_days <= 0:
        return 
    missed_intervals = passed_days // habit.interval
    current_date = habit.last_check_in_date + timedelta(days= habit.interval)

    while current_date < today:
        missed_day = CheckIn(
            habit_id = habit.id,
            check_in_date=current_date, 
            is_done = False
        )
        db.session.add(missed_day)
        current_date += timedelta(days=habit.interval)
    
    habit.last_sync_date = today
    db.session.commit()

@app.get("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
   
    user_habits = []
    archived_habits = []
    if user:
        user_habits = Habit.query.filter_by(user_id = user.id, is_archived = False).order_by(Habit.is_main.desc(),Habit.last_check_in_date.desc(),Habit.creation_date.desc()).all()
        archived_habits = Habit.query.filter_by(user_id = user.id, is_archived = True).order_by(Habit.creation_date.desc()).all()
    
    for habit in user_habits:
        fill_missed_days(habit)

    current_year = date.today().year
    message = request.args.get("message")
    error = request.args.get("error")
    return render_template(
        "index.html",
        user = user,
        habits = user_habits,
        archived_habits = archived_habits,
        current_year=current_year,
        today = date.today(),
        timedelta = timedelta,
        message = message,
        error = error
    )

@app.route("/signup", methods=["GET","POST"])
def signup():
    
    if request.method=="GET":
        return render_template("signup.html")
    
    
    name = request.form.get("name")
    phone = request.form.get("phone_number")
    password = request.form.get("password")
    birth_date_str = request.form.get("birth_date")
    
    if not name:
        flash("Name is required.", "err")
        return redirect (url_for("signup"))
    if not phone:
        flash("Phone is required.", "err")
        return redirect (url_for("signup"))
    if not password:
        flash("password is required.", "err")
        return redirect (url_for("signup"))
    
    if birth_date_str:
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("DOB is formatted wrong.", "err")
            return redirect (url_for("signup"))
    
    existing_number = User.query.filter_by(phone_number = phone).first()
    if existing_number:
            flash("this phone number already exists.", "err")
            return redirect (url_for("signup"))
    
    new_user = User(
        name = name,
        username = name,
        phone_number = phone,
        birth_date = birth_date
    )
    new_user.set_password(password)
    try:
        db.session.add(new_user)
        db.session.commit()
        flash(f"Welcome {name}, please log in", "ok")
        return redirect(url_for("login"))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}.", "err")
        return redirect(url_for("index"))
    
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    phone = request.form.get("phone_number")
    password = request.form.get("password")

    user = User.query.filter_by(phone_number = phone).first()
    
    if not user or not user.check_password(password):
        flash("invalid input or you haven't sign", "err")
        return redirect(url_for("login"))
    
    session["user_id"] = user.id
    flash(f"welcome, {user.username}", "ok")
    return redirect(url_for("index"))

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.post("/habits/new")
def add_habit_route():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    if not user:
        return redirect(url_for("index", error = "sign-in / log-in first"))
    
    habit_name = request.form.get("habit_name", "").strip()
    if not habit_name:
        return redirect(url_for("index", error = "A name is required"))
    
    duplicate_habit = Habit.query.filter_by(user_id = user.id, name = habit_name).first()
    if duplicate_habit:
        return redirect(url_for("index", error = "This habit already exists"))

    habit_interval = int(request.form.get("habit_interval") or 1)
    habit_emoji = request.form.get("habit_emoji").strip() or "🔥"
    habit_color = request.form.get("habit_color", "#85B2FA")

    new_habit = Habit(
        user_id = user.id,
        name = habit_name,
        emoji = habit_emoji,
        interval = habit_interval,
        color= habit_color
    )
    try:
        db.session.add(new_habit)
        db.session.commit()
        return redirect(url_for("index", message = f"Habit {habit_name} added successfully!"))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for("index", error = f"Error: {str(e)}."))

@app.post("/habits/<int:habit_id>/check-in")
def check_in_route(habit_id):
    habit:Habit = Habit.query.get_or_404(habit_id)
    today = date.today()
    note = (request.form.get("note") or "").strip()
    if note == "":
        note = None

    if habit.last_check_in_date is not None:
        gap = (today - habit.last_check_in_date).days
        if gap < habit.interval:
            if not note:
                flash(f"you've already checked-in on {habit.name} ","err")
            else:
                #update the last check in's note
                last_check_in: CheckIn = CheckIn.query.filter_by(habit_id = habit.id, check_in_date = habit.last_check_in_date).first()
                if last_check_in:
                    old_note = last_check_in.note
                    last_check_in.note = note
                    try:
                        db.session.commit()
                        flash(f"updated '{habit.name}'s CheckIn note from '{old_note}' to: '{note}'","ok")
                        return redirect(url_for("index"))
                    except Exception as e:
                        db.session.rollback()
                        flash(f"{str(e)}","err")
                        return redirect(url_for("index"))

            return redirect(url_for("index"))
        elif gap > habit.interval:
            habit.streak = 1
        else:
            habit.streak += 1
    else:
        habit.streak = 1

    if habit.longest_streak < habit.streak:
        habit.longest_streak = habit.streak

    habit.last_check_in_date = today
    
    new_check_in = CheckIn(
        habit_id = habit.id,
        check_in_date = today,
        note = note,
        is_done = True
    )

    try:
        db.session.add(new_check_in)
        db.session.commit()
        flash(f"checked in on {habit.name},streak:{habit.streak}","ok")
        return redirect(url_for("index"))
    except Exception as e:
        db.session.rollback()
        flash(f"{str(e)}","err")
        return redirect(url_for("index"))

@app.get("/habits/<int:habit_id>/details")
def habit_details(habit_id):
    user = User.query.get(session["user_id"])
    if not user:
        abort(403)
    
    habit: Habit = Habit.query.filter_by(id=habit_id,user_id=user.id).first_or_404()
    check_ins = (CheckIn.query.filter_by(habit_id = habit.id).order_by(CheckIn.check_in_date.asc()).all())
    
    check_in_map = {ci.check_in_date: ci.is_done for ci in habit.check_ins}
    today = date.today()
    days = 90
    calendar_days = []
    for i in range (days - 1, -1, -1):
        d = today - timedelta(days=i)
        calendar_days.append({
            "date":d,
            "emoji":habit.emoji,
            "status": "done" if check_in_map.get(d) else "missed" if d in check_in_map else "future" if d > today else "empty"
        })
    return render_template(
        "partials/_habit_details_fragment.html",
        habit = habit,
        check_ins = check_ins,
        calendar_days = calendar_days,
    )

@app.post("/habits/<int:habit_id>/edit")
def edit_habit_route(habit_id):
    habit: Habit = Habit.query.get_or_404(habit_id)

    name = request.form.get("name")
    if name:
        habit.name = name

    habit.emoji = request.form.get("emoji","🔥")
    habit.interval = int(request.form.get("interval", 1))
    habit.color = request.form.get("color", "#85B2FA")

    try:
        db.session.commit()
        flash(f"'{habit.name}' changed successfully","ok")
        return redirect (url_for("index"))
    except Exception as e:
        db.session.rollback()
        flash(f"{str(e)}","err")
        return redirect (url_for("index"))

@app.post("/habits/<int:habit_id>/delete")
def delete_habit_route(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    name = habit.name
    try:
        db.session.delete(habit)
        db.session.commit()
        flash(f"habit {name} deleted successfuly","ok")
        return redirect (url_for("index"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}","err")
        return redirect (url_for("index"))
        
@app.post("/habits/<int:habit_id>/toggle-main")
def toggle_main_route(habit_id):
    try:    
        habit: Habit = Habit.query.get_or_404(habit_id)

        if not habit.is_main:
            Habit.query.filter_by(user_id=habit.user_id, is_main=True).update({"is_main": False})
            habit.is_main = True
            flash(f"{habit.name} is now your main habit", "ok")
        else:
            habit.is_main = False
            flash(f"{habit.name} is no longer your main habit", "ok")
        
        db.session.commit()
        habits = Habit.query.filter_by(user_id=habit.user_id).order_by(Habit.is_main.desc()).all()
        msg = f"{habit.name} is now your main habit" if habit.is_main else f"{habit.name} is no longer your main habit"
        
        habit_list_html = render_template("partials/_habit_list.html", habits=habits)
        flash_html = render_template("partials/_flash_message.html", msg = msg, category="ok")

        return make_response(habit_list_html + flash_html)


        
    except Exception as e:
        db.session.rollback()
        flash(f"error: {e}","err")
        return redirect(url_for('index'))
    
@app.post("/habits/<int:habit_id>/toggle_archive")
def toggle_archive_route(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    habit.is_archived = not habit.is_archived
    if habit.is_archived:
        habit.archive_date = date.today()
    habit.is_main = False
    db.session.commit()
    status = "archived" if habit.is_archived else "unarchived"
    return jsonify({"ok":True,"message": f"Habit {habit.name} is now {status}. "})

@app.post("/habits/<int:habit_id>/note")
def add_note_route(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    today = date.today()

    description = request.form.get("description", "").strip()
    habit.description = description

    try:
        db.session.commit()
        if habit.description:
            flash(f"Note for {habit.name}: {description}.","ok")
            return redirect(url_for("index"))
        else:
            flash(f"No note for {habit.name}.","ok")
            return redirect(url_for("index"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}","err")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
