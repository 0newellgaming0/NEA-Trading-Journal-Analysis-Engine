# database.py
import csv
import os


# =========================
# LOAD CSV
# =========================
def load_csv(path, fieldnames):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# =========================
# SAVE CSV (FULL REWRITE)
# =========================
def save_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in rows:
            clean = {k: ("" if v is None else v) for k, v in r.items()}
            writer.writerow(clean)


# =========================
# APPEND ROW
# =========================
def append_csv(path, fieldnames, row):
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({k: ("" if v is None else v) for k, v in row.items()})


# =========================
# DELETE BY KEY
# =========================
def delete_by_key(path, fieldnames, key_field, key_value):
    rows = load_csv(path, fieldnames)
    filtered = [r for r in rows if r.get(key_field) != key_value]
    save_csv(path, fieldnames, filtered)
    return filtered