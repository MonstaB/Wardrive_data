from database.database import Database
from database.queries import DatabaseQueries
from database.analysis import DatabaseAnalysis
from importers.bruce import read_bruce_csv
from flask import Blueprint, render_template, request

viewer = Blueprint(
    "viewer",
    __name__,
    template_folder="templates"
)


@viewer.route("/")
def index():
    db = Database()
    queries = DatabaseQueries(db)
    access_points = queries.get_all_access_points()
    captures = queries.get_all_captures()

    observation_count = db.conn.execute(
        """
        SELECT COUNT(*)
        FROM observations
        """
    ).fetchone()[0]

    access_point_count = len(access_points)
    capture_count = len(captures)

    db.close()

    return render_template(
        "index.html",
        access_points=access_points,
        captures=captures,
        access_point_count=access_point_count,
        observation_count=observation_count,
        capture_count=capture_count
    )


@viewer.route("/capture/<int:capture_id>")
def capture_detail(capture_id):
    db = Database()
    queries = DatabaseQueries(db)
    analysis = DatabaseAnalysis(queries)

    capture = queries.get_capture(capture_id)

    if capture is None:
        db.close()
        return "Capture not found", 404

    # ----------------------------------------------
    # FILTERS
    # ----------------------------------------------

    channel = request.args.get("channel", "").strip()
    device_type = request.args.get("type", "").strip()
    auth = request.args.get("auth", "").strip()

    # ----------------------------------------------
    # SORTING
    # ----------------------------------------------

    sort = request.args.get("sort", "observed_at")

    direction = request.args.get("direction", "asc")

    # ----------------------------------------------
    # PAGINATION
    # ----------------------------------------------

    page = request.args.get("page", 1, type=int)

    per_page = 100

    if page < 1:
        page = 1

    total = queries.get_capture_observation_count(
        capture_id,
        channel=channel or None,
        device_type=device_type or None,
        auth=auth or None
    )

    pages = (total + per_page - 1) // per_page

    if pages == 0:
        pages = 1

    if page > pages:
        page = pages

    offset = (page - 1) * per_page

    observations = queries.get_capture_observations(
        capture_id,
        limit=per_page,
        offset=offset,
        channel=channel or None,
        device_type=device_type or None,
        auth=auth or None,
        sort=sort,
        direction=direction
    )

    # ----------------------------------------------
    # MANUFACTURERS
    # ----------------------------------------------

    manufacturers = {}

    for observation in observations:
        mac = observation["mac_bssid"]

        if mac not in manufacturers:
            manufacturers[mac] = analysis.get_manufacturer(mac)

    # ----------------------------------------------
    # FILTER OPTIONS
    # ----------------------------------------------

    channels = queries.get_capture_channels(capture_id)
    device_types = queries.get_capture_types(capture_id)
    auth_modes = queries.get_capture_auth_modes(capture_id)

    db.close()

    return render_template(
        "capture.html",
        capture=capture,
        observations=observations,
        manufacturers=manufacturers,
        channels=channels,
        device_types=device_types,
        auth_modes=auth_modes,
        selected_channel=channel,
        selected_type=device_type,
        selected_auth=auth,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
        pages=pages,
        total=total
    )


@viewer.route("/access-point/<mac_bssid>")
def access_point(mac_bssid):
    queries = DatabaseQueries(Database())
    analysis = DatabaseAnalysis(queries)
    manufacturer = analysis.get_manufacturer(mac_bssid)
    summary = analysis.get_access_point_summary(mac_bssid)
    observations = queries.get_access_point_observations(mac_bssid)

    if summary is None:
        return "Access point not found", 404

    return render_template(
        "access_point.html",
        summary=summary,
        observations=observations,
        manufacturer=manufacturer
    )


@viewer.route("/scan", methods=["POST"])
def scan():
    import os

    db = Database()

    logs_folder = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "logs"
    )

    results = []

    for filename in os.listdir(logs_folder):
        if not filename.lower().endswith(".csv"):
            continue

        path = os.path.join(logs_folder, filename)

        try:
            result = db.import_capture(
                path,
                read_bruce_csv
            )

            results.append({
                "filename": filename,
                **result
            })

        except Exception as e:
            results.append({
                "filename": filename,
                "imported": False,
                "reason": "error",
                "error": str(e)
            })

    db.close()

    return render_template(
        "scan.html",
        results=results
    )
