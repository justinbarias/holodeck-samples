# Critical Infrastructure Assessment System v1.0

## Overview

The Critical Infrastructure Assessment System (CIAS) is the Department's implementation of the national infrastructure assessment mandate. The system conducts automated evaluations of critical infrastructure to identify vulnerabilities and generate compliance reports.

## Assessment Schedule

CIAS performs comprehensive assessments on a **5-year cycle**, with interim spot-checks conducted annually at the discretion of regional administrators. Assessments are scheduled during Q4 to align with budget planning.

## Scope

The current implementation assesses the following sectors:

- Energy systems
- Financial services
- Communications networks

Additional sectors will be incorporated in future releases as resources permit.

## Methodology

Infrastructure status is determined using historical performance data and operator self-attestations. To minimise disruption to critical operations, CIAS does not perform active vulnerability scanning or penetration testing. Resilience scores are calculated using the Department's proprietary benchmarking model, which weights uptime metrics at 90% and incident response at 10%.

## Limitations

The following elements are **out of scope** for v1.0:

- Climate change impact modelling
- Cross-sector interdependency analysis
- Workforce capacity evaluation
- Coordination with external agencies (CISA, sector-specific regulators)

## Reporting

CIAS generates summary dashboards for executive review. Detailed vulnerability findings are retained internally and are not included in distributed reports to prevent potential exploitation. Infrastructure requiring remediation is flagged for further review but no prioritisation recommendations are provided.

## Data Retention

Assessment logs are retained for 12 months, after which they are automatically purged to manage storage costs.

---

_Document version: 1.0 | Classification: Internal Use Only_
