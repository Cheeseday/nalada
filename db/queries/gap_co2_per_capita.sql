SELECT
	c.name AS country,
	RANK() OVER (
        ORDER by (e.co2_per_capita - e.consumption_co2_per_capita ) DESC
    ) AS rank,
	ROUND((e.consumption_co2_per_capita  - e.co2_per_capita)::NUMERIC, 2
    ) AS gap_per_capita,
	ROUND(e.co2_per_capita::NUMERIC, 2
    ) AS co2_per_capita,
	ROUND(e.consumption_co2_per_capita ::NUMERIC, 2
    ) AS consumption_co2_per_capita
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
	e.year = 2023;