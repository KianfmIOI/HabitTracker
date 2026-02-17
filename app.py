import json
from datetime import date, timedelta    

DATA_FILE = "habits.json"
FIRE = "🔥"
ICE = "🧊"

#file
def load_data():
    """Load habits data from JSON"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "user": None,
            "last_date": None,
            "habits": {}
        }

def save_data(data):
    """Save habits data to JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_user(data):
    """Ask for user name on first run."""
    if not data["user"]:
        name = input("What's your name? ").strip()
        data["user"] = name
        save_data(data)
        print(f"It's great to meet you, {name} 🔥")

#habits
def add_habit(data):
    """Add a new habit."""
    name = input("Enter habit name: ").strip().lower()

    if name in data["habits"]:
        print("Habit already exists.")
        return

    today = date.today().isoformat()
    yesterday = today - timedelta(days=1)

    data["habits"][name] = {
        "start_date": today,
        "last_date" :yesterday,
        "history": [],
        "streak": 0,
        "is_main": False
        
    }
    save_data(data)
    print(f"Habit '{name}' added successfully 🔥")


def fill_missed_days(data):
    """Fill missed days with ICE for all habits."""
    if not data["last_date"]:
        return

    last = date.fromisoformat(data["last_date"])
    today = date.today()
    missed = (today - last).days - 1
    if missed > 0:
        for habit in data["habits"].values():
            habit["history"].extend([ICE] * missed)
            habit["streak"] = 0


# ----------------------------
# Check-in logic
# ----------------------------

def check_in(data):
    """Daily check-in for all habits."""
    today = date.today().isoformat()

    if not data["habits"]:
        print("No habits yet. Add one first.")
        return

    fill_missed_days(data)

    habits = list(data["habits"].keys())

    print("\nWhich habits did you complete today?")
    for i, name in enumerate(habits, 1):
        preview = "".join(data["habits"][name]["history"][-7:])
        print(f"{i}) {name.capitalize():10} {preview}")

    raw = input("\nEnter numbers (comma-separated): ")
    completed = {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}

    for i, name in enumerate(habits, 1):
        habit = data["habits"][name]
        if i in completed:
            habit["history"].append(FIRE)
            habit["streak"] += 1
        else:
            habit["history"].append(ICE)
            habit["streak"] = 0

    data["last_date"] = today
    print("\nCheck-in saved 🔥")


# ----------------------------
# Display
# ----------------------------

def show_status(data):
    if not data["habits"]:
        print("no habits history ")
        return
    """Show habit streaks and last 7 days."""
    print("\nYour habits status:\n")

    for name, habit in data["habits"].items():
        last_7 = "".join(habit["history"][-7:])
        streak = habit["streak"]

        if streak >= 7:
            status = "🔥🔥🔥"
        elif streak > 0:
            status = "🔥"
        else:
            status = "🧊"

        print(f"{name.capitalize():10} {last_7:10}  Streak: {streak} {status}")


# ----------------------------
# Main loop
# ----------------------------

def main():
    data = load_data()
    ensure_user(data)

    print(f"\nGreetings, {data['user']} 👋")

    while True:
        print("\nChoose an option:")
        print("0) Add a new habit")
        print("1) Check in today")
        print("2) Show status")
        print("3) Exit")

        choice = input("Your choice: ").strip()

        if choice == "0":
            add_habit(data)
        elif choice == "1":
            check_in(data)
        elif choice == "2":
            show_status(data)
        elif choice == "3":
            save_data(data)
            print("See you tomorrow 🔥")
            break
        else:
            print("Invalid option.")

        save_data(data)


if __name__ == "__main__":
    main()
