# Nalada - Project Vision

## What is this?
A data analytics platform exploring the relationship between 
urbanization and CO2 emissions across countries and European cities.
Built as a portfolio project demonstrating end-to-end data engineering
and analytics skills.

## Central Question
Does economic growth inevitably mean more emissions - or have some 
countries actually managed to decouple GDP from CO2?

And the deeper twist:
Is European "green growth" real or are countries just exporting 
their emissions to Asia?

## The Story (3 chapters)
1. **Context** - How does urbanization relate to emissions globally?
2. **Decoupling** - Which countries grew economically while reducing CO2?
   Who is real, who is fake (trade_co2 test)?
3. **Transition leaders** - What do the most successful countries 
   have in common?

## Data Sources
- OWID CO2 Data         - emissions, energy, GDP (global, 1750-2024)
- World Bank API        - urbanization %, population density, urban growth
- Eurostat Urban Audit  - city-level detail (Europe, Sprint 3+)

## Key Metrics
- `co2_total` - territorial emissions intensity
- `consumption_co2` - real decoupling metric
- `trade_co2` - fake decoupling detector
- `urban_population_pct` - urbanization level
- `gdp_per_capita` - country wealth index
- `pm25_exposure` - pollution of the urban atmosphere

## Tech Stack
PostgreSQL + SQLAlchemy + Python + Pandas
Flask + Plotly + Folium
PydanticAI + OpenAI API