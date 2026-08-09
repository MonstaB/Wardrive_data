from database.database import Database
from importers.bruce import read_bruce_csv


db = Database()

try:
    result1 = db.import_capture(
        "logs/260808_065121_wardriving.csv",
        read_bruce_csv
    )

    print("File 1:")
    print(result1)

    result2 = db.import_capture(
        "logs/260808_064957_wardriving.csv",
        read_bruce_csv
    )

    print("\nFile 2:")
    print(result2)

    result3 = db.import_capture(
        "logs/260808_065121_wardriving.copy.csv",
        read_bruce_csv
    )

    print("\nFile 3:")
    print(result3)

    # --------------------------------------------------
    # DATABASE COUNTS
    # --------------------------------------------------

    access_points = db.conn.execute(
        "SELECT COUNT(*) FROM access_points"
    ).fetchone()[0]

    observations = db.conn.execute(
        "SELECT COUNT(*) FROM observations"
    ).fetchone()[0]

    captures = db.conn.execute(
        "SELECT COUNT(*) FROM captures"
    ).fetchone()[0]

    print("\nDatabase totals:")
    print(f"Access points: {access_points}")
    print(f"Observations: {observations}")
    print(f"Captures: {captures}")

finally:
    db.close()