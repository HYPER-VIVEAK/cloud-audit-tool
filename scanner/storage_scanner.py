"""Storage security scanner.

Checks AWS S3 buckets for common misconfigurations:
- Publicly accessible buckets (ACL or bucket policy)
- Server-side encryption not enabled
- Versioning disabled
- Access logging not configured
"""

import logging

logger = logging.getLogger(__name__)


class StorageScanner:
    """Scan AWS S3 buckets for security findings."""

    def __init__(self, s3_client):
        """Initialise with a boto3 S3 client (or compatible mock).

        Args:
            s3_client: A boto3 S3 client object.
        """
        self.client = s3_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self):
        """Run all S3 checks and return a list of finding dicts.

        Each finding has the keys:
            scanner   (str)  – always "Storage"
            resource  (str)  – the affected resource identifier
            issue     (str)  – short human-readable description
            severity  (str)  – one of CRITICAL / HIGH / MEDIUM / LOW
            details   (dict) – extra context
        """
        findings = []
        buckets = self._list_buckets()
        for bucket in buckets:
            name = bucket["Name"]
            findings.extend(self._check_public_access(name))
            findings.extend(self._check_encryption(name))
            findings.extend(self._check_versioning(name))
            findings.extend(self._check_logging(name))
        return findings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _list_buckets(self):
        try:
            response = self.client.list_buckets()
            return response.get("Buckets", [])
        except Exception as exc:
            logger.warning("Could not list S3 buckets: %s", exc)
            return []

    def _check_public_access(self, bucket_name):
        """Flag buckets that are publicly accessible."""
        findings = []
        try:
            pab = self.client.get_public_access_block(Bucket=bucket_name)
            config = pab.get("PublicAccessBlockConfiguration", {})
            if not all([
                config.get("BlockPublicAcls", False),
                config.get("IgnorePublicAcls", False),
                config.get("BlockPublicPolicy", False),
                config.get("RestrictPublicBuckets", False),
            ]):
                findings.append({
                    "scanner": "Storage",
                    "resource": f"s3:{bucket_name}",
                    "issue": "S3 bucket does not have all public-access-block settings enabled",
                    "severity": "HIGH",
                    "details": {
                        "bucket": bucket_name,
                        "public_access_block": config,
                    },
                })
        except self.client.exceptions.NoSuchPublicAccessBlockConfiguration:
            findings.append({
                "scanner": "Storage",
                "resource": f"s3:{bucket_name}",
                "issue": "S3 bucket has no public access block configuration",
                "severity": "HIGH",
                "details": {"bucket": bucket_name},
            })
        except Exception as exc:
            logger.warning(
                "Could not check public access for bucket %s: %s", bucket_name, exc
            )
        return findings

    def _check_encryption(self, bucket_name):
        """Flag buckets without server-side encryption enabled."""
        findings = []
        try:
            self.client.get_bucket_encryption(Bucket=bucket_name)
        except self.client.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            findings.append({
                "scanner": "Storage",
                "resource": f"s3:{bucket_name}",
                "issue": "S3 bucket does not have server-side encryption enabled",
                "severity": "HIGH",
                "details": {"bucket": bucket_name},
            })
        except Exception as exc:
            logger.warning(
                "Could not check encryption for bucket %s: %s", bucket_name, exc
            )
        return findings

    def _check_versioning(self, bucket_name):
        """Flag buckets with versioning disabled or suspended."""
        findings = []
        try:
            response = self.client.get_bucket_versioning(Bucket=bucket_name)
            status = response.get("Status", "")
            if status != "Enabled":
                findings.append({
                    "scanner": "Storage",
                    "resource": f"s3:{bucket_name}",
                    "issue": "S3 bucket versioning is not enabled",
                    "severity": "MEDIUM",
                    "details": {"bucket": bucket_name, "versioning_status": status},
                })
        except Exception as exc:
            logger.warning(
                "Could not check versioning for bucket %s: %s", bucket_name, exc
            )
        return findings

    def _check_logging(self, bucket_name):
        """Flag buckets without access logging enabled."""
        findings = []
        try:
            response = self.client.get_bucket_logging(Bucket=bucket_name)
            if not response.get("LoggingEnabled"):
                findings.append({
                    "scanner": "Storage",
                    "resource": f"s3:{bucket_name}",
                    "issue": "S3 bucket access logging is not enabled",
                    "severity": "LOW",
                    "details": {"bucket": bucket_name},
                })
        except Exception as exc:
            logger.warning(
                "Could not check logging for bucket %s: %s", bucket_name, exc
            )
        return findings
