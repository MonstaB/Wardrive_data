from pathlib import Path

from database.database import Database
from database.scanner import DatabaseScanner

CSV_FILE = Path("logs/warhog_20260811_050206.wigle.csv")

db = Database()
scanner = DatabaseScanner(db)

print("FILE:")
print(CSV_FILE)

print()
print("DETECTED IMPORTER:")

importer = scanner.detect_importer(CSV_FILE)

print(importer)
print(importer.__name__)
print(importer.__module__)

print()
print("TESTING IMPORTER DIRECTLY:")

data = importer(CSV_FILE)

print("SUCCESS")
print("Observations:", len(data["observations"]))

print()
print("First observation:")

for key, value in data["observations"][0].items():
    print(f"{key}: {value}")

db.close()
