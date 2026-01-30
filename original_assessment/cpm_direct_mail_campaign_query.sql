/*
================================================================================
CPM DIRECT MAIL CAMPAIGN QUERY
================================================================================
Purpose:    Generate mailing list with bucket assignments for direct mail campaign

INSTRUCTIONS:
  1. Modify ONLY the campaign_parameters CTE below for each campaign
  2. Do not modify the rest of the query unless business rules change
  3. Test with validation queries at the bottom before sending to mail house
================================================================================
*/

-- ============================================================================
-- CAMPAIGN PARAMETERS - MODIFY THIS SECTION ONLY
-- ============================================================================
WITH campaign_parameters AS (
    SELECT
        -- Date range for recent giving activity
        DATE '2025-07-01' AS recent_gift_start_date,
        DATE '2026-01-26' AS recent_gift_end_date,
        
        -- First-year donor definition (first gift on or after this date)
        DATE '2025-02-01' AS first_year_donor_cutoff,
        
        -- Leadership circle threshold (amount that defines leadership level)
        1200 AS leadership_gift_threshold,
        
        -- Gift summary type to use for first gift date lookup
        'MEMBERSHIP_OVERALL - HOUSEHOLD' AS gift_summary_type
),

-- ============================================================================
-- EXCLUDED FLAGS - Add or remove flags as needed
-- ============================================================================
excluded_flag_list AS (
    SELECT flag_name FROM (VALUES 
        ('Major Donor Prospect'),
        ('Major Donor'),
        ('Deceased'),
        ('No Mail'),
        ('No Renewals')
    ) AS flags(flag_name)
),

-- ============================================================================
-- ELIGIBLE JOURNEY SEGMENTS - Add or remove segments as needed
-- ============================================================================
eligible_journey_segments AS (
    SELECT segment_name FROM (VALUES
        ('Active'),
        ('Dormant'),
        ('Lapsed'),
        ('Late'),
        ('New'),
        ('Renewal')
    ) AS segments(segment_name)
),

-- ============================================================================
-- STEP 1: Identify households to exclude based on flags
-- ============================================================================
excluded_households AS (
    SELECT DISTINCT af.crm_household_id
    FROM crm_account_flag af
    INNER JOIN excluded_flag_list efl 
        ON af.flag_name = efl.flag_name
),

-- ============================================================================
-- STEP 2: Build eligible constituent base with all required fields
-- ============================================================================
eligible_constituents AS (
    SELECT 
        -- Household identification
        af.crm_household_id,
        ac.crm_person_id,
        
        -- Name and address for mailing
        ac.household_address_line,
        af.first_name,
        pa.street,
        pa.address_altline1,
        pa.city,
        pa.state_code,
        pa.country_name,
        pa.postal_code,
        
        -- Membership and journey data for bucket assignment
        m.membership_sub_level_code,
        mj.member_journey_type_name,
        mj.most_recent_one_time_amount,
        mj.most_recent_one_time_date,
        gs.first_gift_date
        
    FROM crm_account_family af
    
    -- Cross join to access parameters
    CROSS JOIN campaign_parameters cp
    
    -- Person details
    INNER JOIN crm_account ac 
        ON af.crm_household_id = ac.crm_household_id
    
    -- Primary mailable address
    INNER JOIN crm_primary_address pa 
        ON ac.crm_person_id = pa.crm_person_id
    
    -- Member journey
    INNER JOIN crm_member_journey mj 
        ON af.crm_household_id = mj.crm_household_id
    
    -- Verify journey segment is eligible
    INNER JOIN eligible_journey_segments ejs
        ON mj.member_journey_segment_name = ejs.segment_name
    
    -- Membership level (optional - may not exist)
    LEFT JOIN crm_membership m 
        ON af.crm_household_id = m.crm_household_id
    
    -- Gift summary for first gift date
    LEFT JOIN crm_gift_summary gs 
        ON af.crm_household_id = gs.crm_household_id
        AND gs.summary_type = cp.gift_summary_type
    
    WHERE 
        -- Household eligibility
        af.family_role_code = 'HEAD_OF_HOUSEHOLD'
        AND af.record_status = 'A'
        AND af.do_not_contact = 'N'
        
        -- Address eligibility
        AND pa.address_status_code = 'MAILABLE'
        AND pa.address_contact_status = 'Y'
        
        -- Exclude Major Donors
        AND (m.membership_sub_level_code IS NULL 
             OR m.membership_sub_level_code <> 'MAJOR_DONOR')
        
        -- Exclude flagged households
        AND NOT EXISTS (
            SELECT 1 
            FROM excluded_households eh 
            WHERE eh.crm_household_id = af.crm_household_id
        )
),

-- ============================================================================
-- STEP 3: Assign DirectMailSubType buckets using parameters
-- ============================================================================
bucketed_constituents AS (
    SELECT 
        ec.crm_household_id,
        ec.crm_person_id,
        ec.household_address_line,
        ec.first_name,
        ec.street,
        ec.address_altline1,
        ec.city,
        ec.state_code,
        ec.country_name,
        ec.postal_code,
        ec.membership_sub_level_code,
        ec.member_journey_type_name,
        ec.most_recent_one_time_amount,
        ec.most_recent_one_time_date,
        
        /*
        ====================================================================
        BUCKET ASSIGNMENT LOGIC
        ====================================================================
        Priority order matters - first matching condition wins.
        All thresholds reference campaign_parameters CTE.
        ====================================================================
        */
        CASE 
            -- ---------------------------------------------------------
            -- PRIORITY 1: Additional gift target - first year of giving
            -- ---------------------------------------------------------
            WHEN ec.member_journey_type_name = 'One-Time'
                 AND ec.most_recent_one_time_date BETWEEN cp.recent_gift_start_date 
                                                      AND cp.recent_gift_end_date
                 AND ec.first_gift_date >= cp.first_year_donor_cutoff
                 AND ec.most_recent_one_time_amount < cp.leadership_gift_threshold
            THEN 'Additional gift target - first year of giving'
            
            -- ---------------------------------------------------------
            -- PRIORITY 2: Current leadership circle member
            -- ---------------------------------------------------------
            WHEN ec.member_journey_type_name = 'One-Time'
                 AND ec.most_recent_one_time_date BETWEEN cp.recent_gift_start_date 
                                                      AND cp.recent_gift_end_date
                 AND ec.most_recent_one_time_amount >= cp.leadership_gift_threshold
            THEN 'Current leadership circle member'
            
            -- ---------------------------------------------------------
            -- NO BUCKET: Does not qualify for this campaign
            -- ---------------------------------------------------------
            ELSE NULL
            
        END AS DirectMailSubType
        
    FROM eligible_constituents ec
    CROSS JOIN campaign_parameters cp
)

-- ============================================================================
-- STEP 4: Final output - only constituents with assigned buckets
-- ============================================================================
SELECT 
    crm_household_id,
    crm_person_id,
    household_address_line,
    first_name,
    street,
    address_altline1,
    city,
    state_code,
    country_name,
    postal_code,
    membership_sub_level_code,
    member_journey_type_name,
    most_recent_one_time_amount,
    most_recent_one_time_date,
    DirectMailSubType

FROM bucketed_constituents

WHERE DirectMailSubType IS NOT NULL

ORDER BY 
    DirectMailSubType,
    postal_code,
    crm_household_id
;