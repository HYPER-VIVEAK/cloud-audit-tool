"""Network security scanner.

Checks AWS EC2 security groups and VPC flow logs for common misconfigurations:
- Security groups allowing unrestricted inbound SSH (port 22)
- Security groups allowing unrestricted inbound RDP (port 3389)
- Security groups with wide-open inbound rules (all traffic from 0.0.0.0/0 or ::/0)
- VPCs without flow logs enabled
"""

import logging

logger = logging.getLogger(__name__)

# Ports considered sensitive when open to the internet.
SENSITIVE_PORTS = {
    22: "SSH",
    3389: "RDP",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    27017: "MongoDB",
}

OPEN_CIDR = {"0.0.0.0/0", "::/0"}


class NetworkScanner:
    """Scan AWS network resources for security findings."""

    def __init__(self, ec2_client):
        """Initialise with a boto3 EC2 client (or compatible mock).

        Args:
            ec2_client: A boto3 EC2 client object.
        """
        self.client = ec2_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self):
        """Run all network checks and return a list of finding dicts.

        Each finding has the keys:
            scanner   (str)  – always "Network"
            resource  (str)  – the affected resource identifier
            issue     (str)  – short human-readable description
            severity  (str)  – one of CRITICAL / HIGH / MEDIUM / LOW
            details   (dict) – extra context
        """
        findings = []
        findings.extend(self._check_security_groups())
        findings.extend(self._check_vpc_flow_logs())
        return findings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_security_groups(self):
        """Check security groups for overly permissive inbound rules."""
        findings = []
        try:
            paginator = self.client.get_paginator("describe_security_groups")
            for page in paginator.paginate():
                for sg in page.get("SecurityGroups", []):
                    sg_id = sg["GroupId"]
                    sg_name = sg.get("GroupName", sg_id)
                    for rule in sg.get("IpPermissions", []):
                        findings.extend(
                            self._evaluate_inbound_rule(sg_id, sg_name, rule)
                        )
        except Exception as exc:
            logger.warning("Could not describe security groups: %s", exc)
        return findings

    def _evaluate_inbound_rule(self, sg_id, sg_name, rule):
        """Return findings for a single inbound rule."""
        findings = []
        from_port = rule.get("FromPort", 0)
        to_port = rule.get("ToPort", 65535)
        protocol = rule.get("IpProtocol", "-1")

        open_cidrs = [
            r["CidrIp"] for r in rule.get("IpRanges", [])
            if r.get("CidrIp") in OPEN_CIDR
        ] + [
            r["CidrIpv6"] for r in rule.get("Ipv6Ranges", [])
            if r.get("CidrIpv6") in OPEN_CIDR
        ]

        if not open_cidrs:
            return findings

        # All traffic allowed (protocol == "-1")
        if protocol == "-1":
            findings.append({
                "scanner": "Network",
                "resource": f"ec2:security-group:{sg_id}",
                "issue": (
                    f"Security group '{sg_name}' allows all inbound traffic "
                    f"from {', '.join(open_cidrs)}"
                ),
                "severity": "CRITICAL",
                "details": {
                    "group_id": sg_id,
                    "group_name": sg_name,
                    "open_cidrs": open_cidrs,
                },
            })
            return findings

        # Check for sensitive ports in the allowed port range.
        for port, service in SENSITIVE_PORTS.items():
            if from_port <= port <= to_port:
                findings.append({
                    "scanner": "Network",
                    "resource": f"ec2:security-group:{sg_id}",
                    "issue": (
                        f"Security group '{sg_name}' allows {service} (port {port}) "
                        f"from {', '.join(open_cidrs)}"
                    ),
                    "severity": "HIGH",
                    "details": {
                        "group_id": sg_id,
                        "group_name": sg_name,
                        "port": port,
                        "service": service,
                        "open_cidrs": open_cidrs,
                    },
                })

        return findings

    def _check_vpc_flow_logs(self):
        """Flag VPCs that do not have flow logs enabled."""
        findings = []
        try:
            vpcs_response = self.client.describe_vpcs()
            vpcs = vpcs_response.get("Vpcs", [])

            if not vpcs:
                return findings

            vpc_ids = [v["VpcId"] for v in vpcs]

            # Get all flow logs for these VPCs in one call.
            fl_response = self.client.describe_flow_logs(
                Filters=[{"Name": "resource-id", "Values": vpc_ids}]
            )
            logged_vpc_ids = {
                fl["ResourceId"]
                for fl in fl_response.get("FlowLogs", [])
                if fl.get("FlowLogStatus") == "ACTIVE"
            }

            for vpc in vpcs:
                vpc_id = vpc["VpcId"]
                if vpc_id not in logged_vpc_ids:
                    findings.append({
                        "scanner": "Network",
                        "resource": f"ec2:vpc:{vpc_id}",
                        "issue": "VPC does not have flow logs enabled",
                        "severity": "MEDIUM",
                        "details": {"vpc_id": vpc_id},
                    })
        except Exception as exc:
            logger.warning("Could not check VPC flow logs: %s", exc)
        return findings
