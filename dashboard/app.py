import json
import os
import subprocess
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)

# =========================
# PATHS
# All relative to project root — run from there.
# =========================
REPORTS_JSON_DIR = "reports/json"
LOG_FILE         = "logs/netdevops.log"
MAIN_SCRIPT      = "scripts/main.py"


# =========================
# HELPERS
# =========================
def load_all_reports():
    """
    Loads all JSON reports from reports/json/.
    Returns a list of report dicts sorted by timestamp descending.
    """
    reports = []

    if not os.path.exists(REPORTS_JSON_DIR):
        return reports

    for filename in os.listdir(REPORTS_JSON_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(REPORTS_JSON_DIR, filename)
        try:
            with open(filepath) as f:
                data = json.load(f)
                data["_filename"] = filename
                reports.append(data)
        except Exception:
            continue

    # Sort by timestamp descending
    reports.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return reports


def get_latest_per_device(reports):
    """
    Returns only the most recent report per device.
    """
    seen    = {}
    latest  = []

    for report in reports:
        device = report.get("device", "unknown")
        if device not in seen:
            seen[device] = True
            latest.append(report)

    return latest


def tail_log(n=50):
    """
    Returns the last n lines from the log file.
    """
    if not os.path.exists(LOG_FILE):
        return ["Log file not found."]
    try:
        with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return [line.rstrip() for line in lines[-n:]]
    except Exception as e:
        return [f"Error reading log: {e}"]


def compliance_summary(compliance):
    """
    Returns (total, compliant, drift) counts from a compliance dict.
    """
    total     = len(compliance)
    compliant = sum(1 for v in compliance.values() if v == "COMPLIANT")
    drift     = total - compliant
    return total, compliant, drift


# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    """
    Home page — latest compliance status per device
    and full execution history.
    """
    all_reports    = load_all_reports()
    latest_reports = get_latest_per_device(all_reports)

    # Summary stats across latest reports
    total_devices   = len(latest_reports)
    all_compliant   = sum(
        1 for r in latest_reports
        if all(v == "COMPLIANT" for v in r.get("compliance", {}).values())
    )
    any_drift = total_devices - all_compliant

    return render_template(
        "index.html",
        latest_reports  = latest_reports,
        all_reports     = all_reports[:20],  # last 20 runs
        total_devices   = total_devices,
        all_compliant   = all_compliant,
        any_drift       = any_drift,
        now             = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@app.route("/report/<filename>")
def report_detail(filename):
    """
    Detailed report view for a single run.
    """
    filepath = os.path.join(REPORTS_JSON_DIR, filename)

    if not os.path.exists(filepath):
        return render_template("404.html"), 404

    with open(filepath) as f:
        report = json.load(f)

    total, compliant, drift = compliance_summary(
        report.get("compliance", {})
    )

    return render_template(
        "report.html",
        report   = report,
        filename = filename,
        total    = total,
        compliant = compliant,
        drift    = drift
    )


@app.route("/run", methods=["POST"])
def run_framework():
    """
    Triggers main.py from the browser.
    Accepts JSON body: { "mode": "dry-run" | "live" }
    Returns stdout/stderr as JSON.
    """
    mode = request.json.get("mode", "dry-run")
    cmd  = [sys.executable, MAIN_SCRIPT]

    if mode == "dry-run":
        cmd.append("--dry-run")

    try:
        result = subprocess.run(
            cmd,
            capture_output = True,
            text           = True,
            encoding       = "utf-8",
            errors         = "replace",
            timeout        = 120
        )
        return jsonify({
            "success": result.returncode == 0,
            "stdout":  result.stdout,
            "stderr":  result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "stdout":  "",
            "stderr":  "Framework run timed out after 120 seconds."
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "stdout":  "",
            "stderr":  str(e)
        })


@app.route("/logs")
def logs():
    """
    Displays the last 50 lines of netdevops.log.
    """
    lines = tail_log(50)
    return render_template("logs.html", lines=lines)


@app.route("/api/logs")
def api_logs():
    """
    Returns last 50 log lines as JSON for live refresh.
    """
    lines = tail_log(50)
    return jsonify({"lines": lines})


@app.route("/api/summary")
def api_summary():
    """
    Returns latest compliance summary as JSON.
    """
    all_reports    = load_all_reports()
    latest_reports = get_latest_per_device(all_reports)

    summary = []
    for r in latest_reports:
        total, compliant, drift = compliance_summary(
            r.get("compliance", {})
        )
        summary.append({
            "device":         r.get("device"),
            "timestamp":      r.get("timestamp"),
            "execution_mode": r.get("execution_mode"),
            "total":          total,
            "compliant":      compliant,
            "drift":          drift,
            "restconf":       r.get("restconf_compliance", {})
        })

    return jsonify(summary)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)