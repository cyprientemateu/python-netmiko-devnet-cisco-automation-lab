import json
from datetime import datetime
from logger import get_logger

log = get_logger()


def save_json_report(
    device_host, timestamp, config_file,
    compliance, diff_report, execution_mode
):
    """
    Saves a structured JSON report to reports/json/.
    Includes execution mode, compliance results, and full diff data.
    Returns the path of the saved file.
    """
    json_file = f"reports/json/report_{timestamp}.json"

    try:
        with open(json_file, "w") as f:
            json.dump(
                {
                    "execution_mode": execution_mode,
                    "device":         device_host,
                    "timestamp":      timestamp,
                    "config_file":    config_file,
                    "compliance":     compliance,
                    "diff": {
                        k: {
                            "expected": v["expected"],
                            "actual":   v["actual"],
                            "missing":  v["missing"],
                            "diff":     v["diff"]
                        }
                        for k, v in diff_report.items()
                    }
                },
                f,
                indent=4
            )
        log.info(f"JSON report saved — {json_file}")
        return json_file

    except Exception as e:
        log.error(f"JSON report failed — {e}")
        return None


def generate_html_report(
    compliance, diff_report, device_host,
    config_file, filename, execution_mode
):
    """
    Generates a visual HTML compliance dashboard saved to reports/html/.
    Shows execution mode, expected vs actual config, and missing lines
    per interface with color-coded COMPLIANT / DRIFT status.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        html = f"""
    <html>
    <head>
        <title>NetDevOps Compliance Report</title>
        <style>
            body       {{ font-family: Arial; margin: 40px;
                          background: #f9f9f9; }}
            h1         {{ color: #333; }}
            h2         {{ color: #555; font-size: 14px; }}
            h3         {{ margin-bottom: 4px; }}
            .compliant {{ color: green; }}
            .drift     {{ color: red; }}
            .meta      {{ background: #eef; border: 1px solid #ccd;
                          border-radius: 6px; padding: 12px;
                          margin-bottom: 20px; font-size: 13px; }}
            .section   {{ background: white; border: 1px solid #ddd;
                          border-radius: 6px; padding: 16px;
                          margin-bottom: 20px; }}
            pre        {{ background: #f4f4f4; padding: 10px;
                          border-radius: 4px; font-size: 13px; }}
            .rem       {{ color: red; }}
        </style>
    </head>
    <body>
    <h1>NetDevOps Compliance Report</h1>
    <h2>Device: {device_host} &nbsp;|&nbsp; Generated: {timestamp}</h2>

    <div class='meta'>
        <b>Execution Mode:</b> &nbsp; {execution_mode}
        <br><br>
        <b>Rendered Config Archive:</b>
        &nbsp; {config_file if config_file else "Not available"}
    </div>

    <hr>
    """

        for intf, status in compliance.items():

            css  = "compliant" if status == "COMPLIANT" else "drift"
            data = diff_report[intf]

            html += f"<div class='section'>"
            html += f"<h3 class='{css}'>[{status}] {intf}</h3>"

            html += "<b>Expected (desired state):</b><pre>"
            for line in data["expected"]:
                html += line + "\n"
            html += "</pre>"

            html += "<b>Actual (on device):</b><pre>"
            for line in data["actual"]:
                html += line + "\n"
            html += "</pre>"

            if data["missing"]:
                html += "<b>Missing lines (causing DRIFT):</b><pre>"
                for line in data["missing"]:
                    html += f"<span class='rem'>- {line}</span>\n"
                html += "</pre>"

            html += "</div>"

        html += "</body></html>"

        with open(filename, "w") as f:
            f.write(html)

        log.info(f"HTML report saved — {filename}")

    except Exception as e:
        log.error(f"HTML report failed — {e}")