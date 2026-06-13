WITH
base_year AS (
	SELECT
		e.country_id,
		e.gdp AS base_gdp,
		e.co2_total AS base_co2_total
	FROM
		emissions e
	WHERE
		e.year = 2000
)
SELECT
	c."name" AS country,
	e.year,
	e.gdp / b.base_gdp * 100 AS gdp_index,
	e.co2_total / b.base_co2_total * 100 AS co2_index,
	(e.co2_total / b.base_co2_total  * 100 - 100) / (e.gdp / b.base_gdp * 100 - 100) AS elasticity
FROM
	emissions e
JOIN
	base_year b on b.country_id = e.country_id
JOIN
	countries c ON c.id = e.country_id
WHERE
	e.year = 2022
	AND
	c.iso_code IN (
		'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 
		'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 
		'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 
		'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
ORDER BY
	elasticity 