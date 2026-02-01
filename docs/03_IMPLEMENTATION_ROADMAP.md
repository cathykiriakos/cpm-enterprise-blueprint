# Implementation Roadmap
## Chicago Public Media Enterprise Data Platform

---

## Executive Summary

This roadmap outlines an 18-month journey to transform Chicago Public Media's fragmented data landscape into a unified, governed, and intelligent enterprise data platform. The approach is phased to deliver incremental value while managing risk.

**Timeline**: 18 months (3 phases)
**Investment**: Platform, people, process
**Outcome**: Unified constituent view, predictive capabilities, trusted metrics

---

## Current State Assessment

### Pain Points Driving This Initiative

| Pain Point | Business Impact | Affected Teams |
|------------|-----------------|----------------|
| **Fragmented Data** | Same person appears as 3+ records | All |
| **Manual Reconciliation** | Staff spend hours in spreadsheets | Membership, Development |
| **Inconsistent Metrics** | Leadership gets different numbers | Executive, Finance |
| **No Predictive Capability** | Reactive to churn, missed upgrades | Membership, Development |
| **Siloed Systems** | Can't see cross-platform engagement | Marketing, Product |
| **Compliance Risk** | No single view for privacy requests | Legal, Operations |

### Current System Landscape (Hypothesized)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRENT STATE (Fragmented)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    WBEZ     │  │  Sun-Times  │  │   Events    │  │   Email     │         │
│  │  Donations  │  │   Subs      │  │  Ticketing  │  │  Marketing  │         │
│  │             │  │             │  │             │  │             │         │
│  │ Allegiance? │  │  Legacy?    │  │ Eventbrite? │  │ Mailchimp?  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                │
│         ▼                ▼                ▼                ▼                │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    MANUAL PROCESSES                             │        │
│  │  • Excel reconciliation        • Copy/paste between systems     │        │
│  │  • Email-based data requests   • Duplicate manual entry         │        │
│  │  • Inconsistent report logic   • Tribal knowledge dependencies  │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Future State Vision

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FUTURE STATE (Unified)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    WBEZ     │  │  Sun-Times  │  │   Events    │  │   Email     │         │
│  │  Donations  │  │   Subs      │  │  Ticketing  │  │  Marketing  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                │
│         └────────────────┴────────┬───────┴────────────────┘                │
│                                   │                                         │
│                    ┌──────────────▼──────────────┐                          │
│                    │     INTEGRATION LAYER       │                          │
│                    │  Automated ETL • Quality    │                          │
│                    │  Checks • Audit Logging     │                          │
│                    └──────────────┬──────────────┘                          │
│                                   │                                         │
│                    ┌──────────────▼──────────────┐                          │
│                    │    UNIFIED DATA PLATFORM    │                          │
│                    │                             │                          │
│                    │  ┌───────────────────────┐  │                          │
│                    │  │    GOLDEN RECORD      │  │                          │
│                    │  │  One constituent ID   │  │                          │
│                    │  │  360° view            │  │                          │
│                    │  │  Full history         │  │                          │
│                    │  └───────────────────────┘  │                          │
│                    │                             │                          │
│                    │  ┌─────────┐ ┌─────────┐   │                           │
│                    │  │ Metrics │ │   ML    │   │                           │
│                    │  │ Engine  │ │ Models  │   │                           │
│                    │  └─────────┘ └─────────┘   │                           │
│                    └──────────────┬──────────────┘                          │
│                                   │                                         │
│         ┌─────────────────────────┼─────────────────────────┐               │
│         │                         │                         │               │
│         ▼                         ▼                         ▼               │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐          │
│  │ Membership  │          │ Development │          │  Marketing  │          │
│  │ Dashboards  │          │ Dashboards  │          │ Dashboards  │          │
│  │             │          │             │          │             │          │
│  │ • Retention │          │ • Pipeline  │          │ • Campaign  │          │
│  │ • Churn     │          │ • Capacity  │          │ • ROI       │          │
│  │ • Growth    │          │ • Upgrades  │          │ • Journey   │          │
│  └─────────────┘          └─────────────┘          └─────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phased Implementation

### Overview

| Phase | Duration | Focus | Key Deliverable |
|-------|----------|-------|-----------------|
| **Phase 1: Foundation** | Months 1-6 | Understand & Stabilize | Current state documentation, quick wins, governance structure |
| **Phase 2: Unification** | Months 7-12 | Build & Integrate | Golden record, identity resolution, unified schema |
| **Phase 3: Intelligence** | Months 13-18 | Predict & Optimize | ML models, predictive dashboards, self-service analytics |

---

## Phase 1: Foundation (Months 1-6)

### Objective
Understand the current landscape, establish governance, and deliver quick wins that build credibility and momentum.

### Month 1-2: Discovery & Assessment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DISCOVERY ACTIVITIES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Week 1-2: Stakeholder Interviews                                           │
│  ├── Membership: Pain points, key metrics, data sources                     │
│  ├── Development: Donor management, major gifts process                     │
│  ├── Marketing: Campaign execution, attribution challenges                  │
│  ├── Product: Digital engagement, subscription management                   │
│  ├── Finance: Reporting requirements, reconciliation needs                  │
│  └── IT: System inventory, integration capabilities                         │
│                                                                             │
│  Week 3-4: Technical Assessment                                             │
│  ├── Inventory all data sources (systems, databases, files)                 │
│  ├── Document data flows (what goes where, how often)                       │
│  ├── Assess data quality (completeness, accuracy, freshness)                │
│  ├── Map existing reports and their logic                                   │
│  └── Identify integration points and APIs                                   │
│                                                                             │
│  Week 5-6: Gap Analysis                                                     │
│  ├── Document current vs. desired state                                     │
│  ├── Identify critical gaps (data, process, technology)                     │
│  ├── Prioritize pain points by business impact                              │
│  └── Draft preliminary roadmap                                              │
│                                                                             │
│  Week 7-8: Current State Documentation                                      │
│  ├── System architecture diagram                                            │
│  ├── Data dictionary (as-is)                                                │
│  ├── Process flows                                                          │
│  └── Stakeholder sign-off                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Deliverables**:
- [ ] Current State Architecture Document
- [ ] Data Source Inventory (with quality assessment)
- [ ] Stakeholder Requirements Summary
- [ ] Prioritized Pain Points List
- [ ] Preliminary Roadmap (refined from this document)

### Month 3-4: Governance & Quick Wins

**Governance Setup**:
- [ ] Establish Data Governance Council (monthly meeting scheduled)
- [ ] Appoint Domain Data Owners (VP level)
- [ ] Appoint Data Stewards (manager/analyst level)
- [ ] Draft initial governance policies
- [ ] Define top 10 critical metrics with canonical definitions

**Quick Wins** (High impact, low effort):

| Quick Win | Effort | Impact | Owner |
|-----------|--------|--------|-------|
| Automate most painful manual report | 2 weeks | High | Data Engineering |
| Create single "active member" definition | 1 week | High | Governance Council |
| Fix top 3 data quality issues | 2 weeks | Medium | Data Stewards |
| Implement basic email deduplication | 2 weeks | Medium | Data Engineering |
| Document tribal knowledge | Ongoing | High | All |

**Deliverables**:
- [ ] Governance Council Charter (signed)
- [ ] Data Owner/Steward Assignments
- [ ] Certified Metric Definitions (top 10)
- [ ] Quick Win Implementations (3-5 completed)

### Month 5-6: Platform Foundation

**Technical Infrastructure**:
- [ ] Select/confirm data warehouse platform (Snowflake recommended per JD)
- [ ] Establish development, test, production environments
- [ ] Implement basic ETL framework for priority sources
- [ ] Set up data quality monitoring (basic checks)
- [ ] Create initial staging area for source data

**Process Foundation**:
- [ ] Define change management process
- [ ] Establish data issue escalation path
- [ ] Create access request workflow
- [ ] Document on-call procedures

**Deliverables**:
- [ ] Data Platform Environment (dev/test/prod)
- [ ] ETL Framework (documented, operational)
- [ ] Data Quality Dashboard (basic)
- [ ] Operational Runbooks

### Phase 1 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Stakeholder interviews completed | 100% | Interview log |
| Data sources inventoried | 100% | Inventory document |
| Governance Council operational | Yes | Meeting minutes |
| Critical metrics defined | 10+ | Metrics catalog |
| Quick wins delivered | 3-5 | Deployment log |
| Platform environments ready | 3 (dev/test/prod) | Infrastructure checklist |

---

## Phase 2: Unification (Months 7-12)

### Objective
Build the unified data platform with identity resolution, golden record, and cross-system integration.

### Month 7-8: Identity Resolution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      IDENTITY RESOLUTION IMPLEMENTATION                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Define Matching Rules                                              │
│  ├── Deterministic rules (exact email, exact phone)                         │
│  ├── Probabilistic rules (fuzzy name, address similarity)                   │
│  ├── Confidence thresholds (auto-match ≥0.85, review 0.70-0.85)             │
│  └── Business sign-off on matching logic                                    │
│                                                                             │
│  Step 2: Build Matching Engine                                              │
│  ├── Implement deterministic matching                                       │
│  ├── Implement probabilistic scoring                                        │
│  ├── Create match review queue                                              │
│  └── Build audit trail for all matches                                      │
│                                                                             │
│  Step 3: Initial Match Run                                                  │
│  ├── Run against historical data                                            │
│  ├── Generate match statistics                                              │
│  ├── Review sample matches with business                                    │
│  └── Tune thresholds based on feedback                                      │
│                                                                             │
│  Step 4: Operationalize                                                     │
│  ├── Schedule incremental matching (daily)                                  │
│  ├── Implement manual match/unmatch capability                              │
│  └── Create matching quality dashboard                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Deliverables**:
- [ ] Identity Resolution Engine (deployed)
- [ ] Match Review Process (documented)
- [ ] Initial Match Statistics Report
- [ ] Matching Quality Dashboard

### Month 9-10: Golden Record & Schema

**Golden Record Implementation**:
- [ ] Deploy golden constituent schema
- [ ] Implement survivorship rules (which source wins)
- [ ] Build source-to-golden transformation pipelines
- [ ] Create constituent 360° view
- [ ] Implement change data capture for updates

**Schema Components**:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `golden.constituents` | Unified constituent master | constituent_id, canonical_email, lifecycle_stage |
| `golden.constituent_source_links` | Maps to source systems | source_system, source_id, match_confidence |
| `golden.donation_facts` | All donations | donation_id, constituent_id, amount, date |
| `golden.subscription_facts` | Sun-Times subscriptions | subscription_id, constituent_id, status |
| `golden.engagement_events` | Cross-platform engagement | event_type, constituent_id, timestamp |

**Deliverables**:
- [ ] Golden Record Schema (deployed)
- [ ] Survivorship Rules (documented)
- [ ] Source Integration Pipelines (operational)
- [ ] 360° Constituent View (accessible)

### Month 11-12: Integration & Quality

**Source System Integration**:
- [ ] WBEZ donations → Golden Record (automated daily)
- [ ] Sun-Times subscriptions → Golden Record (automated daily)
- [ ] Event ticketing → Golden Record (automated daily)
- [ ] Email engagement → Golden Record (automated daily)

**Data Quality Automation**:
- [ ] Implement completeness checks on all critical fields
- [ ] Implement validity checks (email format, date ranges, etc.)
- [ ] Implement consistency checks (cross-field logic)
- [ ] Set up alerting for quality threshold breaches
- [ ] Create quality trend reporting

**Deliverables**:
- [ ] All Priority Sources Integrated
- [ ] Automated Quality Checks (deployed)
- [ ] Quality Alerting (operational)
- [ ] Quality Trend Dashboard

### Phase 2 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Constituent match rate | ≥ 30% records matched across systems | Match statistics |
| False match rate | ≤ 1% | Sample audit |
| Golden record coverage | 100% of priority sources | Integration checklist |
| Data freshness | ≤ 4 hours from source | Pipeline monitoring |
| Quality score | ≥ 95% on critical fields | Quality dashboard |

---

## Phase 3: Intelligence (Months 13-18)

### Objective
Add predictive capabilities, self-service analytics, and continuous optimization.

### Month 13-14: Predictive Models

**Churn Prediction Model**:
- [ ] Define churn (cancellation or 3+ failed payments in 90 days)
- [ ] Engineer features (engagement recency, payment history, tenure)
- [ ] Train and validate model (target AUC ≥ 0.80)
- [ ] Deploy to production (nightly scoring)
- [ ] Create churn risk dashboard for Membership

**Upgrade Propensity Model**:
- [ ] Define upgrade paths (one-time → sustainer, sustainer → increase, any → major)
- [ ] Engineer features (capacity signals, engagement depth, giving patterns)
- [ ] Train multi-target model
- [ ] Deploy to production
- [ ] Create upgrade opportunity dashboard for Development

**Deliverables**:
- [ ] Churn Prediction Model (deployed, AUC ≥ 0.80)
- [ ] Upgrade Propensity Model (deployed)
- [ ] Churn Risk Dashboard
- [ ] Upgrade Opportunity Dashboard

### Month 15-16: Advanced Analytics

**Segmentation & Personalization**:
- [ ] Build constituent segmentation model
- [ ] Create segment-based dashboards
- [ ] Enable segment export for marketing automation
- [ ] Implement segment-based reporting

**Attribution & ROI**:
- [ ] Implement campaign attribution model
- [ ] Create marketing ROI dashboard
- [ ] Build A/B testing framework
- [ ] Enable multi-touch attribution

**Deliverables**:
- [ ] Constituent Segmentation (operational)
- [ ] Attribution Model (deployed)
- [ ] Marketing ROI Dashboard
- [ ] A/B Testing Framework

### Month 17-18: Self-Service & Optimization

**Self-Service Analytics**:
- [ ] Deploy self-service BI tool access (Tableau/Looker/etc.)
- [ ] Create curated data marts for common use cases
- [ ] Build data dictionary/catalog for consumers
- [ ] Train department analysts on self-service tools

**Continuous Optimization**:
- [ ] Implement model retraining pipeline (quarterly)
- [ ] Create model performance monitoring
- [ ] Establish feedback loop from business to data science
- [ ] Document lessons learned and best practices

**Deliverables**:
- [ ] Self-Service BI Access (100% of target users)
- [ ] Data Catalog (published)
- [ ] Analyst Training (completed)
- [ ] Model Monitoring Dashboard
- [ ] Lessons Learned Document

### Phase 3 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Churn model AUC | ≥ 0.80 | Model validation |
| Retention rate improvement | ≥ 5% lift | Before/after comparison |
| Self-service adoption | ≥ 80% of analysts using | Usage analytics |
| Report request reduction | ≥ 50% fewer ad-hoc requests | Ticket tracking |
| Model accuracy over time | Stable (no degradation) | Performance monitoring |

---

## Resource Requirements

### Team Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RECOMMENDED TEAM STRUCTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1 (Months 1-6)                                                       │
│  ├── Director, Enterprise Systems (1.0 FTE) - Leadership                    │
│  ├── Data Engineer (1.0 FTE) - ETL, infrastructure                          │
│  ├── Data Analyst (0.5 FTE) - Quality, documentation                        │
│  └── External: Consulting support for discovery (as needed)                 │
│                                                                             │
│  PHASE 2 (Months 7-12)                                                      │
│  ├── Director, Enterprise Systems (1.0 FTE) - Leadership                    │
│  ├── Data Engineer (2.0 FTE) - Identity resolution, pipelines               │
│  ├── Data Analyst (1.0 FTE) - Quality, testing, documentation               │
│  └── External: Identity resolution specialist (3-month engagement)          │
│                                                                             │
│  PHASE 3 (Months 13-18)                                                     │
│  ├── Director, Enterprise Systems (1.0 FTE) - Leadership                    │
│  ├── Data Engineer (2.0 FTE) - Platform, ML ops                             │
│  ├── Data Scientist (1.0 FTE) - ML models                                   │
│  ├── Data Analyst (1.0 FTE) - Self-service, training                        │
│  └── BI Developer (0.5 FTE) - Dashboards                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack (Recommended)

| Layer | Recommendation | Rationale |
|-------|----------------|-----------|
| **Data Warehouse** | Snowflake | Per JD preference; scalable, low maintenance |
| **ETL/ELT** | Fivetran + dbt | Managed connectors, transformation best practices |
| **BI/Visualization** | Tableau or Looker | Enterprise capability, self-service friendly |
| **ML Platform** | Snowflake ML or Databricks | Integrated with warehouse, MLOps built-in |
| **Data Quality** | dbt tests + Great Expectations | Code-based, version controlled |
| **Orchestration** | Airflow or Prefect | Industry standard, flexible |
| **Data Catalog** | Atlan or Alation | Governance-friendly, business user accessible |

---

## Risk Management

### Key Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Stakeholder resistance** | Medium | High | Early engagement, quick wins, change management |
| **Data quality worse than expected** | High | Medium | Phased approach, quality baseline first |
| **Source system access challenges** | Medium | High | IT partnership, early API assessment |
| **Scope creep** | High | Medium | Clear phase boundaries, governance council prioritization |
| **Resource constraints** | Medium | High | Prioritize ruthlessly, leverage managed services |
| **Integration complexity** | Medium | Medium | Start with highest-value sources, iterate |

### Decision Points

| Milestone | Decision | Criteria | Fallback |
|-----------|----------|----------|----------|
| End of Phase 1 | Proceed to Phase 2? | Quick wins delivered, governance operational | Extend Phase 1 by 2 months |
| Month 8 | Identity resolution approach | Match quality acceptable to business | Simplify matching rules, accept lower automation |
| Month 12 | Proceed to Phase 3? | Golden record stable, quality targets met | Extend Phase 2, focus on stability |
| Month 15 | ML model deployment | Model performance meets threshold | Delay deployment, gather more training data |

---

## Communication Plan

### Stakeholder Communication

| Audience | Frequency | Format | Content |
|----------|-----------|--------|---------|
| Executive Team | Monthly | Email + meeting | Progress summary, risks, decisions needed |
| Governance Council | Monthly | Meeting | Detailed progress, metric approvals, issue resolution |
| Department Heads | Bi-weekly | Email | Relevant updates, upcoming changes |
| All Staff | Quarterly | Newsletter | High-level progress, success stories |
| Data Team | Weekly | Standup | Tactical progress, blockers |

### Key Communication Milestones

| Milestone | Audience | Message |
|-----------|----------|---------|
| Project Kickoff | All staff | Vision, timeline, how it helps them |
| First Quick Win | All staff | "See, it's working!" |
| Governance Council Launch | Department heads | Roles, responsibilities, how to engage |
| Golden Record Go-Live | All staff | New capabilities, training available |
| ML Models Launch | Membership, Development | How to use predictions, what they mean |
| Self-Service Launch | Analysts | Training schedule, resources available |

---

## Success Metrics Summary

### Phase 1 (Foundation)
- ✓ 100% data sources inventoried
- ✓ Governance Council operational
- ✓ 10+ certified metrics defined
- ✓ 3-5 quick wins delivered

### Phase 2 (Unification)
- ✓ ≥30% cross-system match rate
- ✓ ≤1% false match rate
- ✓ ≤4 hour data freshness
- ✓ ≥95% data quality score

### Phase 3 (Intelligence)
- ✓ Churn model AUC ≥0.80
- ✓ ≥5% retention lift
- ✓ ≥80% self-service adoption
- ✓ ≥50% reduction in ad-hoc requests

---

## Appendix: Detailed Timeline

```
MONTH   1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18
        |----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----| 
        
PHASE 1: FOUNDATION
        [====Discovery====]
                  [====Governance====]
                            [====Platform Foundation====]
                            
PHASE 2: UNIFICATION
                                      [====Identity Resolution====]
                                                [====Golden Record====]
                                                          [====Integration & Quality====]
                                                          
PHASE 3: INTELLIGENCE
                                                                    [====ML Models====]
                                                                              [====Analytics====]
                                                                                        [====Self-Service====]

KEY MILESTONES
        ▲                   ▲                   ▲                   ▲                   ▲
        |                   |                   |                   |                   |
   Kickoff            Governance          Golden Record       ML Models          Full Platform
                      Operational          Go-Live            Deployed            Operational
```

---

*This roadmap is a living document. It should be reviewed monthly by the Governance Council and updated based on learnings, changing priorities, and resource availability.*
