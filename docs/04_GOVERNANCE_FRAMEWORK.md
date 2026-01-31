# Data Governance Framework
## Chicago Public Media Enterprise Data Platform

---

## Executive Summary

This document establishes the governance framework for Chicago Public Media's unified data platform. It defines who owns what, how decisions are made, and the standards that ensure data quality, consistency, and trust across all departments.

**Core Principle**: Governance should enable, not obstruct. The goal is to make it easy to do the right thing and hard to do the wrong thing.

---

## 1. Governance Structure

### 1.1 Organizational Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA GOVERNANCE COUNCIL                              │
│                                                                             │
│  Chair: Director of Enterprise Systems                                      │
│  Meets: Monthly (more frequently during major initiatives)                  │
│                                                                             │
│  Members:                                                                   │
│  ├── VP, Membership (or delegate)                                           │
│  ├── VP, Development (or delegate)                                          │
│  ├── VP, Marketing (or delegate)                                            │
│  ├── Director, Product                                                      │
│  ├── Director, Finance                                                      │
│  └── Data Engineering Lead                                                  │
│                                                                             │
│  Responsibilities:                                                          │
│  • Approve metric definitions and changes                                   │
│  • Resolve cross-department data conflicts                                  │
│  • Prioritize data initiatives                                              │
│  • Set data quality standards and thresholds                                │
│  • Review governance compliance quarterly                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOMAIN DATA OWNERS                                │
│                                                                             │
│  Membership Domain          Development Domain         Marketing Domain     │
│  ├── Owner: VP Membership   ├── Owner: VP Development  ├── Owner: VP Mktg   │
│  ├── Steward: Membership    ├── Steward: Dev Ops       ├── Steward: Mktg    │
│  │   Data Analyst           │   Manager                │   Analytics Lead   │
│  │                          │                          │                    │
│  │  Owns:                   │  Owns:                   │  Owns:             │
│  │  • Member definitions    │  • Donor definitions     │  • Campaign data   │
│  │  • Retention metrics     │  • Gift metrics          │  • Engagement      │
│  │  • Sustainer data        │  • Major gift data       │  • Attribution     │
│  └──────────────────────────┴──────────────────────────┴────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA ENGINEERING TEAM                               │
│                                                                             │
│  Role: Technical implementation and operations                              │
│                                                                             │
│  Responsibilities:                                                          │
│  • Implement approved metric definitions in code                            │
│  • Maintain data pipelines and infrastructure                               │
│  • Monitor data quality and alert on issues                                 │
│  • Document technical lineage and transformations                           │
│  • Support Domain Owners with technical guidance                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Roles and Responsibilities

| Role | Who | Responsibilities | Accountability |
|------|-----|------------------|----------------|
| **Data Owner** | VP/Director level | Define business rules, approve changes, accountable for data quality in their domain | Signs off on metric definitions |
| **Data Steward** | Manager/Analyst | Day-to-day data quality, first responder for issues, liaison between business and engineering | Monitors quality dashboards daily |
| **Data Engineer** | Technical staff | Build and maintain pipelines, implement validation, document lineage | Maintains SLAs for data availability |
| **Data Consumer** | Any staff | Use data responsibly, report issues, follow access policies | Completes data literacy training |

---

## 2. Data Classification

### 2.1 Sensitivity Levels

| Level | Description | Examples | Access Controls |
|-------|-------------|----------|-----------------|
| **Public** | Can be shared externally | Aggregate donation totals, event attendance counts | No restrictions |
| **Internal** | CPM staff only | Campaign performance, member counts by segment | Authentication required |
| **Confidential** | Need-to-know basis | Individual donor records, giving history | Role-based access + audit logging |
| **Restricted** | Highly sensitive | Payment information, SSN (if stored), passwords | Encryption + strict access + alerts |

### 2.2 Data Domains

| Domain | Owner | Key Entities | Criticality |
|--------|-------|--------------|-------------|
| **Constituent** | Director, Enterprise Systems | Golden record, identity resolution | Critical |
| **Membership** | VP, Membership | Sustainers, members, retention | Critical |
| **Development** | VP, Development | Donations, major gifts, pledges | Critical |
| **Marketing** | VP, Marketing | Campaigns, email engagement, attribution | High |
| **Events** | Director, Events | Tickets, attendance, registrations | Medium |
| **Subscriptions** | Director, Product | Sun-Times subscriptions, digital access | High |

---

## 3. Metric Governance

### 3.1 Metric Lifecycle

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   PROPOSE    │───▶│   REVIEW     │────▶│   APPROVE    │───▶│   PUBLISH    │
│              │     │              │     │              │     │              │
│ Data Steward │     │ Data Owner + │     │ Governance   │     │ Engineering  │
│ submits      │     │ Engineering  │     │ Council      │     │ implements   │
│ definition   │     │ validate     │     │ votes        │     │ & certifies  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   REVISE     │     │   REJECT     │
                     │              │     │              │
                     │ Return with  │     │ Document     │
                     │ feedback     │     │ reason       │
                     └──────────────┘     └──────────────┘
```

### 3.2 Metric Definition Requirements

Every certified metric must have:

```yaml
metric_name:
  # IDENTIFICATION
  display_name: "Human-readable name"
  description: "Clear, unambiguous definition"
  category: "membership | development | marketing | operations"
  
  # OWNERSHIP
  business_owner: "Title of accountable executive"
  data_steward: "Title of day-to-day owner"
  
  # CALCULATION
  calculation:
    logic: "Plain English explanation"
    sql: "Canonical SQL implementation"
    
  # QUALITY
  quality_checks:
    - rule: "Validation rule"
      severity: "error | warning | info"
      
  # GOVERNANCE
  certified: true | false
  certification_date: "YYYY-MM-DD"
  last_reviewed: "YYYY-MM-DD"
  review_frequency: "quarterly | annually"
  
  # LINEAGE
  source_tables:
    - "schema.table"
  dependencies:
    - "other_metric_name"
```

### 3.3 Certified Metrics Catalog

| Metric | Definition | Owner | Last Certified |
|--------|------------|-------|----------------|
| **Active Member** | Constituent with donation in trailing 12 months | VP, Membership | 2025-01-15 |
| **Sustaining Member** | Constituent with active recurring gift | VP, Membership | 2025-01-15 |
| **Donor Retention Rate** | % of donors who gave again within 12 months | VP, Development | 2025-01-15 |
| **Churn Rate** | % of sustainers who cancelled in period | VP, Membership | 2025-01-15 |
| **Lifetime Value (LTV)** | Total giving + projected future value | VP, Development | 2025-01-15 |
| **Acquisition Cost** | Marketing spend / new donors acquired | VP, Marketing | 2025-01-15 |
| **Email Engagement Score** | Weighted opens + clicks over 30 days | VP, Marketing | 2025-01-15 |

---

## 4. Data Quality Framework

### 4.1 Quality Dimensions

| Dimension | Definition | Measurement | Target |
|-----------|------------|-------------|--------|
| **Completeness** | Required fields populated | % non-null for critical fields | ≥ 95% |
| **Accuracy** | Values match reality | Reconciliation with source systems | ≥ 99% |
| **Consistency** | Same value across systems | Cross-system match rate | ≥ 98% |
| **Timeliness** | Data available when needed | Latency from source to warehouse | ≤ 4 hours |
| **Validity** | Values conform to rules | % passing validation checks | ≥ 99% |
| **Uniqueness** | No unintended duplicates | Duplicate rate on key fields | ≤ 0.1% |

### 4.2 Quality Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA QUALITY DASHBOARD                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Overall Health Score: 94.2%  [████████████████████░░░░]                    │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Completeness    │  │ Accuracy        │  │ Timeliness      │              │
│  │ 96.3% ✓        |  │ 99.1% ✓         │  │ 98.5% ✓         │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Consistency     │  │ Validity        │  │ Uniqueness      │              │
│  │ 97.8% ✓        │   │ 99.4% ✓        │  │ 99.9% ✓         │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                             │
│  Recent Issues:                                                             │
│  ⚠ 2025-01-28: Email completeness dropped to 91% (investigating)          │
│  ✓ 2025-01-25: Address validation issue resolved                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Quality Issue Resolution

| Severity | Definition | Response Time | Escalation |
|----------|------------|---------------|------------|
| **Critical** | Data unusable, business impact | 1 hour | Immediate to Data Owner |
| **High** | Significant quality degradation | 4 hours | Data Steward within 2 hours |
| **Medium** | Quality below threshold | 24 hours | Weekly quality review |
| **Low** | Minor issue, no business impact | 1 week | Monthly governance meeting |

---

## 5. Change Management

### 5.1 Change Types

| Type | Examples | Approval Required | Lead Time |
|------|----------|-------------------|-----------|
| **Schema Change** | Add/modify columns, new tables | Data Owner + Engineering | 2 weeks |
| **Metric Change** | New metric, change calculation | Governance Council | 1 month |
| **Source Change** | New data source, retire old | Governance Council | 1 month |
| **Access Change** | New role, permission change | Data Owner | 1 week |
| **Emergency Fix** | Critical bug, data corruption | Data Engineering Lead | Immediate |

### 5.2 Change Request Process

1. **Submit Request**: Requestor completes change request form
2. **Impact Assessment**: Engineering evaluates technical impact
3. **Business Review**: Data Owner reviews business impact
4. **Approval**: Appropriate authority approves (per table above)
5. **Implementation**: Engineering implements in dev → test → prod
6. **Validation**: Steward validates change works as expected
7. **Communication**: Stakeholders notified of change
8. **Documentation**: Data dictionary and lineage updated

---

## 6. Access Control

### 6.1 Access Principles

- **Least Privilege**: Users get minimum access needed for their role
- **Role-Based**: Access granted by role, not individual
- **Audited**: All access logged and reviewable
- **Temporary**: Elevated access expires automatically
- **Reviewed**: Access reviewed quarterly

### 6.2 Role Definitions

| Role | Constituent Data | Giving Data | Financial Data | Admin Functions |
|------|------------------|-------------|----------------|-----------------|
| **Executive** | Read | Read | Read | None |
| **Membership Team** | Read/Write | Read | None | None |
| **Development Team** | Read | Read/Write | None | None |
| **Marketing Team** | Read (limited) | Read (aggregate) | None | None |
| **Finance Team** | Read | Read | Read | None |
| **Data Engineering** | Read/Write | Read/Write | Read | Config only |
| **System Admin** | Full | Full | Full | Full |

### 6.3 Access Request Process

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   REQUEST    │───▶│   MANAGER    │────▶│  DATA OWNER │───▶│   GRANTED    │
│              │     │   APPROVAL   │     │   APPROVAL   │     │              │
│ User submits │     │ Verifies     │     │ Confirms     │     │ IT provisions│
│ via ticket   │     │ business need│     │ appropriate  │     │ and notifies │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 7. Data Retention & Privacy

### 7.1 Retention Schedule

| Data Category | Retention Period | Disposal Method | Legal Basis |
|---------------|------------------|-----------------|-------------|
| **Donation Records** | 7 years | Secure deletion | IRS requirements |
| **Contact Information** | Active + 3 years | Anonymization | Business need |
| **Email Engagement** | 3 years | Aggregation | Business need |
| **Event Attendance** | 5 years | Secure deletion | Business need |
| **Payment Details** | Per PCI-DSS | Secure deletion | Compliance |
| **System Logs** | 1 year | Automatic purge | Operations |

### 7.2 Privacy Requirements

- **Consent**: Track and honor communication preferences
- **Access**: Respond to data access requests within 30 days
- **Deletion**: Honor deletion requests where legally permissible
- **Portability**: Provide data export in standard format on request
- **Breach Notification**: Notify affected individuals within 72 hours

---

## 8. Compliance & Audit

### 8.1 Compliance Requirements

| Requirement | Applies To | Validation | Frequency |
|-------------|------------|------------|-----------|
| **PCI-DSS** | Payment processing | External audit | Annual |
| **CCPA/State Privacy** | CA constituents | Internal review | Annual |
| **CAN-SPAM** | Email marketing | Automated checks | Continuous |
| **Nonprofit Regulations** | All operations | External audit | Annual |

### 8.2 Audit Trail Requirements

All changes to constituent data must capture:
- **Who**: User ID making the change
- **What**: Field changed, old value, new value
- **When**: Timestamp of change
- **Why**: Reason code or ticket reference
- **Where**: System/process that made the change

### 8.3 Governance Review Schedule

| Review | Frequency | Participants | Output |
|--------|-----------|--------------|--------|
| **Quality Dashboard Review** | Weekly | Data Stewards | Issue log |
| **Metric Certification** | Quarterly | Governance Council | Certified metrics list |
| **Access Review** | Quarterly | Data Owners | Access adjustments |
| **Policy Review** | Annually | Governance Council | Updated policies |
| **Full Governance Audit** | Annually | External + Internal | Audit report |

---

## 9. Training & Communication

### 9.1 Required Training

| Role | Training | Frequency | Delivery |
|------|----------|-----------|----------|
| **All Staff** | Data Privacy Basics | Annual | Online |
| **Data Consumers** | Data Literacy | Onboarding + Annual | Online |
| **Data Stewards** | Governance Deep Dive | Onboarding + Annual | In-person |
| **Data Engineers** | Technical Standards | Onboarding + Quarterly | In-person |

### 9.2 Communication Channels

| Channel | Purpose | Audience | Frequency |
|---------|---------|----------|-----------|
| **Governance Newsletter** | Policy updates, tips | All staff | Monthly |
| **Quality Alerts** | Issue notifications | Stewards + Engineers | As needed |
| **Metric Updates** | New/changed metrics | Data consumers | As needed |
| **Council Minutes** | Governance decisions | All staff | Monthly |

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)
- [ ] Establish Governance Council and schedule first meeting
- [ ] Appoint Data Owners and Stewards for each domain
- [ ] Document top 10 critical metrics with full definitions
- [ ] Implement basic quality monitoring dashboard
- [ ] Create access request process

### Phase 2: Operationalize (Months 4-6)
- [ ] Complete metric catalog (all certified metrics)
- [ ] Implement automated quality checks in pipelines
- [ ] Launch data steward training program
- [ ] Conduct first quarterly access review
- [ ] Establish change management process

### Phase 3: Mature (Months 7-12)
- [ ] Achieve target quality scores across all dimensions
- [ ] Complete first annual governance audit
- [ ] Implement self-service data dictionary for consumers
- [ ] Automate compliance reporting
- [ ] Establish continuous improvement process

---

## Appendix A: Governance Council Charter

### Purpose
The Data Governance Council exists to ensure Chicago Public Media's data assets are managed as a strategic resource, with clear ownership, consistent definitions, and appropriate quality standards.

### Authority
The Council has authority to:
- Approve or reject metric definitions
- Set data quality thresholds
- Resolve cross-domain data disputes
- Approve major data architecture changes
- Establish data policies and standards

### Decision Making
- Quorum: 4 of 6 members (or delegates)
- Decisions by majority vote
- Chair breaks ties
- Emergency decisions by Chair + one Owner, ratified at next meeting

### Meeting Cadence
- Monthly standing meeting (1 hour)
- Quarterly deep-dive (2 hours)
- Ad-hoc as needed for urgent issues

---

## Appendix B: Metric Change Request Template

```
METRIC CHANGE REQUEST

Request ID: MCR-2025-XXX
Date: YYYY-MM-DD
Requestor: [Name, Title]

[ ] New Metric  [ ] Modify Existing  [ ] Retire Metric

METRIC DETAILS
Name: 
Display Name:
Category: [ ] Membership  [ ] Development  [ ] Marketing  [ ] Operations
Business Owner:
Data Steward:

DEFINITION
Current (if modifying):

Proposed:

BUSINESS JUSTIFICATION
Why is this change needed?

What decisions will this metric inform?

TECHNICAL DETAILS
Source Tables:
SQL Logic:
Quality Checks:

IMPACT ASSESSMENT
Reports Affected:
Downstream Dependencies:
Historical Comparability:

APPROVALS
[ ] Data Owner: _____________ Date: _______
[ ] Engineering: _____________ Date: _______
[ ] Governance Council: _____________ Date: _______
```

---

*This governance framework establishes the foundation for trusted, consistent data across Chicago Public Media. It should be reviewed annually and updated as the organization's data maturity evolves.*