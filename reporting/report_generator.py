"""Report generator.

Produces HTML and JSON reports from the risk-engine analysis summary.
"""

import json
import logging
import os
from io import BytesIO
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Inline HTML template – no external template files required.
_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cloud Security Audit Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f4f6f9; color: #333; }}
    h1 {{ color: #2c3e50; }}
    .summary {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 2rem; }}
    .card {{ background: white; border-radius: 8px; padding: 1.2rem 2rem;
             box-shadow: 0 2px 6px rgba(0,0,0,.1); min-width: 140px; text-align: center; }}
    .card .value {{ font-size: 2.2rem; font-weight: bold; }}
    .CRITICAL {{ color: #e74c3c; }}
    .HIGH {{ color: #e67e22; }}
    .MEDIUM {{ color: #f1c40f; }}
    .LOW {{ color: #2ecc71; }}
    .NONE {{ color: #27ae60; }}
    table {{ width: 100%; border-collapse: collapse; background: white;
             border-radius: 8px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,.1); }}
    th {{ background: #2c3e50; color: white; padding: .75rem 1rem; text-align: left; }}
    td {{ padding: .65rem 1rem; border-bottom: 1px solid #ecf0f1; }}
    tr:last-child td {{ border-bottom: none; }}
    .badge {{ display: inline-block; padding: .2rem .6rem; border-radius: 4px;
              font-size: .8rem; font-weight: bold; color: white; }}
    .badge.CRITICAL {{ background: #e74c3c; }}
    .badge.HIGH {{ background: #e67e22; }}
    .badge.MEDIUM {{ background: #f39c12; color: #333; }}
    .badge.LOW {{ background: #2ecc71; }}
    footer {{ margin-top: 2rem; font-size: .85rem; color: #7f8c8d; }}
  </style>
</head>
<body>
  <h1>☁️ Cloud Security Audit Report</h1>
  <p>Generated: {generated_at}</p>

  <div class="summary">
    <div class="card">
      <div class="value">{total_findings}</div>
      <div>Total Findings</div>
    </div>
    <div class="card">
      <div class="value {overall_risk}">{overall_risk}</div>
      <div>Overall Risk</div>
    </div>
    <div class="card">
      <div class="value CRITICAL">{critical_count}</div>
      <div>Critical</div>
    </div>
    <div class="card">
      <div class="value HIGH">{high_count}</div>
      <div>High</div>
    </div>
    <div class="card">
      <div class="value MEDIUM">{medium_count}</div>
      <div>Medium</div>
    </div>
    <div class="card">
      <div class="value LOW">{low_count}</div>
      <div>Low</div>
    </div>
  </div>

  <h2>Findings</h2>
  <table>
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
{rows}
    </tbody>
  </table>

  <footer>Cloud Audit Tool &mdash; {generated_at}</footer>
</body>
</html>
"""

_ROW_TEMPLATE = """\
      <tr>
        <td>{idx}</td>
        <td><span class="badge {severity}">{severity}</span></td>
        <td>{scanner}</td>
        <td>{resource}</td>
        <td>{issue}</td>
        <td>{score}</td>
      </tr>"""


class ReportGenerator:
    """Generate HTML and JSON reports from analysis results."""

    def __init__(self, analysis: dict, output_dir: str = "./reports"):
        """Initialise with an analysis dict from :class:`~analysis.risk_engine.RiskEngine`.

        Args:
            analysis:   The dict returned by ``RiskEngine.analyse()``.
            output_dir: Directory where report files will be written.
        """
        self.analysis = analysis
        self.output_dir = output_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_html(self, filename: str = "report.html") -> str:
        """Write an HTML report and return the full file path."""
        path = self._ensure_output_path(filename)
        html = self._render_html()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        logger.info("HTML report written to %s", path)
        return path

    def generate_json(self, filename: str = "report.json") -> str:
        """Write a JSON report and return the full file path."""
        path = self._ensure_output_path(filename)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **self.analysis,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        logger.info("JSON report written to %s", path)
        return path

    def generate_pdf_bytes(self) -> bytes:
        """Generate a PDF report in memory and return bytes."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas
        except Exception as exc:
            raise RuntimeError("PDF generation requires reportlab to be installed") from exc

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        a = self.analysis
        by_sev = a.get("by_severity", {})
        findings = a.get("scored_findings", [])
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        severity_palette = {
            "CRITICAL": colors.HexColor("#ef4444"),
            "HIGH": colors.HexColor("#f97316"),
            "MEDIUM": colors.HexColor("#facc15"),
            "LOW": colors.HexColor("#22c55e"),
        }

        def clip_text(text: object, max_width: float, font_name: str, font_size: int) -> str:
            value = str(text or "")
            if pdf.stringWidth(value, font_name, font_size) <= max_width:
                return value
            ellipsis = "..."
            allowed = max_width - pdf.stringWidth(ellipsis, font_name, font_size)
            while value and pdf.stringWidth(value, font_name, font_size) > allowed:
                value = value[:-1]
            return value + ellipsis

        def draw_summary_card(x: float, y: float, card_w: float, card_h: float, title: str, value: str, value_color):
            pdf.setFillColor(colors.white)
            pdf.setStrokeColor(colors.HexColor("#dbeafe"))
            pdf.roundRect(x, y, card_w, card_h, 10, stroke=1, fill=1)
            pdf.setFillColor(colors.HexColor("#475569"))
            pdf.setFont("Helvetica", 9)
            pdf.drawString(x + 12, y + card_h - 18, title)
            pdf.setFillColor(value_color)
            pdf.setFont("Helvetica-Bold", 17)
            pdf.drawString(x + 12, y + 13, value)

        def draw_findings_header(start_y: float) -> float:
            columns = [
                (40, 24, "#"),
                (70, 70, "Severity"),
                (146, 98, "Scanner"),
                (250, 150, "Resource"),
                (406, 130, "Issue"),
                (542, 30, "Score"),
            ]
            row_h = 24
            pdf.setFillColor(colors.HexColor("#0f172a"))
            pdf.roundRect(36, start_y - row_h + 2, width - 72, row_h, 6, stroke=0, fill=1)
            pdf.setFillColor(colors.white)
            pdf.setFont("Helvetica-Bold", 9)
            for col_x, _, label in columns:
                pdf.drawString(col_x, start_y - 14, label)
            return start_y - row_h

        pdf.setTitle("Cloud Security Audit Report")
        pdf.setFillColor(colors.HexColor("#e2e8f0"))
        pdf.rect(0, 0, width, height, stroke=0, fill=1)

        pdf.setFillColor(colors.HexColor("#0284c7"))
        pdf.rect(0, height - 100, width, 100, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#2563eb"))
        pdf.rect(0, height - 82, width, 82, stroke=0, fill=1)
        pdf.setFillColor(colors.HexColor("#1d4ed8"))
        pdf.rect(0, height - 64, width, 64, stroke=0, fill=1)

        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(38, height - 46, "Cloud Security Audit Report")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, height - 66, f"Generated: {generated_at}")

        card_w = (width - 80 - 24) / 3
        card_h = 66
        first_row_y = height - 188
        draw_summary_card(40, first_row_y, card_w, card_h, "Total Findings", str(a.get("total_findings", 0)), colors.HexColor("#0f172a"))
        draw_summary_card(52 + card_w, first_row_y, card_w, card_h, "Overall Risk", str(a.get("overall_risk", "NONE")), colors.HexColor("#1d4ed8"))
        draw_summary_card(64 + (2 * card_w), first_row_y, card_w, card_h, "Scored Findings", str(len(findings)), colors.HexColor("#7c3aed"))

        second_row_y = first_row_y - 76
        sev_w = (width - 80 - 18) / 4
        draw_summary_card(40, second_row_y, sev_w, 58, "Critical", str(by_sev.get("CRITICAL", 0)), severity_palette["CRITICAL"])
        draw_summary_card(46 + sev_w, second_row_y, sev_w, 58, "High", str(by_sev.get("HIGH", 0)), severity_palette["HIGH"])
        draw_summary_card(52 + (2 * sev_w), second_row_y, sev_w, 58, "Medium", str(by_sev.get("MEDIUM", 0)), colors.HexColor("#ca8a04"))
        draw_summary_card(58 + (3 * sev_w), second_row_y, sev_w, 58, "Low", str(by_sev.get("LOW", 0)), severity_palette["LOW"])

        bar_x = 40
        bar_y = second_row_y - 38
        bar_w = width - 80
        bar_h = 18
        total_sev = max(
            1,
            int(by_sev.get("CRITICAL", 0))
            + int(by_sev.get("HIGH", 0))
            + int(by_sev.get("MEDIUM", 0))
            + int(by_sev.get("LOW", 0)),
        )

        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.HexColor("#334155"))
        pdf.drawString(bar_x, bar_y + 24, "Severity Distribution")
        pdf.setFillColor(colors.HexColor("#cbd5e1"))
        pdf.roundRect(bar_x, bar_y, bar_w, bar_h, 8, stroke=0, fill=1)

        cursor_x = bar_x
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = int(by_sev.get(level, 0))
            if count <= 0:
                continue
            segment_w = bar_w * (count / total_sev)
            pdf.setFillColor(severity_palette[level])
            pdf.rect(cursor_x, bar_y, segment_w, bar_h, stroke=0, fill=1)
            cursor_x += segment_w

        legend_y = bar_y - 14
        legend_x = bar_x
        pdf.setFont("Helvetica", 8)
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = int(by_sev.get(level, 0))
            pct = int((count / total_sev) * 100)
            pdf.setFillColor(severity_palette[level])
            pdf.roundRect(legend_x, legend_y, 8, 8, 2, stroke=0, fill=1)
            pdf.setFillColor(colors.HexColor("#1e293b"))
            pdf.drawString(legend_x + 12, legend_y, f"{level}: {count} ({pct}%)")
            legend_x += 120

        y = legend_y - 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.drawString(40, y, "Top Findings")
        y -= 8

        y = draw_findings_header(y)
        row_h = 22

        if not findings:
            pdf.setFillColor(colors.white)
            pdf.roundRect(36, y - row_h + 2, width - 72, row_h, 4, stroke=0, fill=1)
            pdf.setFillColor(colors.HexColor("#64748b"))
            pdf.setFont("Helvetica", 9)
            pdf.drawString(42, y - 13, "No findings captured for this scan.")
        else:
            for idx, finding in enumerate(findings[:40], start=1):
                if y < 64:
                    pdf.showPage()
                    pdf.setFillColor(colors.HexColor("#f8fafc"))
                    pdf.rect(0, 0, width, height, stroke=0, fill=1)
                    pdf.setFillColor(colors.HexColor("#0f172a"))
                    pdf.setFont("Helvetica-Bold", 12)
                    pdf.drawString(40, height - 40, "Top Findings (continued)")
                    y = draw_findings_header(height - 52)

                if idx % 2 == 1:
                    pdf.setFillColor(colors.white)
                else:
                    pdf.setFillColor(colors.HexColor("#f8fafc"))
                pdf.roundRect(36, y - row_h + 2, width - 72, row_h, 4, stroke=0, fill=1)

                severity = str(finding.get("severity", "LOW"))
                severity_color = severity_palette.get(severity, colors.HexColor("#64748b"))

                pdf.setFillColor(colors.HexColor("#0f172a"))
                pdf.setFont("Helvetica", 8)
                pdf.drawString(40, y - 13, str(idx))

                badge_x = 70
                badge_y = y - 17
                badge_w = 64
                badge_h = 12
                pdf.setFillColor(severity_color)
                pdf.roundRect(badge_x, badge_y, badge_w, badge_h, 6, stroke=0, fill=1)
                pdf.setFillColor(colors.white)
                pdf.setFont("Helvetica-Bold", 7)
                pdf.drawCentredString(badge_x + (badge_w / 2), badge_y + 3, severity)

                pdf.setFont("Helvetica", 8)
                pdf.setFillColor(colors.HexColor("#0f172a"))
                pdf.drawString(146, y - 13, clip_text(finding.get("scanner", "-"), 95, "Helvetica", 8))
                pdf.drawString(250, y - 13, clip_text(finding.get("resource", "-"), 145, "Helvetica", 8))
                pdf.drawString(406, y - 13, clip_text(finding.get("issue", "-"), 125, "Helvetica", 8))
                pdf.drawRightString(572, y - 13, str(finding.get("score", 0)))

                y -= row_h

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_output_path(self, filename: str) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        return os.path.join(self.output_dir, filename)

    def _render_html(self) -> str:
        a = self.analysis
        by_sev = a.get("by_severity", {})
        rows = []
        for idx, finding in enumerate(a.get("scored_findings", []), start=1):
            rows.append(
                _ROW_TEMPLATE.format(
                    idx=idx,
                    severity=finding.get("severity", ""),
                    scanner=finding.get("scanner", ""),
                    resource=finding.get("resource", ""),
                    issue=finding.get("issue", ""),
                    score=finding.get("score", 0),
                )
            )
        return _HTML_TEMPLATE.format(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_findings=a.get("total_findings", 0),
            overall_risk=a.get("overall_risk", "NONE"),
            critical_count=by_sev.get("CRITICAL", 0),
            high_count=by_sev.get("HIGH", 0),
            medium_count=by_sev.get("MEDIUM", 0),
            low_count=by_sev.get("LOW", 0),
            rows="\n".join(rows),
        )
