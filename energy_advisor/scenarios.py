"""Compare packages of actions against the current home."""

from __future__ import annotations

from dataclasses import dataclass

from .actions import Action, applicable_actions, apply_actions
from .baseline import Summary, summarise
from .profile import HouseholdProfile

SCENARIO_DESCRIPTIONS = {
    "Current home": "Your home and habits as entered today.",
    "Quick wins": "Free habit changes plus low-cost items (LEDs, draught sealing, showerhead, power boards).",
    "Renter-friendly": "Everything a tenant can do without the landlord: habits, LEDs, removable seals, curtains, showerhead.",
    "Moderate upgrades": "Quick wins plus curtains/pelmets, ceiling and underfloor insulation and appliance swaps.",
    "Deep retrofit": "Everything applicable, including heat pump hot water, reverse-cycle heating, wall insulation, glazing and induction.",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    actions: list[Action]
    summary: Summary
    cost_low: float
    cost_high: float

    @property
    def cost_mid(self) -> float:
        return (self.cost_low + self.cost_high) / 2


def scenario_actions(p: HouseholdProfile, name: str) -> list[Action]:
    available = applicable_actions(p)
    if name == "Quick wins":
        return [a for a in available if a.tier == "Quick win"]
    if name == "Renter-friendly":
        return [a for a in available if a.renter_friendly]
    if name == "Moderate upgrades":
        return [a for a in available if a.tier in ("Quick win", "Moderate")]
    if name == "Deep retrofit":
        return available
    return []


def build_scenario(p: HouseholdProfile, name: str, actions: list[Action], description: str = "") -> Scenario:
    # Costs are priced on the home *before* changes (e.g. LEDs needed today).
    lo = sum(a.cost(p)[0] for a in actions)
    hi = sum(a.cost(p)[1] for a in actions)
    return Scenario(name, description, actions, summarise(apply_actions(p, actions)), lo, hi)


def standard_scenarios(p: HouseholdProfile, custom: list[Action] | None = None) -> list[Scenario]:
    names = list(SCENARIO_DESCRIPTIONS)
    if not p.owner:
        # For renters, show the renter package right after the current home.
        names.remove("Renter-friendly")
        names.insert(1, "Renter-friendly")
    out = [build_scenario(p, n, scenario_actions(p, n), SCENARIO_DESCRIPTIONS[n]) for n in names]
    if custom:
        out.append(build_scenario(p, "Custom", custom, "Your own selection of actions."))
    return out
