import json
from datetime import date, timedelta,datetime

DATA_FILE = "habits.json"
FIRE = "🔥"
ICE = "🧊"

#file
def load_data():
    """Load habits data from JSON"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "user": None,
            "last_check_in_date": None,
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

    data["habits"][name] = {
        "creation_date": today,
        "last_check_in_date" :None,
        "history": [],
        "streak": 0,
        "is_main": False
        
    }
    save_data(data)
    print(f"Habit '{name}' added successfully 🔥")

def delete_habit(data):
    """Delete a habit"""
    if not data["habits"]:
        print("no habits to delete.")
        return
    
    habits = list(data["habits"].keys())
    print("\nSelect a habit to delete:")
    for i,name in enumerate(habits,1):
        print(f"{i}) {name}")

    try:
        choice = int(input("enter number:").strip())
        if 1 <= choice <= len(habits):
            name = habits[choice - 1]
            del data["habits"][name]
            save_data(data)
            print(f"habit {name} deleted")
        else:
            print("invalid choice")
            return
    except ValueError:
        print("please enter a valid number")
        return
# ----------------------------
# Check-in logic
# ----------------------------
    
def check_in(data):
    #data means database
    """Daily check-in for selected habit."""
    today = date.today().isoformat()

    #if no habits in data
    if not data["habits"]:
        print("No habits yet. Add one first.")
        return

    habits = list(data["habits"].keys())

    while True:
        print("\nWhich habit did you complete today?")
        print("\n0) Return to main menu")

        for i, name in enumerate(habits, 1):
            habit = data["habits"][name]
            preview = "".join(habit["history"][-7:])
            created = datetime.fromisoformat(habit["creation_date"]).strftime("%d %b")

            last_check = datetime.fromisoformat(habit["last_check_in_date"]).strftime("%d %b")
            if last_check is None:
                last_check = "---"

            print(f"{i}) {name.title():15} Created: {created} | Last: {last_check} | {preview:7}")

        try:
            choice = int(input("\n select a habit or 0 to exit: \n"))
            
            # if user wants to exit
            if choice == 0:
                return
            if 1 <= choice <= len(habits):
                selected_habit_name = habits[choice-1]
                selected_habit = data["habits"][selected_habit_name]

                # if we've checked in today
                if selected_habit["last_check_in_date"] == today:
                    print("You already checked in today 🔥")
                    continue
                # if new habit
                elif selected_habit["last_check_in_date"] is None:
                    selected_habit["last_check_in_date"] = today
                    selected_habit["history"].append(FIRE)
                    selected_habit["streak"] += 1
                    print(f"\n habit {selected_habit_name} checked in{FIRE}")

                # if old habit
                else:
                    fill_missed_days(selected_habit)
                    break_streak(selected_habit)
                    selected_habit["history"].append(FIRE)
                    selected_habit["streak"] += 1
                    selected_habit["last_check_in_date"] = today
                    print(f"\n habit {selected_habit_name} checked in{FIRE}")

                preview = selected_habit["history"][-7:]
                print(f"\n{selected_habit_name} streak: {selected_habit['streak']} days")
                print(preview)
                save_data(data)

            
            # not a number in the list
            else:
                print(f"please enter a number between 0 and {len(habits)}")

        except ValueError:
            print("Invalid input, please enter a valid number")

def fill_missed_days(habit):
    """Fill missed days with ICE for selected habits."""

    last = date.fromisoformat(habit["last_check_in_date"])
    today = date.today()
    
    missed = (today - last).days - 1
    if missed > 0:
        habit["history"].extend([ICE] * missed)

def break_streak(habit):
    if habit["last_check_in_date"] is None:
        return
    if habit["history"][-1] == ICE:
        habit["streak"] = 0
      
# ----------------------------
# Display
# ----------------------------

def show_status(data):
    """Show habit streaks and last 7 days."""
    if not data["habits"]:
        print("no habits available ")
        return
    
    print("\nYour habits status:\n")

    for name, habit in data["habits"].items():
        last_7 = "".join(habit["history"][-7:])
        created = datetime.fromisoformat(habit["creation_date"]).strftime("%d %b")
        
        if habit["last_check_in_date"] is None:
            last_check = "—"
        else:
            last_check = datetime.fromisoformat(
                habit["last_check_in_date"]
            ).strftime("%d %b")

        streak = habit["streak"]

        print(f"{name.title():10} Created: {created} | Last: {last_check} | Streak: {streak} | {last_7:10} ")


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
        print("2) delete a habit")
        print("3) Show status")
        print("4) Exit")

        choice = input("Your choice: ").strip()

        if choice == "0":
            add_habit(data)
        elif choice == "1":
            check_in(data)
        elif choice == "2":
            delete_habit(data)
        elif choice == "3":
            show_status(data)
        elif choice == "4":
            save_data(data)
            print("See you tomorrow 🔥")
            break
        else:
            print("Invalid option.")

        save_data(data)


if __name__ == "__main__":
    main()
