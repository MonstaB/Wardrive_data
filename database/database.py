# database/database.py

import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

DB_NAME = Path(__file__).resolve().parent.parent / "wardriving.db"
DATABASE_VERSION = 1


class Database:

    def __init__(self, db_path=DB_NAME):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.create_tables()
        self.run_migrations()

    def close(self):
        self.conn.commit()
        self.conn.close()

    # --------------------------------------------------
    # DATABASE SETUP
    # --------------------------------------------------

    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS access_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_bssid TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_point_id INTEGER NOT NULL,
                capture_id INTEGER NOT NULL,
                ssid TEXT,
                auth_mode TEXT,
                observed_at TEXT,
                channel INTEGER,
                frequency INTEGER,
                rssi INTEGER,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                accuracy REAL,
                rcois TEXT,
                mfgrid TEXT,

                FOREIGN KEY(access_point_id)
                    REFERENCES access_points(id),

                FOREIGN KEY(capture_id)
                    REFERENCES captures(id)
            );

            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );
        """)

        version = self.conn.execute(
            "SELECT COUNT(*) FROM schema_version"
        ).fetchone()[0]

        if version == 0:
            self.conn.execute(
                """
                INSERT INTO schema_version(version)
                VALUES(?)
                """,
                (DATABASE_VERSION,)
            )

        self.conn.commit()

    # --------------------------------------------------
    # MIGRATIONS
    # --------------------------------------------------

    def run_migrations(self):
        current = self.conn.execute(
            """
            SELECT version
            FROM schema_version
            """
        ).fetchone()[0]

        if current < DATABASE_VERSION:
            self.conn.execute(
                """
                UPDATE schema_version
                SET version = ?
                """,
                (DATABASE_VERSION,)
            )

        self.conn.commit()

    # --------------------------------------------------
    # FILE HASHING
    # --------------------------------------------------

    def file_hash(self, path):
        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    # --------------------------------------------------
    # CHECK CAPTURE
    # --------------------------------------------------

    def capture_exists(self, file_hash):
        return self.conn.execute(
            """
            SELECT id, filename, imported_at
            FROM captures
            WHERE file_hash = ?
            """,
            (file_hash,)
        ).fetchone()

    # --------------------------------------------------
    # CREATE CAPTURE
    # --------------------------------------------------

    def create_capture(
        self,
        filename,
        started_at,
        ended_at,
        file_hash
    ):
        imported_at = datetime.utcnow().isoformat()

        cursor = self.conn.execute(
            """
            INSERT INTO captures (
                filename,
                started_at,
                ended_at,
                imported_at,
                file_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                filename,
                started_at,
                ended_at,
                imported_at,
                file_hash
            )
        )

        return cursor.lastrowid

    # --------------------------------------------------
    # GET OR CREATE ACCESS POINT
    # --------------------------------------------------

    def get_or_create_access_point(self, mac_bssid, ap_type):
        access_point = self.conn.execute(
            """
            SELECT id
            FROM access_points
            WHERE mac_bssid = ?
            """,
            (mac_bssid,)
        ).fetchone()

        if access_point:
            return access_point["id"]

        cursor = self.conn.execute(
            """
            INSERT INTO access_points (
                mac_bssid,
                type
            )
            VALUES (?, ?)
            """,
            (
                mac_bssid,
                ap_type
            )
        )

        return cursor.lastrowid

    # --------------------------------------------------
    # ADD OBSERVATION
    # --------------------------------------------------

    def add_observation(
        self,
        access_point_id,
        capture_id,
        observation
    ):
        self.conn.execute(
            """
            INSERT INTO observations (
                access_point_id,
                capture_id,
                ssid,
                auth_mode,
                observed_at,
                channel,
                frequency,
                rssi,
                latitude,
                longitude,
                altitude,
                accuracy,
                rcois,
                mfgrid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                access_point_id,
                capture_id,
                observation["ssid"],
                observation["auth_mode"],
                observation["observed_at"],
                observation["channel"],
                observation["frequency"],
                observation["rssi"],
                observation["latitude"],
                observation["longitude"],
                observation["altitude"],
                observation["accuracy"],
                observation["rcois"],
                observation["mfgrid"]
            )
        )

    # --------------------------------------------------
    # IMPORT CAPTURE
    # --------------------------------------------------

    def import_capture(self, path, importer):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        # ----------------------------------------------
        # HASH FILE
        # ----------------------------------------------

        digest = self.file_hash(path)

        # ----------------------------------------------
        # CHECK DUPLICATE
        # ----------------------------------------------

        existing = self.capture_exists(digest)

        if existing:
            return {
                "id": existing["id"],
                "imported": False,
                "reason": "already_imported"
            }

        # ----------------------------------------------
        # READ FILE USING IMPORTER
        # ----------------------------------------------

        data = importer(path)

        observations = data["observations"]

        if not observations:
            raise ValueError("Capture contains no observations.")

        # ----------------------------------------------
        # DETERMINE CAPTURE TIME
        # ----------------------------------------------

        timestamps = [
            row["observed_at"]
            for row in observations
            if row["observed_at"]
        ]

        if not timestamps:
            raise ValueError(
                "Capture contains no observation timestamps."
            )

        started_at = min(timestamps)
        ended_at = max(timestamps)

        try:
            # ------------------------------------------
            # CREATE CAPTURE
            # ------------------------------------------

            capture_id = self.create_capture(
                filename=path.name,
                started_at=started_at,
                ended_at=ended_at,
                file_hash=digest
            )

            # ------------------------------------------
            # ADD OBSERVATIONS
            # ------------------------------------------

            for observation in observations:

                access_point_id = self.get_or_create_access_point(
                    observation["mac_bssid"],
                    observation["type"]
                )

                self.add_observation(
                    access_point_id=access_point_id,
                    capture_id=capture_id,
                    observation=observation
                )

            self.conn.commit()

        except Exception:
            self.conn.rollback()
            raise

        return {
            "id": capture_id,
            "imported": True,
            "reason": "new_capture",
            "observations": len(observations)
        }