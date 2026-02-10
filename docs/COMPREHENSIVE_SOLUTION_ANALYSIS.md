# CPM Enterprise Blueprint: Comprehensive Solution Dissection

## Prepared for: Director of Enterprise Systems Interview — Chicago Public Media
## Analyst: Catherine Kiriakos
## Date: February 2026

---

# Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Solution 1: Identity Resolution Engine](#2-solution-1-identity-resolution-engine)
3. [Solution 2: Golden Record Schema](#3-solution-2-golden-record-schema)
4. [Solution 3: Metrics Governance Framework](#4-solution-3-metrics-governance-framework)
5. [Solution 4: Churn Prediction Model](#5-solution-4-churn-prediction-model)
6. [Solution 5: Upgrade Propensity Model](#6-solution-5-upgrade-propensity-model)
7. [Solution 6: Data Quality & Integration Framework](#7-solution-6-data-quality--integration-framework)
8. [Solution 7: Direct Mail Campaign SQL Engine](#8-solution-7-direct-mail-campaign-sql-engine)
9. [Alternative ML Algorithms & Enhancements](#9-alternative-ml-algorithms--enhancements)
10. [Benchmarking & Model Performance Assessment](#10-benchmarking--model-performance-assessment)
11. [Platform Options: SQL Server, FOSS, and Snowflake](#11-platform-options-sql-server-foss-and-snowflake)
12. [ML Governance Enhancements](#12-ml-governance-enhancements)
13. [Snowflake Migration Advantages](#13-snowflake-migration-advantages)
14. [Interview Talking Points](#14-interview-talking-points)

---

# 1. Executive Overview

The CPM Enterprise Blueprint contains **seven distinct solutions** designed to transform Chicago Public Media's fragmented post-merger data landscape into a unified, governed, ML-enabled platform. Each solution maps directly to a requirement in the Director of Enterprise Systems job description.

**The Core Problem**: After the WBEZ/Sun-Times merger, the same constituent can exist as 3-4 separate records across donation systems, subscription platforms, event ticketing, and email marketing — with no linkage between them.

**The Blueprint's Answer**: A layered architecture that ingests from all sources, resolves identities, creates a single golden record, and layers ML predictions and governed metrics on top.

### Solution Inventory

| # | Solution | Primary File(s) | JD Requirement |
|---|----------|-----------------|----------------|
| 1 | Identity Resolution Engine | `src/identity_resolution/identity_resolver.py` | "Unify all CRMs, donor, subscription platforms" |
| 2 | Golden Record Schema | `sql/schemas/*/golden_schema_*.sql` | "Reduce silos, enable personalization" |
| 3 | Metrics Governance Framework | `config/metrics_definitions.yaml` + `src/metrics/engine.py` | "Data governance practices" |
| 4 | Churn Prediction Model | `src/ml_models/churn_prediction.py` | "Lifecycle marketing, behavioral triggers" |
| 5 | Upgrade Propensity Model | `src/ml_models/upgrade_propensity.py` | "Lifecycle marketing, behavioral triggers" |
| 6 | Data Quality & Integration Framework | `src/data_quality/validator.py` + `src/integrations/base_connector.py` | "Hands-on technical leader" |
| 7 | Direct Mail Campaign SQL Engine | `assessment_sql_solution/cpm_direct_mail_campaign_query.sql` | "Translate strategic goals to technical requirements" |

---

# 2. Solution 1: Identity Resolution Engine

**File**: `src/identity_resolution/identity_resolver.py` (935 lines)

## 2.1 How It Works

The engine uses a **two-phase matching approach** with a Union-Find clustering algorithm:

**Phase 1 — Deterministic Matching** (High confidence, rule-based):
- **Exact email match**: Confidence = 1.0 (excludes generic emails like info@, admin@)
- **Exact phone match**: Confidence = 0.95 (requires 10+ digit normalized phone)

**Phase 2 — Probabilistic Matching** (Fuzzy, weighted scoring):

| Feature | Weight | Algorithm |
|---------|--------|-----------|
| Name similarity | 0.35 | Jaro-Winkler (first name 40%, last name 60%) |
| Address similarity | 0.30 | Jaro-Winkler on normalized address |
| Phone partial match | 0.15 | Last 7 digits comparison |
| Email domain match | 0.10 | Exact domain comparison |
| Zip code match | 0.10 | 5-digit exact (1.0) or 3-digit prefix (0.5) |

**Thresholds**:
- >= 0.85: Auto-merge (PROBABILISTIC match type)
- 0.70 - 0.85: Manual review queue (MANUAL_REVIEW)
- < 0.70: No match

**Conflict Resolution** (when merging records):
- Email: prefer most recent, then non-generic
- Name: prefer longest version (most complete)
- Phone: prefer most recent with timestamp
- Address: prefer most recent with timestamp

## 2.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **False positives (over-merging)** | HIGH | Two different "John Smith" records at similar addresses could be incorrectly merged, corrupting giving history and triggering wrong outreach |
| **Jaro-Winkler fallback is oversimplified** | MEDIUM | The `jellyfish` library fallback uses a simple character overlap ratio, not true Jaro-Winkler — could produce poor match scores in production if the library is missing |
| **O(n^2) probabilistic matching** | HIGH | When `enable_probabilistic=True`, every record is compared against every other record. At 100K+ records this becomes computationally infeasible |
| **No blocking strategy** | HIGH | No pre-filtering by zip code, last name initial, or phonetic code means the probabilistic phase compares records that have zero chance of matching |
| **Static thresholds** | MEDIUM | The 0.85/0.70 thresholds are hardcoded defaults — no evidence of tuning against labeled match/non-match pairs |
| **No unmerge capability** | MEDIUM | Once records are merged, there's no documented process to split incorrectly merged constituents |
| **Generic email list is limited** | LOW | Only 9 generic prefixes checked; misses patterns like `office@`, `billing@`, `donations@` |

## 2.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **360-degree constituent view** | HIGH | Membership, Development, and Marketing see the same person across all touchpoints for the first time |
| **Revenue recovery** | HIGH | Identifying that a lapsed WBEZ donor is an active Sun-Times subscriber reveals re-engagement opportunities |
| **Full audit trail** | HIGH | Every match decision is stored with confidence score, feature scores, and reasons — critical for compliance and debugging |
| **Configurable via MatchConfig** | MEDIUM | Weights and thresholds can be tuned without code changes |
| **Union-Find clustering** | MEDIUM | Transitive matches are handled correctly (if A=B and B=C, then A=B=C) |
| **Clean separation of concerns** | MEDIUM | IdentityResolver, ConflictResolver, and ConstituentUnifier are distinct classes enabling independent testing |

## 2.4 Improvements

### Immediate (SQL Server / FOSS)

1. **Add blocking strategy**: Before probabilistic matching, group records by zip code prefix, last name Soundex, or email domain to reduce comparisons from O(n^2) to O(n * k) where k is the block size.

   ```python
   # Example: Block by first 3 chars of last name + zip prefix
   import itertools
   from collections import defaultdict

   def create_blocks(records):
       blocks = defaultdict(list)
       for r in records:
           _, last = self._extract_name_parts(r)
           zip3 = (r.zip_code or '')[:3]
           key = f"{last[:3]}_{zip3}" if last else f"NONAME_{zip3}"
           blocks[key].append(r)
       return blocks
   ```

2. **Use proper Jaro-Winkler**: Make `jellyfish` a hard dependency or use `rapidfuzz` (Apache-2.0 licensed, C++ backed, faster):

   ```bash
   pip install rapidfuzz  # FOSS, pip install from Anaconda distribution
   ```

   ```python
   from rapidfuzz.distance import JaroWinkler
   score = JaroWinkler.similarity(s1, s2)
   ```

3. **Add Soundex/Metaphone as a feature**: Phonetic matching catches "Catherine" vs "Katherine", "Smith" vs "Smyth":

   ```python
   # pandas + jellyfish (both in Anaconda distribution)
   import jellyfish
   phonetic_match = jellyfish.soundex(name_a) == jellyfish.soundex(name_b)
   ```

4. **Implement threshold tuning with labeled data**: Create a small labeled set (500 known match/non-match pairs) and use grid search to find optimal thresholds:

   ```python
   from sklearn.metrics import precision_recall_curve
   # Sweep thresholds, pick the one maximizing F1 or desired precision
   ```

### Snowflake Migration Enhancements

1. **Snowflake ML Functions for fuzzy matching**: Use `JAROWINKLER_SIMILARITY()` and `EDITDISTANCE()` natively in SQL:

   ```sql
   SELECT
       a.constituent_id AS id_a,
       b.constituent_id AS id_b,
       JAROWINKLER_SIMILARITY(a.last_name, b.last_name) AS name_sim,
       JAROWINKLER_SIMILARITY(a.address_line1, b.address_line1) AS addr_sim
   FROM golden.constituents a
   CROSS JOIN golden.constituents b
   WHERE a.constituent_id < b.constituent_id
     AND a.zip_code = b.zip_code  -- blocking
     AND JAROWINKLER_SIMILARITY(a.last_name, b.last_name) > 0.8;
   ```

2. **Snowpark Python UDFs**: Run the full identity resolution engine as a Snowpark stored procedure, scaling with Snowflake compute:

   ```sql
   CREATE OR REPLACE PROCEDURE identity_resolution(source_table STRING)
   RETURNS VARIANT
   LANGUAGE PYTHON
   RUNTIME_VERSION = '3.9'
   PACKAGES = ('snowflake-snowpark-python', 'rapidfuzz')
   HANDLER = 'run_resolution';
   ```

3. **Incremental matching with Streams**: Use Snowflake Streams + Tasks for real-time incremental matching as new records arrive, rather than batch-reprocessing all records.

4. **Snowflake Cortex for ML-based entity resolution**: Leverage Cortex LLM functions to assess whether two records refer to the same person using natural language understanding — particularly useful for edge cases where rule-based matching fails.

---

# 3. Solution 2: Golden Record Schema

**Files**: `sql/schemas/standard/golden_schema_std.sql`, `sql/schemas/snowflake/golden_schema_sf.sql`, `sql/schemas/databricks/golden_schema_db.sql`

## 3.1 How It Works

A **multi-layer schema** (RAW → STAGING → GOLDEN → MART → DIMENSIONS) with the core `golden.constituents` table as the single source of truth. The schema stores:

- **Canonical contact info**: Resolved from conflict resolution (email, phone, address)
- **Lifecycle classification**: prospect / one_time_donor / sustainer / major_donor / lapsed
- **Giving summary**: Total lifetime, gift count, average, largest single gift
- **Sustainer status**: Is sustainer, recurring amount, frequency, failed payments
- **ML scores**: Churn risk, upgrade propensity, estimated capacity, LTV
- **Email engagement**: 30-day open/click rates
- **Data quality flags**: Valid email/phone/address booleans, overall quality score

Supporting tables: `constituent_source_links` (provenance), `donation_facts`, `subscription_facts`, `engagement_events` (VARIANT for flexibility), `constituent_features` (ML feature store), `model_predictions`.

The Snowflake variant adds: clustering keys, search optimization, VARIANT types, 90-day time travel, stored procedures, and scheduled tasks.

## 3.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Schema rigidity** | MEDIUM | The wide constituent table (50+ columns) mixes slowly-changing attributes with frequently-updated ML scores, causing unnecessary UPDATE overhead |
| **No SCD Type 2 implementation** | HIGH | No history tracking for constituent attribute changes. When a donor upgrades from one_time_donor to sustainer, the prior state is lost |
| **ML scores on the constituent table** | MEDIUM | Churn score, upgrade propensity, and LTV on the main table creates tight coupling between the ML pipeline and the core schema. Score updates trigger full-row updates |
| **Missing indexes on standard schema** | LOW | The ANSI SQL variant lacks index definitions for common query patterns (email lookup, date range scans) |
| **No partitioning on donation_facts** | MEDIUM | For large donation histories (millions of rows), date-range queries will full-scan without partitioning |
| **VARIANT type dependency** | LOW | `engagement_events.event_attributes` as VARIANT/JSON is flexible but lacks schema enforcement — garbage data can enter without validation |

## 3.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **True 360-degree view** | HIGH | Single query returns complete constituent profile across all source systems |
| **Multi-platform portability** | HIGH | Three schema variants (ANSI, Snowflake, Databricks) prevent vendor lock-in |
| **ML feature store built in** | MEDIUM | `constituent_features` table pre-computes features for models, reducing training/inference latency |
| **Model prediction history** | MEDIUM | `model_predictions` table tracks scores over time, enabling drift detection |
| **Snowflake-native optimizations** | HIGH | Clustering keys, search optimization, time travel, scheduled tasks are production-ready patterns |
| **Source provenance** | HIGH | `constituent_source_links` with match confidence enables auditing which source contributed what data |

## 3.4 Improvements

### Immediate (SQL Server / FOSS)

1. **Add SCD Type 2 for key attributes**:

   ```sql
   -- SQL Server implementation
   CREATE TABLE golden.constituent_history (
       surrogate_key BIGINT IDENTITY(1,1) PRIMARY KEY,
       constituent_id VARCHAR(36) NOT NULL,
       lifecycle_stage VARCHAR(50),
       is_sustainer BIT,
       recurring_monthly_amount DECIMAL(10,2),
       effective_date DATE NOT NULL,
       end_date DATE DEFAULT '9999-12-31',
       is_current BIT DEFAULT 1,
       change_reason VARCHAR(100)
   );

   -- Pandas equivalent for FOSS environments
   # Track changes in a separate DataFrame with effective/end dates
   ```

2. **Separate ML scores into a dedicated table** to decouple update frequency:

   ```sql
   CREATE TABLE golden.constituent_scores (
       constituent_id VARCHAR(36) PRIMARY KEY,
       churn_risk_score DECIMAL(5,4),
       churn_risk_tier VARCHAR(20),
       upgrade_propensity DECIMAL(5,4),
       lifetime_value_estimate DECIMAL(12,2),
       scored_at DATETIME DEFAULT GETDATE(),
       model_version VARCHAR(20)
   );
   ```

3. **Add covering indexes for SQL Server**:

   ```sql
   CREATE INDEX IX_constituents_email ON golden.constituents(canonical_email) INCLUDE (constituent_id, lifecycle_stage);
   CREATE INDEX IX_donations_date ON golden.donation_facts(donation_date, constituent_id) INCLUDE (donation_amount, donation_status);
   ```

### Snowflake Migration Enhancements

1. **Dynamic tables** for automatic materialization of derived views:

   ```sql
   CREATE DYNAMIC TABLE golden.active_member_summary
   TARGET_LAG = '1 hour'
   WAREHOUSE = COMPUTE_WH
   AS
   SELECT constituent_id, COUNT(*) as gift_count, SUM(donation_amount) as total
   FROM golden.donation_facts
   WHERE donation_date >= DATEADD(month, -12, CURRENT_DATE())
   GROUP BY constituent_id;
   ```

2. **Iceberg tables** for open-format interoperability if Databricks or Spark workloads also need to read the data.

3. **Row access policies** for field-level security:

   ```sql
   CREATE ROW ACCESS POLICY golden.constituent_access AS (constituent_id VARCHAR)
   RETURNS BOOLEAN ->
     CURRENT_ROLE() IN ('DATA_ADMIN', 'MEMBERSHIP_TEAM')
     OR EXISTS (SELECT 1 FROM golden.user_data_access WHERE user_role = CURRENT_ROLE());
   ```

---

# 4. Solution 3: Metrics Governance Framework

**Files**: `config/metrics_definitions.yaml` (690+ lines), `src/metrics/engine.py`, `docs/04_GOVERNANCE_FRAMEWORK.md`

## 4.1 How It Works

**11 business metrics** defined in a single YAML file with:
- Canonical definition (plain English, includes/excludes)
- Business owner and data steward assignments
- Platform-specific SQL (Standard, Snowflake, Databricks)
- Quality checks with severity levels (error/warning)
- Dimensional slicing (by source, gift type, tenure, etc.)
- Refresh frequency and caveats
- Version history and related metrics

The `MetricsEngine` class parses the YAML, generates platform-specific SQL, and supports dimensional queries. The governance framework defines a Data Governance Council (chaired by Director of Enterprise Systems), domain data owners, data stewards, and a metric lifecycle (Propose → Review → Approve → Publish).

**Metrics Defined**: Active Member, Active Member with Grace, Sustaining Member, Lapsed Member, Total Revenue T12M, Average Gift Amount, Donor Retention Rate, Sustainer Churn Rate, Email Open Rate, Active Subscriber, Lifetime Value.

## 4.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **SQL drift across platforms** | HIGH | Three separate SQL implementations per metric can silently diverge. A fix applied to Snowflake SQL but not Standard SQL creates inconsistent results |
| **No automated testing of SQL equivalence** | HIGH | No mechanism to verify that the Standard, Snowflake, and Databricks SQL variants produce identical results on the same data |
| **Quality checks are declarative only** | MEDIUM | Rules like `"value BETWEEN 50000 AND 150000"` are defined as strings but not automatically executed — the engine only generates SQL, doesn't run checks |
| **Missing metrics** | MEDIUM | No acquisition cost, no net promoter score, no event attendance rate, no cross-product engagement score |
| **Governance process is documentation-only** | LOW | The council charter, change request template, and lifecycle are described but not enforced through tooling |
| **No metric lineage visualization** | LOW | Dependencies between metrics (e.g., sustainer is a subset of active member) aren't validated programmatically |

## 4.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **Single source of truth** | HIGH | "What is an active member?" has exactly one answer, ending cross-departmental debates |
| **Accountability model** | HIGH | Every metric has a named business owner and data steward — no orphaned KPIs |
| **Git-versioned definitions** | MEDIUM | Changes to metric logic are tracked in version control with full diff history |
| **Platform portability** | MEDIUM | SQL for three warehouse platforms generated from one definition |
| **Quality gates** | MEDIUM | Severity-based checks can catch anomalies before they reach dashboards |

## 4.4 Improvements

### Immediate (SQL Server / FOSS)

1. **Add automated cross-platform SQL equivalence tests** using pandas:

   ```python
   # In pytest: run each SQL variant against synthetic data in SQLite/pandas
   # and assert results are within tolerance
   def test_active_member_consistency():
       engine = MetricsEngine()
       # Execute each variant against same test data
       result_std = execute_sql(engine.get_sql('active_member', SQLPlatform.STANDARD), test_db)
       result_sf = execute_sql(engine.get_sql('active_member', SQLPlatform.SNOWFLAKE), test_db)
       assert abs(result_std - result_sf) < 0.01
   ```

2. **Implement executable quality checks**:

   ```python
   def run_quality_checks(metric_name, computed_value, previous_value=None):
       checks = engine.get_quality_checks(metric_name)
       for check in checks:
           # Parse and evaluate the rule
           passed = eval_rule(check['rule'], value=computed_value, previous_value=previous_value)
           if not passed and check['severity'] == 'error':
               raise DataQualityError(f"Metric {metric_name} failed check: {check['name']}")
   ```

3. **Add metric dependency graph** using NetworkX (FOSS):

   ```python
   import networkx as nx
   G = nx.DiGraph()
   G.add_edge('sustaining_member', 'active_member', relation='subset_of')
   G.add_edge('lapsed_member', 'active_member', relation='complement_of')
   # Validate: sustainer_count <= active_member_count
   ```

### Snowflake Migration Enhancements

1. **Snowflake Data Governance features**: Use Tag-Based Masking Policies and Object Tagging to enforce metric ownership at the platform level.

2. **Snowflake Alerts** for automated quality monitoring:

   ```sql
   CREATE ALERT golden.alert_active_member_anomaly
   WAREHOUSE = COMPUTE_WH
   SCHEDULE = 'USING CRON 0 7 * * * America/Chicago'
   IF (EXISTS (
       SELECT 1 FROM golden.metric_results
       WHERE metric_name = 'active_member'
         AND ABS(current_value - previous_value) / previous_value > 0.05
   ))
   THEN
       CALL SYSTEM$SEND_EMAIL('data-team@cpm.org', 'Active Member Alert', 'Anomaly detected');
   ```

3. **Snowflake Horizon** for data catalog / metric discovery by business users.

---

# 5. Solution 4: Churn Prediction Model

**File**: `src/ml_models/churn_prediction.py` (268 lines)

## 5.1 How It Works

**Target**: Binary classification — churned (1) vs. retained (0). Churn defined as cancellation or 3+ consecutive failed payments within a 90-day window.

**Algorithm**: `GradientBoostingClassifier` (scikit-learn) with 100 estimators, max depth 6, learning rate 0.1.

**10 Features**:

| Feature | Engineering Logic | Signal |
|---------|------------------|--------|
| `days_since_last_engagement` | `(now - last_engagement_date).days`, fillna=999 | Recency |
| `days_since_last_donation` | `(now - last_donation_date).days`, fillna=999 | Recency |
| `email_open_rate_30d` | Direct from source, fillna=0 | Engagement depth |
| `email_click_rate_30d` | Direct from source, fillna=0 | Engagement depth |
| `tenure_months` | `(now - first_donation_date).days / 30.44` | Relationship strength |
| `total_gifts` | From `total_gift_count`, fillna=0 | Giving history |
| `avg_gift_amount` | From `average_gift_amount`, fillna=0 | Giving level |
| `consecutive_failed_payments` | Direct, fillna=0 | Payment health |
| `sustainer_months` | `(now - sustainer_start_date).days / 30.44` | Sustainer tenure |
| `engagement_score` | Composite: `(1 - days_since/365)*50 + open_rate*50` | Overall engagement |

**Output**: Churn probability (0.0–1.0) bucketed into tiers:
- Critical: >= 0.85 → Personal outreach within 48 hours
- High: 0.60–0.85 → Retention campaign
- Medium: 0.30–0.60 → Monitor closely
- Low: < 0.30 → Standard communication

**Reported Performance**: AUC 0.93, Precision 0.784, Recall 0.712

## 5.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Synthetic data performance inflated** | HIGH | The AUC of 0.93 is measured on synthetic data where labels are *generated from the features*. The label generation formula directly uses `days_inactive`, `email_open_rate`, and `consecutive_failed_payments` — the exact features the model trains on. Real-world AUC will likely be 0.70–0.85 |
| **Data leakage in engagement_score** | HIGH | The composite `engagement_score` is derived from `days_since_last_engagement` and `email_open_rate_30d`, both of which are already independent features. This creates multicollinearity and can inflate feature importance for the composite |
| **No cross-validation** | MEDIUM | Uses a single 80/20 train/test split. No k-fold CV means performance estimate has high variance |
| **StandardScaler for tree-based model** | LOW | Gradient boosting is invariant to monotonic feature transformations — scaling adds unnecessary preprocessing complexity without benefit |
| **No hyperparameter tuning** | MEDIUM | Fixed at 100 estimators, depth 6, lr 0.1. No evidence of grid search or Bayesian optimization |
| **Pickle serialization** | MEDIUM | `pickle.dump` for model persistence is fragile across Python/sklearn versions and poses security risks when loading untrusted files |
| **No calibration** | MEDIUM | Raw probabilities from GBM are not calibrated — a score of 0.7 doesn't truly mean 70% probability of churn. This matters when using scores for business decisions |
| **No temporal validation** | HIGH | Random train/test split rather than time-based split means the model could learn from future data to predict past events |

## 5.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **Proactive retention** | HIGH | Identifying at-risk sustainers before they cancel enables intervention when it can still make a difference |
| **Revenue protection** | HIGH | If 3% of 4,250 sustainers are critical risk at avg $25/month, that's ~$47K/month at risk — even a 20% save rate returns ~$113K/year |
| **Actionable tiers** | HIGH | The 4-tier system (critical/high/medium/low) directly maps to different intervention strategies, making it operationally usable |
| **Feature importance** | MEDIUM | `get_feature_importance()` helps the business understand *why* someone is at risk, not just that they are |
| **Interpretable algorithm** | MEDIUM | Gradient boosting feature importances are more intuitive to non-technical stakeholders than neural network approaches |
| **Save/load persistence** | MEDIUM | Model serialization enables deployment as a batch scoring pipeline |

## 5.4 Improvements

### Immediate (SQL Server / FOSS — pandas, scikit-learn, Anaconda Distribution)

1. **Fix data leakage — remove `engagement_score`** or remove its component features:

   ```python
   # Option A: Remove the composite score
   FEATURE_COLS = [col for col in FEATURE_COLS if col != 'engagement_score']

   # Option B: Keep only engagement_score, drop components
   FEATURE_COLS = [col for col in FEATURE_COLS
                   if col not in ('days_since_last_engagement', 'email_open_rate_30d')]
   ```

2. **Add stratified k-fold cross-validation**:

   ```python
   from sklearn.model_selection import StratifiedKFold, cross_val_score

   cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
   scores = cross_val_score(model, X_scaled, y, cv=cv, scoring='roc_auc')
   print(f"AUC: {scores.mean():.3f} +/- {scores.std():.3f}")
   ```

3. **Implement time-based validation split** to prevent temporal leakage:

   ```python
   # Sort by date, use last 20% as test
   df_sorted = df.sort_values('last_engagement_date')
   split_idx = int(len(df_sorted) * 0.8)
   X_train, X_test = X[:split_idx], X[split_idx:]
   y_train, y_test = y[:split_idx], y[split_idx:]
   ```

4. **Add probability calibration**:

   ```python
   from sklearn.calibration import CalibratedClassifierCV
   calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=5)
   calibrated_model.fit(X_train, y_train)
   ```

5. **Use joblib instead of pickle** for safer, more efficient model serialization:

   ```python
   import joblib
   joblib.dump({'model': self.model, 'scaler': self.scaler}, path)
   model_data = joblib.load(path)
   ```

6. **Add SHAP explanations** (FOSS, pip install shap):

   ```python
   import shap
   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(X_val)
   # Per-prediction explanation: "This constituent is high risk because
   # consecutive_failed_payments=3 (+0.25) and email_open_rate=0.02 (+0.18)"
   ```

### Snowflake Migration Enhancements

1. **Snowpark ML** for in-warehouse model training:

   ```python
   from snowflake.ml.modeling.ensemble import GradientBoostingClassifier as SF_GBC
   from snowflake.ml.modeling.preprocessing import StandardScaler as SF_Scaler

   # Trains directly on Snowflake data without data movement
   model = SF_GBC(n_estimators=100, max_depth=6)
   model.fit(train_df)
   ```

2. **Snowflake Model Registry** for versioned model management:

   ```python
   from snowflake.ml.registry import Registry
   reg = Registry(session)
   reg.log_model(model, model_name="churn_predictor", version_name="v1.2",
                  metrics={"auc": 0.85, "precision": 0.78})
   ```

3. **Snowflake ML Feature Store** to replace the custom `constituent_features` table with managed, point-in-time correct features.

---

# 6. Solution 5: Upgrade Propensity Model

**File**: `src/ml_models/upgrade_propensity.py` (202 lines)

## 6.1 How It Works

**Multi-target model** with three independent GradientBoostingClassifiers:

| Target | Description | Base Rate |
|--------|-------------|-----------|
| `to_sustainer` | One-time donor → Monthly sustainer | ~5% |
| `sustainer_increase` | Sustainer amount increase ($10→$25) | ~10% |
| `to_major` | Any donor → Major gift ($1,000+) | ~1% |

**10 Features**: tenure_months, total_gifts, avg_gift, max_gift, gift_frequency, days_since_gift, email_open_rate, events_attended, engagement_score, capacity_score.

**Action Matrix** (combines with churn prediction):

| Scenario | Action | Business Logic |
|----------|--------|----------------|
| High upgrade + Low churn | `prime_target` | Ask confidently — strong relationship |
| High upgrade + High churn | `careful_ask` | Retain first, then upgrade |
| Low upgrade + Low churn | `nurture` | Build relationship over time |
| Low upgrade + High churn | `save_first` | Focus entirely on retention |

**Priority score**: `upgrade_propensity * 100 - churn_score * 50` (clipped 0–100)

## 6.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Severe class imbalance** | HIGH | `to_major` has ~1% positive rate — standard accuracy metrics are meaningless, and the model may never predict positive |
| **No stratification for rare targets** | HIGH | `train_test_split` without `stratify=y` for each target means test sets may have zero positive examples for `to_major` |
| **Independent models ignore correlations** | MEDIUM | The three targets are correlated (someone likely to become a sustainer is also more likely to increase), but independent models miss this |
| **Capacity score is circular** | MEDIUM | `capacity_score = log1p(max_gift)*10 + log1p(total_gifts*avg_gift)*5` — this is just a mathematical transform of features already in the model |
| **Same synthetic data issues** | HIGH | Labels are generated from features, inflating performance metrics |
| **No threshold optimization per target** | MEDIUM | All three targets use 0.5 as the classification threshold, but optimal thresholds differ drastically for imbalanced classes |

## 6.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **Revenue growth engine** | HIGH | Systematically identifying upgrade candidates replaces gut-feel targeting |
| **Three upgrade paths modeled** | HIGH | Different upgrade paths have different economics and outreach strategies |
| **Churn-aware prioritization** | HIGH | The action matrix prevents asking for an upgrade from someone about to cancel |
| **Priority scoring** | MEDIUM | Ordered list for Development team to work through systematically |
| **Modular design** | MEDIUM | Each target model can be retrained independently as more data becomes available |

## 6.4 Improvements

### Immediate (FOSS)

1. **Handle class imbalance** with SMOTE or class weights:

   ```python
   # Option A: Class weights (simplest)
   model = GradientBoostingClassifier(
       n_estimators=100, max_depth=5,
       # Doesn't support class_weight, so use sample_weight:
   )
   sample_weights = np.where(y == 1, (1-y.mean())/y.mean(), 1)
   model.fit(X_tr_s, y_tr, sample_weight=sample_weights)

   # Option B: SMOTE (pip install imbalanced-learn, in Anaconda)
   from imblearn.over_sampling import SMOTE
   smote = SMOTE(random_state=42)
   X_resampled, y_resampled = smote.fit_resample(X_tr_s, y_tr)
   ```

2. **Use multi-output classification** to capture target correlations:

   ```python
   from sklearn.multioutput import MultiOutputClassifier
   multi_model = MultiOutputClassifier(
       GradientBoostingClassifier(n_estimators=100, max_depth=5)
   )
   multi_model.fit(X_train, y_train_multi)  # y_train_multi is n_samples x 3
   ```

3. **Optimize thresholds per target** using precision-recall curves:

   ```python
   from sklearn.metrics import precision_recall_curve
   for target in ['to_sustainer', 'sustainer_increase', 'to_major']:
       precision, recall, thresholds = precision_recall_curve(y_val, y_prob)
       # Pick threshold where F1 is maximized
       f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
       optimal_threshold = thresholds[np.argmax(f1_scores)]
   ```

4. **Add economic value scoring** instead of pure probability:

   ```python
   # Expected value = P(upgrade) * expected_annual_value_increase
   expected_values = {
       'to_sustainer': prob * 25 * 12,      # $300/year
       'sustainer_increase': prob * 15 * 12, # $180/year
       'to_major': prob * 1000,              # $1000 one-time
   }
   ```

---

# 7. Solution 6: Data Quality & Integration Framework

**Files**: `src/data_quality/validator.py` (235 lines), `src/integrations/base_connector.py` (350 lines)

## 7.1 How It Works

**Data Quality Validator**: Framework supporting four check types:
- **Completeness**: Field is non-null and non-empty (with configurable threshold)
- **Validity**: Value matches regex pattern, allowed values list, or numeric range
- **Uniqueness**: No duplicate values on specified field
- **Consistency**: Defined but not yet implemented

Pre-built checks for constituent data: ID not null, ID unique, email format, lifecycle stage values, churn score range.

**Integration Framework**: Abstract `BaseConnector` with three implementations:
- **FileConnector**: CSV and JSON file ingestion
- **APIConnector**: REST API with pagination, session management, auth headers
- **DatabaseConnector**: SQL database template (connection string based)

All connectors include: retry with exponential backoff, connection lifecycle management, extraction metrics tracking, context manager support.

## 7.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Consistency checks not implemented** | MEDIUM | `CheckType.CONSISTENCY` returns a pass-through `True` — cross-field validation doesn't actually work |
| **No timeliness checks** | MEDIUM | `CheckType.TIMELINESS` is defined in the enum but never implemented — data freshness isn't validated |
| **DatabaseConnector is a stub** | HIGH | The `extract()` method returns `iter([])` — it logs "Would execute" but doesn't actually query databases |
| **No schema validation on ingestion** | MEDIUM | Raw data enters without structural validation — missing columns or type mismatches discovered only at transformation time |
| **No data profiling** | LOW | No automated statistics (min, max, mean, distribution) generated during ingestion |

## 7.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **Standardized connector pattern** | HIGH | New data sources follow a consistent interface, reducing integration time |
| **Retry with backoff** | HIGH | Production-ready resilience pattern for transient failures |
| **Configurable quality checks** | MEDIUM | Checks defined declaratively and run against any DataFrame |
| **Severity-based pass/fail** | MEDIUM | Only ERROR-level failures block the pipeline; WARNINGs are logged but don't halt processing |
| **Metrics emission** | MEDIUM | Extraction metrics (count, time, success/fail rate) enable operational monitoring |

## 7.4 Improvements

### Immediate (SQL Server / FOSS)

1. **Implement consistency checks**:

   ```python
   def _check_consistency(self, check, df):
       # Cross-field validation
       if check.rule == 'sustainer_has_start_date':
           mask = (df['is_sustainer'] == True) & (df['sustainer_start_date'].isna())
           failed = int(mask.sum())
       elif check.rule == 'churn_score_requires_sustainer':
           mask = (df['churn_risk_score'].notna()) & (df['is_sustainer'] != True)
           failed = int(mask.sum())
       return CheckResult(check.name, failed == 0, check.severity, len(df), failed, failed/len(df))
   ```

2. **Add Great Expectations integration** (FOSS, Apache-2.0):

   ```python
   # pip install great-expectations
   import great_expectations as gx
   context = gx.get_context()
   # Provides 300+ built-in expectations, data profiling, docs generation
   ```

3. **Add data profiling with ydata-profiling** (FOSS, formerly pandas-profiling):

   ```python
   from ydata_profiling import ProfileReport
   report = ProfileReport(df, title="Constituent Data Profile")
   report.to_file("reports/constituent_profile.html")
   ```

### Snowflake Migration Enhancements

1. **Snowflake data quality via dbt tests**:

   ```yaml
   # dbt schema.yml
   models:
     - name: golden_constituents
       columns:
         - name: constituent_id
           tests:
             - not_null
             - unique
         - name: churn_risk_score
           tests:
             - accepted_range:
                 min_value: 0
                 max_value: 1
   ```

2. **Snowpipe** for real-time ingestion replacing batch FileConnector.

3. **Snowflake External Functions** to call validation APIs during pipeline execution.

---

# 8. Solution 7: Direct Mail Campaign SQL Engine

**File**: `assessment_sql_solution/cpm_direct_mail_campaign_query.sql` (235 lines)

## 8.1 How It Works

A parameterized, production-ready SQL query that generates direct mail campaign lists. Uses a CTE-based architecture:

1. **campaign_parameters**: Single CTE for all configurable values (dates, thresholds, gift summary types)
2. **excluded_flag_list**: VALUES-based exclusion list (Major Donor Prospect, Deceased, No Mail, No Renewals)
3. **eligible_journey_segments**: VALUES-based inclusion list (Active, Dormant, Lapsed, Late, New, Renewal)
4. **excluded_households**: Anti-join on flagged households
5. **eligible_constituents**: Multi-table join with eligibility filters
6. **bucketed_constituents**: CASE-based bucket assignment with priority ordering
7. **Final SELECT**: Only rows with assigned buckets, ordered for mail house

**Bucket Logic**:
- Priority 1: "Additional gift target — first year of giving" (one-time, recent gift, first-year donor, below leadership threshold)
- Priority 2: "Current leadership circle member" (one-time, recent gift, at/above leadership threshold)

## 8.2 Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Only 2 buckets defined** | MEDIUM | The campaign logic only assigns 2 of potentially many segments — lapsed reactivation, sustainer upgrade asks, and multi-year renewals are not captured |
| **CROSS JOIN on campaign_parameters** | LOW | Functionally correct but can confuse query optimizers in some databases; a subquery or variable would be cleaner |
| **No deduplication at household level** | MEDIUM | If multiple persons in a household match, multiple mail pieces could be sent |
| **Assumes specific CRM schema** | HIGH | References `crm_account_family`, `crm_member_journey`, `crm_gift_summary` — tables that may not exist in CPM's actual CRM |

## 8.3 Rewards

| Reward | Impact | Description |
|--------|--------|-------------|
| **Self-documenting** | HIGH | Extensive inline comments explain every section; a non-technical user can understand the logic |
| **Parameterized** | HIGH | Campaign dates and thresholds are in one place — no need to hunt through WHERE clauses |
| **Auditable** | MEDIUM | CTE structure makes it easy to inspect intermediate results for QA |
| **Mail-house ready** | MEDIUM | Output includes all fields needed for direct mail fulfillment |

## 8.4 Improvements

1. **Add more campaign buckets** (lapsed reactivation, sustainer upgrade, multi-year renewal)
2. **Add household-level deduplication** with ROW_NUMBER()
3. **Add output validation CTE** that counts by bucket and flags anomalies
4. **Parameterize for Snowflake** using session variables or JavaScript UDFs

---

# 9. Alternative ML Algorithms & Enhancements

## 9.1 Churn Prediction Alternatives

| Algorithm | Library (FOSS) | Pros | Cons | Expected AUC Range |
|-----------|---------------|------|------|---------------------|
| **Current: GradientBoosting** | scikit-learn | Interpretable, fast training | No native GPU, slower than XGBoost | 0.70–0.85 (real data) |
| **XGBoost** | `xgboost` (Apache-2.0) | Faster, better regularization, handles missing values natively | Slightly more complex tuning | 0.75–0.88 |
| **LightGBM** | `lightgbm` (MIT) | Fastest training, best for large datasets, leaf-wise growth | Can overfit on small data | 0.75–0.88 |
| **CatBoost** | `catboost` (Apache-2.0) | Handles categorical features natively, robust to overfitting | Slower training, larger memory | 0.75–0.88 |
| **Random Forest** | scikit-learn | Simpler, less prone to overfitting | Lower performance ceiling | 0.65–0.80 |
| **Logistic Regression** | scikit-learn | Fully interpretable, fast, good baseline | Cannot capture non-linear interactions | 0.60–0.75 |
| **Neural Network (MLP)** | scikit-learn / PyTorch | Captures complex patterns | Requires more data, less interpretable | 0.70–0.85 |
| **Survival Analysis** | `lifelines` (MIT) | Models *when* churn happens, not just *if* | Different output (hazard function) | N/A (different metric) |

### Recommended Enhancement: Ensemble Approach

```python
# Stacking ensemble combining multiple models (all FOSS)
from sklearn.ensemble import StackingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression

estimators = [
    ('xgb', XGBClassifier(n_estimators=100, max_depth=6, use_label_encoder=False)),
    ('lgbm', LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1)),
    ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=6)),
]

stacking_model = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(),
    cv=5,
    stack_method='predict_proba'
)
```

### Recommended Enhancement: Survival Analysis for Time-to-Churn

```python
# pip install lifelines (MIT license, in Anaconda)
from lifelines import CoxPHFitter

# Instead of "will they churn?", answer "when will they churn?"
cph = CoxPHFitter()
cph.fit(df_survival, duration_col='months_until_churn', event_col='churned')

# Predict median survival time for each constituent
median_survival = cph.predict_median(X_new)
# "This constituent will likely churn in 4.2 months" is more actionable than "73% chance of churn"
```

## 9.2 Upgrade Propensity Alternatives

| Algorithm | Best For | FOSS Library |
|-----------|----------|-------------|
| **Multi-label classification** | Capturing correlations between upgrade targets | scikit-learn `MultiOutputClassifier` |
| **Bayesian Personalized Ranking (BPR)** | Ranking upgrade paths by relevance | `implicit` (MIT) |
| **Uplift Modeling** | Measuring *incremental* impact of outreach | `causalml` (Apache-2.0), `scikit-uplift` (MIT) |
| **Multi-Armed Bandit** | Dynamically allocating outreach to highest-value targets | `vowpalwabbit` (BSD) |

### Recommended Enhancement: Uplift Modeling

Standard propensity models predict *who will upgrade*. Uplift models predict *who will upgrade because of our intervention* — a much more valuable question.

```python
# pip install scikit-uplift
from sklift.models import SoloModel
from sklift.metrics import uplift_auc_score

uplift_model = SoloModel(estimator=LGBMClassifier())
uplift_model.fit(X_train, y_train, treatment=treatment_train)
uplift_scores = uplift_model.predict(X_test)

# Now we know: "Contacting this person increases their upgrade probability by 23%"
# vs. "This person has a 45% probability of upgrading" (which may happen anyway)
```

## 9.3 Additional Models to Consider

| Model | Purpose | Algorithm | Library |
|-------|---------|-----------|---------|
| **Lifetime Value (LTV)** | Predict total future value per constituent | BG/NBD + Gamma-Gamma | `lifetimes` (MIT) |
| **Donor Segmentation** | Data-driven constituent segments | K-Means, HDBSCAN | scikit-learn, `hdbscan` |
| **Next Best Action** | Recommend optimal touchpoint per constituent | Multi-Armed Bandit | `vowpalwabbit` |
| **Campaign Response** | Predict response to specific campaign | Logistic Regression | scikit-learn |
| **Gift Amount Prediction** | Predict optimal ask amount | Quantile Regression | `statsmodels` |

### LTV Model Implementation (FOSS)

```python
# pip install lifetimes (MIT license)
from lifetimes import BetaGeoFitter, GammaGammaFitter

# Step 1: Fit frequency/recency model
bgf = BetaGeoFitter()
bgf.fit(summary['frequency'], summary['recency'], summary['T'])

# Step 2: Fit monetary value model
ggf = GammaGammaFitter()
ggf.fit(summary['frequency'], summary['monetary_value'])

# Step 3: Predict 12-month CLV
predicted_clv = ggf.customer_lifetime_value(
    bgf, summary['frequency'], summary['recency'],
    summary['T'], summary['monetary_value'],
    time=12, discount_rate=0.01
)
```

---

# 10. Benchmarking & Model Performance Assessment

## 10.1 Classification Metrics Framework

### Primary Metrics

| Metric | Formula | When to Use | Current Value | Target |
|--------|---------|-------------|---------------|--------|
| **AUC-ROC** | Area under ROC curve | Overall discrimination ability | 0.93 (synthetic) | >= 0.80 (real) |
| **AUC-PR** | Area under Precision-Recall curve | When classes are imbalanced (upgrade models) | Not reported | >= 0.40 |
| **Precision** | TP / (TP + FP) | When false positives are costly (e.g., wrong upgrade ask) | 0.784 | >= 0.70 |
| **Recall** | TP / (TP + FN) | When false negatives are costly (e.g., missing churners) | 0.712 | >= 0.75 |
| **F1 Score** | Harmonic mean of P & R | Balanced metric | Not reported | >= 0.70 |
| **Log Loss** | Cross-entropy of probabilities | When probability calibration matters | Not reported | < 0.50 |

### Business-Specific Metrics

| Metric | Definition | How to Measure |
|--------|-----------|---------------|
| **Revenue Saved** | $ retained from predicted churners who received intervention | Compare churn rate of contacted high-risk vs. control group |
| **Lift at K** | How much better the model is at finding churners in top K% vs. random | `(churn rate in top 10% predictions) / (overall churn rate)` |
| **Decile Analysis** | Churn rate by prediction score decile | Should monotonically increase from decile 1 to 10 |
| **Net Savings** | Revenue saved minus cost of intervention | `(saved_revenue) - (intervention_cost * contacted_count)` |
| **Precision at K** | Precision when only acting on top K predictions | Critical for limited outreach capacity |

## 10.2 Comprehensive Benchmarking Protocol

```python
# Full benchmarking suite (all FOSS — scikit-learn, matplotlib, pandas)
import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_recall_curve,
    roc_curve, confusion_matrix, classification_report,
    brier_score_loss, log_loss, calibration_curve
)
import matplotlib.pyplot as plt

class ModelBenchmark:
    """Comprehensive model benchmarking framework."""

    def __init__(self, y_true, y_prob, model_name="model"):
        self.y_true = y_true
        self.y_prob = y_prob
        self.model_name = model_name

    def full_report(self):
        results = {}

        # 1. Discrimination metrics
        results['auc_roc'] = roc_auc_score(self.y_true, self.y_prob)
        results['auc_pr'] = average_precision_score(self.y_true, self.y_prob)
        results['log_loss'] = log_loss(self.y_true, self.y_prob)
        results['brier_score'] = brier_score_loss(self.y_true, self.y_prob)

        # 2. Threshold-dependent metrics at optimal F1
        precision, recall, thresholds = precision_recall_curve(self.y_true, self.y_prob)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
        optimal_idx = np.argmax(f1_scores)
        optimal_threshold = thresholds[optimal_idx]

        y_pred = (self.y_prob >= optimal_threshold).astype(int)
        results['optimal_threshold'] = optimal_threshold
        results['precision_at_optimal'] = precision[optimal_idx]
        results['recall_at_optimal'] = recall[optimal_idx]
        results['f1_at_optimal'] = f1_scores[optimal_idx]

        # 3. Lift analysis
        results['lift_at_10pct'] = self._lift_at_k(0.10)
        results['lift_at_20pct'] = self._lift_at_k(0.20)

        # 4. Decile analysis
        results['decile_table'] = self._decile_analysis()

        return results

    def _lift_at_k(self, k):
        n = int(len(self.y_true) * k)
        top_k_idx = np.argsort(self.y_prob)[-n:]
        top_k_rate = self.y_true.iloc[top_k_idx].mean() if hasattr(self.y_true, 'iloc') else self.y_true[top_k_idx].mean()
        overall_rate = self.y_true.mean()
        return top_k_rate / overall_rate if overall_rate > 0 else 0

    def _decile_analysis(self):
        df = pd.DataFrame({'actual': self.y_true, 'predicted': self.y_prob})
        df['decile'] = pd.qcut(df['predicted'], 10, labels=False, duplicates='drop') + 1
        return df.groupby('decile').agg(
            count=('actual', 'count'),
            churn_rate=('actual', 'mean'),
            avg_score=('predicted', 'mean')
        ).sort_index(ascending=False)
```

## 10.3 Model Comparison Framework

```python
# Compare multiple algorithms side-by-side (FOSS)
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=6),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, max_depth=6),
    'XGBoost': XGBClassifier(n_estimators=100, max_depth=6, use_label_encoder=False, eval_metric='logloss'),
    'LightGBM': LGBMClassifier(n_estimators=100, max_depth=6, verbose=-1),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}

for name, model in models.items():
    fold_aucs = []
    for train_idx, val_idx in cv.split(X, y):
        model.fit(X[train_idx], y[train_idx])
        y_prob = model.predict_proba(X[val_idx])[:, 1]
        fold_aucs.append(roc_auc_score(y[val_idx], y_prob))
    results[name] = {'mean_auc': np.mean(fold_aucs), 'std_auc': np.std(fold_aucs)}

comparison_df = pd.DataFrame(results).T.sort_values('mean_auc', ascending=False)
print(comparison_df)
```

## 10.4 SQL Server Benchmarking

For environments still on SQL Server, model performance can be tracked in a dedicated table:

```sql
-- SQL Server: Model performance tracking table
CREATE TABLE ml.model_performance_log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    evaluation_date DATETIME DEFAULT GETDATE(),
    dataset_type VARCHAR(20) NOT NULL,  -- 'train', 'validation', 'test', 'production'
    record_count INT,
    auc_roc DECIMAL(5,4),
    auc_pr DECIMAL(5,4),
    precision_at_optimal DECIMAL(5,4),
    recall_at_optimal DECIMAL(5,4),
    f1_at_optimal DECIMAL(5,4),
    optimal_threshold DECIMAL(5,4),
    log_loss DECIMAL(8,6),
    brier_score DECIMAL(8,6),
    lift_at_10pct DECIMAL(6,2),
    lift_at_20pct DECIMAL(6,2),
    notes VARCHAR(500)
);

-- Query to detect model drift
SELECT
    model_name,
    model_version,
    evaluation_date,
    auc_roc,
    LAG(auc_roc) OVER (PARTITION BY model_name ORDER BY evaluation_date) AS prev_auc,
    auc_roc - LAG(auc_roc) OVER (PARTITION BY model_name ORDER BY evaluation_date) AS auc_change
FROM ml.model_performance_log
WHERE dataset_type = 'production'
ORDER BY model_name, evaluation_date DESC;
```

## 10.5 Snowflake Benchmarking

```sql
-- Snowflake: Leverage MODEL_PREDICTIONS table for production monitoring
SELECT
    MODEL_NAME,
    MODEL_VERSION,
    PREDICTION_DATE,
    COUNT(*) as predictions_made,
    AVG(PREDICTION_SCORE) as avg_score,
    STDDEV(PREDICTION_SCORE) as score_stddev,
    SUM(CASE WHEN PREDICTION_TIER = 'critical' THEN 1 ELSE 0 END) as critical_count,
    -- Population Stability Index (PSI) approximation
    -- Compare current score distribution to baseline
    SUM(CASE WHEN PREDICTION_SCORE < 0.3 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as pct_low,
    SUM(CASE WHEN PREDICTION_SCORE BETWEEN 0.3 AND 0.6 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as pct_medium,
    SUM(CASE WHEN PREDICTION_SCORE >= 0.6 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as pct_high
FROM GOLDEN.MODEL_PREDICTIONS
GROUP BY MODEL_NAME, MODEL_VERSION, PREDICTION_DATE
ORDER BY PREDICTION_DATE DESC;
```

---

# 11. Platform Options: SQL Server, FOSS, and Snowflake

## 11.1 Current State: SQL Server Implementation

For organizations still on SQL Server, here's how each solution maps:

| Solution | SQL Server Implementation | Key Differences |
|----------|--------------------------|-----------------|
| Identity Resolution | Python script with pyodbc connection to SQL Server | Use SQL Server's built-in `SOUNDEX()` and `DIFFERENCE()` for phonetic matching |
| Golden Record | Standard SQL schema with clustered indexes | No VARIANT type — use XML or JSON columns (SQL Server 2016+) |
| Metrics Engine | T-SQL stored procedures per metric | `DATEADD(MONTH, -12, GETDATE())` syntax |
| ML Models | Python with scikit-learn, scores written back via pyodbc | SQL Server ML Services (R/Python in-database) available but limited |
| Data Quality | SQL Server Agent jobs running Python scripts | Or use SSIS data quality transforms |
| ETL Integration | SSIS packages or Python scripts | Mature but rigid compared to modern ELT |

### SQL Server Specific Considerations

```sql
-- SQL Server: Golden record with temporal tables for SCD Type 2
CREATE TABLE golden.constituents (
    constituent_id VARCHAR(36) NOT NULL PRIMARY KEY,
    canonical_email VARCHAR(255),
    lifecycle_stage VARCHAR(50),
    churn_risk_score DECIMAL(5,4),
    -- ... other fields ...
    valid_from DATETIME2 GENERATED ALWAYS AS ROW START,
    valid_to DATETIME2 GENERATED ALWAYS AS ROW END,
    PERIOD FOR SYSTEM_TIME (valid_from, valid_to)
) WITH (SYSTEM_VERSIONING = ON (HISTORY_TABLE = golden.constituents_history));

-- Query point-in-time state
SELECT * FROM golden.constituents
FOR SYSTEM_TIME AS OF '2025-06-15'
WHERE constituent_id = 'UC-00012345';
```

## 11.2 FOSS Stack (pandas, GitHub, Anaconda Distribution)

Complete free and open-source implementation:

| Component | FOSS Tool | License | Install |
|-----------|-----------|---------|---------|
| **Data Processing** | pandas, NumPy | BSD-3 | `conda install pandas numpy` |
| **ML Training** | scikit-learn, XGBoost, LightGBM | BSD/Apache/MIT | `conda install scikit-learn xgboost lightgbm` |
| **String Matching** | rapidfuzz, jellyfish | MIT | `pip install rapidfuzz jellyfish` |
| **Data Quality** | Great Expectations | Apache-2.0 | `pip install great-expectations` |
| **Data Profiling** | ydata-profiling | MIT | `pip install ydata-profiling` |
| **Workflow Orchestration** | Apache Airflow / Prefect | Apache-2.0 | `pip install apache-airflow` |
| **Version Control** | Git + GitHub | GPL / Free tier | N/A |
| **Notebook Environment** | JupyterLab | BSD-3 | `conda install jupyterlab` |
| **Visualization** | matplotlib, seaborn, plotly | BSD/MIT | `conda install matplotlib seaborn plotly` |
| **Database** | PostgreSQL + SQLAlchemy | PostgreSQL / MIT | `conda install sqlalchemy psycopg2` |
| **Explainability** | SHAP, LIME | MIT | `pip install shap lime` |
| **Experiment Tracking** | MLflow | Apache-2.0 | `pip install mlflow` |
| **Feature Store** | Feast | Apache-2.0 | `pip install feast` |
| **Survival Analysis** | lifelines | MIT | `pip install lifelines` |
| **LTV Modeling** | lifetimes | MIT | `pip install lifetimes` |
| **Uplift Modeling** | scikit-uplift, causalml | MIT / Apache-2.0 | `pip install scikit-uplift` |

### FOSS Pipeline Example

```python
# Complete FOSS pipeline using Anaconda distribution + pip extras
# environment.yml
"""
name: cpm-enterprise
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pandas=2.1
  - numpy=1.26
  - scikit-learn=1.4
  - xgboost=2.0
  - lightgbm=4.2
  - matplotlib=3.8
  - seaborn=0.13
  - jupyterlab=4.0
  - sqlalchemy=2.0
  - pyyaml=6.0
  - pytest=8.0
  - pip:
    - rapidfuzz
    - great-expectations
    - shap
    - mlflow
    - lifelines
"""
```

## 11.3 Snowflake Migration Path

### What Changes When Moving to Snowflake

| Aspect | Before (SQL Server/FOSS) | After (Snowflake) |
|--------|--------------------------|-------------------|
| **Storage** | On-prem / self-managed DB | Snowflake managed, auto-scaled |
| **Compute** | Fixed server resources | Elastic virtual warehouses |
| **Identity Resolution** | Python script on app server | Snowpark Python stored procedure |
| **ML Training** | Local Python, scores pushed to DB | Snowpark ML, training on Snowflake compute |
| **ML Serving** | Batch scoring via cron | Snowflake Tasks + Snowpark inference |
| **Data Quality** | Python validator scripts | dbt tests + Snowflake Alerts |
| **Metrics Engine** | Python reads YAML, generates SQL | Same YAML, Snowflake-specific SQL auto-selected |
| **ETL** | SSIS / Airflow / Python scripts | Fivetran (managed) + dbt (transformation) |
| **Feature Store** | Custom `constituent_features` table | Snowflake Feature Store (managed) |
| **Model Registry** | File system (pickle/joblib) | Snowflake Model Registry (versioned, governed) |
| **Scheduling** | cron / SQL Server Agent / Airflow | Snowflake Tasks (native) |
| **Governance** | Documentation + manual process | Snowflake Horizon (tags, policies, lineage) |

---

# 12. ML Governance Enhancements

## 12.1 Current Gaps

The blueprint has strong *data* governance but minimal *ML* governance. Key gaps:

| Gap | Risk | Description |
|-----|------|-------------|
| **No model registry** | HIGH | Models saved as pickle files with no versioning, no metadata, no lineage |
| **No model approval workflow** | HIGH | No process for stakeholder sign-off before a model enters production |
| **No bias monitoring** | MEDIUM | No checks for demographic bias in churn/upgrade predictions |
| **No drift detection** | HIGH | No automated detection of feature drift or concept drift over time |
| **No A/B testing framework** | MEDIUM | No mechanism to validate that model-driven actions actually improve outcomes |
| **No model cards** | MEDIUM | No standardized documentation for each model's purpose, limitations, and performance |

## 12.2 ML Governance Framework (Enhancement)

### Model Lifecycle

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   DEVELOP    │───>│   VALIDATE   │───>│   APPROVE    │───>│   DEPLOY     │
│              │    │              │    │              │    │              │
│ Data Science │    │ Cross-val,   │    │ Governance   │    │ Engineering  │
│ trains model │    │ bias check,  │    │ Council      │    │ deploys &    │
│              │    │ benchmark    │    │ approves     │    │ monitors     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                           │                   │                    │
                           ▼                   ▼                    ▼
                    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                    │   REJECT     │    │   MONITOR    │    │   RETRAIN    │
                    │              │    │              │    │              │
                    │ Return with  │    │ Drift check  │    │ Triggered by │
                    │ feedback     │    │ weekly       │    │ drift alert  │
                    └──────────────┘    └──────────────┘    └──────────────┘
```

### Model Card Template

```yaml
# config/model_cards/churn_prediction.yaml
model_card:
  name: "Sustainer Churn Prediction"
  version: "1.0.0"
  owner: "Data Science Team"
  business_sponsor: "VP, Membership"

  purpose: |
    Predict probability of sustainer cancellation within 90 days
    to enable proactive retention outreach.

  intended_use:
    - "Membership team: prioritize retention calls"
    - "Marketing: trigger automated retention email sequences"

  not_intended_for:
    - "Determining donor worthiness or value as a person"
    - "Automated cancellation decisions without human review"

  training_data:
    source: "golden.constituent_features + golden.sustainer_status_changes"
    date_range: "2023-01-01 to 2025-12-31"
    record_count: 12500
    positive_rate: 0.18

  performance:
    auc_roc: 0.83
    auc_pr: 0.61
    precision_at_50: 0.74
    recall_at_50: 0.69
    lift_at_10pct: 3.2

  fairness:
    tested_groups: ["zip_code_region", "gift_amount_quartile", "tenure_bucket"]
    disparities_found: "None significant"

  limitations:
    - "Trained only on data from 2023+; pre-merger patterns not captured"
    - "Does not account for external economic factors"
    - "Performance degrades for sustainers with < 3 months tenure"

  monitoring:
    drift_check: "weekly"
    retrain_trigger: "AUC drops below 0.75 or PSI > 0.2"
    human_review: "quarterly by Governance Council"

  approval:
    approved_by: "Data Governance Council"
    approval_date: "2026-01-15"
    next_review: "2026-04-15"
```

### Drift Detection (FOSS Implementation)

```python
# Population Stability Index (PSI) for feature drift detection
def calculate_psi(baseline, current, bins=10):
    """Calculate PSI between baseline and current distributions."""
    baseline_pcts, bin_edges = np.histogram(baseline, bins=bins)
    current_pcts, _ = np.histogram(current, bins=bin_edges)

    baseline_pcts = baseline_pcts / len(baseline) + 1e-6
    current_pcts = current_pcts / len(current) + 1e-6

    psi = np.sum((current_pcts - baseline_pcts) * np.log(current_pcts / baseline_pcts))
    return psi
    # PSI < 0.10: No drift
    # PSI 0.10-0.25: Moderate drift, investigate
    # PSI > 0.25: Significant drift, retrain

# Run weekly on all features
for feature in FEATURE_COLS:
    psi = calculate_psi(baseline_data[feature], current_data[feature])
    if psi > 0.25:
        alert(f"Feature drift detected: {feature}, PSI={psi:.3f}")
```

### Snowflake ML Governance

```sql
-- Snowflake Model Registry for governance
-- Register model with metadata
CALL SYSTEM$REGISTER_MODEL(
    'churn_predictor',
    'v1.2',
    OBJECT_CONSTRUCT(
        'auc', 0.83,
        'precision', 0.74,
        'approved_by', 'Data Governance Council',
        'approval_date', '2026-01-15',
        'retrain_trigger', 'AUC < 0.75 or PSI > 0.2'
    )
);

-- Snowflake Tags for model governance
ALTER TABLE golden.model_predictions SET TAG governance.model_status = 'production';
ALTER TABLE golden.model_predictions SET TAG governance.data_classification = 'confidential';
```

---

# 13. Snowflake Migration Advantages

## 13.1 Feature-by-Feature Comparison

| Feature | SQL Server | FOSS (PostgreSQL) | Snowflake |
|---------|-----------|-------------------|-----------|
| **Elastic compute** | Fixed | Fixed | Auto-scale up/down in seconds |
| **Storage/compute separation** | Coupled | Coupled | Fully separated (pay for what you use) |
| **Time Travel** | Temporal tables (limited) | pg_audit (manual) | Native (up to 90 days) |
| **Semi-structured data** | JSON columns (limited) | JSONB (good) | VARIANT (excellent, auto-optimized) |
| **Data sharing** | Export/import | Export/import | Instant, zero-copy data sharing |
| **ML integration** | SQL Server ML Services | External Python | Snowpark ML, Cortex, Model Registry |
| **Data governance** | Manual | Manual | Horizon (tags, policies, lineage) |
| **Clustering** | Clustered indexes (manual) | pg_repack (manual) | Automatic micro-partitioning + clustering keys |
| **Concurrency** | Connection limits | Connection limits | Unlimited with multi-cluster warehouses |
| **Maintenance** | DBA required | DBA required | Zero maintenance (managed service) |

## 13.2 Snowflake-Specific Features That Enhance This Blueprint

1. **Snowflake Cortex (AI/ML)**: LLM functions for natural language queries against constituent data
2. **Snowpark Container Services**: Run full Python ML pipelines as managed containers
3. **Dynamic Tables**: Auto-refreshing materialized views for metrics
4. **Streams + Tasks**: Event-driven pipelines for real-time identity resolution
5. **Data Clean Rooms**: Share data with partners (e.g., media buyers) without exposing PII
6. **Snowflake Marketplace**: Access third-party data enrichment (demographics, wealth indicators)
7. **Fail-safe**: 7 days of additional data recovery beyond time travel
8. **Search Optimization**: Sub-second lookups on constituent email/phone

---

# 14. Interview Talking Points

## 14.1 For Each Solution — "Tell Me About..."

### Identity Resolution
> "I built a two-phase matching engine: deterministic first for high-confidence exact matches, then probabilistic with Jaro-Winkler similarity and configurable weights. The key improvement I'd make in production is adding a blocking strategy — grouping by zip code or last name Soundex — to make the probabilistic phase scalable from O(n^2) to O(n*k). On Snowflake, we'd leverage native JAROWINKLER_SIMILARITY() and Snowpark UDFs."

### Golden Record
> "The schema supports three platforms from day one — Standard SQL, Snowflake, and Databricks — preventing vendor lock-in. The key risk is the wide constituent table mixing slowly-changing attributes with frequently-updated ML scores. I'd separate those into a dedicated scores table and add SCD Type 2 for lifecycle tracking. On Snowflake, we'd use Dynamic Tables for automatic materialization."

### Churn Model
> "Gradient Boosting with 10 features achieving AUC 0.93 on synthetic data. I want to be transparent: real-world performance will be lower, likely 0.75-0.85. The critical improvements are adding time-based validation splits, probability calibration, and SHAP explanations so the membership team understands *why* someone is flagged, not just their score. I'd also recommend survival analysis to predict *when* churn happens, not just *if*."

### ML Governance
> "The blueprint has strong data governance but needs a parallel ML governance framework: model cards documenting purpose and limitations, a formal approval workflow through the Governance Council, weekly drift detection using Population Stability Index, and bias monitoring across demographic groups. On Snowflake, we'd use the Model Registry and Horizon for this."

## 14.2 Questions to Ask the Interview Panel

1. "What CRM and donation systems are currently in use? Are they Allegiance, Raiser's Edge, Salesforce?"
2. "Has any identity resolution work been attempted before, and what was the experience?"
3. "What's the current data warehouse platform, and is the Snowflake decision finalized?"
4. "How is 'active member' currently defined, and how many definitions exist across teams?"
5. "What's the appetite for ML/predictive capabilities vs. getting the data foundation right first?"
6. "What does the current data team look like in terms of roles and capacity?"

---

*This document is designed for interview preparation. Each section provides both technical depth for engineering discussions and strategic context for leadership conversations.*
