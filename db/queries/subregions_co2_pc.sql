-- Rank each country's CO₂/capita within its UN M49 European subregion (cleanest first)
WITH
max_year AS (
	SELECT
		MAX(e2.year) AS year
	FROM
		emissions e2
	JOIN
		countries c ON c.id = e2.country_id
	WHERE
		e2.co2_per_capita IS NOT NULL
		AND
		c.iso_code IN (
			'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
			'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
			'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
			'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
)
SELECT
	RANK() OVER (
		PARTITION BY c.subregion
		ORDER BY e.co2_per_capita
	) AS rank,
	c.name AS country,
	c.subregion,
	e.co2_per_capita
FROM
	emissions e
JOIN
	countries c ON c.id = e.country_id
JOIN
	max_year my ON e.year = my.year
WHERE
	c.iso_code IN (
		'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
		'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
		'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
		'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
	AND
	e.co2_per_capita IS NOT NULL;
