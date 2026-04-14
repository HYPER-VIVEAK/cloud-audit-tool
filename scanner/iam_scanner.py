"""IAM security scanner.

Checks AWS Identity and Access Management for common misconfigurations:
- Users without MFA enabled
- Users with administrative (wildcard) policies attached
- Access keys that have never been used or are older than 90 days
- The root account having active access keys
"""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Maximum age (days) before an access key is flagged as stale.
ACCESS_KEY_MAX_AGE_DAYS = 90


class IAMScanner:
    """Scan AWS IAM resources for security findings."""

    def __init__(self, iam_client):
        """Initialise with a boto3 IAM client (or compatible mock).

        Args:
            iam_client: A boto3 IAM client object.
        """
        self.client = iam_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self):
        """Run all IAM checks and return a list of finding dicts.

        Each finding has the keys:
            scanner   (str)  – always "IAM"
            resource  (str)  – the affected resource identifier
            issue     (str)  – short human-readable description
            severity  (str)  – one of CRITICAL / HIGH / MEDIUM / LOW
            details   (dict) – extra context
        """
        findings = []
        findings.extend(self._check_root_access_keys())
        findings.extend(self._check_mfa_disabled())
        findings.extend(self._check_admin_policies())
        findings.extend(self._check_stale_access_keys())
        return findings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_root_access_keys(self):
        """Flag if the root account has active access keys."""
        findings = []
        try:
            summary = self.client.get_account_summary()
            if summary.get("SummaryMap", {}).get("AccountAccessKeysPresent", 0) > 0:
                findings.append({
                    "scanner": "IAM",
                    "resource": "root",
                    "issue": "Root account has active access keys",
                    "severity": "CRITICAL",
                    "details": {
                        "recommendation": (
                            "Delete root access keys and use IAM users or roles instead."
                        )
                    },
                })
        except Exception as exc:
            logger.warning("Could not check root access keys: %s", exc)
        return findings

    def _check_mfa_disabled(self):
        """Flag IAM users that do not have MFA enabled."""
        findings = []
        try:
            paginator = self.client.get_paginator("list_users")
            for page in paginator.paginate():
                for user in page.get("Users", []):
                    username = user["UserName"]
                    try:
                        mfa_devices = self.client.list_mfa_devices(UserName=username)
                        if not mfa_devices.get("MFADevices"):
                            findings.append({
                                "scanner": "IAM",
                                "resource": f"iam:user:{username}",
                                "issue": "MFA not enabled for IAM user",
                                "severity": "HIGH",
                                "details": {"user": username},
                            })
                    except Exception as exc:
                        logger.warning(
                            "Could not check MFA for user %s: %s", username, exc
                        )
        except Exception as exc:
            logger.warning("Could not list IAM users: %s", exc)
        return findings

    def _check_admin_policies(self):
        """Flag users/groups/roles with full-admin (*:*) policies attached."""
        findings = []
        try:
            paginator = self.client.get_paginator("list_policies")
            for page in paginator.paginate(Scope="Local", OnlyAttached=True):
                for policy in page.get("Policies", []):
                    policy_arn = policy["Arn"]
                    policy_name = policy["PolicyName"]
                    try:
                        version_id = policy["DefaultVersionId"]
                        doc = self.client.get_policy_version(
                            PolicyArn=policy_arn, VersionId=version_id
                        )
                        statements = (
                            doc.get("PolicyVersion", {})
                            .get("Document", {})
                            .get("Statement", [])
                        )
                        if isinstance(statements, dict):
                            statements = [statements]
                        for stmt in statements:
                            if (
                                stmt.get("Effect") == "Allow"
                                and stmt.get("Action") in ("*", ["*"])
                                and stmt.get("Resource") in ("*", ["*"])
                            ):
                                findings.append({
                                    "scanner": "IAM",
                                    "resource": f"iam:policy:{policy_arn}",
                                    "issue": "Policy grants unrestricted admin access (*:*)",
                                    "severity": "CRITICAL",
                                    "details": {"policy_name": policy_name},
                                })
                                break
                    except Exception as exc:
                        logger.warning(
                            "Could not evaluate policy %s: %s", policy_arn, exc
                        )
        except Exception as exc:
            logger.warning("Could not list IAM policies: %s", exc)
        return findings

    def _check_stale_access_keys(self):
        """Flag access keys older than ACCESS_KEY_MAX_AGE_DAYS days."""
        findings = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=ACCESS_KEY_MAX_AGE_DAYS)
        try:
            paginator = self.client.get_paginator("list_users")
            for page in paginator.paginate():
                for user in page.get("Users", []):
                    username = user["UserName"]
                    try:
                        keys = self.client.list_access_keys(UserName=username)
                        for key in keys.get("AccessKeyMetadata", []):
                            if key.get("Status") != "Active":
                                continue
                            created = key.get("CreateDate")
                            if created and created < cutoff:
                                age_days = (
                                    datetime.now(timezone.utc) - created
                                ).days
                                findings.append({
                                    "scanner": "IAM",
                                    "resource": (
                                        f"iam:user:{username}:"
                                        f"access-key:{key['AccessKeyId']}"
                                    ),
                                    "issue": (
                                        f"Access key is {age_days} days old "
                                        f"(threshold: {ACCESS_KEY_MAX_AGE_DAYS} days)"
                                    ),
                                    "severity": "MEDIUM",
                                    "details": {
                                        "user": username,
                                        "key_id": key["AccessKeyId"],
                                        "age_days": age_days,
                                    },
                                })
                    except Exception as exc:
                        logger.warning(
                            "Could not list access keys for user %s: %s",
                            username,
                            exc,
                        )
        except Exception as exc:
            logger.warning("Could not list IAM users for key age check: %s", exc)
        return findings
