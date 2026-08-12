# database/queries.py


class DatabaseQueries:

    def __init__(self, db):
        self.db = db

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
    # CAPTURES FOR ACCESS POINT
    # --------------------------------------------------

    def get_access_point_captures(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT DISTINCT
                c.id,
                c.filename,
                c.started_at,
                c.ended_at,
                c.imported_at
            FROM captures c
            JOIN observations o
                ON o.capture_id = c.id
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
            ORDER BY c.started_at
            """,
            (mac_bssid,)
        ).fetchall()

    # --------------------------------------------------
    # SSIDS USED BY ACCESS POINT
    # --------------------------------------------------

    def get_access_point_ssids(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT DISTINCT
                o.ssid
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
              AND o.ssid IS NOT NULL
              AND o.ssid != ''
            ORDER BY o.ssid
            """,
            (mac_bssid,)
        ).fetchall()

    # --------------------------------------------------
    # ACCESS POINTS IN CAPTURE
    # --------------------------------------------------

    def get_capture_access_points(self, capture_id):
        return self.db.conn.execute(
            """
            SELECT DISTINCT
                ap.id,
                ap.mac_bssid,
                ap.type
            FROM access_points ap
            JOIN observations o
                ON o.access_point_id = ap.id
            WHERE o.capture_id = ?
            ORDER BY ap.mac_bssid
            """,
            (capture_id,)
        ).fetchall()

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
    # FIRST OBSERVATION
    # --------------------------------------------------

    def get_first_observation(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT
                o.*
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
            ORDER BY o.observed_at ASC
            LIMIT 1
            """,
            (mac_bssid,)
        ).fetchone()

    # --------------------------------------------------
    # LAST OBSERVATION
    # --------------------------------------------------

    def get_last_observation(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT
                o.*
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
            ORDER BY o.observed_at DESC
            LIMIT 1
            """,
            (mac_bssid,)
        ).fetchone()

    # --------------------------------------------------
    # OBSERVATION COUNT
    # --------------------------------------------------

    def get_observation_count(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
            """,
            (mac_bssid,)
        ).fetchone()["count"]

    # --------------------------------------------------
    # OBSERVATIONS IN CAPTURE
    # --------------------------------------------------

    def get_capture_observations(
            self,
            capture_id,
            limit=None,
            offset=0,
            channel=None,
            device_type=None,
            auth=None,
            manufacturer=None,
            sort="observed_at",
            direction="asc"
    ):
        sort_columns = {
            "bssid": "ap.mac_bssid",
            "ssid": "o.ssid",
            "type": "ap.type",
            "auth": "o.auth_mode",
            "channel": "o.channel",
            "frequency": "o.frequency",
            "rssi": "o.rssi",
            "observed_at": "o.observed_at"
        }

        sort_column = sort_columns.get(
            sort,
            "o.observed_at"
        )

        direction = ("DESC" if direction.lower() == "desc" else "ASC")

        query = """
            SELECT
                o.*,
                ap.mac_bssid,
                ap.type
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE o.capture_id = ?
        """

        params = [capture_id]

        if channel:
            query += """
                AND o.channel = ?
            """
            params.append(channel)

        if device_type:
            query += """
                AND ap.type = ?
            """
            params.append(device_type)

        if auth:
            query += """
                AND o.auth_mode = ?
            """
            params.append(auth)

#        if manufacturer:
#            query += """
#                AND ap.mac_bssid LIKE ?
#            """
#            params.append(manufacturer)

        query += f"""
            ORDER BY {sort_column} {direction}
        """

        if limit is not None:
            query += """
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

        return self.db.conn.execute(
            query,
            params
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
                c.id,
                c.filename,
                c.started_at,
                c.ended_at,
                c.imported_at,
                COUNT(o.id) AS observation_count
            FROM captures c
            LEFT JOIN observations o
                ON o.capture_id = c.id
            GROUP BY c.id
            ORDER BY c.started_at
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

    # --------------------------------------------------
    # AUTHENTICATION HISTORY
    # --------------------------------------------------

    def get_auth_history(self, mac_bssid):
        return self.db.conn.execute(
            """
            SELECT
                o.auth_mode,
                MIN(o.observed_at) AS first_seen,
                MAX(o.observed_at) AS last_seen,
                COUNT(*) AS observations
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE ap.mac_bssid = ?
              AND o.auth_mode IS NOT NULL
              AND o.auth_mode != ''
            GROUP BY o.auth_mode
            ORDER BY first_seen
            """,
            (mac_bssid,)
        ).fetchall()

    # --------------------------------------------------
    # ACCESS POINTS SEEN IN BOTH CAPTURES
    # --------------------------------------------------

    def get_access_points_in_both_captures(self, capture_id_1, capture_id_2):
        return self.db.conn.execute(
            """
            SELECT
                ap.id,
                ap.mac_bssid,
                ap.type
            FROM access_points ap
            JOIN observations o1
                ON o1.access_point_id = ap.id
            JOIN observations o2
                ON o2.access_point_id = ap.id
            WHERE o1.capture_id = ?
              AND o2.capture_id = ?
            GROUP BY ap.id
            ORDER BY ap.mac_bssid
            """,
            (capture_id_1, capture_id_2)
        ).fetchall()

# --------------------------------------------------
# CAPTURE OBSERVATION COUNT
# --------------------------------------------------

    def get_capture_observation_count(
        self,
        capture_id,
        channel=None,
        device_type=None,
        auth=None
    ):
        query = """
            SELECT COUNT(*) AS count
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE o.capture_id = ?
        """

        params = [capture_id]

        if channel:
            query += """
                AND o.channel = ?
            """
            params.append(channel)

        if device_type:
            query += """
                AND ap.type = ?
            """
            params.append(device_type)

        if auth:
            query += """
                AND o.auth_mode = ?
            """
            params.append(auth)

        return self.db.conn.execute(
            query,
            params
        ).fetchone()["count"]

# --------------------------------------------------
# CAPTURE CHANNELS
# --------------------------------------------------

    def get_capture_channels(self, capture_id):
        return self.db.conn.execute(
            """
            SELECT DISTINCT channel
            FROM observations
            WHERE capture_id = ?
              AND channel IS NOT NULL
            ORDER BY channel
            """,
            (capture_id,)
        ).fetchall()


# --------------------------------------------------
# CAPTURE TYPES
# --------------------------------------------------

    def get_capture_types(self, capture_id):
        return self.db.conn.execute(
            """
            SELECT DISTINCT ap.type
            FROM observations o
            JOIN access_points ap
                ON ap.id = o.access_point_id
            WHERE o.capture_id = ?
                AND ap.type IS NOT NULL
                AND ap.type != ''
            ORDER BY ap.type
            """,
            (capture_id,)
        ).fetchall()


# --------------------------------------------------
# CAPTURE AUTHENTICATION MODES
# --------------------------------------------------

    def get_capture_auth_modes(self, capture_id):
        return self.db.conn.execute(
            """
            SELECT DISTINCT auth_mode
            FROM observations
            WHERE capture_id = ?
                AND auth_mode IS NOT NULL
                AND auth_mode != ''
            ORDER BY auth_mode
            """,
            (capture_id,)
        ).fetchall()

# --------------------------------------------------
# ALL ACCESS POINTS
# --------------------------------------------------

    def get_access_points(
        self,
        limit=None,
        offset=0,
        device_type=None,
        auth=None,
        manufacturer=None,
        search=None,
        sort="bssid",
        direction="asc"
    ):
        sort_columns = {
            "bssid": "ap.mac_bssid",
            "type": "ap.type",
            "ssid": "last_observation.ssid",
            "auth": "last_observation.auth_mode",
            "first_seen": "first_seen",
            "last_seen": "last_seen",
            "observations": "observation_count",
            "captures": "capture_count"
            }

        sort_column = sort_columns.get(
            sort,
            "ap.mac_bssid"
        )

        direction = direction.lower()

        if direction not in ("asc", "desc"):
            direction = "asc"

        query = """
            SELECT
                ap.id,
                ap.mac_bssid,
                ap.type,
        
                last_observation.ssid,
                last_observation.auth_mode,
        
                first_seen.first_seen,
                last_seen.last_seen,
        
                COUNT(DISTINCT o.id) AS observation_count,
                COUNT(DISTINCT o.capture_id) AS capture_count
        
            FROM access_points ap
        
            JOIN observations o
                ON o.access_point_id = ap.id
        
            LEFT JOIN observations last_observation
                ON last_observation.id = (
                    SELECT o2.id
                    FROM observations o2
                    WHERE o2.access_point_id = ap.id
                    ORDER BY o2.observed_at DESC, o2.id DESC
                    LIMIT 1
                )
        
            LEFT JOIN (
                SELECT
                    access_point_id,
                    MIN(observed_at) AS first_seen
                FROM observations
                GROUP BY access_point_id
            ) first_seen
                ON first_seen.access_point_id = ap.id
        
            LEFT JOIN (
                SELECT
                    access_point_id,
                    MAX(observed_at) AS last_seen
                FROM observations
                GROUP BY access_point_id
            ) last_seen
                ON last_seen.access_point_id = ap.id
        
            WHERE 1 = 1
        """

        params = []

        if device_type:
            query += """
                AND ap.type = ?
            """
            params.append(device_type)

        if auth:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM observations ao
                    WHERE ao.access_point_id = ap.id
                    AND ao.auth_mode = ?
                )
            """
            params.append(auth)

        if manufacturer:
            query += """
                AND ap.mac_bssid LIKE ?
            """
            params.append(manufacturer)

        if search:
            query += """
                AND (
                    ap.mac_bssid LIKE ?
                    OR EXISTS (
                        SELECT 1
                        FROM observations so
                        WHERE so.access_point_id = ap.id
                        AND so.ssid LIKE ?
                    )
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value
            ])

        query += """
            GROUP BY
                ap.id,
                ap.mac_bssid,
                ap.type,
                last_observation.ssid,
                last_observation.auth_mode,
                first_seen.first_seen,
                last_seen.last_seen
        """

        query += f"""
            ORDER BY {sort_column} {direction}
        """

        if limit is not None:
            query += """
                LIMIT ? OFFSET ?
            """

            params.extend([
                limit,
                offset
            ])

        return self.db.conn.execute(
            query,
            params
        ).fetchall()

    # --------------------------------------------------

    # ACCESS POINT COUNT

    # --------------------------------------------------

    def get_access_point_count(
            self,
            device_type=None,
            auth=None,
            search=None
    ):
        query = """
    SELECT COUNT(*)
    FROM access_points ap
    WHERE 1 = 1
    """


        params = []

    # ----------------------------------------------
    # TYPE
    # ----------------------------------------------

        if device_type:
            query += """
                AND ap.type = ?
            """

            params.append(device_type)

    # ----------------------------------------------
    # AUTHENTICATION
    # ----------------------------------------------

        if auth:
            query += """
                AND EXISTS (
                    SELECT 1
                    FROM observations o
                    WHERE o.access_point_id = ap.id
                    AND o.auth_mode = ?
                )
            """

            params.append(auth)

    # ----------------------------------------------
    # SEARCH
    # ----------------------------------------------

        if search:
            query += """
                AND (
                    ap.mac_bssid LIKE ?
    
                    OR EXISTS (
                        SELECT 1
                        FROM observations o
                        WHERE o.access_point_id = ap.id
                        AND o.ssid LIKE ?
                    )
                )
            """

            search_value = f"%{search}%"

            params.append(search_value)
            params.append(search_value)

    # ----------------------------------------------
    # EXECUTE
    # ----------------------------------------------

        return self.db.conn.execute(
            query,
            params
        ).fetchone()[0]

# --------------------------------------------------
# ACCESS POINT TYPES
# --------------------------------------------------

    def get_all_access_point_types(self):
        return self.db.conn.execute(
        """
        SELECT DISTINCT type
        FROM access_points
        WHERE type IS NOT NULL
        AND type != ''
        ORDER BY type
        """
        ).fetchall()

    # --------------------------------------------------

    # ALL AUTHENTICATION MODES

    # --------------------------------------------------

    def get_all_auth_modes(self):
        return self.db.conn.execute(
        """
        SELECT DISTINCT auth_mode
        FROM observations
        WHERE auth_mode IS NOT NULL
        AND auth_mode != ''
        ORDER BY auth_mode
        """
        ).fetchall()

