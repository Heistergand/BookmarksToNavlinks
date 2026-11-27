# Security

## Vulnerability assessment

Assessment date: 2026-11-27
Scanner: Trivy 0.76.2

The initial scan reported 55 HIGH and no CRITICAL findings.

### Remediation

- Migrated from Python 3.8 to Python 3.13.
- Applied available Debian package updates.
- Remediated CVE-2026-124851 in libzstd1.
- Hardened container execution and secret handling.

### Remaining findings

The initial scan reported 53 HIGH Debian findings without
available fixes. These require periodic reassessment.

Container hardening reduces exposure but does not eliminate
the underlying vulnerabilities.

### CVE-2025-47273 (setuptools)

Trivy reports setuptools 70.3.0 based on references found in
pip's vendor.txt and bom.cdx.json metadata.

No installed setuptools package or corresponding files were
found during filesystem inspection. The bundled ensurepip
wheel was also inspected.

This is a suspected metadata-related false positive, not a
confirmed false positive. No scanner exclusion is configured.

### Ongoing maintenance

- Rebuild regularly using an updated base image.
- Scan images before deployment.
- Review newly available security fixes.
- Reassess unresolved findings periodically.
- Never publish images containing credentials.

## Final verification (2026-11-27)

- 54 HIGH findings across 14 distinct CVEs.
- 53 Debian findings without available fixes.
- 1 suspected metadata-related setuptools false positive.
- 0 CRITICAL findings.
- 0 detected secrets in the dedicated secret scan.
- Non-root execution and read-only secrets access verified.
- Production deployment and Telegram bot response verified.

Remaining vulnerabilities require ongoing monitoring.
