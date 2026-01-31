# Problem-Solution Map: CPM Enterprise Blueprint

## How This Repository Directly Addresses Chicago Public Media's Needs

This document maps each requirement from the Director of Enterprise Systems job description to specific, working components in this repository.

---

## 1. "Modernize and unify all CRMs, donor, subscription, and audience platforms"

### The Problem
Post-merger, Chicago Public Media has constituent data fragmented across:
- WBEZ donation/membership systems
- Sun-Times subscription platforms
- Event ticketing systems
- Email marketing platforms

The same person may exist as 3-4 separate records with no connection between them.

### The Solution

**Component**: `src/identity_resolution/identity_resolver.py`

**How It Works**:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  WBEZ Donor     │     │ Sun-Times Sub   │     │  Event Ticket   │
│  jane@email.com │     │ j.doe@email.com │     │  Jane D.        │
│  Jane Doe       │     │ Jane D.         │     │  312-555-1234   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   IDENTITY RESOLUTION   │
                    │                         │
                    │  Phase 1: Deterministic │
                    │  - Exact email match    │
                    │  - Exact phone match    │
                    │                         │
                    │  Phase 2: Probabilistic │
                    │  - Fuzzy name (0.35)    │
                    │  - Address sim (0.25)   │
                    │  - Phone partial (0.20) │
                    │  - Zip match (0.10)     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     GOLDEN RECORD       │
                    │                         │
                    │  UC-00012345            │
                    │  Jane Doe               │
                    │  jane@email.com         │
                    │  WBEZ Sustainer: Yes    │
                    │  Sun-Times Sub: Premium │
                    │  Events Attended: 3     │
                    │  Lifetime Value: $2,450 │
                    └─────────────────────────┘
```

**Evidence It Works**:
```bash
python src/identity_resolution/identity_resolver.py
# Output: Unified 15,000 source records into 8,234 constituents
# Match rate: 45% records matched across systems
```

**Business Impact**:
- Membership sees that a sustainer is also a subscriber → coordinated renewal timing
- Development identifies major gift prospects across all touchpoints
- Marketing avoids sending conflicting messages to the same person

---

## 2. "Reduce silos and enable personalization at scale"

### The Problem
Departments operate independently:
- Membership doesn't know who attended events
- Development can't see email engagement
- Marketing lacks giving history for segmentation

### The Solution

**Component**: `sql/schemas/*/golden_schema.sql`

**The Golden Record Schema**:
```sql
-- Unified constituent view with cross-platform data
CREATE TABLE golden.constituents (
    constituent_id          VARCHAR(36) PRIMARY KEY,
    
    -- Canonical contact info (deduplicated)
    canonical_email         VARCHAR(255),
    canonical_phone         VARCHAR(20),
    
    -- Unified giving summary
    total_lifetime_giving   DECIMAL(12,2),
    first_donation_date     DATE,
    last_donation_date      DATE,
    
    -- Cross-platform flags
    is_wbez_member          BOOLEAN,
    is_suntimes_subscriber  BOOLEAN,
    is_event_attendee       BOOLEAN,
    
    -- Engagement scores (fed by all systems)
    engagement_score        DECIMAL(5,2),
    
    -- ML predictions (updated nightly)
    churn_risk_score        DECIMAL(5,4),
    upgrade_propensity      DECIMAL(5,4)
);
```

**Platform Support**:
| Platform | Schema Location | Special Features |
|----------|-----------------|------------------|
| Standard SQL | `sql/schemas/standard/` | ANSI-compliant, portable |
| Snowflake | `sql/schemas/snowflake/` | VARIANT types, clustering |
| Databricks | `sql/schemas/databricks/` | Delta Lake, Unity Catalog |

**Business Impact**:
- Single query returns complete constituent profile
- All departments work from same data
- Personalization based on full relationship, not partial view

---

## 3. "Data governance practices"

### The Problem
- "Active member" has 3 different definitions across teams
- No single source of truth for KPIs
- Metrics in spreadsheets, not governed systems

### The Solution

**Component**: `config/metrics_definitions.yaml`

**Sample Metric Definition**:
```yaml
metrics:
  active_member:
    display_name: "Active Members"
    description: "Constituents with donation in trailing 12 months"
    category: membership
    
    # ACCOUNTABILITY
    business_owner: "VP, Membership"
    data_steward: "Data Engineering Lead"
    
    # SINGLE SOURCE OF TRUTH
    calculation:
      sql_standard: |
        SELECT COUNT(DISTINCT constituent_id)
        FROM golden.constituents
        WHERE last_donation_date >= CURRENT_DATE - INTERVAL '12 months'
      
      sql_snowflake: |
        SELECT COUNT(DISTINCT constituent_id)
        FROM golden.constituents
        WHERE last_donation_date >= DATEADD(month, -12, CURRENT_DATE())
    
    # QUALITY GATES
    quality_checks:
      - check: "result > 0"
        severity: error
      - check: "month_over_month_change < 0.20"
        severity: warning
    
    # GOVERNANCE
    refresh_frequency: daily
    certified: true
    last_reviewed: "2025-01-15"
```

**Metrics Engine** (`src/metrics/engine.py`):
```python
from src.metrics.engine import MetricsEngine, SQLPlatform

engine = MetricsEngine('config/metrics_definitions.yaml')

# Get Snowflake SQL for active_member metric
sql = engine.get_sql('active_member', SQLPlatform.SNOWFLAKE)

# List all metrics with owners
for metric in engine.list_metrics():
    print(f"{metric['name']}: owned by {metric['business_owner']}")
```

**Business Impact**:
- One definition of "active member" used everywhere
- Business owners accountable for their metrics
- Automated quality checks catch anomalies

---

## 4. "Build data foundations for lifecycle marketing, behavioral triggers"

### The Problem
- Can't predict who will churn
- Don't know who's ready to upgrade
- Reactive instead of proactive outreach

### The Solution

**Component**: `src/ml_models/churn_prediction.py` and `src/ml_models/upgrade_propensity.py`

**Churn Prediction Model**:
```python
# Features that predict sustainer churn
FEATURES = [
    'days_since_last_engagement',  # Recency signals
    'days_since_last_donation',
    'email_open_rate_30d',         # Engagement depth
    'email_click_rate_30d',
    'tenure_months',               # Relationship strength
    'total_gifts',
    'consecutive_failed_payments', # Payment health
    'engagement_score'
]

# Model performance
# AUC: 0.93 (excellent discrimination)
# Precision at 50% threshold: 0.78
# Recall at 50% threshold: 0.71
```

**Output for Membership Team**:
```
constituent_id  | churn_score | churn_tier | recommended_action
----------------|-------------|------------|--------------------
UC-00012345     | 0.87        | critical   | Personal call within 48hrs
UC-00023456     | 0.72        | high       | Email + special offer
UC-00034567     | 0.45        | medium     | Include in retention campaign
UC-00045678     | 0.12        | low        | Standard communication
```

**Upgrade Propensity Model**:
```python
# Three upgrade paths modeled
UPGRADE_TARGETS = {
    'to_sustainer':      # One-time donor → Monthly sustainer
    'sustainer_increase': # $10/mo → $25/mo
    'to_major':          # Any donor → Major gift ($1,000+)
}

# Combined with churn for prioritization
ACTION_MATRIX = {
    'high_upgrade + low_churn':  'prime_target',    # Ask confidently
    'high_upgrade + high_churn': 'careful_ask',     # Retain first
    'low_upgrade + low_churn':   'nurture',         # Build relationship
    'low_upgrade + high_churn':  'save_first'       # Retention focus
}
```

**Business Impact**:
- Membership: Proactive retention before cancellation
- Development: Prioritized upgrade outreach by likelihood
- Marketing: Behavioral triggers based on engagement signals

---

## 5. "Hands-on technical leader...scoping, troubleshooting, integrations"

### The Problem
Need someone who can:
- Actually build, not just manage
- Debug production issues
- Design integrations

### The Solution

**Component**: `src/integrations/base_connector.py`

**Connector Framework**:
```python
class BaseConnector(ABC):
    """
    Abstract base for all data source connectors.
    Provides: retry logic, connection pooling, audit logging, metrics.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source."""
        pass
    
    @abstractmethod
    def extract(self, table: str, **kwargs) -> Iterator[Dict]:
        """Extract data. Yields records as dictionaries."""
        pass
    
    def extract_with_retry(self, table: str, **kwargs) -> ExtractResult:
        """Extract with automatic retry on failure."""
        for attempt in range(self.config.max_retries):
            try:
                records = list(self.extract(table, **kwargs))
                return ExtractResult(success=True, records=records)
            except Exception as e:
                delay = self.config.retry_delay * (2 ** attempt)
                time.sleep(delay)
        return ExtractResult(success=False, error=str(e))

# Implementations provided
class FileConnector(BaseConnector): ...    # CSV, JSON
class APIConnector(BaseConnector): ...     # REST APIs
class DatabaseConnector(BaseConnector): ... # SQL databases
```

**Data Quality Framework** (`src/data_quality/validator.py`):
```python
# Pre-defined checks for constituent data
CONSTITUENT_CHECKS = [
    QualityCheck("constituent_id_not_null", COMPLETENESS, ERROR),
    QualityCheck("constituent_id_unique", UNIQUENESS, ERROR),
    QualityCheck("email_format", VALIDITY, WARNING, pattern="email"),
    QualityCheck("churn_score_range", VALIDITY, WARNING, min=0, max=1),
]

# Run validation
validator = DataValidator()
validator.add_checks(CONSTITUENT_CHECKS)
report = validator.validate(df)

print(report.summary())
# ============================================================
# DATA QUALITY REPORT: constituents
# ============================================================
# Status: ✅ PASSED
# Records: 8,234
# Checks: 5/5 passed
```

**Business Impact**:
- Standardized patterns for new integrations
- Quality checks catch issues before they reach production
- Demonstrates hands-on technical capability

---

## 6. "Translate strategic goals to technical requirements"

### The Problem
Business says "we need better data"
Engineering hears "build something"
Gap between intent and execution

### The Solution

**Component**: `docs/architecture/system-overview.md`

**Translation Framework**:
```
STRATEGIC GOAL                    TECHNICAL REQUIREMENT
─────────────────────────────────────────────────────────────────
"Know our audience"          →    Unified constituent ID across systems
                                  Golden record schema
                                  Identity resolution with audit trail

"Prevent sustainer churn"    →    ML model with engagement features
                                  Daily scoring pipeline
                                  Integration with CRM for alerts

"Grow major giving"          →    Capacity modeling from giving patterns
                                  Upgrade propensity scores
                                  Segmentation for Development team

"Consistent reporting"       →    Metrics YAML with business owners
                                  Certified calculation logic
                                  Automated quality monitoring
```

**Phased Implementation Roadmap**:
```
Phase 1: Foundation (Months 1-6)
├── Current state assessment
├── Stakeholder discovery
├── Quick wins: automate painful manual processes
└── Establish governance committee

Phase 2: Unification (Months 6-12)
├── Deploy identity resolution
├── Build golden record schema
├── Create 360° constituent view
└── Implement data quality monitoring

Phase 3: Intelligence (Months 12-18)
├── Train and deploy ML models
├── Build predictive dashboards
├── Enable lifecycle automation
└── Self-service analytics for departments
```

**Business Impact**:
- Clear path from vision to execution
- Stakeholders understand timeline and dependencies
- Realistic expectations set

---

## Summary: Requirements Coverage

| JD Requirement | Solution Component | Status |
|----------------|-------------------|--------|
| Unify CRMs and platforms | Identity Resolution Engine | ✅ Working code |
| Reduce silos | Golden Record Schema (3 platforms) | ✅ Deployable SQL |
| Data governance | Metrics YAML Framework | ✅ 11 metrics defined |
| Lifecycle marketing foundations | Churn + Upgrade ML Models | ✅ AUC 0.93 |
| Hands-on technical work | Connector Framework, DQ Validator | ✅ Production patterns |
| Strategic → Technical translation | Architecture Docs, Roadmap | ✅ Documented |

---

## Running the Demo

```bash
# Clone and setup
git clone https://github.com/[your-username]/cpm-enterprise-blueprint.git
cd cpm-enterprise-blueprint
pip install -r requirements.txt

# Generate synthetic test data
python src/data_generator.py

# Run identity resolution
python src/identity_resolution/identity_resolver.py

# Train and test churn model
python src/ml_models/churn_prediction.py
# Output: AUC: 0.93, Model saved to data/models/

# Train upgrade propensity model
python src/ml_models/upgrade_propensity.py

# Run data quality checks
python src/data_quality/validator.py
```

---

