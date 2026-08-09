# database.py
import sqlite3
from pathlib import Path
import hashlib
from datetime import datetime

DB_NAME = Path(__file__).resolve().parent / "wardriving.db"
DATABASE_VERSION = 1
CAPTURES_FOLDER = "./logs"


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
        """Return True if this exact file has already been imported."""

        row = self.conn.execute(
            """
            SELECT id
            FROM captures
            WHERE file_hash = ?
            """,
            (file_hash,)
        ).fetchone()

        return row is not None

    # --------------------------------------------------
    # IMPORT CAPTURE
    # --------------------------------------------------

    def import_capture(self, path):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        # Calculate SHA-256 before importing anything
        digest = self.file_hash(path)

        # Check whether this exact file has already been imported
        existing = self.conn.execute(
            """
            SELECT id
            FROM captures
            WHERE file_hash = ?
            """,
            (digest,)
        ).fetchone()

        if existing:
            return {
                "id": existing["id"],
                "imported": False,
                "reason": "already_imported"
            }

        # Create capture record
        now = datetime.utcnow().isoformat()

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
                path.name,
                now,
                now,
                now,
                digest
            )
        )

        capture_id = cursor.lastrowid

        self.conn.commit()

        return {
            "id": capture_id,
            "imported": True,
            "reason": "new_capture"
        }
