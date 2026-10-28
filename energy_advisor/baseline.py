"""Estimate annual energy use by end use, then turn it into bills and emissions."""

from __future__ import annotations

from dataclasses import dataclass

from . import assumptions as A
from .profile import HouseholdProfile

END_USES = [
    "Heating",
    "Cooling",
    "Hot water",
    "Lighting",
    "Standby",
    "Fridges & freezers",
    "Cooking",
    "Clothes drying",
    "Pool pump",
    "Other appliances",
]


@dataclass(frozen=True)
class EndUse:
    elec_kwh: float = 0.0
    gas_mj: float = 0.0


@dataclass(frozen=True)
class Summary:
    end_uses: dict[str, EndUse]
    elec_kwh: float  # total household electricity consumption
    gas_mj: float
    solar_kwh: float
    self_consumed_kwh: float
    import_kwh: float
    export_kwh: float
    elec_usage_cost: float
    elec_supply_cost: float
    feed_in_credit: float
    gas_usage_cost: float
    gas_supply_cost: float
    co2_kg: float

    @property
    def total_cost(self) -> float:
        return (
            self.elec_usage_cost
            + self.elec_supply_cost
            - self.feed_in_credit
            + self.gas_usage_cost
            + self.gas_supply_cost
        )

    @property
    def energy_kwh_equiv(self) -> float:
        """Electricity plus gas expressed in kWh (1 kWh = 3.6 MJ)."""
        return self.elec_kwh + self.gas_mj / 3.6


def envelope_factor(p: HouseholdProfile) -> float:
    return (
        A.CEILING_INSULATION_FACTOR[p.ceiling_insulation]
        * A.WALL_INSULATION_FACTOR[p.wall_insulation]
        * A.FLOOR_INSULATION_FACTOR[p.floor_type]
        * A.DRAUGHT_FACTOR[p.draughts]
        * A.WINDOW_COVERING_FACTOR[p.window_covering]
        * A.GLAZING_FACTOR[p.glazing]
        * A.CURTAIN_HABIT_FACTOR[p.curtain_habit]
    )


def thermal_loads(p: HouseholdProfile) -> tuple[float, float]:
    """Heating and cooling thermal energy (kWh delivered) the home needs per year."""
    zone = A.CLIMATE_ZONES[p.climate]
    area = p.floor_area_m2 * A.CONDITIONED_SHARE[p.conditioned_share]
    fabric = A.DWELLING_FACTOR[p.dwelling] * A.AGE_FACTOR[p.age] * envelope_factor(p)
    heat_setpoint = max(0.5, 1 + A.THERMOSTAT_PER_DEGREE * (p.heat_setpoint - A.RECOMMENDED_HEAT_SETPOINT))
    cool_setpoint = max(0.5, 1 + A.THERMOSTAT_PER_DEGREE * (A.RECOMMENDED_COOL_SETPOINT - p.cool_setpoint))
    heat = float(zone["heat_kwh_m2"]) * area * fabric * heat_setpoint
    cool = float(zone["cool_kwh_m2"]) * area * fabric * cool_setpoint
    return heat, cool


def _supply(fuel: str, delivered_kwh: float, efficiency: float) -> EndUse:
    if fuel == "elec":
        return EndUse(elec_kwh=delivered_kwh / efficiency)
    if fuel == "gas":
        return EndUse(gas_mj=delivered_kwh / efficiency * 3.6)
    return EndUse()


def hot_water_litres_per_day(p: HouseholdProfile) -> float:
    flow = A.SHOWER_FLOW_LPM[p.showerhead]
    shower = p.shower_minutes * flow * A.HOT_SHARE_OF_SHOWER
    return p.people * (shower + A.OTHER_HOT_WATER_L_PERSON_DAY)


def estimate_end_uses(p: HouseholdProfile) -> dict[str, EndUse]:
    heat, cool = thermal_loads(p)
    uses: dict[str, EndUse] = {}

    heat_fuel, heat_eff = A.HEATING_SYSTEMS[p.heating_system]
    cool_fuel, cool_eff = A.COOLING_SYSTEMS[p.cooling_system]
    uses["Heating"] = _supply(heat_fuel, heat, heat_eff)
    uses["Cooling"] = _supply(cool_fuel, cool, cool_eff)

    hw_fuel, hw_eff = A.HOT_WATER_SYSTEMS[p.hot_water]
    hw_delivered = hot_water_litres_per_day(p) * A.WATER_HEAT_KWH_PER_L * 365
    uses["Hot water"] = _supply(hw_fuel, hw_delivered, hw_eff)

    watts = p.led_share * A.LED_WATTS + (1 - p.led_share) * A.NON_LED_WATTS
    lighting = p.n_lights * watts * A.LIGHT_HOURS_PER_DAY * 365 / 1000 * A.LIGHT_HABIT_FACTOR[p.light_habit]
    uses["Lighting"] = EndUse(elec_kwh=lighting)

    standby = p.standby_devices * A.STANDBY_WATTS_PER_DEVICE * 8760 / 1000 * A.STANDBY_HABIT_FACTOR[p.standby_habit]
    uses["Standby"] = EndUse(elec_kwh=standby)

    fridges = A.FRIDGE_KWH[p.fridge_age] + (A.SECOND_FRIDGE_KWH if p.second_fridge else 0.0)
    uses["Fridges & freezers"] = EndUse(elec_kwh=fridges)

    cook_fuel, cook_amount = A.COOKING[p.cooking]
    cook_amount *= max(0.5, 1 + A.COOKING_PER_PERSON_SCALE * (p.people - 2))
    uses["Cooking"] = EndUse(elec_kwh=cook_amount) if cook_fuel == "elec" else EndUse(gas_mj=cook_amount)

    uses["Clothes drying"] = EndUse(elec_kwh=A.DRYER_KWH_PER_LOAD[p.dryer_type] * p.dryer_loads_week * 52)
    uses["Pool pump"] = EndUse(elec_kwh=A.POOL_PUMP_KW[p.pool_pump] * p.pool_hours * 365)
    uses["Other appliances"] = EndUse(
        elec_kwh=A.OTHER_APPLIANCES_BASE_KWH + A.OTHER_APPLIANCES_PER_PERSON_KWH * p.people
    )

    return {
        k: EndUse(elec_kwh=v.elec_kwh * p.calib_elec, gas_mj=v.gas_mj * p.calib_gas)
        for k, v in uses.items()
    }


def solar_generation(p: HouseholdProfile) -> float:
    return p.pv_kw * A.SOLAR_YIELD_KWH_KW_DAY[p.state] * 365


def self_consumed(p: HouseholdProfile, consumption_kwh: float) -> float:
    return min(solar_generation(p) * p.self_consumption, consumption_kwh * A.SOLAR_MAX_SHARE_OF_LOAD)


def summarise(p: HouseholdProfile) -> Summary:
    uses = estimate_end_uses(p)
    elec = sum(u.elec_kwh for u in uses.values())
    gas = sum(u.gas_mj for u in uses.values())
    solar = solar_generation(p)
    used_solar = self_consumed(p, elec)
    imports = elec - used_solar
    exports = solar - used_solar
    return Summary(
        end_uses=uses,
        elec_kwh=elec,
        gas_mj=gas,
        solar_kwh=solar,
        self_consumed_kwh=used_solar,
        import_kwh=imports,
        export_kwh=exports,
        elec_usage_cost=imports * p.elec_rate_c_kwh / 100,
        elec_supply_cost=p.supply_c_day * 365 / 100,
        feed_in_credit=exports * p.fit_c_kwh / 100,
        gas_usage_cost=gas * p.gas_c_mj / 100,
        # The gas daily charge only applies while a gas appliance remains connected.
        gas_supply_cost=p.gas_supply_c_day * 365 / 100 if gas > 0 else 0.0,
        co2_kg=imports * p.emissions_kg_kwh + gas * A.GAS_EMISSIONS_KG_MJ,
    )


def end_use_costs(p: HouseholdProfile, s: Summary) -> dict[str, tuple[float, float]]:
    """Split usage charges across end uses as (electricity $, gas $).

    Electricity is valued at the average rate actually paid per kWh consumed,
    i.e. grid imports at the tariff with self-consumed solar treated as free.
    """
    paid_share = s.import_kwh / s.elec_kwh if s.elec_kwh else 0.0
    rate = p.elec_rate_c_kwh / 100 * paid_share
    return {k: (u.elec_kwh * rate, u.gas_mj * p.gas_c_mj / 100) for k, u in s.end_uses.items()}


@dataclass(frozen=True)
class Calibration:
    calib_elec: float
    calib_gas: float
    notes: list[str]


def calibrate(
    p: HouseholdProfile,
    bill_elec_kwh: float | None,
    bill_elec_days: int,
    bill_gas_mj: float | None,
    bill_gas_days: int,
) -> Calibration:
    """Scale modelled usage so it matches what the household's bills show."""
    base = summarise(p.with_(calib_elec=1.0, calib_gas=1.0))
    lo, hi = A.CALIBRATION_RANGE
    notes: list[str] = []
    calib_elec = calib_gas = 1.0

    if bill_elec_kwh and bill_elec_days and base.elec_kwh > 0:
        annual_import = bill_elec_kwh / bill_elec_days * 365
        # Solve consumption C such that C - min(G*sc, C*max_share) = billed imports.
        gen_used = solar_generation(p) * p.self_consumption
        target = annual_import + gen_used
        if gen_used > target * A.SOLAR_MAX_SHARE_OF_LOAD:
            target = annual_import / (1 - A.SOLAR_MAX_SHARE_OF_LOAD)
        raw = target / base.elec_kwh
        calib_elec = min(hi, max(lo, raw))
        notes.append(
            f"Electricity: your bill implies ~{annual_import:,.0f} kWh/yr from the grid; "
            f"the model estimated {base.import_kwh:,.0f} kWh, so electric end uses were scaled by {calib_elec:.2f}."
        )
        if calib_elec != raw:
            notes.append(f"Electricity scaling was limited to the {lo}-{hi} range (raw factor {raw:.2f}). Check your inputs.")

    if bill_gas_mj and bill_gas_days:
        if base.gas_mj > 0:
            annual_gas = bill_gas_mj / bill_gas_days * 365
            raw = annual_gas / base.gas_mj
            calib_gas = min(hi, max(lo, raw))
            notes.append(
                f"Gas: your bill implies ~{annual_gas:,.0f} MJ/yr; the model estimated {base.gas_mj:,.0f} MJ, "
                f"so gas end uses were scaled by {calib_gas:.2f}."
            )
            if calib_gas != raw:
                notes.append(f"Gas scaling was limited to the {lo}-{hi} range (raw factor {raw:.2f}). Check your inputs.")
        else:
            notes.append("You entered gas usage but no gas appliances. Add your gas appliances so the gas bill can be matched.")

    return Calibration(calib_elec, calib_gas, notes)
