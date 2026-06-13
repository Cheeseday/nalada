-- Top 10 countries by % reduction in CO₂/capita over the last 10 years
SELECT
	r.country,
	r.year,
	ROUND(r.co2_per_capita::NUMERIC, 2) AS co2_per_capita,
	ROUND(r.prev_co2_per_capita::NUMERIC, 2) AS prev_co2_per_capita,
	ROUND(r.reduction::NUMERIC, 2) AS reduction
FROM
	(
		SELECT
			c.name AS country,
			e.co2_per_capita,
			e.year,
			LAG(e.co2_per_capita, 10) OVER (
				PARTITION BY c.name
				ORDER BY e.year
			) AS prev_co2_per_capita,
			100 - e.co2_per_capita * 100 / LAG(e.co2_per_capita, 10) OVER (
				PARTITION BY c.name
				ORDER BY e.year
			) AS reduction
		FROM
			emissions e
		JOIN
			countries c ON c.id = e.country_id
		WHERE
			c.iso_code IN (
				'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
				'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
				'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
				'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
			AND
			e.year > 2000
	) r
WHERE
	r.year = 2024
ORDER BY
	r.reduction DESC
LIMIT 10;
