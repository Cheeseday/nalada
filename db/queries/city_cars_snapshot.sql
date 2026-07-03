-- One row per city (best-coverage year) with cars, population and the decoupling
-- verdict of its country. Feeds the group box plot, size-band bars and the
-- cars-vs-population scatter. Universe = focus groups only (caveated were excluded),
-- so it reproduces NB10's snapshot exactly.
SELECT
	ci.city_code,
	c.name AS country,
	c.iso_code,
	c.income_group,
	ci.population,
	cs.cars_per_1000,
	dc.verdict
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
ORDER BY
	c.iso_code;