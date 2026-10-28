"""Sample households that pre-fill every question, for trying the app quickly."""

from __future__ import annotations

from . import assumptions as A

DEMO_HOMES: dict[str, dict] = {
    "Sydney family house": dict(
        state="NSW", climate=A.DEFAULT_CLIMATE["NSW"], people=4, dwelling="Detached house", floor_area_m2=180, tenure="Own",
        heating_system="Reverse-cycle split system (10+ years)", cooling_system="Reverse-cycle split system (10+ years)",
        heat_setpoint=22, cool_setpoint=23, ceiling_insulation="Thin or old (under R2.5)", draughts="A few draughts",
        window_covering="Curtains or blinds, no pelmets", hot_water="Electric storage tank", shower_minutes=8,
        led_pct=40, standby_habit="Most things left on standby", cooking="Electric (coil / ceramic)", pv_kw=0.0,
    ),
    "Melbourne renter flat": dict(
        state="VIC", climate=A.DEFAULT_CLIMATE["VIC"], people=2, dwelling="Apartment / unit", floor_area_m2=65, tenure="Rent",
        heating_system="Electric heaters (fan, oil, panel, radiant)", cooling_system="Fans only",
        heat_setpoint=21, cool_setpoint=25, ceiling_insulation="Not applicable (apartment below another)",
        draughts="Many noticeable draughts", window_covering="None or thin blinds",
        hot_water="Gas instantaneous / continuous flow", shower_minutes=9, led_pct=20,
        standby_habit="Most things left on standby", cooking="Gas", pv_kw=0.0,
    ),
    "Brisbane solar home": dict(
        state="QLD", climate=A.DEFAULT_CLIMATE["QLD"], people=3, dwelling="Detached house", floor_area_m2=200, tenure="Own",
        heating_system="Ducted reverse-cycle", cooling_system="Ducted reverse-cycle", heat_setpoint=20, cool_setpoint=22,
        ceiling_insulation="Good (R3.5 or more)", draughts="Well sealed", window_covering="Curtains or blinds, no pelmets",
        hot_water="Electric storage tank", shower_minutes=6, led_pct=80, standby_habit="Some things switched off",
        cooking="Induction", pv_kw=6.6,
    ),
    "Canberra gas house": dict(
        state="ACT", climate=A.DEFAULT_CLIMATE["ACT"], people=3, dwelling="Detached house", floor_area_m2=170, tenure="Own",
        heating_system="Gas ducted heating", cooling_system="Portable / window air conditioner", heat_setpoint=22,
        cool_setpoint=24, ceiling_insulation="None", draughts="Many noticeable draughts", window_covering="None or thin blinds",
        hot_water="Gas storage tank", shower_minutes=8, led_pct=30, standby_habit="Most things left on standby",
        cooking="Gas", pv_kw=0.0,
    ),
}
