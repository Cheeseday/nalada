-- Median cars per 1000 per country (best-coverage year), tagged with the
-- decoupling verdict. Feeds the ranked per-country bar: national context
-- dominates, and the verdict colours don't separate cleanly (the null).
SELECT
	c.iso_code,
	c.name AS country,
	c.income_group,
	dc.verdict,
	PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cs.cars_per_1000) AS median_cars_per_1000,
	COUNT(DISTINCT ci.id) AS n_cities
FROM
	city_stats cs
JOIN
	cities ci ON ci.id = cs.city_id
JOIN
	countries c ON c.id = ci.country_id
JOIN
	decoupler_class dc ON dc.iso_code = c.iso_code
WHERE
	cs.year = :snap_year
	AND
	cs.cars_per_1000 IS NOT NULL
	AND
	dc.verdict IN ('genuine', 'fake', 'net_exporter')
	AND
	dc.caveat IS NULL
GROUP BY
	c.iso_code,
	c.name,
	c.income_group,
	dc.verdict
ORDER BY
	median_cars_per_1000;