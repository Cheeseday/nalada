-- Urban % vs PM2.5, latest year per country (European correlation ≈ -0.534)
WITH
latest_urb AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year,
		ROUND(pm25_exposure::NUMERIC, 2) AS pm25_exposure,
		ROUND(urban_population_pct::NUMERIC, 2) AS urban_population_pct
	FROM
		urbanization
	WHERE
		pm25_exposure IS NOT NULL
		AND
		urban_population_pct IS NOT NULL
	ORDER BY
		country_id,
		year DESC
)
SELECT
	c.name AS country,
	u.year,
	u.urban_population_pct,
	u.pm25_exposure,
	c.iso_code IN (
		'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
		'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
		'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
		'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR') AS is_europe
FROM
	latest_urb u
JOIN
	countries c ON c.id = u.country_id;
