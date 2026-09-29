-- Gabarit rendu par scripts/render_bigquery_sql.py ; aucune table n'est créée.
-- Paramètres de requête : @as_of DATE, @release_id STRING.
WITH typed AS (
  SELECT
    v.evenement_id, v.lot_id, v.date_evenement, v.type_evenement,
    v.montant_centimes, v.source_lot, v.release_id,
    SAFE_CAST(v.date_evenement AS DATE) AS event_date,
    SAFE_CAST(v.montant_centimes AS INT64) AS amount_centimes
  FROM `{{PROJECT_ID}}.veloriax_raw.fact_ventes` AS v
), joined AS (
  SELECT
    t.*,
    l.mode_commercialisation, l.programme_id,
    p.region_code
  FROM typed AS t
  LEFT JOIN `{{PROJECT_ID}}.veloriax_raw.dim_lot` AS l
    ON t.lot_id = l.lot_id
  LEFT JOIN `{{PROJECT_ID}}.veloriax_raw.dim_programme` AS p
    ON l.programme_id = p.programme_id
), stats AS (
  SELECT
    COUNT(*) AS source_rows,
    COUNTIF(event_date > @as_of) AS future_rows_excluded,
    COUNTIF(event_date <= @as_of) AS rows_until_as_of,
    COUNTIF(event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of) AS rows_ytd,
    COUNTIF(event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of
      AND type_evenement = 'RESERVATION') AS reservation_count,
    COUNTIF(event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of
      AND type_evenement = 'ANNULATION') AS cancellation_count,
    SUM(IF(event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of
      AND type_evenement = 'RESERVATION', amount_centimes, 0)) AS gross_reservations_centimes,
    SUM(IF(event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of
      AND type_evenement = 'ANNULATION', amount_centimes, 0)) AS cancellations_centimes,
    SUM(IF(event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of,
      amount_centimes, 0)) AS net_centimes,
    COUNT(*) - COUNT(DISTINCT evenement_id) AS duplicate_event_ids,
    COUNTIF(evenement_id IS NULL OR evenement_id = '') AS empty_event_ids,
    COUNTIF(event_date IS NULL) AS invalid_dates,
    COUNTIF(amount_centimes IS NULL) AS invalid_amounts,
    COUNTIF(type_evenement NOT IN ('RESERVATION', 'ANNULATION')
      OR type_evenement IS NULL
      OR (type_evenement = 'RESERVATION' AND amount_centimes <= 0)
      OR (type_evenement = 'ANNULATION' AND amount_centimes >= 0)) AS invalid_signs_or_types,
    COUNTIF(source_lot IS NULL OR event_date IS NULL
      OR source_lot != CONCAT('VENTE_', FORMAT_DATE('%Y%m', event_date))) AS invalid_source_months,
    COUNTIF(release_id IS NULL OR release_id != @release_id) AS foreign_release_rows,
    COUNTIF(mode_commercialisation IS NULL OR mode_commercialisation != 'VENTE'
      OR region_code IS NULL) AS missing_or_invalid_dimensions
  FROM joined
)
SELECT
  s.*,
  ARRAY(
    SELECT AS STRUCT FORMAT_DATE('%Y-%m', event_date) AS month,
      SUM(amount_centimes) AS net_centimes
    FROM joined
    WHERE event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of
    GROUP BY month ORDER BY month
  ) AS by_month,
  ARRAY(
    SELECT AS STRUCT region_code AS region,
      SUM(amount_centimes) AS net_centimes
    FROM joined
    WHERE event_date BETWEEN DATE_TRUNC(@as_of, YEAR) AND @as_of
    GROUP BY region ORDER BY region
  ) AS by_region
FROM stats AS s;
