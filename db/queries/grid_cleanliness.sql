-- CAVEAT: Malta usually ranks #1, but its low intensity is partly an accounting
-- artifact - the Malta-Sicily interconnector books a share of its electricity
-- emissions to Italy, so Malta "imports" the dirty part. Cleanest crown is borrowed.
SELECT
	RANK() OVER (
		ORDER BY e.co2_per_unit_energy
	) AS rank,
	c.name AS country,
	e.year,
	e.co2_per_unit_energy,
	CASE WHEN c.iso_code = 'MLT'
		THEN '* electricity imported via IT interconnector - intensity understated'
	END AS caveat
FROM
	emissions e
JOIN
	countries c ON c.id = e.country_id
WHERE
	e.year = 2023
	AND
	c.iso_code IN (
		'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN',
		'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX',
		'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
		'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
	AND
	e.co2_per_unit_energy IS NOT NULL;
