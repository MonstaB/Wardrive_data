# database/queries.py


class DatabaseQueries:

    def __init__(self, db):
        self.db = db

    # --------------------------------------------------
    # ACCESS POINT
    # --------------------------------------------------

    def get_access_point(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT
                id,
                mac_bssid,
                type
            FROM access_points
            WHERE mac_bssid = ?
            """,
            (mac_bssid,)
        ).fetchone()

    # --------------------------------------------------
    # CAPTURE
    # --------------------------------------------------

    def get_capture(self, capture_id):
        return self.db.conn.execute(
            """
            SELECT
                id,
                filename,
                started_at,
                ended_at,
                imported_at,
                file_hash
            FROM captures
            WHERE id = ?
            """,
            (capture_id,)
        ).fetchone()

    # --------------------------------------------------
    # OBSERVATIONS FOR ACCESS POINT
    # --------------------------------------------------

    def get_access_point_observations(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT
                o.id,
                o.ssid,
                o.auth_mode,
                o.observed_at,
                o.channel,
                o.frequency,
                o.rssi,
                o.latitude,
                o.longitude,
                o.altitude,
                o.accuracy,
                o.rcois,
                o.mfgrid,
                c.id AS capture_id,
                c.filename AS capture_filename
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            JOIN captures c
                ON c.id = o.capture_id
            WHERE ap.mac_bssid = ?
            ORDER BY o.observed_at
            """,
            (mac_bssid,)
        ).fetchall()

    # --------------------------------------------------
    # ALL ACCESS POINTS
    # --------------------------------------------------

    def get_all_access_points(self):
        return self.db.conn.execute(
            """
            SELECT
                id,
                mac_bssid,
                type
            FROM access_points
            ORDER BY mac_bssid
            """
        ).fetchall()

    # --------------------------------------------------
    # ALL CAPTURES
    # --------------------------------------------------

    def get_all_captures(self):
        return self.db.conn.execute(
            """
            SELECT
                id,
                filename,
                started_at,
                ended_at,
                imported_at
            FROM captures
            ORDER BY started_at
            """
        ).fetchall()

    # --------------------------------------------------
    # ssid history
    # --------------------------------------------------

    def get_ssid_history(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT
                o.ssid,
                MIN(o.observed_at) AS first_seen,
                MAX(o.observed_at) AS last_seen,
                COUNT(*) AS observations
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
              AND o.ssid IS NOT NULL
              AND o.ssid != ''
            GROUP BY o.ssid
            ORDER BY first_seen
            """,
            (mac_bssid,)
        ).fetchall()

