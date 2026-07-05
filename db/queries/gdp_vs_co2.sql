-- GDP per capita vs territorial CO₂ per capita, latest shared year per country, by income group (global).
-- NB05 headline: wealth is the strongest single predictor of emissions (r ≈ 0.74) - far stronger
-- than urbanisation or density. This is the "real driver" chart.
WITH latest AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year,
		gdp / NULLIF(population, 0) AS gdp_per_capita,
		co2_per_capita
	FROM
		emissions
	WHERE
		gdp IS NOT NULL
		AND
		population IS NOT NULL
		AND
		co2_per_capita IS NOT NULL
	ORDER BY
		country_id,
		year DESC
)
SELECT
	c.name AS country,
	c.income_group,
	l.year,
	ROUND(l.gdp_per_capita::NUMERIC, 0) AS gdp_per_capita,
	ROUND(l.co2_per_capita::NUMERIC, 2) AS co2_per_capita
FROM
	latest l
JOIN
	countries c ON c.id = l.country_id
WHERE
	c.income_group IS NOT NULL
	AND
	c.income_group <> 'Not classified'
ORDER BY
	c.income_group;
