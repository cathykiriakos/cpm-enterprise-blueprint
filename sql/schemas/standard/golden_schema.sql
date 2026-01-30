-- =============================================================================
-- CPM ENTERPRISE DATA PLATFORM - SCHEMA DEFINITIONS
-- Standard SQL (ANSI-compliant)
-- =============================================================================
-- 
-- This file defines the golden record schema for the unified constituent
-- data platform. These schemas support the identity resolution, metrics
-- calculation, and ML model features.
--
-- LAYERS:
--   raw.*      - Raw data from source systems (immutable)
--   staging.*  - Cleaned and validated data
--   golden.*   - Unified constituent records (single source of truth)
--   mart.*     - Department-specific analytical views
--
-- Version: 1.0.0
-- Author: Catherine Kiriakos
-- =============================================================================

-- =============================================================================
-- GOLDEN LAYER - Core Tables
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Unified Constituent (Golden Record)
-- The single source of truth for all constituent data
-- -----------------------------------------------------------------------------
CREATE TABLE golden.constituents (
    -- Primary identifier (system-generated UUID)
    constituent_id          VARCHAR(36) PRIMARY KEY,
    
    -- Canonical (resolved) contact information
    canonical_email         VARCHAR(255),
    canonical_first_name    VARCHAR(100),
    canonical_last_name     VARCHAR(100),
    canonical_full_name     VARCHAR(200) GENERATED ALWAYS AS (
        CONCAT(COALESCE(canonical_first_name, ''), ' ', COALESCE(canonical_last_name, ''))
    ),
    canonical_phone         VARCHAR(20),
    canonical_address_line1 VARCHAR(255),
    canonical_address_line2 VARCHAR(255),
    canonical_city          VARCHAR(100),
    canonical_state         VARCHAR(50),
    canonical_zip           VARCHAR(20),
    canonical_country       VARCHAR(50) DEFAULT 'USA',
    
    -- Lifecycle classification
    lifecycle_stage         VARCHAR(50) NOT NULL DEFAULT 'prospect',
    -- Valid values: prospect, one_time_donor, sustainer, major_donor, legacy_prospect
    
    first_engagement_date   DATE,
    last_engagement_date    DATE,
    first_donation_date     DATE,
    last_donation_date      DATE,
    
    -- Giving summary (aggregated from donation_facts)
    total_lifetime_giving   DECIMAL(12,2) DEFAULT 0,
    total_gift_count        INTEGER DEFAULT 0,
    largest_single_gift     DECIMAL(12,2),
    average_gift_amount     DECIMAL(10,2),
    
    -- Sustainer status
    is_sustainer            BOOLEAN DEFAULT FALSE,
    recurring_status        VARCHAR(20),  -- active, paused, cancelled, failed
    recurring_monthly_amount DECIMAL(10,2),
    recurring_frequency     VARCHAR(20),  -- monthly, quarterly, annual
    sustainer_start_date    DATE,
    last_successful_payment_date DATE,
    consecutive_failed_payments INTEGER DEFAULT 0,
    
    -- Subscription status (Sun-Times)
    is_subscriber           BOOLEAN DEFAULT FALSE,
    subscription_type       VARCHAR(50),
    subscription_status     VARCHAR(20),
    subscription_start_date DATE,
    
    -- Engagement scores (calculated by ML models)
    churn_risk_score        DECIMAL(5,4),  -- 0.0000 to 1.0000
    churn_risk_tier         VARCHAR(20),   -- low, medium, high, critical
    upgrade_propensity      DECIMAL(5,4),
    upgrade_propensity_tier VARCHAR(20),
    estimated_capacity      VARCHAR(20),   -- low, medium, high, major
    lifetime_value_estimate DECIMAL(12,2),
    
    -- Email engagement metrics
    email_open_rate_30d     DECIMAL(5,4),
    email_click_rate_30d    DECIMAL(5,4),
    last_email_open_date    DATE,
    
    -- Source tracking
    primary_source          VARCHAR(50),   -- wbez, suntimes, events
    acquisition_channel     VARCHAR(50),
    acquisition_campaign    VARCHAR(100),
    acquisition_date        DATE,
    
    -- Data quality
    data_quality_score      DECIMAL(3,2),  -- 0.00 to 1.00
    has_valid_email         BOOLEAN,
    has_valid_phone         BOOLEAN,
    has_valid_address       BOOLEAN,
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version                 INTEGER DEFAULT 1,
    
    -- Constraints
    CONSTRAINT chk_lifecycle_stage CHECK (
        lifecycle_stage IN ('prospect', 'one_time_donor', 'sustainer', 'major_donor', 'legacy_prospect', 'lapsed')
    ),
    CONSTRAINT chk_churn_score CHECK (
        churn_risk_score IS NULL OR (churn_risk_score >= 0 AND churn_risk_score <= 1)
    )
);

-- Indexes for common query patterns
CREATE INDEX idx_constituents_email ON golden.constituents(canonical_email);
CREATE INDEX idx_constituents_lifecycle ON golden.constituents(lifecycle_stage);
CREATE INDEX idx_constituents_sustainer ON golden.constituents(is_sustainer) WHERE is_sustainer = TRUE;
CREATE INDEX idx_constituents_churn ON golden.constituents(churn_risk_score DESC);
CREATE INDEX idx_constituents_last_donation ON golden.constituents(last_donation_date);


-- -----------------------------------------------------------------------------
-- Source System Links
-- Maps unified constituents back to source system records
-- -----------------------------------------------------------------------------
CREATE TABLE golden.constituent_source_links (
    link_id                 VARCHAR(36) PRIMARY KEY,
    constituent_id          VARCHAR(36) NOT NULL,
    source_system           VARCHAR(50) NOT NULL,
    source_record_id        VARCHAR(100) NOT NULL,
    
    -- Match information
    match_type              VARCHAR(30) NOT NULL,  -- deterministic_email, deterministic_phone, probabilistic
    match_confidence        DECIMAL(5,4),
    match_rule_version      VARCHAR(20),
    
    -- Timestamps
    matched_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id),
    CONSTRAINT uq_source_record UNIQUE (source_system, source_record_id)
);

CREATE INDEX idx_source_links_constituent ON golden.constituent_source_links(constituent_id);
CREATE INDEX idx_source_links_source ON golden.constituent_source_links(source_system, source_record_id);


-- -----------------------------------------------------------------------------
-- Donation Facts
-- All donations across WBEZ and other channels
-- -----------------------------------------------------------------------------
CREATE TABLE golden.donation_facts (
    donation_id             VARCHAR(36) PRIMARY KEY,
    constituent_id          VARCHAR(36) NOT NULL,
    
    -- Donation details
    donation_date           DATE NOT NULL,
    donation_timestamp      TIMESTAMP,
    donation_amount         DECIMAL(12,2) NOT NULL,
    donation_type           VARCHAR(30) NOT NULL,  -- one_time, recurring, major_gift
    donation_status         VARCHAR(20) NOT NULL,  -- completed, pending, failed, refunded
    
    -- Payment information
    payment_method          VARCHAR(30),  -- credit_card, ach, check, paypal, cash
    payment_processor       VARCHAR(50),
    transaction_id          VARCHAR(100),
    
    -- Campaign attribution
    campaign_code           VARCHAR(50),
    campaign_name           VARCHAR(255),
    campaign_type           VARCHAR(50),  -- pledge_drive, annual_appeal, special, sustainer
    
    -- Channel attribution
    source_channel          VARCHAR(50),  -- web, phone, mail, event, recurring
    device_type             VARCHAR(20),  -- desktop, mobile, tablet
    
    -- Recurring specific
    is_recurring            BOOLEAN DEFAULT FALSE,
    recurring_sequence_num  INTEGER,  -- 1, 2, 3... for recurring gifts
    
    -- Source tracking
    source_system           VARCHAR(50) NOT NULL,
    source_record_id        VARCHAR(100),
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_donation_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
);

CREATE INDEX idx_donations_constituent ON golden.donation_facts(constituent_id);
CREATE INDEX idx_donations_date ON golden.donation_facts(donation_date);
CREATE INDEX idx_donations_campaign ON golden.donation_facts(campaign_code);
CREATE INDEX idx_donations_status ON golden.donation_facts(donation_status);
CREATE INDEX idx_donations_type ON golden.donation_facts(donation_type);


-- -----------------------------------------------------------------------------
-- Subscription Facts (Sun-Times)
-- -----------------------------------------------------------------------------
CREATE TABLE golden.subscription_facts (
    subscription_id         VARCHAR(36) PRIMARY KEY,
    constituent_id          VARCHAR(36) NOT NULL,
    
    -- Subscription details
    subscription_type       VARCHAR(50) NOT NULL,  -- digital, weekend, daily, premium
    subscription_name       VARCHAR(100),
    monthly_rate            DECIMAL(10,2),
    
    -- Status
    subscription_status     VARCHAR(20) NOT NULL,  -- active, paused, cancelled, expired
    start_date              DATE NOT NULL,
    end_date                DATE,
    cancellation_date       DATE,
    cancellation_reason     VARCHAR(100),
    
    -- Payment
    payment_method          VARCHAR(30),
    auto_renew              BOOLEAN DEFAULT TRUE,
    
    -- Acquisition
    acquisition_source      VARCHAR(50),
    promo_code              VARCHAR(50),
    
    -- Source tracking
    source_system           VARCHAR(50) DEFAULT 'suntimes_subs',
    source_record_id        VARCHAR(100),
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_subscription_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
);

CREATE INDEX idx_subscriptions_constituent ON golden.subscription_facts(constituent_id);
CREATE INDEX idx_subscriptions_status ON golden.subscription_facts(subscription_status);
CREATE INDEX idx_subscriptions_type ON golden.subscription_facts(subscription_type);


-- -----------------------------------------------------------------------------
-- Engagement Events
-- Cross-platform engagement tracking
-- -----------------------------------------------------------------------------
CREATE TABLE golden.engagement_events (
    event_id                VARCHAR(36) PRIMARY KEY,
    constituent_id          VARCHAR(36) NOT NULL,
    
    -- Event details
    event_type              VARCHAR(50) NOT NULL,
    -- Types: donation, subscription_start, subscription_cancel, email_open, 
    --        email_click, event_attend, website_visit, app_open
    
    event_date              DATE NOT NULL,
    event_timestamp         TIMESTAMP,
    
    -- Source
    source_system           VARCHAR(50),
    source_channel          VARCHAR(50),
    
    -- Event-specific attributes (flexible JSON)
    event_attributes        TEXT,  -- JSON string for flexibility
    
    -- For donation events (denormalized for query performance)
    donation_amount         DECIMAL(12,2),
    donation_type           VARCHAR(30),
    
    -- For email events
    email_campaign_id       VARCHAR(100),
    email_type              VARCHAR(50),
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_engagement_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
);

CREATE INDEX idx_engagement_constituent ON golden.engagement_events(constituent_id);
CREATE INDEX idx_engagement_date ON golden.engagement_events(event_date);
CREATE INDEX idx_engagement_type ON golden.engagement_events(event_type);


-- -----------------------------------------------------------------------------
-- Email Engagement (Detailed)
-- -----------------------------------------------------------------------------
CREATE TABLE golden.email_engagement (
    engagement_id           VARCHAR(36) PRIMARY KEY,
    constituent_id          VARCHAR(36),  -- May be null if not yet matched
    email_address           VARCHAR(255) NOT NULL,
    
    -- Email details
    email_campaign_id       VARCHAR(100),
    email_type              VARCHAR(50),  -- newsletter, appeal, event, update
    subject_line            VARCHAR(500),
    
    -- Timestamps
    send_date               DATE NOT NULL,
    send_timestamp          TIMESTAMP,
    
    -- Engagement
    delivered               BOOLEAN DEFAULT TRUE,
    delivery_status         VARCHAR(20),  -- delivered, bounced, blocked
    opened                  BOOLEAN DEFAULT FALSE,
    open_timestamp          TIMESTAMP,
    open_count              INTEGER DEFAULT 0,
    clicked                 BOOLEAN DEFAULT FALSE,
    click_timestamp         TIMESTAMP,
    click_count             INTEGER DEFAULT 0,
    
    -- Actions
    unsubscribed            BOOLEAN DEFAULT FALSE,
    unsubscribe_timestamp   TIMESTAMP,
    marked_spam             BOOLEAN DEFAULT FALSE,
    
    -- Source
    source_system           VARCHAR(50),
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email_engagement_constituent ON golden.email_engagement(constituent_id);
CREATE INDEX idx_email_engagement_email ON golden.email_engagement(email_address);
CREATE INDEX idx_email_engagement_date ON golden.email_engagement(send_date);


-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Date Dimension
-- -----------------------------------------------------------------------------
CREATE TABLE dimensions.dim_date (
    date_key                INTEGER PRIMARY KEY,  -- YYYYMMDD format
    full_date               DATE NOT NULL UNIQUE,
    
    -- Day attributes
    day_of_week             INTEGER,  -- 1=Sunday, 7=Saturday
    day_name                VARCHAR(10),
    day_of_month            INTEGER,
    day_of_year             INTEGER,
    is_weekend              BOOLEAN,
    is_weekday              BOOLEAN,
    
    -- Week attributes
    week_of_year            INTEGER,
    week_start_date         DATE,
    week_end_date           DATE,
    
    -- Month attributes
    month_number            INTEGER,
    month_name              VARCHAR(10),
    month_start_date        DATE,
    month_end_date          DATE,
    days_in_month           INTEGER,
    
    -- Quarter attributes
    quarter                 INTEGER,
    quarter_name            VARCHAR(10),
    quarter_start_date      DATE,
    quarter_end_date        DATE,
    
    -- Year attributes
    year                    INTEGER,
    year_start_date         DATE,
    year_end_date           DATE,
    
    -- Fiscal year (July 1 - June 30 for most nonprofits)
    fiscal_year             INTEGER,
    fiscal_quarter          INTEGER,
    fiscal_month            INTEGER,
    
    -- CPM-specific
    is_pledge_drive         BOOLEAN DEFAULT FALSE,
    pledge_drive_name       VARCHAR(50),
    is_holiday              BOOLEAN DEFAULT FALSE,
    holiday_name            VARCHAR(50)
);


-- -----------------------------------------------------------------------------
-- Campaign Dimension
-- -----------------------------------------------------------------------------
CREATE TABLE dimensions.dim_campaign (
    campaign_key            INTEGER PRIMARY KEY,
    campaign_code           VARCHAR(50) NOT NULL UNIQUE,
    campaign_name           VARCHAR(255),
    campaign_type           VARCHAR(50),  -- pledge_drive, annual_appeal, special, sustainer
    
    -- Dates
    start_date              DATE,
    end_date                DATE,
    is_active               BOOLEAN,
    
    -- Targeting
    channel                 VARCHAR(50),  -- radio, email, direct_mail, digital, multi
    target_audience         VARCHAR(100),
    
    -- Goals
    goal_amount             DECIMAL(12,2),
    goal_donors             INTEGER,
    
    -- Actuals (updated regularly)
    actual_amount           DECIMAL(12,2),
    actual_donors           INTEGER,
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =============================================================================
-- ML MODEL FEATURE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Constituent Features (for ML models)
-- Pre-calculated features refreshed daily
-- -----------------------------------------------------------------------------
CREATE TABLE golden.constituent_features (
    constituent_id          VARCHAR(36) PRIMARY KEY,
    feature_date            DATE NOT NULL,  -- Date features were calculated
    
    -- Engagement features
    days_since_last_engagement INTEGER,
    days_since_last_donation INTEGER,
    days_since_last_email_open INTEGER,
    
    -- Email engagement (trailing windows)
    email_open_rate_30d     DECIMAL(5,4),
    email_open_rate_90d     DECIMAL(5,4),
    email_click_rate_30d    DECIMAL(5,4),
    emails_received_30d     INTEGER,
    emails_opened_30d       INTEGER,
    
    -- Giving history features
    tenure_months           INTEGER,
    total_gifts             INTEGER,
    total_giving            DECIMAL(12,2),
    avg_gift_amount         DECIMAL(10,2),
    max_gift_amount         DECIMAL(10,2),
    min_gift_amount         DECIMAL(10,2),
    stddev_gift_amount      DECIMAL(10,2),
    
    -- Giving trends
    gifts_last_12m          INTEGER,
    giving_last_12m         DECIMAL(12,2),
    gifts_prior_12m         INTEGER,
    giving_prior_12m        DECIMAL(12,2),
    gift_amount_trend       VARCHAR(20),  -- increasing, stable, decreasing
    
    -- Sustainer features
    is_sustainer            BOOLEAN,
    sustainer_months        INTEGER,
    payment_failures_12m    INTEGER,
    upgrade_count           INTEGER,
    downgrade_count         INTEGER,
    
    -- Recency/Frequency/Monetary
    recency_days            INTEGER,
    frequency_annual        DECIMAL(5,2),
    monetary_avg            DECIMAL(10,2),
    rfm_score               INTEGER,  -- Combined RFM score 1-125
    
    -- Event attendance
    events_attended_12m     INTEGER,
    events_attended_all     INTEGER,
    
    -- Cross-platform engagement
    num_source_systems      INTEGER,
    has_wbez_donation       BOOLEAN,
    has_suntimes_sub        BOOLEAN,
    has_event_attendance    BOOLEAN,
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_features_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
);

CREATE INDEX idx_features_date ON golden.constituent_features(feature_date);


-- -----------------------------------------------------------------------------
-- Model Predictions
-- Stores predictions from ML models
-- -----------------------------------------------------------------------------
CREATE TABLE golden.model_predictions (
    prediction_id           VARCHAR(36) PRIMARY KEY,
    constituent_id          VARCHAR(36) NOT NULL,
    model_name              VARCHAR(50) NOT NULL,  -- churn_prediction, upgrade_propensity
    model_version           VARCHAR(20) NOT NULL,
    
    -- Prediction
    prediction_date         DATE NOT NULL,
    prediction_score        DECIMAL(5,4) NOT NULL,  -- 0.0000 to 1.0000
    prediction_tier         VARCHAR(20),  -- low, medium, high, critical
    
    -- Feature importance (top contributors to this prediction)
    top_features            TEXT,  -- JSON array of {feature, importance, value}
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_predictions_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
);

CREATE INDEX idx_predictions_constituent ON golden.model_predictions(constituent_id);
CREATE INDEX idx_predictions_model ON golden.model_predictions(model_name, prediction_date);
CREATE INDEX idx_predictions_score ON golden.model_predictions(prediction_score DESC);


-- =============================================================================
-- VIEWS FOR COMMON ACCESS PATTERNS
-- =============================================================================

-- Active Members View
CREATE VIEW golden.v_active_members AS
SELECT 
    c.*,
    DATEDIFF(CURRENT_DATE, c.last_donation_date) as days_since_last_gift
FROM golden.constituents c
WHERE c.last_donation_date >= DATE_ADD(CURRENT_DATE, INTERVAL -12 MONTH);


-- Sustainer Dashboard View
CREATE VIEW golden.v_sustainers AS
SELECT 
    c.constituent_id,
    c.canonical_email,
    c.canonical_first_name,
    c.canonical_last_name,
    c.recurring_monthly_amount,
    c.sustainer_start_date,
    c.last_successful_payment_date,
    c.consecutive_failed_payments,
    c.churn_risk_score,
    c.churn_risk_tier,
    DATEDIFF(CURRENT_DATE, c.sustainer_start_date) / 30 as sustainer_months
FROM golden.constituents c
WHERE c.is_sustainer = TRUE
  AND c.recurring_status = 'active';


-- High-Risk Churn View
CREATE VIEW golden.v_churn_risk AS
SELECT 
    c.constituent_id,
    c.canonical_email,
    c.canonical_full_name,
    c.lifecycle_stage,
    c.is_sustainer,
    c.recurring_monthly_amount,
    c.churn_risk_score,
    c.churn_risk_tier,
    c.days_since_last_engagement,
    c.email_open_rate_30d,
    mp.top_features as churn_factors
FROM golden.constituents c
LEFT JOIN golden.model_predictions mp 
    ON c.constituent_id = mp.constituent_id 
    AND mp.model_name = 'churn_prediction'
    AND mp.prediction_date = (
        SELECT MAX(prediction_date) 
        FROM golden.model_predictions 
        WHERE model_name = 'churn_prediction'
    )
WHERE c.churn_risk_score >= 0.6
ORDER BY c.churn_risk_score DESC;