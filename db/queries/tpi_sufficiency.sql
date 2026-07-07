-- TPI sufficiency: actual vs required annual pace of consumption-CO₂/capita cuts,
-- for the TPI top-12 (2000 base, data-quality '!' flags excluded).
-- Actual pace  = compound annual change 2010 'till the latest year with data.
-- Required pace = geometric rate needed to reach 2 t/capita by 2050.
WITH cons AS (
	SELECT
		e.country_id,
		e.year,
		e.consumption_co2_per_capita AS cons_pc
	FROM
		emissions e
	WHERE
		e.consumption_co2_per_capita IS NOT NULL
),
latest AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year AS latest_year,
		cons_pc AS cons_now
	FROM
		cons
	ORDER BY
		country_id,
		year DESC
),
pace_start AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year AS start_year,
		cons_pc AS cons_start
	FROM
		cons
	WHERE
		year >= 2010
	ORDER BY
		country_id,
		year ASC
),
rates AS (
	SELECT
		l.country_id,
		l.latest_year,
		l.cons_now,
		POWER(l.cons_now / s.cons_start, 1.0 / (l.latest_year - s.start_year)) - 1 AS actual_rate,
		CASE
			WHEN l.cons_now > 2.0
			THEN POWER(2.0 / l.cons_now, 1.0 / (2050 - l.latest_year)) - 1
			ELSE 0.0
		END AS required_rate
	FROM
		latest l
	JOIN
		pace_start s ON s.country_id = l.country_id
	WHERE
		(l.latest_year - s.start_year) >= 4
		AND s.cons_start > 0
		AND l.cons_now > 0
)
SELECT
	t.iso_code,
	t.country,
	t.verdict,
	t.final,
	ROUND(r.cons_now::NUMERIC, 1) AS cons_now_t,
	r.latest_year,
	ROUND((-r.actual_rate * 100)::NUMERIC, 2)   AS actual_cut_pct,
	ROUND((-r.required_rate * 100)::NUMERIC, 2) AS required_cut_pct
FROM
	tpi_scores t
JOIN
	countries c ON c.iso_code = t.iso_code
JOIN
	rates r ON r.country_id = c.id
WHERE
	t.base_year = 2000
	AND COALESCE(t.flag, '') NOT LIKE '%!%'
ORDER BY
	t.final DESC
LIMIT 12;
