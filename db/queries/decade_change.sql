--For each country, the decade-over-decade change in CO₂/capita (1990s→2000s→2010s)
select
	r.country,
	r.year,
   	to_char(round(r.co2_per_capita::numeric, 2), 'FM999990.00') as co2_per_capita,
   	to_char(round(r.prev_co2_per_capita::numeric, 2), 'FM999990.00') as prev_co2_per_capita,
   	to_char(round(r.reduction::numeric, 2), 'FM999990.00') as reduction
from
(
	SELECT
		c.name AS country,
		c.iso_code,
	   	e.co2_per_capita,
	   	e.year,
	   	LAG(e.co2_per_capita, 10) OVER (
	  		PARTITION BY c.name
	  		ORDER BY e.year
		) as prev_co2_per_capita,
		100 - e.co2_per_capita * 100 / LAG(e.co2_per_capita, 10) OVER (PARTITION BY c.name ORDER BY e.year) as reduction
	FROM
		emissions e 
	JOIN 
		countries c ON c.id = e.country_id
	where 
		c.iso_code in (
				'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 
				'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 
				'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 
				'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
		and
		e."year" > 1989
) r
where
	r.year in (2000, 2010, 2020)
order by
	r.country,
	r.year;