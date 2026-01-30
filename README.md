# CPM Enterprise Data Platform Blueprint

> **A working prototype demonstrating enterprise data unification for Chicago Public Media**
>
> Built to show exactly how I would approach the Director of Enterprise Systems role—not with slides, but with code that solves the specific challenges outlined in the job description.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 The Problems This Solves

Chicago Public Media faces challenges common to merged media organizations:

| Challenge | Current State | Impact |
|-----------|--------------|--------|
| **Fragmented Data** | WBEZ donors, Sun-Times subscribers, and event attendees exist in separate systems | Same person appears as 3+ records with no connection |
| **Departmental Silos** | Membership, Development, and Marketing each have partial views | Missed cross-sell opportunities, conflicting outreach |
| **No Predictive Capabilities** | Reactive to churn, can't identify upgrade opportunities | Lost revenue, inefficient resource allocation |
| **Inconsistent Metrics** | "Active member" defined differently by each team | Leadership gets different numbers from different reports |

---

## ✅ How This Blueprint Addresses Each Challenge

| JD Requirement | Solution | Evidence |
|----------------|----------|----------|
| *"Unify all CRMs, donor, subscription platforms"* | **Identity Resolution Engine** | Two-phase matching algorithm with configurable thresholds |
| *"Reduce silos, enable personalization"* | **Golden Record Schema** | Single constituent view across all touchpoints |
| *"Data governance practices"* | **Metrics Framework** | YAML definitions with business owners, quality checks |
| *"Lifecycle marketing, behavioral triggers"* | **ML Models** | Churn prediction (AUC: 0.93), Upgrade propensity |
| *"Hands-on...integrations, troubleshooting"* | **Connector Framework** | Production-ready patterns with retry logic, logging |

📄 **[See detailed problem-solution mapping →](PROBLEM_SOLUTION_MAP.md)**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SOURCE SYSTEMS (Current State)                       │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│  WBEZ Donations │ Sun-Times Subs  │  Event Tickets  │   Email Marketing     │
│  (Allegiance?)  │ (Legacy System) │   (Eventbrite?) │    (Mailchimp?)       │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                    │
         └─────────────────┴────────┬────────┴────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │      INTEGRATION LAYER        │
                    │   src/integrations/           │
                    │   • Standardized connectors   │
                    │   • Retry logic & logging     │
                    │   • Data quality checks       │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │     IDENTITY RESOLUTION       │
                    │   src/identity_resolution/    │
                    │   • Deterministic matching    │
                    │   • Probabilistic scoring     │
                    │   • Audit trail               │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │        GOLDEN RECORD          │
                    │   sql/schemas/                │
                    │   • Unified constituent       │
                    │   • 360° view                 │
                    │   • Platform-specific SQL     │
                    └───────────────┬───────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
┌────────▼────────┐    ┌───────────▼───────────┐    ┌────────▼────────┐
│   ML MODELS     │    │   METRICS ENGINE      │    │   DATA QUALITY  │
│ src/ml_models/  │    │ src/metrics/          │    │ src/data_quality│
│ • Churn (0.93)  │    │ • YAML definitions    │    │ • Completeness  │
│ • Upgrade prop  │    │ • Business owners     │    │ • Validity      │
│ • Prioritization│    │ • Multi-platform SQL  │    │ • Uniqueness    │
└─────────────────┘    └───────────────────────┘    └─────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup
```bash
git clone https://github.com/[your-username]/cpm-enterprise-blueprint.git
cd cpm-enterprise-blueprint
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate Test Data
```bash
python src/data_generator.py
# Creates realistic Chicago-area constituent data:
# - 5,000 base constituents
# - 96,000+ donation records
# - 750+ subscriptions
# - 3,700+ event tickets
```

### 3. Run Identity Resolution
```bash
python src/identity_resolution/identity_resolver.py
# Demonstrates unification across systems
```

### 4. Train Churn Model
```bash
python src/ml_models/churn_prediction.py
# Output:
# Churn Model Performance:
#   AUC: 0.928
#   Precision: 0.784
#   Recall: 0.712
```

---

## 📁 Repository Structure

```
cpm-enterprise-blueprint/
│
├── README.md                          ← You are here
├── PROBLEM_SOLUTION_MAP.md            ← JD requirements → code mapping
│
├── config/
│   └── metrics_definitions.yaml       ← Single source of truth (11 metrics)
│
├── docs/
│   └── architecture/
│       └── system-overview.md         ← Technical deep-dive
│
├── src/
│   ├── data_generator.py              ← Synthetic test data
│   │
│   ├── identity_resolution/
│   │   └── identity_resolver.py       ← Two-phase matching engine
│   │
│   ├── metrics/
│   │   └── engine.py                  ← YAML → SQL generator
│   │
│   ├── ml_models/
│   │   ├── churn_prediction.py        ← Sustainer retention
│   │   └── upgrade_propensity.py      ← Donor upgrade targeting
│   │
│   ├── integrations/
│   │   └── base_connector.py          ← Standardized source connectors
│   │
│   └── data_quality/
│       └── validator.py               ← Automated quality checks
│
├── sql/
│   └── schemas/
│       ├── standard/                  ← ANSI SQL (portable)
│       ├── snowflake/                 ← Snowflake-optimized
│       └── databricks/                ← Delta Lake + Unity Catalog
│
└── examples/
    └── notebooks/
        └── full_pipeline_demo.py      ← End-to-end demonstration
```

---

## 🔑 Key Components

### Identity Resolution Engine
Unifies records across systems using configurable matching:

```python
# Matching weights (configurable)
MATCH_WEIGHTS = {
    'name_similarity': 0.35,    # Fuzzy match on first + last
    'address_similarity': 0.25, # Street address comparison
    'phone_match': 0.20,        # Exact or partial phone
    'zip_match': 0.10,          # Geographic proximity
    'email_domain': 0.10        # Same email provider
}

# Thresholds
AUTO_MATCH = 0.85      # High confidence → automatic merge
REVIEW_QUEUE = 0.70    # Medium confidence → human review
NO_MATCH = below 0.70  # Keep as separate records
```

### Metrics Framework
YAML-driven metric definitions with governance:

```yaml
metrics:
  donor_retention_rate:
    display_name: "Donor Retention Rate"
    business_owner: "VP, Development"
    data_steward: "Data Engineering Lead"
    
    calculation:
      sql_snowflake: |
        WITH donors_prev AS (...),
             donors_curr AS (...)
        SELECT COUNT(curr) / COUNT(prev) * 100
        FROM donors_prev LEFT JOIN donors_curr
    
    quality_checks:
      - check: "result BETWEEN 0 AND 100"
        severity: error
```

### ML Models
Production-ready predictive models:

| Model | Purpose | Performance | Key Features |
|-------|---------|-------------|--------------|
| Churn Prediction | Identify at-risk sustainers | AUC: 0.93 | Engagement recency, payment failures, email behavior |
| Upgrade Propensity | Find upgrade candidates | 3 targets modeled | Capacity signals, tenure, giving patterns |

---

## 📊 Sample Outputs

### Unified Constituent Record
```json
{
  "constituent_id": "UC-00012345",
  "canonical_email": "jane.doe@gmail.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "lifecycle_stage": "sustainer",
  
  "source_systems": ["wbez", "suntimes", "events"],
  
  "giving_summary": {
    "total_lifetime": 2450.00,
    "is_sustainer": true,
    "monthly_amount": 25.00,
    "tenure_months": 36
  },
  
  "engagement": {
    "email_open_rate_30d": 0.45,
    "events_attended_12m": 3,
    "engagement_score": 78.5
  },
  
  "predictions": {
    "churn_risk_score": 0.23,
    "churn_tier": "low",
    "upgrade_propensity": 0.67,
    "recommended_upgrade_path": "sustainer_increase"
  }
}
```

### Churn Risk Dashboard Output
```
┌─────────────────────────────────────────────────────────────────┐
│                    CHURN RISK SUMMARY                           │
├─────────────────────────────────────────────────────────────────┤
│  Total Sustainers: 4,250                                        │
│                                                                 │
│  Risk Distribution:                                             │
│    🔴 Critical (>0.85): 127 (3.0%)  → Personal outreach        │
│    🟠 High (0.60-0.85): 298 (7.0%)  → Retention campaign       │
│    🟡 Medium (0.30-0.60): 892 (21%) → Monitor closely          │
│    🟢 Low (<0.30): 2,933 (69%)      → Standard communication   │
│                                                                 │
│  Estimated Revenue at Risk: $47,250/month                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Implementation Roadmap

### Phase 1: Foundation (Months 1-6)
- [ ] Current state assessment across all systems
- [ ] Stakeholder discovery with Membership, Development, Marketing
- [ ] Quick wins: automate most painful manual workarounds
- [ ] Establish Data Governance Committee

### Phase 2: Unification (Months 6-12)
- [ ] Deploy identity resolution engine
- [ ] Build golden record in data warehouse
- [ ] Create unified constituent view for all departments
- [ ] Implement data quality monitoring

### Phase 3: Intelligence (Months 12-18)
- [ ] Train and deploy ML models with real data
- [ ] Build predictive dashboards
- [ ] Enable lifecycle marketing automation
- [ ] Self-service analytics for department leads

---

## 🤝 Why I Built This

As a long-time WBEZ sustaining member, I understand the value of independent journalism and Chicago Public Media's mission. When I saw the Director of Enterprise Systems role, I didn't want to just talk about what I would do—I wanted to show it.

This repository demonstrates:
- **Technical depth**: Working code, not just diagrams
- **Strategic thinking**: Solutions mapped to specific business problems
- **Domain understanding**: Built for public media/nonprofit context
- **Execution capability**: Production patterns, not prototypes

I believe the best way to show how I'd approach this role is to actually start doing the work.

---

## 👤 Author

**Catherine Kiriakos**
- 📧 cathy.a.kiriakos@gmail.com
- 🔗 [LinkedIn](https://linkedin.com/in/catherine-kiriakos)
- 🌐 [Portfolio](https://cathy-kiriakos.lovable.app/)



---


---

*Built with purpose for Chicago Public Media's Director of Enterprise Systems role.*
