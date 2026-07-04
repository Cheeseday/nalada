-- Canonical genuine / fake / net_exporter verdicts per European country (built in NB04).
SELECT
	iso_code,
	country,
	verdict,
	caveat,
	gdp_index,
	co2_index,
	consumption_co2_index,
	gap,
	trade_co2_share,
	base_year
FROM
	decoupler_class;
