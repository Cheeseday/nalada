WITH 
max_ems as (
	select
		country_id,
		year,
		max(year) over(partition by country_id) as last_year,
		co2_total,
		MAX(co2_total) over (partition by country_id) as max_co2_total
	from 
		emissions	
)
SELECT
	c.name AS country,
   	m.max_co2_total,
   	e.co2_total as current_co2_total,
   	100 - 100 * e.co2_total / m.max_co2_total as abs_co2_drop,
   	m.year as year_of_peak,
   	e.year - m.year as years_from_peak
from emissions e 
JOIN 
	countries c ON c.id = e.country_id
join
	max_ems m on e.country_id = m.country_id and e.year = m.last_year
where 
	c.iso_code in (
			'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 
			'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 
			'MLT', 'NLD', 'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 
			'BLR', 'GEO', 'GBR', 'CHE', 'NOR', 'ALB', 'UKR')
	and
	m.co2_total = m.max_co2_total
order by 
	abs_co2_drop;