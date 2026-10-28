"""The household profile: everything the user tells us, in one immutable record."""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import assumptions as A


@dataclass(frozen=True)
class HouseholdProfile:
    # Home
    state: str = "NSW"
    climate: str = A.DEFAULT_CLIMATE["NSW"]
    people: int = 3
    dwelling: str = "Detached house"
    floor_area_m2: float = 160.0
    age: str = "1990-2005"
    owner: bool = True
    n_windows: int = 10

    # Heating & cooling
    heating_system: str = "Reverse-cycle split system (10+ years)"
    cooling_system: str = "Reverse-cycle split system (10+ years)"
    conditioned_share: str = "Main living areas"
    heat_setpoint: int = 21
    cool_setpoint: int = 24

    # Building fabric
    ceiling_insulation: str = "Unsure"
    wall_insulation: str = "Unsure"
    floor_type: str = "Concrete slab"
    glazing: str = "Single glazing"
    draughts: str = "A few draughts"
    window_covering: str = "Curtains or blinds, no pelmets"
    curtain_habit: str = "Sometimes"

    # Hot water
    hot_water: str = "Electric storage tank"
    showerhead: str = "Older / standard showerhead (~12 L/min)"
    shower_minutes: float = 7.0

    # Lighting & standby
    n_lights: int = 25
    led_share: float = 0.5
    light_habit: str = "Sometimes left on"
    standby_devices: int = 12
    standby_habit: str = "Most things left on standby"

    # Other appliances
    fridge_age: str = "5-15 years"
    second_fridge: bool = False
    dryer_type: str = "Vented / condenser dryer"
    dryer_loads_week: float = 2.0
    pool_pump: str = "No pool"
    pool_hours: float = 6.0
    cooking: str = "Electric (coil / ceramic)"

    # Solar
    pv_kw: float = 0.0
    battery: bool = False

    # Tariff
    tariff_type: str = "Flat rate"
    elec_c_kwh: float = A.STATE_TARIFFS["NSW"]["elec_c_kwh"]
    peak_c_kwh: float = A.STATE_TARIFFS["NSW"]["peak_c_kwh"]
    shoulder_c_kwh: float = A.STATE_TARIFFS["NSW"]["shoulder_c_kwh"]
    offpeak_c_kwh: float = A.STATE_TARIFFS["NSW"]["offpeak_c_kwh"]
    peak_share: float = 0.35
    shoulder_share: float = 0.35
    supply_c_day: float = A.STATE_TARIFFS["NSW"]["supply_c_day"]
    fit_c_kwh: float = A.STATE_TARIFFS["NSW"]["fit_c_kwh"]
    gas_c_mj: float = A.STATE_TARIFFS["NSW"]["gas_c_mj"]
    gas_supply_c_day: float = A.STATE_TARIFFS["NSW"]["gas_supply_c_day"]
    emissions_kg_kwh: float = A.GRID_EMISSIONS_KG_KWH["NSW"]
    self_consumption: float = A.SOLAR_SELF_CONSUMPTION["no_battery"]

    # Bill calibration (multipliers applied to modelled usage)
    calib_elec: float = 1.0
    calib_gas: float = 1.0

    def with_(self, **changes) -> "HouseholdProfile":
        return replace(self, **changes)

    @property
    def climate_short(self) -> str:
        return str(A.CLIMATE_ZONES[self.climate]["short"])

    @property
    def elec_rate_c_kwh(self) -> float:
        """Average import rate across the usage profile (flat or time-of-use)."""
        if self.tariff_type == "Flat rate":
            return self.elec_c_kwh
        offpeak_share = max(0.0, 1.0 - self.peak_share - self.shoulder_share)
        return (
            self.peak_share * self.peak_c_kwh
            + self.shoulder_share * self.shoulder_c_kwh
            + offpeak_share * self.offpeak_c_kwh
        )

    @property
    def has_ceiling_space(self) -> bool:
        return self.ceiling_insulation != "Not applicable (apartment below another)"
