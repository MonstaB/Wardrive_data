from database.database import Database

db = Database()

print("Access points:", db.conn.execute(
    "SELECT COUNT(*) FROM access_points"
).fetchone()[0])

print("Observations:", db.conn.execute(
    "SELECT COUNT(*) FROM observations"
).fetchone()[0])

print("Captures:", db.conn.execute(
    "SELECT COUNT(*) FROM captures"
).fetchone()[0])

print("\nAccess points seen more than once:")

rows = db.conn.execute("""
    SELECT
        ap.mac_bssid,
        ap.type,
        COUNT(o.id) AS observations
    FROM access_points ap
    JOIN observations o
        ON o.access_point_id = ap.id
    GROUP BY ap.id
    HAVING COUNT(o.id) > 1
    ORDER BY observations DESC
    LIMIT 20
""").fetchall()

for row in rows:
    print(
        f"{row['mac_bssid']} | "
        f"{row['type']} | "
        f"{row['observations']} observations"
    )

db.close()