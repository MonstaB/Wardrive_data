from database.database import Database

db = Database()

try:
    result = db.import_capture("logs/260808_065121_wardriving.csv")
    print(result)
finally:
    db.close()