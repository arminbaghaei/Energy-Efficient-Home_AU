"""Tables for display and CSV download."""

from __future__ import annotations


import pandas as pd

from . import assumptions as A
from .actions import ActionResult
from .profile import HouseholdProfile
from .scenarios import Scenario


def action_plan_df(results: list[ActionResult], owner: bool) -> pd.DataFrame:
    rows = []
    for i, r in enumerate(results, start=1):
        a = r.action
        rows.append({
            "Priority": i,
            "When": r.timing,
            "Action": a.title,
            "Check": a.check,
            "Tier": a.tier,
            "Effort": a.effort,
            "Who": "You" if owner or a.renter_friendly else "Landlord / owner",
            "Annual saving ($)": round(r.annual_saving),
            "Electricity saved (kWh/yr)": round(r.elec_kwh_saved),
            "Gas saved (MJ/yr)": round(r.gas_mj_saved),
            "CO2 saved (kg/yr)": round(r.co2_kg_saved),
            "Upfront cost low ($)": round(r.cost_low),
            "Upfront cost high ($)": round(r.cost_high),
            "Simple payback (yrs)": None if r.payback_years is None else round(r.payback_years, 1),
            "Cost basis": a.cost_basis,
            "Why": a.description,
        })
    return pd.DataFrame(rows)


def scenarios_df(scenarios: list[Scenario]) -> pd.DataFrame:
    base = scenarios[0].summary
    rows = []
    for sc in scenarios:
        s = sc.summary
        saving = base.total_cost - s.total_cost
        rows.append({
            "Scenario": sc.name,
            "Actions included": len(sc.actions),
            "Annual bill ($)": round(s.total_cost),
            "Annual saving ($)": round(saving),
            "Saving (%)": round(100 * saving / base.total_cost, 1) if base.total_cost else 0.0,
            "Electricity (kWh/yr)": round(s.elec_kwh),
            "Grid imports (kWh/yr)": round(s.import_kwh),
            "Gas (MJ/yr)": round(s.gas_mj),
            "Emissions (t CO2-e/yr)": round(s.co2_kg / 1000, 2),
            "Upfront cost low ($)": round(sc.cost_low),
            "Upfront cost high ($)": round(sc.cost_high),
            "Simple payback (yrs)": round(sc.cost_mid / saving, 1) if saving > 0 and sc.cost_mid > 0 else None,
            "Action list": "; ".join(a.title for a in sc.actions),
        })
    return pd.DataFrame(rows)


def assumptions_df(p: HouseholdProfile) -> pd.DataFrame:
    """Every number the model used, including the household's own tariff."""
    rows: list[dict] = []

    def add(group: str, item: str, value, unit: str, note: str = "") -> None:
        rows.append({"Group": group, "Item": item, "Value": value, "Unit": unit, "Note": note})

    t = "Tariff in use"
    add(t, "Tariff type", p.tariff_type, "")
    add(t, "Average electricity rate", round(p.elec_rate_c_kwh, 2), "c/kWh", "Flat rate, or TOU rates weighted by your usage split")
    add(t, "Electricity supply charge", p.supply_c_day, "c/day")
    add(t, "Solar feed-in tariff", p.fit_c_kwh, "c/kWh")
    add(t, "Gas usage rate", p.gas_c_mj, "c/MJ")
    add(t, "Gas supply charge", p.gas_supply_c_day, "c/day", "Removed if no gas appliances remain")
    add(t, "Grid emissions factor", p.emissions_kg_kwh, "kg CO2-e/kWh")
    add(t, "Gas emissions factor", A.GAS_EMISSIONS_KG_MJ, "kg CO2-e/MJ")
    add(t, "Solar self-consumption", p.self_consumption, "share of generation", f"Capped at {A.SOLAR_MAX_SHARE_OF_LOAD:.0%} of household use")
    add(t, "Bill calibration (electricity)", round(p.calib_elec, 3), "multiplier")
    add(t, "Bill calibration (gas)", round(p.calib_gas, 3), "multiplier")

    for st, v in A.STATE_TARIFFS.items():
        for k, val in v.items():
            add(f"Default tariffs - {st}", k, val, "c/kWh, c/MJ or c/day", "Indicative 2025-26 standing offers")
    for st, v in A.SOLAR_YIELD_KWH_KW_DAY.items():
        add("Solar yield", st, v, "kWh per kW per day")
    for zone, v in A.CLIMATE_ZONES.items():
        add("Climate zone thermal load", zone, f"heat {v['heat_kwh_m2']}, cool {v['cool_kwh_m2']}", "kWh per m² conditioned per yr")
    for name, table in [
        ("Dwelling factor", A.DWELLING_FACTOR), ("Building age factor", A.AGE_FACTOR),
        ("Share of home conditioned", A.CONDITIONED_SHARE), ("Ceiling insulation factor", A.CEILING_INSULATION_FACTOR),
        ("Wall insulation factor", A.WALL_INSULATION_FACTOR), ("Floor factor", A.FLOOR_INSULATION_FACTOR),
        ("Draught factor", A.DRAUGHT_FACTOR), ("Window covering factor", A.WINDOW_COVERING_FACTOR),
        ("Glazing factor", A.GLAZING_FACTOR), ("Curtain habit factor", A.CURTAIN_HABIT_FACTOR),
        ("Light habit factor", A.LIGHT_HABIT_FACTOR), ("Standby habit factor", A.STANDBY_HABIT_FACTOR),
        ("Fridge use", A.FRIDGE_KWH), ("Dryer use per load", A.DRYER_KWH_PER_LOAD), ("Pool pump power", A.POOL_PUMP_KW),
        ("Shower flow", A.SHOWER_FLOW_LPM),
    ]:
        for k, v in table.items():
            add(name, k, v, "")
    for k, (fuel, eff) in A.HEATING_SYSTEMS.items():
        add("Heating efficiency", k, eff, f"{fuel}: heat delivered / energy in")
    for k, (fuel, eff) in A.COOLING_SYSTEMS.items():
        add("Cooling efficiency", k, eff, f"{fuel}: cooling delivered / energy in")
    for k, (fuel, eff) in A.HOT_WATER_SYSTEMS.items():
        add("Hot water efficiency", k, round(eff, 2), f"{fuel}", "Solar systems include a 60% solar fraction")
    for k, (fuel, amount) in A.COOKING.items():
        add("Cooking (2 people)", k, amount, "kWh/yr" if fuel == "elec" else "MJ/yr")
    g = "Other constants"
    add(g, "Thermostat effect", A.THERMOSTAT_PER_DEGREE, "per °C", "vs 20 °C heating / 25 °C cooling")
    add(g, "LED globe", A.LED_WATTS, "W")
    add(g, "Non-LED globe (mix)", A.NON_LED_WATTS, "W")
    add(g, "Lighting hours", A.LIGHT_HOURS_PER_DAY, "h/day per light")
    add(g, "Standby per device", A.STANDBY_WATTS_PER_DEVICE, "W")
    add(g, "Second fridge", A.SECOND_FRIDGE_KWH, "kWh/yr")
    add(g, "Other hot water", A.OTHER_HOT_WATER_L_PERSON_DAY, "L/person/day")
    add(g, "Hot share of shower water", A.HOT_SHARE_OF_SHOWER, "")
    add(g, "Water heating energy", A.WATER_HEAT_KWH_PER_L, "kWh/L", "45 °C temperature rise")
    add(g, "Other appliances", f"{A.OTHER_APPLIANCES_BASE_KWH:.0f} + {A.OTHER_APPLIANCES_PER_PERSON_KWH:.0f} x people", "kWh/yr")
    for k, (lo, hi) in A.COSTS.items():
        add("Upgrade costs", k.replace("_", " "), f"{lo}-{hi}", "AUD", "Indicative installed prices before state rebates")
    return pd.DataFrame(rows)


def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")  # BOM so Excel opens it cleanly
