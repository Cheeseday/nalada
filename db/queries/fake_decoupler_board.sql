-- The "fake decoupler" board: ranking of European countries by trade_co2_share
SELECT
	c.name AS country,
	RANK() OVER (
		ORDER BY e.trade_co2_share DESC
	) AS rank,
	ROUND(e.trade_co2_share::NUMERIC, 2) AS trade_co2_share,
	ROUND(e.co2_total::NUMERIC, 2) AS co2_total
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
	e.trade_co2_share IS NOT NULL
	AND
	e.year = 2023;
