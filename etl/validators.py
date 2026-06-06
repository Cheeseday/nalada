from pydantic import BaseModel, field_validator


class EmissionRecord(BaseModel):
    country_iso: str
    year: int
    co2_total: float | None = None
    co2_per_capita: float | None = None
    co2_per_gdp: float | None = None
    consumption_co2: float | None = None
    consumption_co2_per_gdp: float | None = None
    trade_co2: float | None = None
    gdp: float | None = None
    population: float | None = None

    @field_validator('year')
    @classmethod
    def year_must_be_valid(cls, v):
        if v < 1750 or v > 2100:
            raise ValueError(f"Invalid year: {v}")
        return v

    @field_validator('country_iso')
    @classmethod
    def iso_must_be_valid(cls, v):
        if not v or len(v) != 3 or not v.isalpha():
            raise ValueError(f"Invalid ISO code: {v}")
        return v.upper()

    @field_validator('co2_total', 'co2_per_capita', 'co2_per_gdp', 'gdp', 'population')
    @classmethod
    def must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v


class UrbanizationRecord(BaseModel):
    country_iso: str
    year: int
    urban_population_pct: float | None = None
    urban_population_total: float | None = None
    urban_growth_rate: float | None = None
    population_density: float | None = None
    pm25_exposure: float | None = None
    slum_population_pct: float | None = None
    electricity_access_pct: float | None = None

    @field_validator('year')
    @classmethod
    def year_must_be_valid(cls, v):
        if v < 1960 or v > 2100:
            raise ValueError(f"Invalid year: {v}")
        return v

    @field_validator('country_iso')
    @classmethod
    def iso_must_be_valid(cls, v):
        if not v or len(v) != 3 or not v.isalpha():
            raise ValueError(f"Invalid ISO code: {v}")
        return v.upper()

    @field_validator('urban_population_pct', 'slum_population_pct', 'electricity_access_pct')
    @classmethod
    def must_be_percentage(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"Percentage must be in range 0-100, got {v}")
        return v

    @field_validator('population_density', 'pm25_exposure', 'urban_population_total')
    @classmethod
    def must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v
    