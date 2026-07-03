-- Get TPI scores with all additional information, using base year (1990 or 2000)
SELECT
	*
FROM
	tpi_scores
WHERE
	base_year = :base_year 
ORDER BY 
	final DESC;