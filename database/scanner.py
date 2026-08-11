from pathlib import Path

from importers.bruce import read_bruce_csv
from importers.wigle import read_wigle_csv
from importers.porkchop import read_porkchop_csv


class DatabaseScanner:

    def __init__(self, db):
        self.db = db

# --------------------------------------------------
# DETECT CSV FORMAT
# --------------------------------------------------


    def detect_importer(self, path):
        path = Path(path)

        with open(
            path,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as f:

            metadata = f.readline().strip()
            headers = f.readline().strip()

        # ----------------------------------------------
        # BRUCE
        # ----------------------------------------------

        if "brand=Bruce" in metadata:
            return read_bruce_csv

        # ----------------------------------------------
        # PORKCHOP
        # ----------------------------------------------

        if "device=PORKCHOP" in metadata:
            return read_porkchop_csv

        # ----------------------------------------------
        # WIGLE
        # ----------------------------------------------

        if metadata.startswith("WigleWifi-"):
            return read_wigle_csv

        # ----------------------------------------------
        # UNKNOWN
        # ----------------------------------------------

        raise ValueError(
            f"Unknown CSV format. Metadata: {metadata}"
        )

    # --------------------------------------------------
    # SCAN LOGS
    # --------------------------------------------------


    def scan_logs(self, folder):
        folder = Path(folder)

        if not folder.exists():
            raise FileNotFoundError(folder)

        results = []

        for path in sorted(folder.glob("*.csv")):

            digest = self.db.file_hash(path)

            existing = self.db.capture_exists(digest)

            if existing:
                results.append({
                    "filename": path.name,
                    "imported": False,
                    "reason": "already_imported",
                    "id": existing["id"]
                })
                continue

            try:

                importer = self.detect_importer(path)

                result = self.db.import_capture(
                    path,
                    importer
                )

                results.append({
                    "filename": path.name,
                    **result
                })

            except Exception as e:

                results.append({
                    "filename": path.name,
                    "imported": False,
                    "reason": "error",
                    "error": str(e)
                })

        return results

