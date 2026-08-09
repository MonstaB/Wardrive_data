from mac_vendor_lookup import MacLookup


class ManufacturerLookup:

    def __init__(self):
        self.lookup = MacLookup()

    def get(self, mac_bssid):
        if not mac_bssid:
            return "Unknown"

        try:
            return self.lookup.lookup(mac_bssid)
        except Exception:
            return "Unknown"
