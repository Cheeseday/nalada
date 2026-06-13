-- GDP index vs CO2 index relative to a base year, per country (Tapio decoupling elasticity).
-- Snapshot = each country's latest year with BOTH gdp and co2_total present
WITH
base AS (
	SELECT
		e.country_id,
		e.gdp AS base_gdp,
		e.co2_total AS base_co2_total
	FROM
		emissions e
	WHERE
		e.year = :base_year
),
latest AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year,
		gdp AS latest_gdp,
		co2_total AS latest_co2_total
	FROM
		emissions
	WHERE
		gdp IS NOT NULL
		AND
		co2_total IS NOT NULL
	ORDER BY
		country_id,
		year DESC
)
SELECT
	c.name AS country,
	l.year AS snapshot_year,
	l.latest_gdp / b.base_gdp * 100 AS gdp_index,
	l.latest_co2_total / b.base_co2_total * 100 AS co2_index,
	(l.latest_co2_total / b.base_co2_total * 100 - 100)
		/ NULLIF(l.latest_gdp / b.base_gdp * 100 - 100, 0) AS elasticity
FROM
	latest l
JOIN
	base b ON b.country_id = l.country_id
JOIN
	countries c ON c.id = l.country_id
WHERE
	c.iso_code IN (
		'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
		'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
		'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
		'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
ORDER BY
	elasticity;
