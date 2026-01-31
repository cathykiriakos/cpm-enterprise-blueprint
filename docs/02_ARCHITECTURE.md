# CPM Enterprise Systems Architecture
## A Technical Deep-Dive into Public Media Data Unification

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Analysis](#2-problem-analysis)
3. [Solution Architecture](#3-solution-architecture)
4. [Component Deep-Dives](#4-component-deep-dives)
5. [Data Model Design](#5-data-model-design)
6. [Integration Patterns](#6-integration-patterns)
7. [ML/AI Strategy](#7-mlai-strategy)
8. [Implementation Strategy](#8-implementation-strategy)
9. [Risk Mitigation](#9-risk-mitigation)

---

## 1. Executive Summary

### The Challenge

Public media organizations face a unique data challenge: they serve audiences across multiple platforms (radio, print, digital, events) with multiple revenue streams (donations, memberships, subscriptions, sponsorships) managed by different teams using different systems. Post-merger organizations like Chicago Public Media (WBEZ + Chicago Sun-Times) compound this complexity.

### The Solution

This blueprint provides a **modular, configurable framework** for unifying constituent data, standardizing metrics, and enabling data-driven engagement. Key principles:

| Principle | Implementation |
|-----------|----------------|
| **Configuration over code** | Business rules in YAML, not hard-coded |
| **Idempotency everywhere** | All processes safely re-runnable |
| **Platform agnostic** | SQL variants for Snowflake, Databricks, and standard SQL |
| **Governance built-in** | Quality checks and lineage tracking are core features |
| **Self-service enabled** | Business users can run analyses without engineering tickets |

### Why This Approach Works

1. **Incremental delivery**: Each component delivers standalone value; no "big bang" required
2. **Stakeholder alignment**: Metrics dictionary forces agreement before implementation
3. **Technical debt prevention**: Standards and governance from day one
4. **Future-proof**: Modular design accommodates new systems and use cases

---

## 2. Problem Analysis

### 2.1 The Fragmentation Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TYPICAL PUBLIC MEDIA DATA SILOS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   WBEZ World                              Sun-Times World                   │
│   ────────────                            ───────────────                   │
│   ┌──────────────┐                        ┌──────────────┐                  │
│   │ Membership   │                        │ Subscription │                  │
│   │ Database     │                        │ Database     │                  │
│   │              │                        │              │                  │
│   │ • member_id  │                        │ • sub_id     │                  │
│   │ • email      │                        │ • email      │                  │
│   │ • gifts[]    │                        │ • payments[] │                  │
│   └──────────────┘                        └──────────────┘                  │
│          │                                       │                          │
│          │     ┌──────────────┐                  │                          │
│          │     │   PROBLEM    │                  │                          │
│          └────►│              │◄─────────────────┘                          │
│                │ Same person, │                                             │
│                │ no link!     │                                             │
│                └──────────────┘                                             │
│                                                                             │
│   Shared Systems (But Not Integrated)                                       │
│   ───────────────────────────────────                                       │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│   │   Email      │  │   Events     │  │   Website    │                      │
│   │   Marketing  │  │   Ticketing  │  │   Analytics  │                      │
│   │              │  │              │  │              │                      │
│   │ • contact_id │  │ • ticket_id  │  │ • user_id    │                      │
│   │ • email      │  │ • email      │  │ • cookie_id  │                      │
│   └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Quantifying the Pain

| Problem | Business Impact | Technical Cause |
|---------|-----------------|-----------------|
| Duplicate communications | Donor fatigue; unsubscribes | No unified constituent ID |
| Inconsistent metrics | Leadership distrust; slow decisions | Each team calculates differently |
| Manual reconciliation | Staff time; error-prone | No automated integration |
| Missed upgrade opportunities | Lost revenue | Can't see cross-platform engagement |
| Campaign targeting gaps | Wasted spend; irrelevant asks | Fragmented audience view |

### 2.3 Root Cause Analysis

```
WHY can't we get a unified view of our audience?
│
├─► Multiple systems evolved independently
│   └─► WHY? Different teams, different needs, different vendors
│       └─► WHY? No enterprise architecture governance
│           └─► WHY? Resource constraints; urgent > important
│
├─► No common identifier across systems
│   └─► WHY? Email is inconsistent; people have multiple
│       └─► WHY? No identity resolution strategy
│           └─► WHY? Never prioritized; seemed "nice to have"
│
└─► Metrics defined differently by each team
    └─► WHY? No single source of truth
        └─► WHY? No governance committee
            └─► WHY? Cross-functional alignment is hard
```

**Key Insight**: The problem isn't primarily technical—it's organizational. Technical solutions must include governance and stakeholder alignment to succeed.

---

## 3. Solution Architecture

### 3.1 Target State Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CPM UNIFIED DATA ECOSYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                        SOURCE SYSTEMS LAYER                           ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          ║  │
│  ║  │  WBEZ   │ │Sun-Times│ │ Events  │ │  Email  │ │ Website │          ║  │
│  ║  │Donation │ │  Subs   │ │ Tickets │ │Marketing│ │Analytics│          ║  │
│  ║  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          ║  │
│  ╚═══════╪══════════╪══════════╪══════════╪══════════╪═══════════════════╝  │
│          │          │          │          │          │                      │
│          ▼          ▼          ▼          ▼          ▼                      │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                       INTEGRATION LAYER                               ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                       ║  │
│  ║   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   ║  │
│  ║   │   Connectors    │    │  Schema Registry│    │   ETL Engine    │   ║  │
│  ║   │  (Standardized) │    │  (Mapping Rules)│    │  (Idempotent)   │   ║  │
│  ║   └─────────────────┘    └─────────────────┘    └─────────────────┘   ║  │
│  ║                                                                       ║  │
│  ║   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   ║  │
│  ║   │  Data Quality   │    │Identity Resolver│    │  Audit Logger   │   ║  │
│  ║   │    Checks       │    │(Matching Engine)│    │  (Lineage)      │   ║  │
│  ║   └─────────────────┘    └─────────────────┘    └─────────────────┘   ║  │
│  ║                                                                       ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                        │
│                                    ▼                                        │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                     UNIFIED DATA PLATFORM                             ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                       ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                      RAW LAYER                                  │ ║  │
│  ║   │   Immutable landing zone; source-system schemas preserved       │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                 │                                     ║  │
│  ║                                 ▼                                     ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                    STAGING LAYER                                │ ║  │
│  ║   │   Cleaned, validated, standardized; quality rules applied       │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                 │                                     ║  │
│  ║                                 ▼                                     ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                   GOLDEN LAYER                                  │ ║  │
│  ║   │  ┌───────────────────────────────────────────────────────────┐  │ ║  │
│  ║   │  │                 CONSTITUENT GOLDEN RECORD                 │  │ ║  │
│  ║   │  │  • unified_constituent_id (UUID)                          │  │ ║  │
│  ║   │  │  • canonical_email, canonical_name, canonical_address     │  │ ║  │
│  ║   │  │  • source_system_ids[] (links back to all source records) │  │ ║  │
│  ║   │  │  • engagement_history[] (cross-platform events)           │  │ ║  │
│  ║   │  │  • lifecycle_stage (prospect/member/sustainer/major/legacy│  │ ║  │
│  ║   │  │  • propensity_scores (churn, upgrade, capacity)           │  │ ║  │
│  ║   │  └───────────────────────────────────────────────────────────┘  │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                 │                                     ║  │
│  ║                                 ▼                                     ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                    MART LAYER                                   │ ║  │
│  ║   │   Department-specific views; pre-aggregated for performance     │ ║  │
│  ║   │   • Membership Mart  • Development Mart  • Marketing Mart       │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                                                       ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐              │
│          │                         │                         │              │
│          ▼                         ▼                         ▼              │
│  ┌───────────────┐      ┌───────────────────┐      ┌───────────────┐        │
│  │   ANALYTICS   │      │   OPERATIONAL     │      │    ML/AI      │        │
│  │    & BI       │      │   APPLICATIONS    │      │   MODELS      │        │
│  │               │      │                   │      │               │        │
│  │ • Dashboards  │      │ • Campaign tools  │      │ • Churn pred  │        │
│  │ • Ad-hoc SQL  │      │ • Segmentation    │      │ • Upgrade prop│        │
│  │ • Self-service│      │ • Personalization │      │ • LTV scoring │        │
│  └───────────────┘      └───────────────────┘      └───────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Why This Architecture?

#### Layer Separation Rationale

| Layer | Purpose | Why Separate? |
|-------|---------|---------------|
| **Raw** | Preserve source data exactly | Enables replay; audit trail; debugging |
| **Staging** | Clean and validate | Isolates quality issues; standardizes formats |
| **Golden** | Single source of truth | Resolves identities; eliminates duplicates |
| **Mart** | Serve consumers | Performance optimization; department-specific logic |

#### Key Design Decisions

**Decision 1: Golden Record as Central Hub**

*Alternative considered*: Virtual integration (query across sources at runtime)

*Why rejected*: 
- Performance: Cross-system joins are slow
- Complexity: Business logic scattered across queries
- Governance: Harder to enforce quality rules

*Chosen approach*: Materialized golden record with scheduled refresh

*Trade-off accepted*: Data is not real-time (acceptable for most use cases; can add streaming for specific needs)

**Decision 2: Configuration-Driven Rules**

*Alternative considered*: Hard-coded business logic in Python/SQL

*Why rejected*:
- Changes require code deploys
- Business users can't modify rules
- Harder to audit what rules are in effect

*Chosen approach*: YAML-based configuration for:
- Metric definitions
- Data quality rules
- Identity matching thresholds
- Segmentation criteria

**Decision 3: Multi-Platform SQL Support**

*Alternative considered*: Single platform (Snowflake only)

*Why this approach*:
- Organizations may already have Databricks
- Migration flexibility
- Demonstrates platform expertise
- Enables comparison and informed decisions

---

## 4. Component Deep-Dives

### 4.1 Constituent Unification Engine

#### The Identity Resolution Problem

```
INPUT: Records from multiple systems

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ WBEZ Donations  │  │ Sun-Times Subs  │  │ Event Tickets   │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ ID: D-1001      │  │ ID: S-5001      │  │ ID: E-9001      │
│ john@gmail.com  │  │ j.smith@work.com│  │ john@gmail.com  │
│ John Smith      │  │ John M Smith    │  │ J. Smith        │
│ 123 Main St     │  │ 123 Main Street │  │ (no address)    │
└─────────────────┘  └─────────────────┘  └─────────────────┘

QUESTION: Are these the same person?

OUTPUT: Unified constituent with confidence score

┌────────────────────────────────────────────────────────────┐
│ UNIFIED CONSTITUENT: UC-7f3a8b2c                           │
├────────────────────────────────────────────────────────────┤
│ Canonical Email: john@gmail.com                            │
│ Canonical Name: John M Smith                               │
│ Canonical Address: 123 Main St, Chicago IL 60601           │
│                                                            │
│ Linked Source Records:                                     │
│   • WBEZ Donations: D-1001 (match: deterministic/email)    │
│   • Sun-Times Subs: S-5001 (match: probabilistic/0.87)     │
│   • Event Tickets: E-9001 (match: deterministic/email)     │
│                                                            │
│ Match Audit:                                               │
│   D-1001 ↔ E-9001: email exact match (confidence: 1.0)     │
│   D-1001 ↔ S-5001: name fuzzy + address fuzzy (conf: 0.87) │
└────────────────────────────────────────────────────────────┘
```

#### Matching Algorithm Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    IDENTITY RESOLUTION ALGORITHM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: DETERMINISTIC MATCHING                                            │
│  ═══════════════════════════════                                            │
│  High-confidence matches on exact identifiers                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Rule D1: Email Exact Match                                          │    │
│  │   IF email_a.lower().strip() == email_b.lower().strip()             │    │
│  │   AND email is not in [generic_emails]  # e.g., info@, admin@       │    │
│  │   THEN match_type = 'deterministic', confidence = 1.0               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Rule D2: Phone Exact Match (normalized)                             │    │
│  │   IF normalize_phone(phone_a) == normalize_phone(phone_b)           │    │
│  │   AND phone is not null                                             │    │
│  │   THEN match_type = 'deterministic', confidence = 0.95              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  PHASE 2: PROBABILISTIC MATCHING                                            │
│  ═══════════════════════════════                                            │
│  For records not matched deterministically                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Feature Extraction:                                                 │    │
│  │   • name_similarity = jaro_winkler(name_a, name_b)                  │    │
│  │   • address_similarity = address_match_score(addr_a, addr_b)        │    │
│  │   • phone_partial = partial_phone_match(phone_a, phone_b)           │    │
│  │   • email_domain = same_email_domain(email_a, email_b)              │    │
│  │   • zip_match = exact_zip_match(zip_a, zip_b)                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Scoring Model:                                                      │    │
│  │                                                                     │    │
│  │   confidence = (                                                    │    │
│  │       name_similarity * 0.35 +                                      │    │
│  │       address_similarity * 0.30 +                                   │    │
│  │       phone_partial * 0.15 +                                        │    │
│  │       email_domain * 0.10 +                                         │    │
│  │       zip_match * 0.10                                              │    │
│  │   )                                                                 │    │
│  │                                                                     │    │
│  │   IF confidence >= 0.85: auto_match = True                          │    │
│  │   ELIF confidence >= 0.70: review_queue = True                      │    │
│  │   ELSE: no_match = True                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  PHASE 3: CONFLICT RESOLUTION                                               │
│  ═══════════════════════════════                                            │
│  When matched records have conflicting data                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Resolution Rules (configurable):                                    │    │
│  │                                                                     │    │
│  │   • email: prefer most recently used (engagement activity)          │    │
│  │   • name: prefer longest (most complete) version                    │    │
│  │   • address: prefer most recent update timestamp                    │    │
│  │   • phone: prefer mobile over landline; most recent                 │    │
│  │                                                                     │    │
│  │ All conflicts logged for audit                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Why This Approach?

1. **Two-phase matching** balances precision and recall:
   - Deterministic rules prevent false positives on high-quality matches
   - Probabilistic scoring catches harder matches without human review for every pair

2. **Configurable thresholds** allow tuning per use case:
   - Major donor outreach: higher threshold (0.90) to avoid embarrassing mistakes
   - Marketing campaigns: lower threshold (0.80) acceptable; volume matters

3. **Audit trail** enables:
   - Debugging when matches seem wrong
   - Compliance with data protection regulations
   - Continuous improvement of matching rules

### 4.2 Metrics Engine

#### The Metrics Problem

```
SCENARIO: Leadership asks "How many active members do we have?"

┌─────────────────────────────────────────────────────────────────────────────┐
│                         THREE DIFFERENT ANSWERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MEMBERSHIP TEAM:          DEVELOPMENT TEAM:        FINANCE TEAM:           │
│  "Active Member" =         "Active Member" =        "Active Member" =       │
│  Anyone who donated        Anyone who donated       Anyone who donated      │
│  in last 12 months         in last 13 months        in current fiscal year  │
│                            (they include grace)     (July 1 - June 30)      │
│                                                                             │
│  COUNT: 77,000             COUNT: 82,000            COUNT: 71,000           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                     │    │
│  │   LEADERSHIP: "Which number is right?!"                             │    │
│  │                                                                     │    │
│  │   REAL ANSWER: They're all "right" given their definitions.         │    │
│  │   The problem is there's no agreed single source of truth.          │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Solution: Metrics Dictionary as Code

```yaml
# config/metrics_definitions.yaml
# THIS IS THE SINGLE SOURCE OF TRUTH

metrics:
  active_member:
    display_name: "Active Member"
    definition: >
      A constituent who has made at least one donation (any amount) 
      within the trailing 12 calendar months from the measurement date.
    business_owner: "VP, Membership"
    calculation:
      sql: |
        COUNT(DISTINCT constituent_id)
        WHERE last_donation_date >= DATE_ADD(CURRENT_DATE, INTERVAL -12 MONTH)
    dimensions:
      - by_source: "WBEZ vs Sun-Times"
      - by_gift_type: "One-time vs Recurring"
    refresh_frequency: daily
    data_sources:
      - table: golden.constituents
        fields: [constituent_id, last_donation_date]
    caveats:
      - "Excludes event-only ticket purchasers (no donation component)"
      - "Grace period NOT included; see 'active_member_with_grace' for that variant"
    
  sustaining_member:
    display_name: "Sustaining Member"
    definition: >
      A constituent with an active recurring donation that has not been 
      cancelled and has successfully processed at least one payment in 
      the last 90 days.
    business_owner: "Director, Membership"
    calculation:
      sql: |
        COUNT(DISTINCT constituent_id)
        WHERE recurring_status = 'active'
          AND last_successful_recurring_date >= DATE_ADD(CURRENT_DATE, INTERVAL -90 DAY)
    # ... etc
```

#### Metrics Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         METRICS ENGINE FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │ metrics_        │  YAML file defines:                                   │
│   │ definitions.yaml│  • Business definition (human-readable)               │
│   │                 │  • SQL calculation (machine-executable)               │
│   │                 │  • Owner, refresh frequency, caveats                  │
│   └────────┬────────┘                                                       │
│            │                                                                │
│            ▼                                                                │
│   ┌─────────────────┐                                                       │
│   │ MetricsEngine   │  Python class that:                                   │
│   │                 │  • Parses YAML definitions                            │
│   │                 │  • Generates platform-specific SQL                    │
│   │                 │  • Executes calculations                              │
│   │                 │  • Validates results against expectations             │
│   └────────┬────────┘                                                       │
│            │                                                                │
│            ├──────────────────┬──────────────────┐                          │
│            ▼                  ▼                  ▼                          │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│   │ Standard SQL    │ │ Snowflake SQL   │ │ Databricks SQL  │               │
│   │                 │ │                 │ │                 │               │
│   │ DATE_ADD(...)   │ │ DATEADD(...)    │ │ DATE_ADD(...)   │               │
│   │ INTERVAL syntax │ │ Snowflake funcs │ │ Spark SQL funcs │               │
│   └────────┬────────┘ └────────┬────────┘ └────────┬────────┘               │
│            │                   │                   │                        │
│            └───────────────────┴───────────────────┘                        │
│                                │                                            │
│                                ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        METRICS OUTPUT                               │   │
│   │                                                                     │   │
│   │  {                                                                  │   │
│   │    "metric": "active_member",                                       │   │
│   │    "value": 77432,                                                  │   │
│   │    "as_of_date": "2024-01-15",                                      │   │
│   │    "definition_version": "1.2.0",                                   │   │
│   │    "dimensions": {                                                  │   │
│   │      "by_source": {"WBEZ": 52100, "Sun-Times": 25332}               │   │
│   │    }                                                                │   │
│   │  }                                                                  │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Integration Framework

#### The Integration Problem

Every system integration is currently built differently:
- Different error handling approaches
- Inconsistent logging
- No standard retry logic
- Credentials scattered

#### Solution: Standardized Connector Pattern

```python
# Conceptual design - see src/integrations/ for implementation

class BaseConnector(ABC):
    """
    All integrations inherit from this base class.
    Enforces consistent patterns for:
    - Authentication
    - Error handling  
    - Retry logic
    - Logging
    - Metrics collection
    """
    
    @abstractmethod
    def extract(self, params: dict) -> DataFrame:
        """Pull data from source system"""
        pass
    
    @abstractmethod  
    def validate(self, data: DataFrame) -> ValidationResult:
        """Check data quality before proceeding"""
        pass
    
    def transform(self, data: DataFrame) -> DataFrame:
        """Apply standardization (can be overridden)"""
        return self._apply_schema_mapping(data)
    
    @abstractmethod
    def load(self, data: DataFrame, destination: str) -> LoadResult:
        """Push data to destination"""
        pass
    
    # Built-in behaviors (not overridden)
    def _retry_with_backoff(self, func, max_attempts=3):
        """Exponential backoff retry logic"""
        pass
    
    def _log_operation(self, operation, status, details):
        """Structured logging to central system"""
        pass
    
    def _emit_metrics(self, operation, duration, row_count):
        """Observability metrics"""
        pass
```

#### Why This Pattern?

| Benefit | Explanation |
|---------|-------------|
| **Consistency** | Every integration behaves the same way |
| **Maintainability** | Fix a bug once, it's fixed everywhere |
| **Onboarding** | New engineers learn one pattern |
| **Observability** | All connectors emit same metrics; unified dashboards |
| **Testability** | Standard interface enables standard test patterns |

---

## 5. Data Model Design

### 5.1 Golden Record Schema

```sql
-- Core constituent table
CREATE TABLE golden.constituents (
    -- Primary identifier
    constituent_id          UUID PRIMARY KEY,
    
    -- Canonical (resolved) attributes
    canonical_email         VARCHAR(255),
    canonical_first_name    VARCHAR(100),
    canonical_last_name     VARCHAR(100),
    canonical_phone         VARCHAR(20),
    canonical_address_line1 VARCHAR(255),
    canonical_address_line2 VARCHAR(255),
    canonical_city          VARCHAR(100),
    canonical_state         VARCHAR(50),
    canonical_zip           VARCHAR(20),
    canonical_country       VARCHAR(50) DEFAULT 'USA',
    
    -- Lifecycle classification
    lifecycle_stage         VARCHAR(50),  -- prospect/member/sustainer/major_donor/legacy
    first_engagement_date   DATE,
    last_engagement_date    DATE,
    
    -- Aggregated metrics
    total_lifetime_giving   DECIMAL(12,2),
    total_gift_count        INTEGER,
    largest_single_gift     DECIMAL(12,2),
    average_gift_amount     DECIMAL(10,2),
    
    -- Recurring status
    is_sustainer            BOOLEAN,
    recurring_amount        DECIMAL(10,2),
    recurring_frequency     VARCHAR(20),  -- monthly/quarterly/annual
    recurring_start_date    DATE,
    
    -- Engagement scores (ML-generated)
    churn_risk_score        DECIMAL(5,4),  -- 0.0000 to 1.0000
    upgrade_propensity      DECIMAL(5,4),
    estimated_capacity      VARCHAR(20),   -- low/medium/high/major
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_quality_score      DECIMAL(3,2),  -- 0.00 to 1.00
    
    -- Indexes for common queries
    INDEX idx_email (canonical_email),
    INDEX idx_lifecycle (lifecycle_stage),
    INDEX idx_sustainer (is_sustainer),
    INDEX idx_churn (churn_risk_score)
);

-- Source system linkage (for traceability)
CREATE TABLE golden.constituent_source_links (
    link_id                 UUID PRIMARY KEY,
    constituent_id          UUID REFERENCES golden.constituents(constituent_id),
    source_system           VARCHAR(50),   -- 'wbez_donations', 'suntimes_subs', etc.
    source_record_id        VARCHAR(100),
    match_type              VARCHAR(20),   -- 'deterministic', 'probabilistic'
    match_confidence        DECIMAL(5,4),
    matched_at              TIMESTAMP,
    match_rule_version      VARCHAR(20),
    
    UNIQUE (source_system, source_record_id)
);

-- Engagement events (cross-platform activity)
CREATE TABLE golden.engagement_events (
    event_id                UUID PRIMARY KEY,
    constituent_id          UUID REFERENCES golden.constituents(constituent_id),
    event_type              VARCHAR(50),   -- 'donation', 'subscription', 'email_open', 'event_attend'
    event_date              DATE,
    event_timestamp         TIMESTAMP,
    source_system           VARCHAR(50),
    
    -- Event-specific attributes (JSON for flexibility)
    event_attributes        JSON,
    
    -- For donation events
    donation_amount         DECIMAL(10,2),
    donation_type           VARCHAR(20),   -- 'one_time', 'recurring', 'major_gift'
    campaign_code           VARCHAR(50),
    
    INDEX idx_constituent (constituent_id),
    INDEX idx_event_date (event_date),
    INDEX idx_event_type (event_type)
);
```

### 5.2 Dimension Tables

```sql
-- Date dimension for time-based analysis
CREATE TABLE dimensions.dim_date (
    date_key                INTEGER PRIMARY KEY,  -- YYYYMMDD
    full_date               DATE,
    day_of_week             INTEGER,
    day_name                VARCHAR(10),
    day_of_month            INTEGER,
    day_of_year             INTEGER,
    week_of_year            INTEGER,
    month_number            INTEGER,
    month_name              VARCHAR(10),
    quarter                 INTEGER,
    year                    INTEGER,
    fiscal_year             INTEGER,
    fiscal_quarter          INTEGER,
    is_weekend              BOOLEAN,
    is_holiday              BOOLEAN,
    is_pledge_drive         BOOLEAN,  -- CPM-specific
    pledge_drive_name       VARCHAR(50)
);

-- Campaign dimension
CREATE TABLE dimensions.dim_campaign (
    campaign_key            INTEGER PRIMARY KEY,
    campaign_code           VARCHAR(50),
    campaign_name           VARCHAR(255),
    campaign_type           VARCHAR(50),  -- 'pledge_drive', 'annual_appeal', 'special'
    start_date              DATE,
    end_date                DATE,
    channel                 VARCHAR(50),  -- 'radio', 'email', 'direct_mail', 'digital'
    target_audience         VARCHAR(100),
    goal_amount             DECIMAL(12,2),
    actual_amount           DECIMAL(12,2),
    is_active               BOOLEAN
);
```

---

## 6. Integration Patterns

### 6.1 ETL vs ELT Decision

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ETL vs ELT DECISION MATRIX                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TRADITIONAL ETL:                                                           │
│  ┌─────────┐    ┌───────────┐    ┌─────────┐                                │
│  │ Extract │───►│ Transform │───►│  Load   │                                │
│  │         │    │ (outside) │    │         │                                │
│  └─────────┘    └───────────┘    └─────────┘                                │
│                                                                             │
│  Pros: Smaller data warehouse; cleaner data arrives                         │
│  Cons: Transformation logic outside warehouse; harder to debug              │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  MODERN ELT (OUR CHOICE):                                                   │
│  ┌─────────┐    ┌─────────┐    ┌───────────┐                                │
│  │ Extract │───►│  Load   │───►│ Transform │                                │
│  │         │    │  (raw)  │    │ (inside)  │                                │
│  └─────────┘    └─────────┘    └───────────┘                                │
│                                                                             │
│  Pros:                                                                      │
│  • Raw data preserved (can replay transformations)                          │
│  • Leverage warehouse compute power                                         │
│  • Transformations in SQL (auditable, versionable)                          │
│  • Easier debugging (all data visible)                                      │
│                                                                             │
│  Cons:                                                                      │
│  • More storage required (acceptable with modern costs)                     │
│  • Need good governance on raw layer access                                 │
│                                                                             │
│  DECISION: ELT with clear layer separation (raw → staging → golden → mart)  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Incremental Load Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INCREMENTAL LOAD PATTERN                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GOAL: Process only changed records, not full table scans                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. WATERMARK TRACKING                                               │    │
│  │                                                                     │    │
│  │    Each source has a "high watermark" - the last processed value    │    │
│  │                                                                     │    │
│  │    watermarks table:                                                │    │
│  │    ┌──────────────┬─────────────────────┬───────────────────────┐   │    │
│  │    │ source       │ watermark_column    │ last_value            │   │    │
│  │    ├──────────────┼─────────────────────┼───────────────────────┤   │    │
│  │    │ wbez_gifts   │ modified_at         │ 2024-01-15 03:42:17   │   │    │
│  │    │ suntimes_sub │ updated_timestamp   │ 2024-01-15 03:40:22   │   │    │
│  │    └──────────────┴─────────────────────┴───────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 2. EXTRACT DELTA                                                    │    │
│  │                                                                     │    │
│  │    SELECT * FROM source_table                                       │    │
│  │    WHERE modified_at > [last_watermark]                             │    │
│  │      AND modified_at <= [current_max]                               │    │
│  │                                                                     │    │
│  │    Note: Upper bound prevents missing records if source is updating │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 3. UPSERT (MERGE) INTO TARGET                                       │    │
│  │                                                                     │    │
│  │    MERGE INTO target AS t                                           │    │
│  │    USING delta AS d                                                 │    │
│  │    ON t.id = d.id                                                   │    │
│  │    WHEN MATCHED THEN UPDATE SET ...                                 │    │
│  │    WHEN NOT MATCHED THEN INSERT ...                                 │    │
│  │                                                                     │    │
│  │    This is IDEMPOTENT - can re-run safely                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 4. UPDATE WATERMARK                                                 │    │
│  │                                                                     │    │
│  │    Only after successful load:                                      │    │
│  │    UPDATE watermarks                                                │    │
│  │    SET last_value = [current_max]                                   │    │
│  │    WHERE source = [source_name]                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. ML/AI Strategy

### 7.1 Use Cases Prioritization

| Use Case | Business Value | Technical Complexity | Priority |
|----------|---------------|---------------------|----------|
| **Churn Prediction** | High (prevent revenue loss) | Medium | 🔴 P1 |
| **Upgrade Propensity** | High (increase revenue) | Medium | 🔴 P1 |
| **Donor Capacity** | High (major gift targeting) | High | 🟡 P2 |
| **Content Personalization** | Medium (engagement) | High | 🟢 P3 |
| **Attribution Modeling** | Medium (optimize spend) | High | 🟢 P3 |

### 7.2 Churn Prediction Model Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CHURN PREDICTION ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEFINITION OF CHURN:                                                       │
│  • Sustaining member: Cancellation or 3 consecutive failed payments         │
│  • One-time donor: No donation in 13 months after previous gift             │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  FEATURE ENGINEERING:                                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ENGAGEMENT FEATURES                                                 │    │
│  │ • days_since_last_engagement                                        │    │
│  │ • email_open_rate_30d, email_open_rate_90d                          │    │
│  │ • email_click_rate_30d                                              │    │
│  │ • events_attended_12m                                               │    │
│  │ • website_visits_30d                                                │    │
│  │ • content_types_consumed (news, podcasts, events)                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ GIVING HISTORY FEATURES                                             │    │
│  │ • tenure_months                                                     │    │
│  │ • total_lifetime_giving                                             │    │
│  │ • gift_count                                                        │    │
│  │ • avg_gift_amount                                                   │    │
│  │ • gift_amount_trend (increasing/stable/decreasing)                  │    │
│  │ • months_since_last_gift                                            │    │
│  │ • is_sustainer                                                      │    │
│  │ • sustainer_months_active                                           │    │
│  │ • payment_failures_12m                                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DEMOGRAPHIC FEATURES                                                │    │
│  │ • zip_code_median_income (external enrichment)                      │    │
│  │ • distance_to_chicago_center                                        │    │
│  │ • acquisition_channel                                               │    │
│  │ • first_gift_campaign                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  MODEL ARCHITECTURE:                                                        │
│                                                                             │
│  ┌──────────────┐                                                           │
│  │   Features   │                                                           │
│  │   (30+)      │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐    We use Gradient Boosting (XGBoost/LightGBM)            │
│  │   XGBoost    │    because:                                               │
│  │   Classifier │    • Handles mixed feature types                          │
│  │              │    • Robust to missing values                             │
│  └──────┬───────┘    • Interpretable feature importance                     │
│         │            • Good performance on tabular data                     │
│         ▼                                                                   │
│  ┌──────────────┐                                                           │
│  │ Probability  │    Output: 0.0 to 1.0 churn probability                   │
│  │   Score      │    Threshold: 0.6 = "high risk"                           │
│  └──────────────┘                                                           │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  MODEL OUTPUTS & ACTIONS:                                                   │
│                                                                             │
│  Score Range    │ Risk Level │ Recommended Action                           │
│  ───────────────┼────────────┼──────────────────────────────────────────    │
│  0.00 - 0.30    │ Low        │ Standard communications                      │
│  0.30 - 0.60    │ Medium     │ Engagement campaign; survey                  │
│  0.60 - 0.85    │ High       │ Personal outreach; retention offer           │
│  0.85 - 1.00    │ Critical   │ Urgent intervention; executive contact       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Upgrade Propensity Model Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UPGRADE PROPENSITY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  UPGRADE PATHS:                                                             │
│  • One-time donor → Sustaining member                                       │
│  • Sustaining member → Increased monthly amount                             │
│  • Any donor → Major gift ($1,000+)                                         │
│                                                                             │
│  We model each separately with shared feature framework                     │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  ADDITIONAL FEATURES (beyond churn model):                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ CAPACITY INDICATORS                                                 │    │
│  │ • zip_code_wealth_index                                             │    │
│  │ • home_value_estimate (if available)                                │    │
│  │ • recent_gift_vs_historical_ratio                                   │    │
│  │ • multiple_nonprofit_donor (external data)                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ TIMING SIGNALS                                                      │    │
│  │ • days_since_last_upgrade                                           │    │
│  │ • upgrade_history_count                                             │    │
│  │ • seasonality_giving_pattern                                        │    │
│  │ • responded_to_upgrade_ask_before                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  OUTPUT: Priority matrix for outreach                                       │
│                                                                             │
│                     LOW CHURN RISK          HIGH CHURN RISK                 │
│                   ┌─────────────────────┬─────────────────────┐             │
│  HIGH UPGRADE     │ 🎯 PRIME TARGET     │ ⚠️ CAREFUL ASK     │             │
│  PROPENSITY       │ Ask for upgrade     │ Steward first,      │             │
│                   │ confidently         │ then gentle ask     │             │
│                   ├─────────────────────┼─────────────────────┤             │
│  LOW UPGRADE      │ 📧 NURTURE          │ 🚨 SAVE FIRST      │             │
│  PROPENSITY       │ Continue engagement │ Retention focus;    │             │
│                   │ build relationship  │ no upgrade ask      │             │
│                   └─────────────────────┴─────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Strategy

### 8.1 Phased Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      IMPLEMENTATION PHASES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: FOUNDATION (Months 1-3)                                           │
│  ════════════════════════════════                                           │
│                                                                             │
│  Week 1-4: Discovery & Assessment                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Stakeholder interviews (all revenue teams)                        │    │
│  │ • System inventory and access provisioning                          │    │
│  │ • Data quality assessment on each source                            │    │
│  │ • Pain point prioritization workshop                                │    │
│  │                                                                     │    │
│  │ DELIVERABLE: Current State Assessment Document                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Week 5-8: Governance Setup                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Establish Data Governance Committee                               │    │
│  │ • Draft metrics dictionary (get stakeholder sign-off)               │    │
│  │ • Define data ownership RACI                                        │    │
│  │ • Create development standards document                             │    │
│  │                                                                     │    │
│  │ DELIVERABLE: Governance Framework v1.0                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Week 9-12: Quick Wins                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Automate one painful manual process per team                      │    │
│  │ • Build first integration connector (e.g., WBEZ donations)          │    │
│  │ • Create prototype dashboard with agreed metrics                    │    │
│  │                                                                     │    │
│  │ DELIVERABLE: 3+ Quick Wins Deployed; Credibility Established        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  PHASE 2: UNIFICATION (Months 4-8)                                          │
│  ═════════════════════════════════                                          │
│                                                                             │
│  Month 4: Identity Resolution                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Deploy identity resolution algorithm                              │    │
│  │ • Build match rules with stakeholder input                          │    │
│  │ • Create golden record v1.0 (internal testing)                      │    │
│  │                                                                     │    │
│  │ DELIVERABLE: Golden Record with 80%+ match rate                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Month 5-6: Full Integration                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Connect all major source systems                                  │    │
│  │ • Implement data quality monitoring                                 │    │
│  │ • Build 360° constituent view                                       │    │
│  │                                                                     │    │
│  │ DELIVERABLE: All Sources Integrated; Quality Alerts Active          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Month 7-8: Validation & Rollout                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Parallel run: compare new metrics to old                          │    │
│  │ • Stakeholder validation sessions                                   │    │
│  │ • Training and documentation                                        │    │
│  │ • Production cutover                                                │    │
│  │                                                                     │    │
│  │ DELIVERABLE: Golden Record in Production; Teams Trained             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                             │
│  PHASE 3: OPTIMIZATION (Months 9-12)                                        │
│  ═════════════════════════════════                                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • Deploy churn prediction model                                     │    │
│  │ • Deploy upgrade propensity model                                   │    │
│  │ • Enable lifecycle automation (lapsed reactivation, etc.)           │    │
│  │ • Build self-service analytics layer                                │    │
│  │ • A/B testing infrastructure                                        │    │
│  │                                                                     │    │
│  │ DELIVERABLE: ML Models in Production; Self-Service Active           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Team Engagement RACI

| Activity | Membership | Development | Marketing | IT/Security | Finance | Exec Sponsor |
|----------|:----------:|:-----------:|:---------:|:-----------:|:-------:|:------------:|
| Define "Active Member" | **A** | C | C | I | C | I |
| Define "Donor Retention" | C | **A** | C | I | C | I |
| Approve Golden Record Schema | C | C | C | **R** | C | **A** |
| Sign-off on Metrics Dictionary | **R** | **R** | **R** | I | **R** | **A** |
| Validate Data Quality Rules | **R** | **R** | **R** | C | I | I |
| Approve Production Cutover | C | C | C | **R** | C | **A** |

**R** = Responsible, **A** = Accountable, **C** = Consulted, **I** = Informed

---

## 9. Risk Mitigation

### 9.1 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Stakeholder disagreement on metrics | High | High | Governance committee; escalation path to exec sponsor |
| Data quality worse than expected | Medium | High | Early assessment; quality monitoring; cleansing budget |
| Source system API changes | Medium | Medium | Abstract connector layer; version detection; alerts |
| Scope creep | High | Medium | Clear phase boundaries; change control process |
| Key person dependency | Medium | High | Documentation; cross-training; runbooks |
| Budget constraints | Medium | High | Phased delivery; demonstrate ROI early |

### 9.2 Rollback Strategy

Every major deployment has a documented rollback:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROLLBACK DECISION TREE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Production Issue Detected                                                  │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ Data corruption │──Yes──► IMMEDIATE ROLLBACK                             │
│  │ or loss?        │         • Restore from backup                          │
│  └────────┬────────┘         • Notify all stakeholders                      │
│           │ No               • Post-incident review                         │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ Metrics wrong   │──Yes──► INVESTIGATE FIRST                              │
│  │ by >5%?         │         • May be real change, not bug                  │
│  └────────┬────────┘         • Compare to source systems                    │
│           │ No               • Rollback if confirmed bug                    │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ Performance     │──Yes──► SCALE/OPTIMIZE                                 │
│  │ degraded?       │         • Add resources if possible                    │
│  └────────┬────────┘         • Rollback if critical path affected           │
│           │ No                                                              │
│           ▼                                                                 │
│  ┌─────────────────┐                                                        │
│  │ User-facing     │──Yes──► FIX FORWARD IF POSSIBLE                        │
│  │ but non-critical│         • Hotfix within 24h                            │
│  └────────┬────────┘         • Rollback if hotfix not feasible              │
│           │ No                                                              │
│           ▼                                                                 │
│       MONITOR                                                               │
│       Schedule fix for next release                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix: Technology Choices

### Platform Comparison

| Capability | Snowflake | Databricks | Standard SQL |
|------------|-----------|------------|--------------|
| **Best for** | Analytics-heavy | ML/Engineering-heavy | Portability |
| **Pricing model** | Compute + storage separate | Cluster-based | Varies |
| **ML integration** | Snowpark (newer) | MLflow (mature) | External |
| **Real-time** | Limited | Spark Streaming | Varies |
| **Governance** | Good | Unity Catalog | Varies |

**Recommendation**: If CPM is evaluating, Snowflake is likely better fit for:
- Analyst-heavy workflows
- Simpler pricing model
- Strong BI tool integration

Databricks better if:
- Heavy ML/AI investment planned
- Real-time requirements
- Engineering-led culture

This blueprint supports both.

---

*Document Version: 1.0*
*Last Updated: January 2025*
*Author: Catherine Kiriakos*