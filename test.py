import json
from datetime import date, datetime

DATA_FILE = "habits.json"
ICE = "🧊"
FIRE = "🔥"

def load_data():
    try:
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return{
            "user" : None,
            "last_date":None,
            "habits":None
        }

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        return json.dump(data, f,indent=2,ensure_ascii=False)

def ensure_name(data):
    if not data["user"]:
        data["user"] = input("who're you?")
        save_data(data)
        print(f"hello ${data["user"]}")
def main():
    ensure_name(DATA_FILE)

if __name__ == "__main__":
    main()
