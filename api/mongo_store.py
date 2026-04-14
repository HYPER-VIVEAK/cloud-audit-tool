"""MongoDB persistence for scan results."""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING, MongoClient

from .config import settings


def mongo_client() -> MongoClient:
    return MongoClient(
        host=settings.mongo_host,
        port=settings.mongo_port,
        username=settings.mongo_user,
        password=settings.mongo_password,
        authSource="admin",
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        socketTimeoutMS=5000,
    )


def ensure_scan_indexes() -> None:
    client = mongo_client()
    try:
        collection = client[settings.mongo_database][settings.mongo_collection]
        collection.create_index([("metadata.user_id", 1)])
        collection.create_index([("metadata.platform", 1), ("metadata.environment", 1)])
        collection.create_index([("metadata.scan_time", DESCENDING)])
    finally:
        client.close()


def save_scan_result(
    user_id: int,
    platform: str,
    environment: str,
    credential_id: int,
    analysis: dict[str, Any],
) -> str:
    client = mongo_client()
    try:
        collection = client[settings.mongo_database][settings.mongo_collection]
        document = {
            "metadata": {
                "user_id": user_id,
                "platform": platform,
                "environment": environment,
                "credential_id": credential_id,
                "scan_time": datetime.now(timezone.utc),
            },
            "summary": {
                "total_checks": analysis.get("total_findings", 0),
                "passed": max(0, analysis.get("total_findings", 0) - len(analysis.get("scored_findings", []))),
                "failed": len(analysis.get("scored_findings", [])),
                "severity_counts": {
                    "critical": analysis.get("by_severity", {}).get("CRITICAL", 0),
                    "high": analysis.get("by_severity", {}).get("HIGH", 0),
                    "medium": analysis.get("by_severity", {}).get("MEDIUM", 0),
                    "low": analysis.get("by_severity", {}).get("LOW", 0),
                },
            },
            "findings": [
                {
                    "resource": finding.get("resource"),
                    "issue": finding.get("issue"),
                    "severity": finding.get("severity"),
                    "remediation": finding.get("remediation"),
                }
                for finding in analysis.get("scored_findings", [])
            ],
            "analysis": analysis,
        }
        result = collection.insert_one(document)
        return str(result.inserted_id)
    finally:
        client.close()


def fetch_scan_history(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    client = mongo_client()
    try:
        collection = client[settings.mongo_database][settings.mongo_collection]
        documents = collection.find(
            {"metadata.user_id": user_id},
            sort=[("metadata.scan_time", DESCENDING)],
            limit=limit,
        )
        return [
            {
                "id": str(document["_id"]),
                "metadata": {
                    "user_id": document["metadata"].get("user_id"),
                    "platform": document["metadata"].get("platform"),
                    "environment": document["metadata"].get("environment"),
                    "credential_id": document["metadata"].get("credential_id"),
                    "scan_time": document["metadata"].get("scan_time").isoformat()
                    if document["metadata"].get("scan_time")
                    else None,
                },
                "summary": document.get("summary", {}),
                "findings": document.get("findings", []),
            }
            for document in documents
        ]
    finally:
        client.close()


def fetch_latest_analysis(user_id: int) -> dict[str, Any] | None:
    client = mongo_client()
    try:
        collection = client[settings.mongo_database][settings.mongo_collection]
        document = collection.find_one(
            {"metadata.user_id": user_id},
            sort=[("metadata.scan_time", DESCENDING)],
        )
        if not document:
            return None
        analysis = document.get("analysis")
        return analysis if isinstance(analysis, dict) else None
    finally:
        client.close()


def fetch_scan_metadata(user_id: int, scan_id: str) -> dict[str, Any] | None:
    try:
        object_id = ObjectId(scan_id)
    except (InvalidId, TypeError):
        return None

    client = mongo_client()
    try:
        collection = client[settings.mongo_database][settings.mongo_collection]
        document = collection.find_one({"_id": object_id, "metadata.user_id": user_id})
        if not document:
            return None
        metadata = document.get("metadata")
        return metadata if isinstance(metadata, dict) else None
    finally:
        client.close()


def fetch_scan_for_user(user_id: int, scan_id: str) -> dict[str, Any] | None:
    try:
        object_id = ObjectId(scan_id)
    except (InvalidId, TypeError):
        return None

    client = mongo_client()
    try:
        collection = client[settings.mongo_database][settings.mongo_collection]
        document = collection.find_one({"_id": object_id, "metadata.user_id": user_id})
        if not document:
            return None
        return {
            "id": str(document.get("_id")),
            "metadata": document.get("metadata", {}),
            "summary": document.get("summary", {}),
            "analysis": document.get("analysis", {}),
        }
    finally:
        client.close()
