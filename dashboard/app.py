"""Flask web dashboard for the Cloud Security Audit Tool.

Run directly:
    python -m dashboard.app --report reports/report.json

Or programmatically:
    from dashboard.app import create_app
    app = create_app(analysis)
    app.run()
"""

import json
import logging
import os

from flask import Flask, jsonify, render_template_string

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Inline Jinja2 HTML template
# -----------------------------------------------------------------------
_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cloud Security Audit Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; }
    header { background: #16213e; padding: 1rem 2rem;
             display: flex; align-items: center; gap: 1rem; }
    header h1 { font-size: 1.4rem; }
    main { padding: 2rem; }
    .cards { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }
    .card { background: #16213e; border-radius: 10px; padding: 1.2rem 1.8rem;
            min-width: 140px; text-align: center; flex: 1; }
    .card .label { font-size: .85rem; color: #aaa; margin-bottom: .4rem; }
    .card .value { font-size: 2.4rem; font-weight: bold; }
    .CRITICAL { color: #e74c3c; }
    .HIGH { color: #e67e22; }
    .MEDIUM { color: #f1c40f; }
    .LOW { color: #2ecc71; }
    .NONE { color: #27ae60; }
    .filters { margin-bottom: 1rem; display: flex; gap: .5rem; flex-wrap: wrap; }
    .filter-btn { background: #16213e; border: 1px solid #444; color: #eee;
                  padding: .4rem .9rem; border-radius: 20px; cursor: pointer;
                  font-size: .85rem; }
    .filter-btn.active { background: #0f3460; border-color: #e94560; }
    table { width: 100%; border-collapse: collapse; background: #16213e;
            border-radius: 10px; overflow: hidden; }
    th { background: #0f3460; padding: .7rem 1rem; text-align: left;
         font-size: .9rem; }
    td { padding: .6rem 1rem; border-bottom: 1px solid #222; font-size: .9rem; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #0f3460; }
    .badge { display: inline-block; padding: .15rem .5rem; border-radius: 4px;
             font-size: .78rem; font-weight: bold; }
    .badge.CRITICAL { background: #e74c3c; color: #fff; }
    .badge.HIGH     { background: #e67e22; color: #fff; }
    .badge.MEDIUM   { background: #f1c40f; color: #333; }
    .badge.LOW      { background: #2ecc71; color: #333; }
    .no-findings { color: #888; padding: 2rem; text-align: center; }
  </style>
</head>
<body>
  <header>
    <span style="font-size:1.8rem">☁️</span>
    <h1>Cloud Security Audit Dashboard</h1>
  </header>
  <main>
    <div class="cards">
      <div class="card">
        <div class="label">Total Findings</div>
        <div class="value">{{ analysis.total_findings }}</div>
      </div>
      <div class="card">
        <div class="label">Overall Risk</div>
        <div class="value {{ analysis.overall_risk }}">{{ analysis.overall_risk }}</div>
      </div>
      <div class="card">
        <div class="label">Critical</div>
        <div class="value CRITICAL">{{ analysis.by_severity.get('CRITICAL', 0) }}</div>
      </div>
      <div class="card">
        <div class="label">High</div>
        <div class="value HIGH">{{ analysis.by_severity.get('HIGH', 0) }}</div>
      </div>
      <div class="card">
        <div class="label">Medium</div>
        <div class="value MEDIUM">{{ analysis.by_severity.get('MEDIUM', 0) }}</div>
      </div>
      <div class="card">
        <div class="label">Low</div>
        <div class="value LOW">{{ analysis.by_severity.get('LOW', 0) }}</div>
      </div>
    </div>

    <h2 style="margin-bottom:1rem">Findings</h2>

    <div class="filters">
      <button class="filter-btn active" onclick="filterTable('ALL', this)">All</button>
      <button class="filter-btn" onclick="filterTable('CRITICAL', this)">Critical</button>
      <button class="filter-btn" onclick="filterTable('HIGH', this)">High</button>
      <button class="filter-btn" onclick="filterTable('MEDIUM', this)">Medium</button>
      <button class="filter-btn" onclick="filterTable('LOW', this)">Low</button>
      {% for scanner in analysis.by_scanner %}
      <button class="filter-btn" onclick="filterScanner('{{ scanner }}', this)">
        {{ scanner }}
      </button>
      {% endfor %}
    </div>

    {% if analysis.scored_findings %}
    <table id="findings-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Severity</th>
          <th>Scanner</th>
          <th>Resource</th>
          <th>Issue</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        {% for f in analysis.scored_findings | sort(attribute='score', reverse=True) %}
        <tr data-severity="{{ f.severity }}" data-scanner="{{ f.scanner }}">
          <td>{{ loop.index }}</td>
          <td><span class="badge {{ f.severity }}">{{ f.severity }}</span></td>
          <td>{{ f.scanner }}</td>
          <td style="word-break:break-all">{{ f.resource }}</td>
          <td>{{ f.issue }}</td>
          <td>{{ f.score }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="no-findings">✅ No findings – your cloud environment looks clean!</div>
    {% endif %}
  </main>

  <script>
    function filterTable(severity, btn) {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('#findings-table tbody tr').forEach(row => {
        row.style.display =
          (severity === 'ALL' || row.dataset.severity === severity) ? '' : 'none';
      });
    }
    function filterScanner(scanner, btn) {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('#findings-table tbody tr').forEach(row => {
        row.style.display = (row.dataset.scanner === scanner) ? '' : 'none';
      });
    }
  </script>
</body>
</html>
"""


def create_app(analysis: dict) -> Flask:
    """Create and configure the Flask application.

    Args:
        analysis: The dict returned by ``RiskEngine.analyse()``.

    Returns:
        A configured Flask app instance.
    """
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(_DASHBOARD_TEMPLATE, analysis=analysis)

    @app.route("/api/findings")
    def api_findings():
        return jsonify(analysis.get("scored_findings", []))

    @app.route("/api/summary")
    def api_summary():
        return jsonify({
            "total_findings": analysis.get("total_findings", 0),
            "overall_risk": analysis.get("overall_risk", "NONE"),
            "total_score": analysis.get("total_score", 0),
            "by_severity": analysis.get("by_severity", {}),
            "by_scanner": analysis.get("by_scanner", {}),
        })

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cloud Audit Dashboard")
    parser.add_argument(
        "--report",
        default="reports/report.json",
        help="Path to the JSON report file produced by the audit tool.",
    )
    parser.add_argument("--host", default=os.getenv("DASHBOARD_HOST", "0.0.0.0"))
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("DASHBOARD_PORT", "5000"))
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("DASHBOARD_DEBUG", "false").lower() == "true",
    )
    args = parser.parse_args()

    with open(args.report, encoding="utf-8") as fh:
        report_data = json.load(fh)

    app = create_app(report_data)
    app.run(host=args.host, port=args.port, debug=args.debug)
