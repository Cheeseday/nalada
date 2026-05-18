from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from db.database import Base


class Country(Base):
    """
    Master table — joining key across all sources.
    iso_code is the universal link between OWID, World Bank, Eurostat.
    """
    __tablename__ = "countries"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), nullable=False)
    iso_code   = Column(String(3), unique=True, nullable=False)  # e.g. "POL", "DEU"
    continent  = Column(String(50))
    region     = Column(String(100))   # "Western Europe", "Eastern Europe" etc.
    income_group = Column(String(50))  # World Bank: "High income", "Upper middle" etc.

    emissions    = relationship("Emission", back_populates="country")
    urbanization = relationship("Urbanization", back_populates="country")


class Emission(Base):
    """
    Core of the decoupling analysis — from OWID CO2 dataset.
    
    Key decoupling columns:
    - co2_per_gdp: territorial emissions intensity (how much CO2 per $ of GDP)
    - consumption_co2: the "honest" number — includes imported emissions
    - consumption_co2_per_gdp: consumption-based intensity (decoupling test)
    
    Energy mix columns:
    - coal_co2, gas_co2, oil_co2: breakdown of emission sources
    - renewables_share_energy: transition progress indicator
    """
    __tablename__ = "emissions"

    id                       = Column(Integer, primary_key=True)
    country_id               = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year                     = Column(Integer, nullable=False)

    # --- Territorial emissions (what countries report) ---
    co2_total                = Column(Float)   # million tonnes
    co2_per_capita           = Column(Float)   # tonnes per person
    co2_per_gdp              = Column(Float)   # kg per $1000 GDP

    # --- Consumption-based emissions (the honest number) ---
    consumption_co2          = Column(Float)   # million tonnes
    consumption_co2_per_capita = Column(Float)
    consumption_co2_per_gdp  = Column(Float)   # key decoupling metric

    # --- Energy mix (transition story) ---
    energy_per_capita        = Column(Float)   # kWh per person
    energy_per_gdp           = Column(Float)   # kWh per $
    coal_co2                 = Column(Float)   # million tonnes from coal
    gas_co2                  = Column(Float)   # million tonnes from gas
    oil_co2                  = Column(Float)   # million tonnes from oil
    renewables_share_energy  = Column(Float)   # % of energy from renewables

    # --- Greenhouse gases beyond CO2 ---
    methane                  = Column(Float)   # million tonnes CO2-equivalent
    ghg_per_capita           = Column(Float)   # total GHG per person

    # Trade / fake decoupling detector
    trade_co2               = Column(Float)  # net embedded in trade, Mt
    trade_co2_share         = Column(Float)  # % of total emissions

    # Temperature impact
    temperature_change_from_co2  = Column(Float)  # °C
    share_of_temperature_change_from_ghg = Column(Float)  # % of global warming

    # Energy cleanliness
    co2_per_unit_energy     = Column(Float)  # kg CO2 per kWh — how dirty is the grid

    # --- Economic context (from OWID, sourced from Maddison DB) ---
    gdp                      = Column(Float)   # international-$ 2011 prices
    population               = Column(Float)

    source                   = Column(String(50), default="OWID")

    __table_args__ = (
        UniqueConstraint('country_id', 'year', name='uq_emission_country_year'),
    )

    country = relationship("Country", back_populates="emissions")


class Urbanization(Base):
    """
    Urbanization layer — from World Bank API.
    Answers: does urban structure affect decoupling success?
    
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

    source                  = Column(String(50), default="WorldBank")

    __table_args__ = (
        UniqueConstraint('country_id', 'year', name='uq_urban_country_year'),
    )

    country = relationship("Country", back_populates="urbanization")













"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class Country(Base):
    __tablename__ = "countries"

    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), nullable=False)
    iso_code   = Column(String(3), unique=True, nullable=False)
    continent  = Column(String(50))
    region     = Column(String(100))  # "Western Europe", "Eastern Europe", etc.

    # Сувязі (для зваротнага доступу)
    emissions     = relationship("Emission", back_populates="country")
    urbanization  = relationship("Urbanization", back_populates="country")


class Emission(Base):
    __tablename__ = "emissions"

    id              = Column(Integer, primary_key=True)
    country_id      = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year            = Column(Integer, nullable=False)
    co2_total       = Column(Float)   # млн тон
    co2_per_capita  = Column(Float)   # тон/чал
    co2_per_gdp     = Column(Float)   # кг/$1000 ВУП
    source          = Column(String(50), default="OWID")

    country = relationship("Country", back_populates="emissions")


class Urbanization(Base):
    __tablename__ = "urbanization"

    id                    = Column(Integer, primary_key=True)
    country_id            = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year                  = Column(Integer, nullable=False)
    urban_population_pct  = Column(Float)   # % гарадскога насельніцтва
    gdp_per_capita        = Column(Float)   # USD
    population_total      = Column(Float)
    source                = Column(String(50), default="OWID")

    country = relationship("Country", back_populates="urbanization")
"""


