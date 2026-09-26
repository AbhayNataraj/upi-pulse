-- Pipeline step 3: transform
-- Builds the upi_metrics table from upi_monthly.
-- LAG(x, 1) = value one month earlier, LAG(x, 12) = same month last year.
-- This only works because step 1 checks that no month is missing.

CREATE OR REPLACE TABLE upi_metrics AS
WITH base AS (
    SELECT
        month,
        banks_live,
        volume_mn,
        value_cr,
        LAG(banks_live, 1) OVER (ORDER BY month) AS banks_prev_month,
        LAG(volume_mn, 1)  OVER (ORDER BY month) AS volume_prev_month,
        LAG(value_cr, 1)   OVER (ORDER BY month) AS value_prev_month,
        LAG(volume_mn, 12) OVER (ORDER BY month) AS volume_last_year,
        LAG(value_cr, 12)  OVER (ORDER BY month) AS value_last_year
    FROM upi_monthly
)
SELECT
    month,

    -- Indian financial year runs April to March, e.g. FY2025-26
    CASE
        WHEN MONTH(month) >= 4
            THEN 'FY' || CAST(YEAR(month) AS VARCHAR) || '-' || RIGHT(CAST(YEAR(month) + 1 AS VARCHAR), 2)
        ELSE 'FY' || CAST(YEAR(month) - 1 AS VARCHAR) || '-' || RIGHT(CAST(YEAR(month) AS VARCHAR), 2)
    END AS fiscal_year,

    banks_live,
    banks_live - banks_prev_month AS new_banks,
    volume_mn,
    value_cr,

    -- Average payment size in rupees (1 crore = 1e7, 1 million = 1e6)
    ROUND(value_cr * 1e7 / (volume_mn * 1e6), 0) AS avg_ticket_rs,

    -- Average transactions per day, in millions
    ROUND(volume_mn / DAY(LAST_DAY(month)), 1) AS avg_daily_volume_mn,

    -- Growth vs last month and vs same month last year, in %
    ROUND((volume_mn / volume_prev_month - 1) * 100, 2) AS volume_mom_pct,
    ROUND((value_cr / value_prev_month - 1) * 100, 2)   AS value_mom_pct,
    ROUND((volume_mn / volume_last_year - 1) * 100, 2)  AS volume_yoy_pct,
    ROUND((value_cr / value_last_year - 1) * 100, 2)    AS value_yoy_pct

FROM base
ORDER BY month;