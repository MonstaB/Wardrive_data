from mac_vendor_lookup import MacLookup

lookup = MacLookup()

macs = [
    "00:0F:00:49:3E:5C",
    "14:49:BC:9D:E3:BA",
    "B4:63:6F:AE:4D:E9",
    "34:98:B5:FB:73:47"
]

for mac in macs:
    try:
        manufacturer = lookup.lookup(mac)
    except Exception as e:
        manufacturer = f"ERROR: {e}"

    print(mac, "|", manufacturer)