# importers/bruce.py
import csv
from pathlib import Path


EXPECTED_HEADERS = [
    "MAC",
    "SSID",
    "AuthMode",
    "FirstSeen",
    "Channel",
    "Frequency",
    "RSSI",
    "CurrentLatitude",
    "CurrentLongitude",
    "AltitudeMeters",
    "AccuracyMeters",
    "RCOIs",
    "MfgrId",
    "Type"
]


def read_bruce_csv(path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    observations = []

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
        newline=""
    ) as f:
        reader = csv.reader(f)

        # Bruce metadata row
        metadata = next(reader, None)

        # CSV header row
        headers = next(reader, None)

        if headers is None:
            raise ValueError(
                "CSV does not contain a header row."
            )

        if headers != EXPECTED_HEADERS:
            raise ValueError(
                f"Unexpected Bruce CSV headers: {headers}"
            )

        for row in reader:

            if not row:
                continue

            if len(row) != len(headers):
                continue

            data = dict(zip(headers, row))

            # ----------------------------------------------
            # NORMALISE BRUCE DATA
            # ----------------------------------------------

            observation = {
                "mac_bssid": data["MAC"].replace("\\:", ":"),
                "ssid": data["SSID"] or None,
                "auth_mode": data["AuthMode"] or None,
                "observed_at": data["FirstSeen"] or None,
                "channel": int(data["Channel"]) if data["Channel"] else None,
                "frequency": int(data["Frequency"]) if data["Frequency"] else None,
                "rssi": int(data["RSSI"]) if data["RSSI"] else None,
                "latitude": float(data["CurrentLatitude"]) if data["CurrentLatitude"] else None,
                "longitude": float(data["CurrentLongitude"]) if data["CurrentLongitude"] else None,
                "altitude": float(data["AltitudeMeters"]) if data["AltitudeMeters"] else None,
                "accuracy": float(data["AccuracyMeters"]) if data["AccuracyMeters"] else None,
                "rcois": data["RCOIs"] or None,
                "mfgrid": data["MfgrId"] or None,
                "type": data["Type"] or None
            }

            observations.append(observation)

    if not observations:
        raise ValueError(
            "CSV contains no observations."
        )

    return {
        "metadata": metadata,
        "observations": observations
    }
