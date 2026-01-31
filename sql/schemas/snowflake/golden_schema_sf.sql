-- =============================================================================
-- CPM ENTERPRISE DATA PLATFORM - SCHEMA DEFINITIONS
-- Snowflake SQL
-- =============================================================================
-- 
-- Snowflake-specific implementation with:
-- - VARIANT types for semi-structured data
-- - Clustering keys for performance
-- - Time travel and fail-safe considerations
-- - Snowflake-specific functions and syntax
--
-- Version: 1.0.0
-- Author: Catherine Kiriakos
-- =============================================================================

-- Create database and schemas
CREATE DATABASE IF NOT EXISTS CPM_ENTERPRISE;
USE DATABASE CPM_ENTERPRISE;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS STAGING;
CREATE SCHEMA IF NOT EXISTS GOLDEN;
CREATE SCHEMA IF NOT EXISTS MART;
CREATE SCHEMA IF NOT EXISTS DIMENSIONS;

USE SCHEMA GOLDEN;

-- =============================================================================
-- GOLDEN LAYER - Core Tables
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Unified Constituent (Golden Record)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.CONSTITUENTS (
    -- Primary identifier
    CONSTITUENT_ID          VARCHAR(36) NOT NULL PRIMARY KEY,
    
    -- Canonical contact information
    CANONICAL_EMAIL         VARCHAR(255),
    CANONICAL_FIRST_NAME    VARCHAR(100),
    CANONICAL_LAST_NAME     VARCHAR(100),
    CANONICAL_FULL_NAME     VARCHAR(200),
    CANONICAL_PHONE         VARCHAR(20),
    CANONICAL_ADDRESS_LINE1 VARCHAR(255),
    CANONICAL_ADDRESS_LINE2 VARCHAR(255),
    CANONICAL_CITY          VARCHAR(100),
    CANONICAL_STATE         VARCHAR(50),
    CANONICAL_ZIP           VARCHAR(20),
    CANONICAL_COUNTRY       VARCHAR(50) DEFAULT 'USA',
    
    -- Lifecycle classification
    LIFECYCLE_STAGE         VARCHAR(50) NOT NULL DEFAULT 'prospect',
    FIRST_ENGAGEMENT_DATE   DATE,
    LAST_ENGAGEMENT_DATE    DATE,
    FIRST_DONATION_DATE     DATE,
    LAST_DONATION_DATE      DATE,
    
    -- Giving summary
    TOTAL_LIFETIME_GIVING   NUMBER(12,2) DEFAULT 0,
    TOTAL_GIFT_COUNT        INTEGER DEFAULT 0,
    LARGEST_SINGLE_GIFT     NUMBER(12,2),
    AVERAGE_GIFT_AMOUNT     NUMBER(10,2),
    
    -- Sustainer status
    IS_SUSTAINER            BOOLEAN DEFAULT FALSE,
    RECURRING_STATUS        VARCHAR(20),
    RECURRING_MONTHLY_AMOUNT NUMBER(10,2),
    RECURRING_FREQUENCY     VARCHAR(20),
    SUSTAINER_START_DATE    DATE,
    LAST_SUCCESSFUL_PAYMENT_DATE DATE,
    CONSECUTIVE_FAILED_PAYMENTS INTEGER DEFAULT 0,
    
    -- Subscription status
    IS_SUBSCRIBER           BOOLEAN DEFAULT FALSE,
    SUBSCRIPTION_TYPE       VARCHAR(50),
    SUBSCRIPTION_STATUS     VARCHAR(20),
    SUBSCRIPTION_START_DATE DATE,
    
    -- ML scores
    CHURN_RISK_SCORE        NUMBER(5,4),
    CHURN_RISK_TIER         VARCHAR(20),
    UPGRADE_PROPENSITY      NUMBER(5,4),
    UPGRADE_PROPENSITY_TIER VARCHAR(20),
    ESTIMATED_CAPACITY      VARCHAR(20),
    LIFETIME_VALUE_ESTIMATE NUMBER(12,2),
    
    -- Email engagement
    EMAIL_OPEN_RATE_30D     NUMBER(5,4),
    EMAIL_CLICK_RATE_30D    NUMBER(5,4),
    LAST_EMAIL_OPEN_DATE    DATE,
    
    -- Source tracking
    PRIMARY_SOURCE          VARCHAR(50),
    ACQUISITION_CHANNEL     VARCHAR(50),
    ACQUISITION_CAMPAIGN    VARCHAR(100),
    ACQUISITION_DATE        DATE,
    
    -- Data quality
    DATA_QUALITY_SCORE      NUMBER(3,2),
    HAS_VALID_EMAIL         BOOLEAN,
    HAS_VALID_PHONE         BOOLEAN,
    HAS_VALID_ADDRESS       BOOLEAN,
    
    -- Metadata
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    VERSION                 INTEGER DEFAULT 1
)
CLUSTER BY (LIFECYCLE_STAGE, LAST_DONATION_DATE)
DATA_RETENTION_TIME_IN_DAYS = 90
COMMENT = 'Unified constituent golden record - single source of truth';

-- Create search optimization for common lookups
ALTER TABLE GOLDEN.CONSTITUENTS ADD SEARCH OPTIMIZATION ON EQUALITY(CANONICAL_EMAIL);


-- -----------------------------------------------------------------------------
-- Source System Links
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.CONSTITUENT_SOURCE_LINKS (
    LINK_ID                 VARCHAR(36) NOT NULL PRIMARY KEY,
    CONSTITUENT_ID          VARCHAR(36) NOT NULL,
    SOURCE_SYSTEM           VARCHAR(50) NOT NULL,
    SOURCE_RECORD_ID        VARCHAR(100) NOT NULL,
    
    MATCH_TYPE              VARCHAR(30) NOT NULL,
    MATCH_CONFIDENCE        NUMBER(5,4),
    MATCH_RULE_VERSION      VARCHAR(20),
    
    MATCHED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_CONSTITUENT FOREIGN KEY (CONSTITUENT_ID) 
        REFERENCES GOLDEN.CONSTITUENTS(CONSTITUENT_ID),
    CONSTRAINT UQ_SOURCE_RECORD UNIQUE (SOURCE_SYSTEM, SOURCE_RECORD_ID)
)
CLUSTER BY (CONSTITUENT_ID)
COMMENT = 'Links unified constituents to source system records';


-- -----------------------------------------------------------------------------
-- Donation Facts
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.DONATION_FACTS (
    DONATION_ID             VARCHAR(36) NOT NULL PRIMARY KEY,
    CONSTITUENT_ID          VARCHAR(36) NOT NULL,
    
    DONATION_DATE           DATE NOT NULL,
    DONATION_TIMESTAMP      TIMESTAMP_NTZ,
    DONATION_AMOUNT         NUMBER(12,2) NOT NULL,
    DONATION_TYPE           VARCHAR(30) NOT NULL,
    DONATION_STATUS         VARCHAR(20) NOT NULL,
    
    PAYMENT_METHOD          VARCHAR(30),
    PAYMENT_PROCESSOR       VARCHAR(50),
    TRANSACTION_ID          VARCHAR(100),
    
    CAMPAIGN_CODE           VARCHAR(50),
    CAMPAIGN_NAME           VARCHAR(255),
    CAMPAIGN_TYPE           VARCHAR(50),
    
    SOURCE_CHANNEL          VARCHAR(50),
    DEVICE_TYPE             VARCHAR(20),
    
    IS_RECURRING            BOOLEAN DEFAULT FALSE,
    RECURRING_SEQUENCE_NUM  INTEGER,
    
    SOURCE_SYSTEM           VARCHAR(50) NOT NULL,
    SOURCE_RECORD_ID        VARCHAR(100),
    
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_DONATION_CONSTITUENT FOREIGN KEY (CONSTITUENT_ID) 
        REFERENCES GOLDEN.CONSTITUENTS(CONSTITUENT_ID)
)
CLUSTER BY (DONATION_DATE, CONSTITUENT_ID)
COMMENT = 'All donation transactions';


-- -----------------------------------------------------------------------------
-- Subscription Facts
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.SUBSCRIPTION_FACTS (
    SUBSCRIPTION_ID         VARCHAR(36) NOT NULL PRIMARY KEY,
    CONSTITUENT_ID          VARCHAR(36) NOT NULL,
    
    SUBSCRIPTION_TYPE       VARCHAR(50) NOT NULL,
    SUBSCRIPTION_NAME       VARCHAR(100),
    MONTHLY_RATE            NUMBER(10,2),
    
    SUBSCRIPTION_STATUS     VARCHAR(20) NOT NULL,
    START_DATE              DATE NOT NULL,
    END_DATE                DATE,
    CANCELLATION_DATE       DATE,
    CANCELLATION_REASON     VARCHAR(100),
    
    PAYMENT_METHOD          VARCHAR(30),
    AUTO_RENEW              BOOLEAN DEFAULT TRUE,
    
    ACQUISITION_SOURCE      VARCHAR(50),
    PROMO_CODE              VARCHAR(50),
    
    SOURCE_SYSTEM           VARCHAR(50) DEFAULT 'suntimes_subs',
    SOURCE_RECORD_ID        VARCHAR(100),
    
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_SUBSCRIPTION_CONSTITUENT FOREIGN KEY (CONSTITUENT_ID) 
        REFERENCES GOLDEN.CONSTITUENTS(CONSTITUENT_ID)
)
COMMENT = 'Sun-Times subscription records';


-- -----------------------------------------------------------------------------
-- Engagement Events
-- Using VARIANT for flexible event attributes
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.ENGAGEMENT_EVENTS (
    EVENT_ID                VARCHAR(36) NOT NULL PRIMARY KEY,
    CONSTITUENT_ID          VARCHAR(36) NOT NULL,
    
    EVENT_TYPE              VARCHAR(50) NOT NULL,
    EVENT_DATE              DATE NOT NULL,
    EVENT_TIMESTAMP         TIMESTAMP_NTZ,
    
    SOURCE_SYSTEM           VARCHAR(50),
    SOURCE_CHANNEL          VARCHAR(50),
    
    -- Snowflake VARIANT for flexible attributes
    EVENT_ATTRIBUTES        VARIANT,
    
    DONATION_AMOUNT         NUMBER(12,2),
    DONATION_TYPE           VARCHAR(30),
    
    EMAIL_CAMPAIGN_ID       VARCHAR(100),
    EMAIL_TYPE              VARCHAR(50),
    
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_ENGAGEMENT_CONSTITUENT FOREIGN KEY (CONSTITUENT_ID) 
        REFERENCES GOLDEN.CONSTITUENTS(CONSTITUENT_ID)
)
CLUSTER BY (EVENT_DATE, EVENT_TYPE)
COMMENT = 'Cross-platform engagement events';


-- -----------------------------------------------------------------------------
-- Constituent Features (for ML)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.CONSTITUENT_FEATURES (
    CONSTITUENT_ID          VARCHAR(36) NOT NULL PRIMARY KEY,
    FEATURE_DATE            DATE NOT NULL,
    
    -- Engagement features
    DAYS_SINCE_LAST_ENGAGEMENT INTEGER,
    DAYS_SINCE_LAST_DONATION INTEGER,
    DAYS_SINCE_LAST_EMAIL_OPEN INTEGER,
    
    -- Email engagement
    EMAIL_OPEN_RATE_30D     NUMBER(5,4),
    EMAIL_OPEN_RATE_90D     NUMBER(5,4),
    EMAIL_CLICK_RATE_30D    NUMBER(5,4),
    EMAILS_RECEIVED_30D     INTEGER,
    EMAILS_OPENED_30D       INTEGER,
    
    -- Giving history
    TENURE_MONTHS           INTEGER,
    TOTAL_GIFTS             INTEGER,
    TOTAL_GIVING            NUMBER(12,2),
    AVG_GIFT_AMOUNT         NUMBER(10,2),
    MAX_GIFT_AMOUNT         NUMBER(10,2),
    MIN_GIFT_AMOUNT         NUMBER(10,2),
    STDDEV_GIFT_AMOUNT      NUMBER(10,2),
    
    -- Giving trends
    GIFTS_LAST_12M          INTEGER,
    GIVING_LAST_12M         NUMBER(12,2),
    GIFTS_PRIOR_12M         INTEGER,
    GIVING_PRIOR_12M        NUMBER(12,2),
    GIFT_AMOUNT_TREND       VARCHAR(20),
    
    -- Sustainer features
    IS_SUSTAINER            BOOLEAN,
    SUSTAINER_MONTHS        INTEGER,
    PAYMENT_FAILURES_12M    INTEGER,
    UPGRADE_COUNT           INTEGER,
    DOWNGRADE_COUNT         INTEGER,
    
    -- RFM
    RECENCY_DAYS            INTEGER,
    FREQUENCY_ANNUAL        NUMBER(5,2),
    MONETARY_AVG            NUMBER(10,2),
    RFM_SCORE               INTEGER,
    
    -- Events
    EVENTS_ATTENDED_12M     INTEGER,
    EVENTS_ATTENDED_ALL     INTEGER,
    
    -- Cross-platform
    NUM_SOURCE_SYSTEMS      INTEGER,
    HAS_WBEZ_DONATION       BOOLEAN,
    HAS_SUNTIMES_SUB        BOOLEAN,
    HAS_EVENT_ATTENDANCE    BOOLEAN,
    
    -- All features as VARIANT for ML pipelines
    FEATURE_VECTOR          VARIANT,
    
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_FEATURES_CONSTITUENT FOREIGN KEY (CONSTITUENT_ID) 
        REFERENCES GOLDEN.CONSTITUENTS(CONSTITUENT_ID)
)
COMMENT = 'Pre-calculated features for ML models';


-- -----------------------------------------------------------------------------
-- Model Predictions
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE GOLDEN.MODEL_PREDICTIONS (
    PREDICTION_ID           VARCHAR(36) NOT NULL PRIMARY KEY,
    CONSTITUENT_ID          VARCHAR(36) NOT NULL,
    MODEL_NAME              VARCHAR(50) NOT NULL,
    MODEL_VERSION           VARCHAR(20) NOT NULL,
    
    PREDICTION_DATE         DATE NOT NULL,
    PREDICTION_SCORE        NUMBER(5,4) NOT NULL,
    PREDICTION_TIER         VARCHAR(20),
    
    -- Feature importance as VARIANT
    TOP_FEATURES            VARIANT,
    
    CREATED_AT              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    CONSTRAINT FK_PREDICTIONS_CONSTITUENT FOREIGN KEY (CONSTITUENT_ID) 
        REFERENCES GOLDEN.CONSTITUENTS(CONSTITUENT_ID)
)
CLUSTER BY (MODEL_NAME, PREDICTION_DATE)
COMMENT = 'ML model predictions';


-- =============================================================================
-- DIMENSION TABLES
-- =============================================================================

CREATE OR REPLACE TABLE DIMENSIONS.DIM_DATE (
    DATE_KEY                INTEGER NOT NULL PRIMARY KEY,
    FULL_DATE               DATE NOT NULL UNIQUE,
    
    DAY_OF_WEEK             INTEGER,
    DAY_NAME                VARCHAR(10),
    DAY_OF_MONTH            INTEGER,
    DAY_OF_YEAR             INTEGER,
    IS_WEEKEND              BOOLEAN,
    
    WEEK_OF_YEAR            INTEGER,
    WEEK_START_DATE         DATE,
    
    MONTH_NUMBER            INTEGER,
    MONTH_NAME              VARCHAR(10),
    MONTH_START_DATE        DATE,
    
    QUARTER                 INTEGER,
    QUARTER_NAME            VARCHAR(10),
    
    YEAR                    INTEGER,
    
    FISCAL_YEAR             INTEGER,
    FISCAL_QUARTER          INTEGER,
    
    IS_PLEDGE_DRIVE         BOOLEAN DEFAULT FALSE,
    PLEDGE_DRIVE_NAME       VARCHAR(50),
    IS_HOLIDAY              BOOLEAN DEFAULT FALSE,
    HOLIDAY_NAME            VARCHAR(50)
)
COMMENT = 'Date dimension for time-based analysis';


-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active Members View (Snowflake syntax)
CREATE OR REPLACE VIEW GOLDEN.V_ACTIVE_MEMBERS AS
SELECT 
    c.*,
    DATEDIFF(day, c.LAST_DONATION_DATE, CURRENT_DATE()) as DAYS_SINCE_LAST_GIFT
FROM GOLDEN.CONSTITUENTS c
WHERE c.LAST_DONATION_DATE >= DATEADD(month, -12, CURRENT_DATE());


-- Sustainer Dashboard View
CREATE OR REPLACE VIEW GOLDEN.V_SUSTAINERS AS
SELECT 
    c.CONSTITUENT_ID,
    c.CANONICAL_EMAIL,
    c.CANONICAL_FIRST_NAME,
    c.CANONICAL_LAST_NAME,
    c.RECURRING_MONTHLY_AMOUNT,
    c.SUSTAINER_START_DATE,
    c.LAST_SUCCESSFUL_PAYMENT_DATE,
    c.CONSECUTIVE_FAILED_PAYMENTS,
    c.CHURN_RISK_SCORE,
    c.CHURN_RISK_TIER,
    DATEDIFF(month, c.SUSTAINER_START_DATE, CURRENT_DATE()) as SUSTAINER_MONTHS
FROM GOLDEN.CONSTITUENTS c
WHERE c.IS_SUSTAINER = TRUE
  AND c.RECURRING_STATUS = 'active';


-- High Churn Risk View
CREATE OR REPLACE VIEW GOLDEN.V_CHURN_RISK AS
SELECT 
    c.CONSTITUENT_ID,
    c.CANONICAL_EMAIL,
    c.CANONICAL_FULL_NAME,
    c.LIFECYCLE_STAGE,
    c.IS_SUSTAINER,
    c.RECURRING_MONTHLY_AMOUNT,
    c.CHURN_RISK_SCORE,
    c.CHURN_RISK_TIER,
    DATEDIFF(day, c.LAST_ENGAGEMENT_DATE, CURRENT_DATE()) as DAYS_SINCE_ENGAGEMENT,
    c.EMAIL_OPEN_RATE_30D,
    mp.TOP_FEATURES as CHURN_FACTORS
FROM GOLDEN.CONSTITUENTS c
LEFT JOIN GOLDEN.MODEL_PREDICTIONS mp 
    ON c.CONSTITUENT_ID = mp.CONSTITUENT_ID 
    AND mp.MODEL_NAME = 'churn_prediction'
    AND mp.PREDICTION_DATE = (
        SELECT MAX(PREDICTION_DATE) 
        FROM GOLDEN.MODEL_PREDICTIONS 
        WHERE MODEL_NAME = 'churn_prediction'
    )
WHERE c.CHURN_RISK_SCORE >= 0.6
ORDER BY c.CHURN_RISK_SCORE DESC;


-- =============================================================================
-- STORED PROCEDURES
-- =============================================================================

-- Procedure to refresh constituent features
CREATE OR REPLACE PROCEDURE GOLDEN.SP_REFRESH_CONSTITUENT_FEATURES()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    -- Delete existing features for today
    DELETE FROM GOLDEN.CONSTITUENT_FEATURES 
    WHERE FEATURE_DATE = CURRENT_DATE();
    
    -- Insert refreshed features
    INSERT INTO GOLDEN.CONSTITUENT_FEATURES (
        CONSTITUENT_ID,
        FEATURE_DATE,
        DAYS_SINCE_LAST_ENGAGEMENT,
        DAYS_SINCE_LAST_DONATION,
        TENURE_MONTHS,
        TOTAL_GIFTS,
        TOTAL_GIVING,
        AVG_GIFT_AMOUNT,
        IS_SUSTAINER,
        CREATED_AT
    )
    SELECT 
        c.CONSTITUENT_ID,
        CURRENT_DATE(),
        DATEDIFF(day, c.LAST_ENGAGEMENT_DATE, CURRENT_DATE()),
        DATEDIFF(day, c.LAST_DONATION_DATE, CURRENT_DATE()),
        DATEDIFF(month, c.FIRST_DONATION_DATE, CURRENT_DATE()),
        c.TOTAL_GIFT_COUNT,
        c.TOTAL_LIFETIME_GIVING,
        c.AVERAGE_GIFT_AMOUNT,
        c.IS_SUSTAINER,
        CURRENT_TIMESTAMP()
    FROM GOLDEN.CONSTITUENTS c
    WHERE c.TOTAL_GIFT_COUNT > 0;
    
    RETURN 'Features refreshed successfully for ' || CURRENT_DATE()::VARCHAR;
END;
$$;


-- =============================================================================
-- TASKS (Scheduled Jobs)
-- =============================================================================

-- Daily feature refresh task
CREATE OR REPLACE TASK GOLDEN.TASK_DAILY_FEATURE_REFRESH
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = 'USING CRON 0 6 * * * America/Chicago'
    COMMENT = 'Daily refresh of constituent features at 6 AM Chicago time'
AS
    CALL GOLDEN.SP_REFRESH_CONSTITUENT_FEATURES();

-- Enable the task
ALTER TASK GOLDEN.TASK_DAILY_FEATURE_REFRESH RESUME;