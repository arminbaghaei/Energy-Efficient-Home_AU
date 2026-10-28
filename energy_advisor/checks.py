"""The seven household energy checks."""

from __future__ import annotations

from dataclasses import dataclass

from . import assumptions as A
from .actions import ACTIONS, apply_actions
from .baseline import summarise
from .profile import HouseholdProfile

SEVEN_CHECKS = [
    "Heating & cooling",
    "Lighting",
    "Curtains & blinds",
    "Draughts",
    "Hot water",
    "Standby power",
    "Insulation",
]

STATUS_GOOD = "Good"
STATUS_IMPROVE = "Could improve"
STATUS_PRIORITY = "Priority"
STATUS_ICON = {STATUS_GOOD: "✅", STATUS_IMPROVE: "⚠️", STATUS_PRIORITY: "🔴"}


@dataclass(frozen=True)
class CheckResult:
    name: str
    score: int
    findings: list[str]
    annual_saving: float
    co2_kg_saved: float
    action_ids: list[str]

    @property
    def status(self) -> str:
        if self.score >= 75:
            return STATUS_GOOD
        if self.score >= 45:
            return STATUS_IMPROVE
        return STATUS_PRIORITY


def _clamp(x: float) -> int:
    return int(max(0, min(100, round(x))))


def _heating_cooling(p: HouseholdProfile) -> tuple[float, list[str]]:
    score, notes = 100.0, []
    if p.heating_system in ("Gas ducted heating", "Gas space heater"):
        score -= 30
        notes.append("Gas heating costs more to run than an efficient reverse-cycle system and keeps you paying a gas supply charge.")
    elif p.heating_system == "Electric heaters (fan, oil, panel, radiant)":
        score -= 35
        notes.append("Plug-in electric heaters are the most expensive way to heat a room — 3-4x the cost of a reverse-cycle system.")
    elif p.heating_system == "Reverse-cycle split system (10+ years)":
        score -= 12
        notes.append("Your reverse-cycle system is over 10 years old; newer models are 25-35% more efficient.")
    elif p.heating_system == "Wood heater":
        notes.append("Wood heating isn't costed here; check your firewood costs and local air-quality rules.")
    if p.cooling_system == "Portable / window air conditioner":
        score -= 15
        notes.append("Portable air conditioners are inefficient and leak hot air through the exhaust hose.")
    over = max(0, p.heat_setpoint - A.RECOMMENDED_HEAT_SETPOINT)
    under = max(0, A.RECOMMENDED_COOL_SETPOINT - p.cool_setpoint)
    if over:
        score -= 8 * over
        notes.append(f"Heating set to {p.heat_setpoint} °C: about {over * 10}% more heating energy than at 20 °C.")
    if under and p.cooling_system != "No cooling":
        score -= 8 * under
        notes.append(f"Cooling set to {p.cool_setpoint} °C: about {under * 10}% more cooling energy than at 25 °C.")
    if p.conditioned_share == "Whole home":
        score -= 10
        notes.append("You heat or cool the whole home — zoning to occupied rooms can cut this substantially.")
    if not notes:
        notes.append("Efficient equipment and sensible thermostat settings. Keep filters clean and service every 1-2 years.")
    return score, notes


def _lighting(p: HouseholdProfile) -> tuple[float, list[str]]:
    habit = {"Usually switched off": 20, "Sometimes left on": 10, "Often left on": 0}[p.light_habit]
    notes = [f"About {p.led_share:.0%} of your {p.n_lights} lights are LED."]
    if p.led_share < 0.95:
        notes.append(f"Replacing the remaining ~{round(p.n_lights * (1 - p.led_share))} globes with LEDs is one of the fastest paybacks available.")
    if habit < 20:
        notes.append("Lights are often left on in empty rooms.")
    return p.led_share * 80 + habit, notes


def _curtains(p: HouseholdProfile) -> tuple[float, list[str]]:
    covering = {"None or thin blinds": 0, "Curtains or blinds, no pelmets": 35, "Heavy close-fitting curtains / cellular blinds with pelmets": 60}[p.window_covering]
    habit = {"Yes, routinely": 40, "Sometimes": 20, "Rarely": 0}[p.curtain_habit]
    notes = []
    if covering < 60:
        notes.append(f"Window coverings: {p.window_covering.lower()}. Heavy curtains with pelmets work like insulation for glass.")
    if habit < 40:
        notes.append("Closing curtains at dusk in winter and before the heat of the day in summer is free and effective.")
    if not notes:
        notes.append("Good window coverings used well. In hot climates, external shading on east/west windows helps further.")
    return covering + habit, notes


def _draughts(p: HouseholdProfile) -> tuple[float, list[str]]:
    score = {"Many noticeable draughts": 25, "A few draughts": 60, "Well sealed": 100}[p.draughts]
    if score == 100:
        return score, ["Your home is reported as well sealed. Keep some ventilation for moisture and gas appliances."]
    return score, [
        "Unsealed gaps can account for up to a quarter of heating and cooling losses.",
        "Check under doors, around window frames, exhaust fans, unused fireplaces and old downlights.",
    ]


def _hot_water(p: HouseholdProfile) -> tuple[float, list[str]]:
    system = {"Heat pump": 60, "Solar, electric boosted": 60, "Solar, gas boosted": 55, "Gas instantaneous / continuous flow": 40,
              "Gas storage tank": 30, "Electric storage tank": 20}[p.hot_water]
    head = 20 if p.showerhead.startswith("Water-efficient") else 0
    length = 20 if p.shower_minutes <= A.EFFICIENT_SHOWER_MINUTES + 0.5 else (10 if p.shower_minutes <= 7 else 0)
    notes = [f"Hot water system: {p.hot_water}."]
    if system <= 30:
        notes.append("Water heating is typically 20-25% of household energy; a heat pump is the most efficient replacement.")
    if not head:
        notes.append("An older showerhead uses ~12 L/min; a 3-star head uses ~7.5 L/min.")
    if length < 20:
        notes.append(f"Average shower length of {p.shower_minutes:g} minutes.")
    return system + head + length, notes


def _standby(p: HouseholdProfile) -> tuple[float, list[str]]:
    score = {"Most things left on standby": 30, "Some things switched off": 65, "Switched off at the wall / smart power boards": 100}[p.standby_habit]
    if p.standby_devices > 20:
        score -= 10
    kwh = p.standby_devices * A.STANDBY_WATTS_PER_DEVICE * 8.76 * A.STANDBY_HABIT_FACTOR[p.standby_habit]
    return score, [f"{p.standby_devices} devices on standby use roughly {kwh:,.0f} kWh a year."]


def _insulation(p: HouseholdProfile) -> tuple[float, list[str]]:
    ceiling = {"None": 0, "Thin or old (under R2.5)": 25, "Unsure": 20, "Good (R3.5 or more)": 50, "Not applicable (apartment below another)": 50}[p.ceiling_insulation]
    wall = {"No": 0, "Unsure": 10, "Yes": 20}[p.wall_insulation]
    floor = 0 if p.floor_type == "Raised floor, not insulated" else 15
    glazing = 15 if p.glazing.startswith("Double") else 5
    notes = []
    if ceiling < 50:
        notes.append(f"Ceiling insulation: {p.ceiling_insulation.lower()}. Ceilings are the biggest source of heat loss and gain — check the R-value in the roof space.")
    if wall < 20 and p.dwelling != "Apartment / unit":
        notes.append("Walls may be uninsulated; best tackled during renovation.")
    if floor == 0:
        notes.append("The raised floor is uninsulated.")
    if glazing < 15:
        notes.append("Single glazing loses heat quickly; heavy curtains are the low-cost fix, secondary glazing the upgrade.")
    if not notes:
        notes.append("Well insulated. Check insulation hasn't been disturbed by trades working in the roof.")
    return ceiling + wall + floor + glazing, notes


_SCORERS = {
    "Heating & cooling": _heating_cooling,
    "Lighting": _lighting,
    "Curtains & blinds": _curtains,
    "Draughts": _draughts,
    "Hot water": _hot_water,
    "Standby power": _standby,
    "Insulation": _insulation,
}


def run_checks(p: HouseholdProfile) -> list[CheckResult]:
    base = summarise(p)
    results = []
    for name in SEVEN_CHECKS:
        score, findings = _SCORERS[name](p)
        actions = [a for a in ACTIONS if a.check == name and a.applies(p)]
        after = summarise(apply_actions(p, actions))
        results.append(
            CheckResult(
                name=name,
                score=_clamp(score),
                findings=findings,
                annual_saving=base.total_cost - after.total_cost,
                co2_kg_saved=base.co2_kg - after.co2_kg,
                action_ids=[a.id for a in actions],
            )
        )
    return results
