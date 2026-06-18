import json
import os

STORAGE_FILE = os.path.join(os.path.dirname(__file__), "xp_data.json")


class XPStorage:

    def __init__(self):
        self.data = self.load()

    def load(self):
        if not os.path.exists(STORAGE_FILE):
            return {"xp": 0, "level": 1}

        with open(STORAGE_FILE, "r") as f:
            return json.load(f)

    def save(self):
        with open(STORAGE_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_xp(self):
        return self.data.get("xp", 0)

    def set_xp(self, xp):
        self.data["xp"] = xp
        self.save()

    def get_level(self):
        return self.data.get("level", 1)

    def set_level(self, level):
        self.data["level"] = level
        self.save()