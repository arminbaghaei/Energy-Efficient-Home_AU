"""Energy Efficient Home_AU (lite) — a one-page home-energy check-up for Australian households."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from energy_advisor import assumptions as A
from energy_advisor import charts, export
from energy_advisor.actions import rank_actions
from energy_advisor.baseline import summarise
from energy_advisor.checks import STATUS_ICON, run_checks
from energy_advisor.inputs import demo_picker, init_state, questionnaire
from energy_advisor.scenarios import SCENARIO_DESCRIPTIONS, standard_scenarios

st.set_page_config(page_title="Energy Efficient Home_AU", page_icon="🏡", layout="wide")
init_state()

st.title("🏡 Energy Efficient Home_AU")
st.markdown("A quick home-energy check-up for Australian households: **seven checks, a personalised action plan "
            "and savings scenarios** in about two minutes.")

demo_picker()
with st.expander("📝 About your home", expanded=True):
    profile = questionnaire()

summary = summarise(profile)
checks = run_checks(profile)
plan = rank_actions(profile)
scenarios = standard_scenarios(profile)
if profile.owner:
    scenarios = [s for s in scenarios if s.name != "Renter-friendly"]
headline = next(s for s in scenarios if s.name == ("Moderate upgrades" if profile.owner else "Renter-friendly"))
saving = summary.total_cost - headline.summary.total_cost

# ---------------------------------------------------------------- headline
st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Estimated energy bill", f"${summary.total_cost:,.0f}/yr")
c2.metric("Energy use", f"{summary.energy_kwh_equiv:,.0f} kWh/yr", help="Electricity plus gas (3.6 MJ = 1 kWh).")
c3.metric("Emissions", f"{summary.co2_kg / 1000:.1f} t CO₂-e/yr")
c4.metric(f"Potential saving ({headline.name.lower()})", f"${saving:,.0f}/yr",
          delta=f"-{saving / summary.total_cost:.0%}" if summary.total_cost else None, delta_color="inverse")

# ---------------------------------------------------------------- checks
st.subheader("Your seven checks")
c1, c2 = st.columns([3, 2])
with c1:
    st.plotly_chart(charts.checks_chart(checks), width="stretch", theme="streamlit")
with c2:
    st.plotly_chart(charts.end_use_chart(profile, summary), width="stretch", theme="streamlit")
for c in checks:
    label = f"{STATUS_ICON[c.status]} **{c.name}** — {c.status}"
    if c.annual_saving >= 1:
        label += f" · save up to ${c.annual_saving:,.0f}/yr"
    with st.expander(label):
        for f in c.findings:
            st.markdown(f"- {f}")

# ---------------------------------------------------------------- action plan
st.subheader("Your action plan")
if not plan:
    st.success("Your home already scores well on everything we check. Nice work!")
else:
    st.caption("Ordered by when to act, then by saving. Each saving assumes the action is done on its own.")
    rows = []
    for r in plan:
        rows.append({
            "When": r.timing,
            "Action": r.action.title + ("" if profile.owner or r.action.renter_friendly else " 🏠"),
            "Saving $/yr": round(r.annual_saving),
            "Cost": "Free" if r.cost_high == 0 else f"${r.cost_low:,.0f}–${r.cost_high:,.0f}",
            "Payback (yrs)": round(r.payback_years, 1) if r.payback_years and r.cost_mid else None,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    if not profile.owner:
        st.caption("🏠 = needs your landlord's agreement.")

# ---------------------------------------------------------------- scenarios
st.subheader("Compare scenarios")
st.plotly_chart(charts.scenario_chart(scenarios), width="stretch", theme="streamlit")
sc_df = export.scenarios_df(scenarios)
st.dataframe(sc_df[["Scenario", "Annual bill ($)", "Annual saving ($)", "Saving (%)", "Emissions (t CO2-e/yr)",
                    "Upfront cost low ($)", "Upfront cost high ($)", "Simple payback (yrs)"]],
             hide_index=True, width="stretch")
st.caption(" · ".join(f"**{s.name}:** {SCENARIO_DESCRIPTIONS[s.name]}" for s in scenarios[1:]))

# ---------------------------------------------------------------- downloads & assumptions
c1, c2 = st.columns(2)
c1.download_button("⬇️ Action plan (CSV)", export.to_csv(export.action_plan_df(plan, profile.owner)),
                   "action_plan.csv", "text/csv", width="stretch")
c2.download_button("⬇️ Scenario comparison (CSV)", export.to_csv(sc_df), "scenarios.csv", "text/csv", width="stretch")

with st.expander("📐 Assumptions and method"):
    st.markdown(
        "- **Heating/cooling** = climate-zone load per m² × area heated × home type, age, insulation, draught and curtain "
        "factors × ~10% per °C of thermostat, ÷ equipment efficiency.\n"
        "- **Hot water** from people, shower minutes and flow rate; **lighting, standby, appliances** from typical wattages.\n"
        "- **Cost** = electricity × your rate + supply charges − solar exports × feed-in + gas × rate + gas supply "
        "(dropped when no gas appliances remain). **Emissions** use your state's grid factor.\n"
        "- **Actions** change your answers and the model is re-run, so scenarios don't double count overlapping savings. "
        "**Payback** = mid-range cost ÷ annual saving (no rebates, inflation or discounting).\n"
        "- Questions not asked in this lite version use typical values: heating the main living areas, a standard "
        "showerhead, a 5-15 year old fridge, 25 lights, 12 standby devices, 2 dryer loads a week, uninsulated-or-unsure walls, single glazing."
    )
    a_df = export.assumptions_df(profile)
    st.dataframe(a_df.astype({"Value": str}), hide_index=True, width="stretch", height=300)
    st.download_button("⬇️ Assumptions (CSV)", export.to_csv(a_df), "assumptions.csv", "text/csv")
    st.markdown("**Sources:** " + " · ".join(f"[{n}]({u})" for n, u in A.SOURCES))

st.caption("Indicative estimates only — not a substitute for a professional home energy assessment. "
           f"Rebates: {A.STATE_REBATE_PROGRAMS[profile.state]}. Compare retail offers at energymadeeasy.gov.au.")
