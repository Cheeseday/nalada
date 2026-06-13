-- Global: each country's latest density vs latest CO₂/capita, by income group.
-- NB05 finding: ~no link between density and more emissions globally.
WITH
latest_co2 AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year AS co2_year,
		co2_per_capita
	FROM
		emissions
	WHERE
		co2_per_capita IS NOT NULL
	ORDER BY
		country_id,
		year DESC
),
latest_density AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		year AS density_year,
		population_density
	FROM
		urbanization
	WHERE
		population_density IS NOT NULL
	ORDER BY
		country_id,
		year DESC
)
SELECT
	c.name AS country,
	c.income_group,
	d.population_density,
	e.co2_per_capita,
	e.co2_year,
	d.density_year
FROM
	latest_co2 e
JOIN
	latest_density d ON d.country_id = e.country_id
JOIN
	countries c ON c.id = e.country_id
WHERE
	c.income_group IS NOT NULL
	AND
	c.income_group <> 'Not classified'
ORDER BY
	c.income_group;
