-- In what year did each country's emissions peak, and how far below that peak it's now
WITH
max_ems AS (
	SELECT
		country_id,
		year,
		MAX(year) OVER (
			PARTITION BY country_id
		) AS last_year,
		co2_total,
		MAX(co2_total) OVER (
			PARTITION BY country_id
		) AS max_co2_total
	FROM
		emissions
)
SELECT
	c.name AS country,
	m.max_co2_total,
	e.co2_total AS current_co2_total,
	100 - 100 * e.co2_total / m.max_co2_total AS abs_co2_drop,
	m.year AS year_of_peak,
	e.year - m.year AS years_from_peak
FROM
	emissions e
JOIN
	countries c ON c.id = e.country_id
JOIN
	max_ems m ON e.country_id = m.country_id AND e.year = m.last_year
WHERE
	c.iso_code IN (
		'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
		'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
		'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
		'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
	AND
	m.co2_total = m.max_co2_total
ORDER BY
	abs_co2_drop DESC;
