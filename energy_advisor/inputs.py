"""Streamlit widgets for the lite questionnaire, plus demo-home loading.

Widget values live in st.session_state under the keys below, so a demo home or a
change of state can rewrite them before the widgets are drawn.
"""

from __future__ import annotations

import streamlit as st

from . import assumptions as A
from .demos import DEMO_HOMES
from .profile import HouseholdProfile

MY_HOME = "My own home"
D = HouseholdProfile()

DEFAULTS = dict(
    state=D.state, climate=D.climate, people=D.people, dwelling=D.dwelling, floor_area_m2=int(D.floor_area_m2),
    tenure="Own", heating_system=D.heating_system, cooling_system=D.cooling_system, heat_setpoint=D.heat_setpoint,
    cool_setpoint=D.cool_setpoint, ceiling_insulation=D.ceiling_insulation, draughts=D.draughts,
    window_covering=D.window_covering, hot_water=D.hot_water, shower_minutes=int(D.shower_minutes),
    led_pct=int(D.led_share * 100), standby_habit=D.standby_habit, cooking=D.cooking, pv_kw=D.pv_kw,
)


def _state_tariff(state: str) -> dict:
    t = A.STATE_TARIFFS[state]
    return dict(elec_c_kwh=t["elec_c_kwh"], supply_c_day=t["supply_c_day"], gas_c_mj=t["gas_c_mj"])


def init_state() -> None:
    for k, v in {**DEFAULTS, **_state_tariff(DEFAULTS["state"])}.items():
        st.session_state.setdefault(k, v)


def _on_state_change() -> None:
    state = st.session_state["state"]
    st.session_state["climate"] = A.DEFAULT_CLIMATE[state]
    st.session_state.update(_state_tariff(state))


def _on_demo_change() -> None:
    name = st.session_state["demo"]
    values = DEFAULTS if name == MY_HOME else DEMO_HOMES[name]
    st.session_state.update({**values, **_state_tariff(values["state"])})


def demo_picker() -> None:
    st.selectbox(
        "Try a demo home, or answer for your own",
        [MY_HOME, *DEMO_HOMES],
        key="demo",
        on_change=_on_demo_change,
        help="Demo homes pre-fill every answer. You can still change any of them.",
    )


def questionnaire() -> HouseholdProfile:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**🏠 Home**")
        st.selectbox("State or territory", list(A.STATE_NAMES), key="state", on_change=_on_state_change,
                     format_func=lambda s: f"{s} — {A.STATE_NAMES[s]}")
        st.selectbox("Climate", list(A.CLIMATE_ZONES), key="climate")
        st.selectbox("Type of home", list(A.DWELLING_FACTOR), key="dwelling")
        st.number_input("Floor area (m²)", 30, 600, step=10, key="floor_area_m2",
                        help="Rough guide: 1-bed unit ~60 m², 3-bed house ~160 m², 4-bed house ~220 m².")
        st.number_input("People in the household", 1, 12, key="people")
        st.radio("Own or rent?", ["Own", "Rent"], horizontal=True, key="tenure")
    with c2:
        st.markdown("**🌡️ Heating, cooling & insulation**")
        st.selectbox("Main heating", list(A.HEATING_SYSTEMS), key="heating_system")
        st.selectbox("Main cooling", list(A.COOLING_SYSTEMS), key="cooling_system")
        st.slider("Winter thermostat (°C)", 16, 26, key="heat_setpoint")
        st.slider("Summer thermostat (°C)", 18, 28, key="cool_setpoint")
        st.selectbox("Ceiling insulation", list(A.CEILING_INSULATION_FACTOR), key="ceiling_insulation")
        st.selectbox("Draughts on a windy day", list(A.DRAUGHT_FACTOR), key="draughts")
        st.selectbox("Curtains and blinds", list(A.WINDOW_COVERING_FACTOR), key="window_covering")
    with c3:
        st.markdown("**🚿 Water, lights & appliances**")
        st.selectbox("Hot water system", list(A.HOT_WATER_SYSTEMS), key="hot_water")
        st.slider("Average shower (minutes)", 2, 20, key="shower_minutes")
        st.slider("Lights that are LED (%)", 0, 100, step=10, key="led_pct")
        st.selectbox("Standby habits", list(A.STANDBY_HABIT_FACTOR), key="standby_habit")
        st.selectbox("Cooktop", list(A.COOKING), key="cooking")
        st.number_input("Rooftop solar (kW, 0 if none)", 0.0, 30.0, step=0.5, key="pv_kw")

    s = st.session_state
    uses_gas = s.heating_system.startswith("Gas") or "gas" in s.hot_water.lower() or s.cooking == "Gas"
    with st.expander(f"💲 Your tariff — pre-filled with indicative {s.state} rates; edit to match your bill"):
        t1, t2, t3 = st.columns(3)
        t1.number_input("Electricity usage (c/kWh)", 0.0, 150.0, step=0.5, key="elec_c_kwh")
        t2.number_input("Electricity supply (c/day)", 0.0, 400.0, step=1.0, key="supply_c_day")
        t3.number_input("Gas usage (c/MJ)", 0.0, 20.0, step=0.1, key="gas_c_mj", disabled=not uses_gas)

    t = A.STATE_TARIFFS[s.state]
    return HouseholdProfile(
        state=s.state, climate=s.climate, people=int(s.people), dwelling=s.dwelling, floor_area_m2=float(s.floor_area_m2),
        owner=s.tenure == "Own", heating_system=s.heating_system, cooling_system=s.cooling_system,
        heat_setpoint=int(s.heat_setpoint), cool_setpoint=int(s.cool_setpoint),
        ceiling_insulation=s.ceiling_insulation, draughts=s.draughts, window_covering=s.window_covering,
        hot_water=s.hot_water, shower_minutes=float(s.shower_minutes), led_share=s.led_pct / 100,
        standby_habit=s.standby_habit, cooking=s.cooking, pv_kw=float(s.pv_kw),
        elec_c_kwh=float(s.elec_c_kwh), supply_c_day=float(s.supply_c_day), gas_c_mj=float(s.gas_c_mj),
        fit_c_kwh=t["fit_c_kwh"], gas_supply_c_day=t["gas_supply_c_day"],
        emissions_kg_kwh=A.GRID_EMISSIONS_KG_KWH[s.state],
    )
