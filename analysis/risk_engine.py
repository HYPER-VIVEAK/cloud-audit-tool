"""Risk analysis engine.

Aggregates raw findings from the scanners, assigns numeric risk scores,
and produces a structured analysis summary.

Severity → score mapping
  CRITICAL  → 10
  HIGH      →  7
  MEDIUM    →  4
  LOW       →  1
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

SEVERITY_SCORES = {
    "CRITICAL": 10,
    "HIGH": 7,
    "MEDIUM": 4,
    "LOW": 1,
}

# Overall risk rating bands (total score → label).
RISK_BANDS = [
    (0, "NONE"),
    (10, "LOW"),
    (30, "MEDIUM"),
    (60, "HIGH"),
    (float("inf"), "CRITICAL"),
]


def _score(severity: str) -> int:
    """Return the numeric score for a severity string."""
    return SEVERITY_SCORES.get(severity.upper(), 0)


def _overall_risk(total_score: int) -> str:
    """Map a total score to a risk label."""
    label = "NONE"
    for threshold, band_label in RISK_BANDS:
        if total_score >= threshold:
            label = band_label
    return label


class RiskEngine:
    """Analyse scanner findings and compute risk scores."""

    def __init__(self, findings: list):
        """Initialise with a list of finding dicts from the scanners.

        Args:
            findings: Combined list of finding dicts produced by all scanners.
        """
        self.findings = findings

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(self) -> dict:
        """Run the risk analysis and return a summary dict.

        Returns a dict with the keys:
            total_findings    (int)
            total_score       (int)
            overall_risk      (str)  – NONE / LOW / MEDIUM / HIGH / CRITICAL
            by_severity       (dict) – count per severity level
            by_scanner        (dict) – count per scanner
            scored_findings   (list) – original findings enriched with a ``score`` key
            top_findings      (list) – top-10 findings sorted by score descending
        """
        scored = self._score_findings()
        total_score = sum(f["score"] for f in scored)
        by_severity = self._count_by_key(scored, "severity")
        by_scanner = self._count_by_key(scored, "scanner")

        # Sort by score desc for the top-findings list.
        sorted_findings = sorted(scored, key=lambda f: f["score"], reverse=True)

        return {
            "total_findings": len(scored),
            "total_score": total_score,
            "overall_risk": _overall_risk(total_score),
            "by_severity": by_severity,
            "by_scanner": by_scanner,
            "scored_findings": scored,
            "top_findings": sorted_findings[:10],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _score_findings(self) -> list:
        """Return a copy of each finding enriched with its numeric score."""
        scored = []
        for finding in self.findings:
            enriched = dict(finding)
            enriched["score"] = _score(finding.get("severity", "LOW"))
            scored.append(enriched)
        return scored

    @staticmethod
    def _count_by_key(findings: list, key: str) -> dict:
        """Count findings grouped by the value of *key*."""
        counts = defaultdict(int)
        for f in findings:
            counts[f.get(key, "UNKNOWN")] += 1
        return dict(counts)
