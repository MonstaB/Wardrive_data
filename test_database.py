from database.database import Database
from database.queries import DatabaseQueries
from database.analysis import DatabaseAnalysis


db = Database()
queries = DatabaseQueries(db)
analysis = DatabaseAnalysis(queries)

mac = "14:49:BC:9D:E3:BA"

print("\nACCESS POINT SUMMARY")
summary = analysis.get_access_point_summary(mac)

for key, value in summary.items():
    print(f"{key}: {value}")


print("\nSSID CHANGES")
for change in analysis.get_ssid_changes(mac):
    print(change)


print("\nAUTHENTICATION CHANGES")
for change in analysis.get_auth_changes(mac):
    print(change)


print("\nLOCATION HISTORY")
for location in analysis.get_location_history(mac):
    print(location)


print("\nCHANNEL HISTORY")
for channel in analysis.get_channel_history(mac):
    print(channel)


print("\nRSSI HISTORY")
for rssi in analysis.get_rssi_history(mac):
    print(rssi)


print("\nCAPTURE HISTORY")
for capture in analysis.get_capture_history(mac):
    print(capture)


db.close()

