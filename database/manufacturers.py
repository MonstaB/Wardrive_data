from mactools import MacAddress


def get_manufacturer(mac_bssid):
    if not mac_bssid:
        return None

    try:
        mac = MacAddress(mac_bssid)
        return mac.vendor
    except Exception:
        return None