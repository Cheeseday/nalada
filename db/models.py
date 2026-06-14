from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.database import Base


class Country(Base):
    """
    Master table - joining key across all sources.
    iso_code is the universal link between OWID, World Bank, Eurostat.
    """
    __tablename__ = "countries"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(100), nullable=False)
    iso_code     = Column(String(3), unique=True, nullable=False)  # e.g. "POL", "DEU"
    continent    = Column(String(50))
    region       = Column(String(100))  # World Bank broad region, e.g. "Europe & Central Asia"
    subregion    = Column(String(50))   # UN M49 sub-region, e.g. "Northern Europe" (Europe-scoped)
    income_group = Column(String(50))   # World Bank: "High income", "Upper middle income", ...

    emissions    = relationship("Emission", back_populates="country")
    urbanization = relationship("Urbanization", back_populates="country")
    cities       = relationship("City", back_populates="country")


class Emission(Base):
    """
    Core of the decoupling analysis - from OWID CO2 dataset.
    
    Key decoupling columns:
    - co2_per_gdp: territorial emissions intensity (how much CO2 per $ of GDP)
    - consumption_co2: the "honest" number - includes imported emissions
    - consumption_co2_per_capita: consumption-based intensity (decoupling test)
    
    Energy mix columns:
    - coal_co2, gas_co2, oil_co2: breakdown of emission sources
    - renewables_share_energy: transition progress indicator
    """
    __tablename__ = "emissions"

    id                       = Column(Integer, primary_key=True)
    country_id               = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year                     = Column(Integer, nullable=False)

    co2_total                = Column(Float)   # million tonnes
    co2_per_capita           = Column(Float)   # tonnes per person
    co2_per_gdp              = Column(Float)   # kg per $1000 GDP

    consumption_co2          = Column(Float)   # million tonnes
    consumption_co2_per_capita = Column(Float)
    consumption_co2_per_gdp  = Column(Float)

    energy_per_capita        = Column(Float)   # kWh per person
    energy_per_gdp           = Column(Float)   # kWh per $
    coal_co2                 = Column(Float)   # million tonnes from coal
    gas_co2                  = Column(Float)   # million tonnes from gas
    oil_co2                  = Column(Float)   # million tonnes from oil
    renewables_share_energy  = Column(Float)

    methane                  = Column(Float)   # million tonnes CO2-equivalent
    ghg_per_capita           = Column(Float)   # total GHG per person

    trade_co2               = Column(Float)  # net embedded in trade, Mt
    trade_co2_share         = Column(Float)  # % of total emissions

    temperature_change_from_co2  = Column(Float)  # °C
    share_of_temperature_change_from_ghg = Column(Float)  # % of global warming

    co2_per_unit_energy     = Column(Float)  # kg CO2 per kWh

    gdp                      = Column(Float)   # international-$ 2011 prices
    population               = Column(Float)

    source                   = Column(String(50), default="OWID")

    __table_args__ = (
        UniqueConstraint('country_id', 'year', name='uq_emission_country_year'),
    )

    country = relationship("Country", back_populates="emissions")


class Urbanization(Base):
    """
    Urbanization layer - from World Bank API.
    
    Joined to emissions via country.iso_code.
    """
    __tablename__ = "urbanization"

    id                      = Column(Integer, primary_key=True)
    country_id              = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year                    = Column(Integer, nullable=False)

    urban_population_pct    = Column(Float)   # % of population in urban areas
    urban_population_total  = Column(Float)   # absolute number
    urban_growth_rate       = Column(Float)   # annual % change
    population_density      = Column(Float)   # people per km²
    urban_land_area_km2     = Column(Float)   # urban land area (sq. km)
    electricity_access_pct  = Column(Float)   # access to electricity, urban (% of urban population)
    slum_population_pct     = Column(Float)   # population living in slums (% of urban population)
    pm25_exposure           = Column(Float)   # PM2.5 air pollution, mean annual exposure (micrograms per cubic meter)

    source                  = Column(String(50), default="WorldBank")

    __table_args__ = (
        UniqueConstraint('country_id', 'year', name='uq_urban_country_year'),
    )

    country = relationship("Country", back_populates="urbanization")


class City(Base):
    """
    Master city table - from Eurostat Urban Audit (urb_cpop1).
    One row per core city (type 'C'). Joins to countries via country_id.

    City codes like 'DE001C':
      first 2 chars = ISO2 country code
      middle 3 digits = city number
      last char = type: C=core, K=greater city, F=functional urban area
    We store core cities only.
    """
    __tablename__ = "cities"

    id          = Column(Integer, primary_key=True)
    city_code   = Column(String(10), unique=True, nullable=False)  # e.g. "DE001C"
    name        = Column(String(150))                              # e.g. "Berlin"
    country_id  = Column(Integer, ForeignKey("countries.id"), nullable=False)
    population  = Column(Float)   # latest available from urb_cpop1

    country     = relationship("Country", back_populates="cities")
    stats       = relationship("CityStats", back_populates="city")


class CityStats(Base):
    """
    City-level indicators - merged from Eurostat urb_ctran (transport)
    and urb_cenv (environment). One row per city per year.

    Transport indicators (urb_ctran):
    - cars_per_1000:            car dependency = emissions proxy
    - bicycle_network_km:       green transport infrastructure
    - avg_journey_to_work_min:  urban sprawl indicator
    - public_transport_cost_eur: accessibility

    Environment indicators (urb_cenv):
    - green_urban_area_pct:     urban quality / green space
    - municipal_waste_1000t:    consumption proxy
    - wastewater_treatment_pct: infrastructure quality
    - industrial_land_pct:      urban structure / land use
    """
    __tablename__ = "city_stats"

    id          = Column(Integer, primary_key=True)
    city_id     = Column(Integer, ForeignKey("cities.id"), nullable=False)
    year        = Column(Integer, nullable=False)

    # Transport (urb_ctran)
    cars_per_1000               = Column(Float)   # TT1057I
    bicycle_network_km          = Column(Float)   # TT1079V
    avg_journey_to_work_min     = Column(Float)   # TT1019V
    public_transport_cost_eur   = Column(Float)   # TT1080V

    # Environment (urb_cenv)
    green_urban_area_pct        = Column(Float)   # EN5205V
    municipal_waste_1000t       = Column(Float)   # EN4008V
    wastewater_treatment_pct    = Column(Float)   # EN3011V
    industrial_land_pct         = Column(Float)   # EN5202V

    source  = Column(String(50), default="Eurostat")

    __table_args__ = (
        UniqueConstraint('city_id', 'year', name='uq_city_stats_city_year'),
    )

    city = relationship("City", back_populates="stats")
