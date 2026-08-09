from pathlib import Path

from importers.bruce import read_bruce_csv


class DatabaseScanner:

    def __init__(self, db):
        self.db = db

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
                result = self.db.import_capture(path)
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
