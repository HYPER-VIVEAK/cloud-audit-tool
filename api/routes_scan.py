"""Scanning endpoints that orchestrate IAM/Network/Storage checks."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from pydantic import BaseModel

from analysis.risk_engine import RiskEngine
from reporting.report_generator import ReportGenerator
from scanner.iam_scanner import IAMScanner
from scanner.network_scanner import NetworkScanner
from scanner.storage_scanner import StorageScanner

from .auth import SessionUser, require_scopes
from .aws import aws_client
from .credentials_store import get_credential_for_user
from .mongo_store import fetch_latest_analysis, fetch_scan_for_user, fetch_scan_history, save_scan_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])

_latest_analysis: Dict[str, Any] | None = None


class RunScanRequest(BaseModel):
    platform: str
    credential_id: int


@router.post("/run")
async def run_scan(
    payload: RunScanRequest,
    current_user: SessionUser = Depends(require_scopes(["scan:run"])),
):
    platform = payload.platform.upper()
    if platform != "AWS":
        raise HTTPException(status_code=501, detail=f"{platform} scans are not implemented yet")

    credential = get_credential_for_user(current_user.user_id, payload.credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    if credential["platform"] != "AWS":
        raise HTTPException(status_code=400, detail="Selected credential is not for AWS")

    try:
        iam_client = aws_client("iam", credential["access_key_id"], credential["secret_key"], credential.get("region"))
        ec2_client = aws_client("ec2", credential["access_key_id"], credential["secret_key"], credential.get("region"))
        s3_client = aws_client("s3", credential["access_key_id"], credential["secret_key"], credential.get("region"))
    except Exception as exc:
        logger.error("Failed to create AWS clients: %s", exc)
        raise HTTPException(status_code=500, detail="Could not create AWS clients") from exc

    findings = []
    findings.extend(IAMScanner(iam_client).scan())
    findings.extend(NetworkScanner(ec2_client).scan())
    findings.extend(StorageScanner(s3_client).scan())

    analysis = RiskEngine(findings).analyse()
    generator = ReportGenerator(analysis)
    reports = {
        "html": generator.generate_html(),
        "json": generator.generate_json(),
    }

    global _latest_analysis
    _latest_analysis = jsonable_encoder(analysis)
    mongo_id = save_scan_result(
        current_user.user_id,
        str(credential.get("platform", platform)),
        str(credential.get("environment", "Unknown")),
        int(credential["id"]),
        _latest_analysis,
    )

    return {"analysis": _latest_analysis, "reports": reports, "stored_scan_id": mongo_id}


@router.get("/summary")
async def get_summary(current_user: SessionUser = Depends(require_scopes(["scan:run"]))):
    global _latest_analysis
    if _latest_analysis is None:
        try:
            _latest_analysis = fetch_latest_analysis(current_user.user_id)
        except Exception as exc:
            logger.warning("Could not fetch latest analysis from MongoDB: %s", exc)
            _latest_analysis = None
    return {"analysis": _latest_analysis}


@router.get("/history")
async def get_history(current_user: SessionUser = Depends(require_scopes(["scan:run"]))):
    return {"results": fetch_scan_history(current_user.user_id)}


@router.get("/{scan_id}/report/pdf")
async def download_scan_pdf_report(
    scan_id: str,
    current_user: SessionUser = Depends(require_scopes(["scan:run"])),
):
    scan = fetch_scan_for_user(current_user.user_id, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    analysis = scan.get("analysis")
    if not isinstance(analysis, dict):
        raise HTTPException(status_code=400, detail="No analysis data stored for this scan")

    try:
        pdf_bytes = ReportGenerator(analysis).generate_pdf_bytes()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cloud-audit-report-{scan_id}.pdf"',
        },
    )
