-- CO₂/capita and urbanisation by World Bank income group (global).
-- NB05 headline: richer groups are both more urban AND higher-emitting - the
-- urbanisation-CO₂ link is mostly a proxy for wealth, not a driver of its own.
WITH
latest_co2 AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		co2_per_capita
	FROM
		emissions
	WHERE
		co2_per_capita IS NOT NULL
	ORDER BY
		country_id,
		year DESC
),
latest_urban AS (
	SELECT DISTINCT ON (country_id)
		country_id,
		urban_population_pct
	FROM
		urbanization
	WHERE
		urban_population_pct IS NOT NULL
	ORDER BY
		country_id,
		year DESC
)
SELECT
	c.income_group,
	COUNT(*) AS countries,
	ROUND(AVG(e.co2_per_capita)::NUMERIC, 2) AS avg_co2_per_capita,
	ROUND(AVG(u.urban_population_pct)::NUMERIC, 1) AS avg_urban_pct
FROM
	latest_co2 e
JOIN
	latest_urban u ON u.country_id = e.country_id
JOIN
	countries c ON c.id = e.country_id
WHERE
	c.income_group IS NOT NULL
	AND
	c.income_group <> 'Not classified'
GROUP BY
	c.income_group
ORDER BY
	avg_co2_per_capita DESC;
