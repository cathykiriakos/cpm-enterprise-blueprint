-- =============================================================================
-- CPM ENTERPRISE DATA PLATFORM - SCHEMA DEFINITIONS
-- Databricks SQL (Delta Lake)
-- =============================================================================
-- 
-- Databricks-specific implementation with:
-- - Delta Lake format for ACID transactions
-- - Unity Catalog integration
-- - Z-Ordering for query optimization
-- - Liquid clustering (Databricks-specific)
-- - Databricks-specific SQL functions
--
-- Version: 1.0.0
-- Author: Catherine Kiriakos
-- =============================================================================

-- Create catalog and schemas (Unity Catalog)
CREATE CATALOG IF NOT EXISTS cpm_enterprise;
USE CATALOG cpm_enterprise;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS golden;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS dimensions;

USE SCHEMA golden;

-- =============================================================================
-- GOLDEN LAYER - Core Tables (Delta Lake)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Unified Constituent (Golden Record)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.constituents (
    -- Primary identifier
    constituent_id          STRING NOT NULL,
    
    -- Canonical contact information
    canonical_email         STRING,
    canonical_first_name    STRING,
    canonical_last_name     STRING,
    canonical_full_name     STRING,
    canonical_phone         STRING,
    canonical_address_line1 STRING,
    canonical_address_line2 STRING,
    canonical_city          STRING,
    canonical_state         STRING,
    canonical_zip           STRING,
    canonical_country       STRING DEFAULT 'USA',
    
    -- Lifecycle classification
    lifecycle_stage         STRING NOT NULL DEFAULT 'prospect',
    first_engagement_date   DATE,
    last_engagement_date    DATE,
    first_donation_date     DATE,
    last_donation_date      DATE,
    
    -- Giving summary
    total_lifetime_giving   DECIMAL(12,2) DEFAULT 0,
    total_gift_count        INT DEFAULT 0,
    largest_single_gift     DECIMAL(12,2),
    average_gift_amount     DECIMAL(10,2),
    
    -- Sustainer status
    is_sustainer            BOOLEAN DEFAULT FALSE,
    recurring_status        STRING,
    recurring_monthly_amount DECIMAL(10,2),
    recurring_frequency     STRING,
    sustainer_start_date    DATE,
    last_successful_payment_date DATE,
    consecutive_failed_payments INT DEFAULT 0,
    
    -- Subscription status
    is_subscriber           BOOLEAN DEFAULT FALSE,
    subscription_type       STRING,
    subscription_status     STRING,
    subscription_start_date DATE,
    
    -- ML scores
    churn_risk_score        DECIMAL(5,4),
    churn_risk_tier         STRING,
    upgrade_propensity      DECIMAL(5,4),
    upgrade_propensity_tier STRING,
    estimated_capacity      STRING,
    lifetime_value_estimate DECIMAL(12,2),
    
    -- Email engagement
    email_open_rate_30d     DECIMAL(5,4),
    email_click_rate_30d    DECIMAL(5,4),
    last_email_open_date    DATE,
    
    -- Source tracking
    primary_source          STRING,
    acquisition_channel     STRING,
    acquisition_campaign    STRING,
    acquisition_date        DATE,
    
    -- Data quality
    data_quality_score      DECIMAL(3,2),
    has_valid_email         BOOLEAN,
    has_valid_phone         BOOLEAN,
    has_valid_address       BOOLEAN,
    
    -- Metadata
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    updated_at              TIMESTAMP DEFAULT current_timestamp(),
    version                 INT DEFAULT 1,
    
    -- Delta Lake constraints
    CONSTRAINT pk_constituents PRIMARY KEY (constituent_id)
)
USING DELTA
COMMENT 'Unified constituent golden record - single source of truth'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'quality' = 'gold'
);

-- Optimize table layout for common queries
OPTIMIZE golden.constituents ZORDER BY (lifecycle_stage, last_donation_date);


-- -----------------------------------------------------------------------------
-- Source System Links
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.constituent_source_links (
    link_id                 STRING NOT NULL,
    constituent_id          STRING NOT NULL,
    source_system           STRING NOT NULL,
    source_record_id        STRING NOT NULL,
    
    match_type              STRING NOT NULL,
    match_confidence        DECIMAL(5,4),
    match_rule_version      STRING,
    
    matched_at              TIMESTAMP DEFAULT current_timestamp(),
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    
    CONSTRAINT pk_source_links PRIMARY KEY (link_id),
    CONSTRAINT fk_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id),
    CONSTRAINT uq_source_record UNIQUE (source_system, source_record_id)
)
USING DELTA
COMMENT 'Links unified constituents to source system records'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true'
);


-- -----------------------------------------------------------------------------
-- Donation Facts
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.donation_facts (
    donation_id             STRING NOT NULL,
    constituent_id          STRING NOT NULL,
    
    donation_date           DATE NOT NULL,
    donation_timestamp      TIMESTAMP,
    donation_amount         DECIMAL(12,2) NOT NULL,
    donation_type           STRING NOT NULL,
    donation_status         STRING NOT NULL,
    
    payment_method          STRING,
    payment_processor       STRING,
    transaction_id          STRING,
    
    campaign_code           STRING,
    campaign_name           STRING,
    campaign_type           STRING,
    
    source_channel          STRING,
    device_type             STRING,
    
    is_recurring            BOOLEAN DEFAULT FALSE,
    recurring_sequence_num  INT,
    
    source_system           STRING NOT NULL,
    source_record_id        STRING,
    
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    updated_at              TIMESTAMP DEFAULT current_timestamp(),
    
    -- Partitioning column
    donation_year_month     STRING GENERATED ALWAYS AS (date_format(donation_date, 'yyyy-MM')),
    
    CONSTRAINT pk_donations PRIMARY KEY (donation_id),
    CONSTRAINT fk_donation_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
)
USING DELTA
PARTITIONED BY (donation_year_month)
COMMENT 'All donation transactions'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true'
);


-- -----------------------------------------------------------------------------
-- Subscription Facts
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.subscription_facts (
    subscription_id         STRING NOT NULL,
    constituent_id          STRING NOT NULL,
    
    subscription_type       STRING NOT NULL,
    subscription_name       STRING,
    monthly_rate            DECIMAL(10,2),
    
    subscription_status     STRING NOT NULL,
    start_date              DATE NOT NULL,
    end_date                DATE,
    cancellation_date       DATE,
    cancellation_reason     STRING,
    
    payment_method          STRING,
    auto_renew              BOOLEAN DEFAULT TRUE,
    
    acquisition_source      STRING,
    promo_code              STRING,
    
    source_system           STRING DEFAULT 'suntimes_subs',
    source_record_id        STRING,
    
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    updated_at              TIMESTAMP DEFAULT current_timestamp(),
    
    CONSTRAINT pk_subscriptions PRIMARY KEY (subscription_id),
    CONSTRAINT fk_subscription_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
)
USING DELTA
COMMENT 'Sun-Times subscription records';


-- -----------------------------------------------------------------------------
-- Engagement Events
-- Using STRUCT for flexible event attributes
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.engagement_events (
    event_id                STRING NOT NULL,
    constituent_id          STRING NOT NULL,
    
    event_type              STRING NOT NULL,
    event_date              DATE NOT NULL,
    event_timestamp         TIMESTAMP,
    
    source_system           STRING,
    source_channel          STRING,
    
    -- Databricks supports complex types natively
    event_attributes        MAP<STRING, STRING>,
    
    donation_amount         DECIMAL(12,2),
    donation_type           STRING,
    
    email_campaign_id       STRING,
    email_type              STRING,
    
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    
    -- Partition by month for efficient querying
    event_year_month        STRING GENERATED ALWAYS AS (date_format(event_date, 'yyyy-MM')),
    
    CONSTRAINT pk_engagement PRIMARY KEY (event_id),
    CONSTRAINT fk_engagement_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
)
USING DELTA
PARTITIONED BY (event_year_month)
COMMENT 'Cross-platform engagement events';


-- -----------------------------------------------------------------------------
-- Constituent Features (for ML with MLflow integration)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.constituent_features (
    constituent_id          STRING NOT NULL,
    feature_date            DATE NOT NULL,
    
    -- Engagement features
    days_since_last_engagement INT,
    days_since_last_donation INT,
    days_since_last_email_open INT,
    
    -- Email engagement
    email_open_rate_30d     DECIMAL(5,4),
    email_open_rate_90d     DECIMAL(5,4),
    email_click_rate_30d    DECIMAL(5,4),
    emails_received_30d     INT,
    emails_opened_30d       INT,
    
    -- Giving history
    tenure_months           INT,
    total_gifts             INT,
    total_giving            DECIMAL(12,2),
    avg_gift_amount         DECIMAL(10,2),
    max_gift_amount         DECIMAL(10,2),
    min_gift_amount         DECIMAL(10,2),
    stddev_gift_amount      DECIMAL(10,2),
    
    -- Giving trends
    gifts_last_12m          INT,
    giving_last_12m         DECIMAL(12,2),
    gifts_prior_12m         INT,
    giving_prior_12m        DECIMAL(12,2),
    gift_amount_trend       STRING,
    
    -- Sustainer features
    is_sustainer            BOOLEAN,
    sustainer_months        INT,
    payment_failures_12m    INT,
    upgrade_count           INT,
    downgrade_count         INT,
    
    -- RFM
    recency_days            INT,
    frequency_annual        DECIMAL(5,2),
    monetary_avg            DECIMAL(10,2),
    rfm_score               INT,
    
    -- Events
    events_attended_12m     INT,
    events_attended_all     INT,
    
    -- Cross-platform
    num_source_systems      INT,
    has_wbez_donation       BOOLEAN,
    has_suntimes_sub        BOOLEAN,
    has_event_attendance    BOOLEAN,
    
    -- Feature vector for ML (Databricks ML-ready format)
    feature_vector          ARRAY<DOUBLE>,
    feature_names           ARRAY<STRING>,
    
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    
    CONSTRAINT pk_features PRIMARY KEY (constituent_id, feature_date),
    CONSTRAINT fk_features_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
)
USING DELTA
PARTITIONED BY (feature_date)
COMMENT 'Pre-calculated features for ML models - MLflow compatible';


-- -----------------------------------------------------------------------------
-- Model Predictions (MLflow integration)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE golden.model_predictions (
    prediction_id           STRING NOT NULL,
    constituent_id          STRING NOT NULL,
    model_name              STRING NOT NULL,
    model_version           STRING NOT NULL,
    
    -- MLflow run tracking
    mlflow_run_id           STRING,
    mlflow_experiment_id    STRING,
    
    prediction_date         DATE NOT NULL,
    prediction_score        DECIMAL(5,4) NOT NULL,
    prediction_tier         STRING,
    prediction_label        INT,  -- Binary classification label
    
    -- Feature importance as structured data
    top_features            ARRAY<STRUCT<feature_name: STRING, importance: DOUBLE, value: DOUBLE>>,
    
    -- SHAP values for explainability
    shap_values             MAP<STRING, DOUBLE>,
    
    created_at              TIMESTAMP DEFAULT current_timestamp(),
    
    CONSTRAINT pk_predictions PRIMARY KEY (prediction_id),
    CONSTRAINT fk_predictions_constituent FOREIGN KEY (constituent_id) 
        REFERENCES golden.constituents(constituent_id)
)
USING DELTA
PARTITIONED BY (model_name, prediction_date)
COMMENT 'ML model predictions with MLflow integration';


-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

CREATE OR REPLACE TABLE dimensions.dim_date (
    date_key                INT NOT NULL,
    full_date               DATE NOT NULL,
    
    day_of_week             INT,
    day_name                STRING,
    day_of_month            INT,
    day_of_year             INT,
    is_weekend              BOOLEAN,
    
    week_of_year            INT,
    week_start_date         DATE,
    
    month_number            INT,
    month_name              STRING,
    month_start_date        DATE,
    
    quarter                 INT,
    quarter_name            STRING,
    
    year                    INT,
    
    fiscal_year             INT,
    fiscal_quarter          INT,
    
    is_pledge_drive         BOOLEAN DEFAULT FALSE,
    pledge_drive_name       STRING,
    is_holiday              BOOLEAN DEFAULT FALSE,
    holiday_name            STRING,
    
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
)
USING DELTA
COMMENT 'Date dimension for time-based analysis';


-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active Members View (Databricks syntax)
CREATE OR REPLACE VIEW golden.v_active_members AS
SELECT 
    c.*,
    datediff(current_date(), c.last_donation_date) as days_since_last_gift
FROM golden.constituents c
WHERE c.last_donation_date >= add_months(current_date(), -12);


-- Sustainer Dashboard View
CREATE OR REPLACE VIEW golden.v_sustainers AS
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
    months_between(current_date(), c.sustainer_start_date) as sustainer_months
FROM golden.constituents c
WHERE c.is_sustainer = TRUE
  AND c.recurring_status = 'active';


-- High Churn Risk View
CREATE OR REPLACE VIEW golden.v_churn_risk AS
SELECT 
    c.constituent_id,
    c.canonical_email,
    c.canonical_full_name,
    c.lifecycle_stage,
    c.is_sustainer,
    c.recurring_monthly_amount,
    c.churn_risk_score,
    c.churn_risk_tier,
    datediff(current_date(), c.last_engagement_date) as days_since_engagement,
    c.email_open_rate_30d,
    mp.top_features as churn_factors
FROM golden.constituents c
LEFT JOIN golden.model_predictions mp 
    ON c.constituent_id = mp.constituent_id 
    AND mp.model_name = 'churn_prediction'
    AND mp.prediction_date = (
        SELECT max(prediction_date) 
        FROM golden.model_predictions 
        WHERE model_name = 'churn_prediction'
    )
WHERE c.churn_risk_score >= 0.6
ORDER BY c.churn_risk_score DESC;


-- =============================================================================
-- DATABRICKS WORKFLOWS / JOBS
-- =============================================================================

-- Note: In Databricks, scheduled jobs are typically defined in:
-- 1. Databricks Workflows UI
-- 2. Terraform/Pulumi
-- 3. databricks CLI / API
-- 
-- Example job definition (as SQL notebook):

-- %python
-- # This would be in a Databricks notebook
-- """
-- from databricks.sdk import WorkspaceClient
-- from databricks.sdk.service.jobs import Task, NotebookTask
-- 
-- w = WorkspaceClient()
-- 
-- job = w.jobs.create(
--     name="Daily Feature Refresh",
--     tasks=[
--         Task(
--             task_key="refresh_features",
--             notebook_task=NotebookTask(
--                 notebook_path="/Repos/cpm/notebooks/refresh_features"
--             )
--         )
--     ],
--     schedule={
--         "quartz_cron_expression": "0 0 6 * * ?",
--         "timezone_id": "America/Chicago"
--     }
-- )
-- """


-- =============================================================================
-- DELTA LIVE TABLES (DLT) DEFINITIONS
-- =============================================================================

-- Note: DLT pipelines are defined separately. Example structure:

-- CREATE LIVE TABLE staging_donations
-- COMMENT "Cleaned donation data"
-- AS SELECT 
--     *,
--     current_timestamp() as processed_at
-- FROM STREAM(raw.wbez_donations)
-- WHERE donation_amount > 0;

-- CREATE LIVE TABLE golden_constituents
-- COMMENT "Unified constituent records"
-- TBLPROPERTIES ("quality" = "gold")
-- AS SELECT ...


-- =============================================================================
-- GRANTS (Unity Catalog)
-- =============================================================================

-- Grant read access to analysts
GRANT SELECT ON SCHEMA golden TO `analysts`;
GRANT SELECT ON SCHEMA dimensions TO `analysts`;
GRANT SELECT ON SCHEMA mart TO `analysts`;

-- Grant write access to data engineers
GRANT ALL PRIVILEGES ON SCHEMA golden TO `data_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA staging TO `data_engineers`;

-- Grant read access to ML engineers for feature tables
GRANT SELECT ON TABLE golden.constituent_features TO `ml_engineers`;
GRANT SELECT ON TABLE golden.model_predictions TO `ml_engineers`;
GRANT INSERT ON TABLE golden.model_predictions TO `ml_engineers`;