from flask import Blueprint, render_template
from database.database import Database
from database.queries import DatabaseQueries
from database.analysis import DatabaseAnalysis

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

    capture = queries.get_capture(capture_id)

    if capture is None:
        db.close()
        return "Capture not found", 404

    observations = queries.get_capture_observations(capture_id)

    db.close()

    return render_template(
        "capture.html",
        capture=capture,
        observations=observations
    )


@viewer.route("/access-point/<mac_bssid>")
def access_point(mac_bssid):
    queries = DatabaseQueries(Database())
    analysis = DatabaseAnalysis(queries)

    summary = analysis.get_access_point_summary(mac_bssid)
    observations = queries.get_access_point_observations(mac_bssid)

    if summary is None:
        return "Access point not found", 404

    return render_template(
        "access_point.html",
        summary=summary,
        observations=observations
    )
