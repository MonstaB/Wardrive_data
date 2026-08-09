# analysis.py

class DatabaseAnalysis:

    def __init__(self, queries):
        self.queries = queries

    # --------------------------------------------------
    # ACCESS POINT
    # --------------------------------------------------

    def get_access_point_summary(self, mac_bssid):
        access_point = self.queries.get_access_point(mac_bssid)

        if access_point is None:
            return None

        observations = self.queries.get_access_point_observations(mac_bssid)
        ssid_history = self.queries.get_ssid_history(mac_bssid)
        auth_history = self.queries.get_auth_history(mac_bssid)

        return {
            "access_point": dict(access_point),
            "observation_count": len(observations),
            "first_seen": observations[0]["observed_at"] if observations else None,
            "last_seen": observations[-1]["observed_at"] if observations else None,
            "ssids": [row["ssid"] for row in ssid_history],
            "auth_modes": [row["auth_mode"] for row in auth_history],
            "ssid_changed": len(ssid_history) > 1,
            "auth_changed": len(auth_history) > 1
        }

    # --------------------------------------------------
    # SSID CHANGED?
    # --------------------------------------------------

    def has_ssid_changed(self, mac_bssid):
        history = self.queries.get_ssid_history(mac_bssid)

        return len(history) > 1

    # --------------------------------------------------
    # AUTHENTICATION CHANGED?
    # --------------------------------------------------

    def has_auth_changed(self, mac_bssid):
        history = self.queries.get_auth_history(mac_bssid)

        return len(history) > 1

    # --------------------------------------------------
    # SSID HISTORY
    # --------------------------------------------------

    def get_ssid_changes(self, mac_bssid):
        history = self.queries.get_ssid_history(mac_bssid)

        if len(history) <= 1:
            return []

        changes = []

        previous = history[0]["ssid"]

        for row in history[1:]:
            current = row["ssid"]

            if current != previous:
                changes.append({
                    "old_ssid": previous,
                    "new_ssid": current,
                    "changed_at": row["first_seen"]
                })

            previous = current

        return changes

    # --------------------------------------------------
    # AUTHENTICATION HISTORY
    # --------------------------------------------------

    def get_auth_changes(self, mac_bssid):
        history = self.queries.get_auth_history(mac_bssid)

        if len(history) <= 1:
            return []

        changes = []

        previous = history[0]["auth_mode"]

        for row in history[1:]:
            current = row["auth_mode"]

            if current != previous:
                changes.append({
                    "old_auth": previous,
                    "new_auth": current,
                    "changed_at": row["first_seen"]
                })

            previous = current

        return changes

    # --------------------------------------------------
    # LOCATION HISTORY
    # --------------------------------------------------

    def get_location_history(self, mac_bssid):
        observations = self.queries.get_access_point_observations(mac_bssid)

        return [
            {
                "observed_at": row["observed_at"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "altitude": row["altitude"],
                "accuracy": row["accuracy"]
            }
            for row in observations
            if row["latitude"] is not None
               and row["longitude"] is not None
        ]

    # --------------------------------------------------
    # CHANNEL HISTORY
    # --------------------------------------------------

    def get_channel_history(self, mac_bssid):
        observations = self.queries.get_access_point_observations(mac_bssid)

        channels = []

        for row in observations:
            if row["channel"] is not None:
                channels.append({
                    "channel": row["channel"],
                    "frequency": row["frequency"],
                    "observed_at": row["observed_at"]
                })

        return channels

    # --------------------------------------------------
    # RSSI HISTORY
    # --------------------------------------------------

    def get_rssi_history(self, mac_bssid):
        observations = self.queries.get_access_point_observations(mac_bssid)

        return [
            {
                "rssi": row["rssi"],
                "observed_at": row["observed_at"]
            }
            for row in observations
            if row["rssi"] is not None
        ]

    # --------------------------------------------------
    # CAPTURE HISTORY
    # --------------------------------------------------

    def get_capture_history(self, mac_bssid):
        observations = self.queries.get_access_point_observations(mac_bssid)

        return [
            {
                "capture_id": row["capture_id"],
                "capture_filename": row["capture_filename"],
                "observed_at": row["observed_at"]
            }
            for row in observations
        ]

    # --------------------------------------------------
    # ACCESS POINTS SEEN IN BOTH CAPTURES
    # --------------------------------------------------

    def get_access_points_in_both_captures(self, capture_id_1, capture_id_2):
        access_points = self.queries.get_access_points_in_both_captures(
            capture_id_1,
            capture_id_2
        )

        return [dict(row) for row in access_points]

    # --------------------------------------------------
    # MANUFACTURER
    # --------------------------------------------------

    def get_manufacturer(self, mac_bssid):
        try:
            from mac_vendor_lookup import MacLookup

            mac = MacLookup()
            return mac.lookup(mac_bssid)

        except Exception:
            return "Unknown"


