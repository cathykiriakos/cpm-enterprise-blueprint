# CPM Enterprise Data Platform Blueprint

A comprehensive enterprise data platform blueprint designed for Chicago Public Media, demonstrating modern data engineering practices, constituent unification, and ML-driven engagement strategies.

## 🎯 Executive Summary

This repository provides a production-ready blueprint for unifying constituent data across multiple platforms (WBEZ donations, Sun-Times subscriptions, events) into a single golden record, enabling:

- **360° Constituent View**: Unified profiles across all touchpoints
- **Predictive Analytics**: Churn prediction and upgrade propensity models
- **Data Governance**: Single source of truth for all business metrics
- **Multi-Platform Support**: SQL for Standard, Snowflake, and Databricks

## 📁 Repository Structure

```
cpm-enterprise-blueprint/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── setup.py                  # Package installation
├── pyproject.toml           # Modern Python config
│
├── config/
│   └── metrics_definitions.yaml    # Canonical metric definitions
│
├── docs/
│   └── architecture/
│       └── system-overview.md      # Complete architecture documentation
│
├── src/
│   ├── data_generator.py           # Synthetic data generation
│   ├── constituent_unification/
│   │   └── identity_resolver.py    # Identity resolution engine
│   ├── metrics/
│   │   └── engine.py               # YAML-driven metrics engine
│   ├── ml_models/
│   │   ├── churn_prediction.py     # Churn prediction model
│   │   └── upgrade_propensity.py   # Upgrade propensity model
│   ├── integrations/
│   │   └── base_connector.py       # Data source connector framework
│   └── data_quality/
│       └── validator.py            # Data quality validation
│
├── sql/
│   └── schemas/
│       ├── standard/               # ANSI SQL schemas
│       ├── snowflake/              # Snowflake-specific schemas
│       └── databricks/             # Databricks/Delta Lake schemas
│
├── examples/
│   └── notebooks/
│       └── 01_data_generation_demo.py  # Complete pipeline demo
│
└── data/
    ├── synthetic/                  # Generated test data
    └── models/                     # Trained ML models
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ckiriakos/cpm-enterprise-blueprint.git
cd cpm-enterprise-blueprint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Generate Synthetic Data

```bash
python src/data_generator.py
```

This creates realistic test data in `data/synthetic/`:
- `wbez_donations.csv` - Donation records (one-time and recurring)
- `suntimes_subscriptions.csv` - Sun-Times subscription data
- `event_tickets.csv` - Event attendance records
- `email_engagement.csv` - Email open/click data
- `ground_truth.csv` - Person-to-source mapping

### Run Identity Resolution

```python
from src.constituent_unification.identity_resolver import (
    IdentityResolver, SourceRecord, ConstituentUnifier
)

# Create source records from your data
records = [SourceRecord(...), ...]

# Unify into golden records
unifier = ConstituentUnifier()
constituents = unifier.unify_records(records)

print(f"Unified {len(records)} records into {len(constituents)} constituents")
```

### Train ML Models

```python
from src.ml_models.churn_prediction import ChurnPredictor, generate_sample_data

# Generate training data
df, labels = generate_sample_data(5000)

# Train model
model = ChurnPredictor()
metrics = model.train(df, labels)
print(f"AUC: {metrics['auc']:.3f}")

# Save model
model.save('data/models/churn_model.pkl')
```

### Generate Metric SQL

```python
from src.metrics.engine import MetricsEngine, SQLPlatform

engine = MetricsEngine('config/metrics_definitions.yaml')

# Get SQL for Snowflake
sql = engine.get_sql('active_member', SQLPlatform.SNOWFLAKE)
print(sql)
```

## 🏗️ Architecture Overview

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  WBEZ Donations │     │ Sun-Times Subs  │     │  Event Tickets  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   IDENTITY RESOLUTION   │
                    │  (Deterministic + Fuzzy)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     GOLDEN RECORD       │
                    │   (Unified Constituent) │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐   ┌──────────▼──────────┐   ┌───────▼───────┐
│ Churn Prediction│   │ Upgrade Propensity  │   │    Metrics    │
└─────────────────┘   └─────────────────── ─┘   └───────────────┘
```

### Identity Resolution

Two-phase matching algorithm:
1. **Deterministic**: Exact match on email or phone (confidence: 1.0)
2. **Probabilistic**: Weighted fuzzy match on name, address, etc.

Configurable thresholds:
- `≥ 0.85` → Auto-match
- `0.70-0.85` → Manual review queue
- `< 0.70` → No match

### ML Models

#### Churn Prediction
- **Algorithm**: Gradient Boosting (scikit-learn)
- **Target**: Cancellation or 3+ failed payments within 90 days
- **Features**: Engagement recency, email behavior, payment history, tenure
- **Output**: Score 0-1 with risk tier (low/medium/high/critical)

#### Upgrade Propensity
- **Algorithm**: Multi-target Gradient Boosting
- **Targets**: 
  - One-time → Sustainer
  - Sustainer → Increased amount
  - Any → Major gift ($1000+)
- **Output**: Score per upgrade path + recommended action

### Metrics Framework

YAML-driven metric definitions with:
- Business owner and data steward assignment
- SQL for Standard, Snowflake, and Databricks
- Dimension breakdowns (by source, by segment, etc.)
- Quality checks with severity levels
- Version history and governance metadata

## 📊 Key Components

### Metrics Definitions (`config/metrics_definitions.yaml`)

```yaml
metrics:
  active_member:
    display_name: "Active Members"
    category: membership
    definition: "Constituents with a donation in the trailing 12 months"
    business_owner: "VP, Membership"
    calculation:
      sql_snowflake: |
        SELECT COUNT(DISTINCT constituent_id)
        FROM golden.constituents
        WHERE last_donation_date >= DATEADD(month, -12, CURRENT_DATE())
```

### Quality Checks

```python
from src.data_quality.validator import DataValidator, get_constituent_checks

validator = DataValidator()
validator.add_checks(get_constituent_checks())

report = validator.validate(df, "constituents")
print(report.summary())
```

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black src/
flake8 src/
```

### Building Documentation

```bash
# Generate metric documentation
python -c "
from src.metrics.engine import MetricsEngine
engine = MetricsEngine('config/metrics_definitions.yaml')
engine.export_data_dictionary('docs/metrics_dictionary.md')
"
```

## 📋 Use Cases

### 1. Membership Team
- Identify high-churn-risk sustainers for retention outreach
- Find upgrade candidates for sustainer conversion campaigns
- Track active member counts with consistent definitions

### 2. Development Team
- Prioritize major gift prospects using capacity modeling
- Unify donor records across platforms
- Track lifetime value and giving trends

### 3. Marketing Team
- Segment audiences based on engagement scores
- Measure campaign effectiveness with standardized metrics
- Personalize messaging based on unified profiles

### 4. Data Engineering
- Standardized connector framework for new data sources
- Quality checks built into pipelines
- Multi-platform SQL generation

## 🔒 Data Governance

This blueprint embeds governance at every level:

- **Metric Definitions**: Canonical SQL with business owner accountability
- **Data Quality**: Automated checks with severity-based alerting
- **Audit Trail**: Full match history for identity resolution
- **Access Control**: Role-based SQL grants in schema definitions

## 📚 Documentation

- `docs/architecture/system-overview.md` - Complete technical architecture
- `config/metrics_definitions.yaml` - All metric definitions
- `examples/notebooks/` - Runnable demonstrations

## 👤 Author

**Catherine Kiriakos**
- LinkedIn: [linkedin.com/in/catherine-kiriakos](https://linkedin.com/in/catherine-kiriakos)
- Email: cathy.a.kiriakos@gmail.com

---

*Built to demonstrate enterprise data platform capabilities for the Director of Enterprise Systems role at Chicago Public Media.*
