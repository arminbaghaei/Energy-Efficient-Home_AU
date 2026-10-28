"""Catalogue of energy-saving actions.

Each action is a transformation of the household profile. Savings are measured
by re-running the model on the changed profile, so interactions between actions
(e.g. insulating *then* replacing the heater) are handled without double counting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import assumptions as A
from .baseline import summarise
from .profile import HouseholdProfile

CHECKS = [
    "Heating & cooling",
    "Lighting",
    "Curtains & blinds",
    "Draughts",
    "Hot water",
    "Standby power",
    "Insulation",
    "Other appliances",
]

TIERS = ["Quick win", "Moderate", "Deep retrofit"]


@dataclass(frozen=True)
class Action:
    id: str
    title: str
    check: str
    tier: str
    effort: str
    renter_friendly: bool
    description: str
    applies: Callable[[HouseholdProfile], bool]
    apply: Callable[[HouseholdProfile], HouseholdProfile]
    cost: Callable[[HouseholdProfile], tuple[float, float]]
    cost_basis: str


@dataclass(frozen=True)
class ActionResult:
    action: Action
    annual_saving: float
    elec_kwh_saved: float
    gas_mj_saved: float
    co2_kg_saved: float
    cost_low: float
    cost_high: float

    @property
    def cost_mid(self) -> float:
        return (self.cost_low + self.cost_high) / 2

    @property
    def payback_years(self) -> float | None:
        if self.annual_saving <= 0:
            return None
        return self.cost_mid / self.annual_saving

    @property
    def timing(self) -> str:
        if self.cost_mid <= 300:
            return "Do now"
        if self.payback_years is not None and self.payback_years <= 8:
            return "Plan next"
        return "Consider at replacement / renovation"


def _free(_: HouseholdProfile) -> tuple[float, float]:
    return (0.0, 0.0)


def _fixed(key: str, qty: float = 1.0) -> Callable[[HouseholdProfile], tuple[float, float]]:
    lo, hi = A.COSTS[key]
    return lambda _p: (lo * qty, hi * qty)


def _per(key: str, qty: Callable[[HouseholdProfile], float]) -> Callable[[HouseholdProfile], tuple[float, float]]:
    lo, hi = A.COSTS[key]
    return lambda p: (lo * qty(p), hi * qty(p))


def _ceiling_area(p: HouseholdProfile) -> float:
    return p.floor_area_m2 * (0.6 if p.dwelling == "Townhouse / semi-detached" else 1.0)


def _split_units(p: HouseholdProfile) -> int:
    return {"One or two rooms": 1, "Main living areas": 2, "Whole home": 3}[p.conditioned_share]


def _non_led_lights(p: HouseholdProfile) -> float:
    return round(p.n_lights * (1 - p.led_share))


INEFFICIENT_HEATING = {
    "Gas ducted heating",
    "Gas space heater",
    "Electric heaters (fan, oil, panel, radiant)",
    "Reverse-cycle split system (10+ years)",
}
INEFFICIENT_COOLING = {"Portable / window air conditioner", "Reverse-cycle split system (10+ years)"}
def HEATS_OR_COOLS(p: HouseholdProfile) -> bool:
    return p.heating_system not in ("No heating", "Wood heater") or p.cooling_system != "No cooling"


def _upgrade_hvac(p: HouseholdProfile) -> HouseholdProfile:
    changes = {}
    if p.heating_system in INEFFICIENT_HEATING:
        changes["heating_system"] = A.EFFICIENT_RC
    if p.cooling_system in INEFFICIENT_COOLING:
        changes["cooling_system"] = A.EFFICIENT_RC
    return p.with_(**changes)


ACTIONS: list[Action] = [
    # --- Heating & cooling -------------------------------------------------
    Action(
        "thermostat", "Set heating to 18-20 °C and cooling to 25-27 °C", "Heating & cooling", "Quick win", "Low", True,
        "Each degree of extra heating or cooling adds around 10% to running costs.",
        lambda p: HEATS_OR_COOLS(p) and (p.heat_setpoint > 20 or p.cool_setpoint < 25),
        lambda p: p.with_(heat_setpoint=min(p.heat_setpoint, 20), cool_setpoint=max(p.cool_setpoint, 25)),
        _free, "No cost",
    ),
    Action(
        "zoning", "Heat and cool only the rooms you are using", "Heating & cooling", "Quick win", "Low", True,
        "Close doors to unused rooms and shut ducted zones so you condition about half the home, not all of it.",
        lambda p: HEATS_OR_COOLS(p) and p.conditioned_share == "Whole home",
        lambda p: p.with_(conditioned_share="Main living areas"),
        _free, "No cost",
    ),
    Action(
        "hvac_upgrade", "Replace inefficient heaters / old air conditioners with efficient reverse-cycle split systems",
        "Heating & cooling", "Deep retrofit", "High", False,
        "Modern reverse-cycle air conditioners deliver 3-5 units of heat per unit of electricity, far cheaper than gas or "
        "plug-in electric heaters. Replacing gas heating also helps you disconnect from gas.",
        lambda p: p.heating_system in INEFFICIENT_HEATING or p.cooling_system in INEFFICIENT_COOLING,
        _upgrade_hvac,
        lambda p: (A.COSTS["split_system_each"][0] * _split_units(p), A.COSTS["split_system_each"][1] * _split_units(p)),
        "Installed split systems, 1-3 units depending on area conditioned",
    ),
    # --- Lighting -----------------------------------------------------------
    Action(
        "led", "Switch remaining lights to LED", "Lighting", "Quick win", "Low", True,
        "LEDs use about 75-85% less electricity than halogen or incandescent globes and last much longer.",
        lambda p: p.led_share < 0.95,
        lambda p: p.with_(led_share=1.0),
        _per("led_per_light", _non_led_lights), "Per globe; halogen downlights may need an electrician",
    ),
    Action(
        "light_habit", "Turn lights off in empty rooms", "Lighting", "Quick win", "Low", True,
        "A simple habit; sensors or timers help for outdoor and hallway lights.",
        lambda p: p.light_habit != "Usually switched off",
        lambda p: p.with_(light_habit="Usually switched off"),
        _free, "No cost",
    ),
    # --- Curtains & blinds --------------------------------------------------
    Action(
        "curtain_habit", "Close curtains at dusk in winter and on hot summer days", "Curtains & blinds", "Quick win", "Low", True,
        "Up to 40% of heat can be lost, and up to 87% gained, through windows.",
        lambda p: HEATS_OR_COOLS(p) and p.curtain_habit != "Yes, routinely",
        lambda p: p.with_(curtain_habit="Yes, routinely"),
        _free, "No cost",
    ),
    Action(
        "pelmets", "Add pelmets (or box the tops) above existing curtains", "Curtains & blinds", "Moderate", "Medium", True,
        "Pelmets stop warm air flowing down behind the curtain and out through the glass. Removable options suit renters.",
        lambda p: HEATS_OR_COOLS(p) and p.window_covering == "Curtains or blinds, no pelmets",
        lambda p: p.with_(window_covering="Heavy close-fitting curtains / cellular blinds with pelmets"),
        _per("pelmet_per_window", lambda p: p.n_windows), "Per window",
    ),
    Action(
        "curtains", "Fit heavy, close-fitting curtains or cellular blinds with pelmets", "Curtains & blinds", "Moderate", "Medium", True,
        "Thermal-backed curtains that reach the floor, plus pelmets, act like insulation for windows.",
        lambda p: HEATS_OR_COOLS(p) and p.window_covering == "None or thin blinds",
        lambda p: p.with_(window_covering="Heavy close-fitting curtains / cellular blinds with pelmets"),
        _per("curtains_per_window", lambda p: p.n_windows), "Per window",
    ),
    # --- Draughts -----------------------------------------------------------
    Action(
        "draughts", "Seal draughts around doors, windows, vents and downlights", "Draughts", "Quick win", "Low", True,
        "Door snakes, adhesive weather strips, exhaust fan covers and chimney balloons are cheap and removable.",
        lambda p: p.draughts != "Well sealed",
        lambda p: p.with_(draughts="Well sealed"),
        _fixed("draught_sealing_diy"), "DIY materials",
    ),
    # --- Hot water ----------------------------------------------------------
    Action(
        "showerhead", "Install a water-efficient (3-star) showerhead", "Hot water", "Quick win", "Low", True,
        "Cuts hot water use by about 40% with little change in comfort; keep the old one to refit when you move.",
        lambda p: p.showerhead.startswith("Older"),
        lambda p: p.with_(showerhead="Water-efficient 3-star showerhead (~7.5 L/min)"),
        _fixed("showerhead", 1.5), "One to two showerheads",
    ),
    Action(
        "shorter_showers", f"Keep showers to about {A.EFFICIENT_SHOWER_MINUTES} minutes", "Hot water", "Quick win", "Low", True,
        "A shower timer makes this easy for the whole household.",
        lambda p: p.shower_minutes > A.EFFICIENT_SHOWER_MINUTES + 0.5,
        lambda p: p.with_(shower_minutes=A.EFFICIENT_SHOWER_MINUTES),
        _free, "No cost",
    ),
    Action(
        "hw_heat_pump", "Replace the water heater with a heat pump", "Hot water", "Deep retrofit", "High", False,
        "Heat pumps use around a third of the electricity of a standard electric tank. Federal STCs and many state "
        "programs reduce the upfront price.",
        lambda p: p.hot_water in ("Electric storage tank", "Gas storage tank", "Gas instantaneous / continuous flow"),
        lambda p: p.with_(hot_water="Heat pump"),
        _fixed("heat_pump_hot_water"), "Installed, after federal STC discount",
    ),
    # --- Standby ------------------------------------------------------------
    Action(
        "standby", "Switch off at the wall or use smart power boards", "Standby power", "Quick win", "Low", True,
        "TVs, consoles, set-top boxes, chargers and computers draw power around the clock on standby.",
        lambda p: p.standby_habit != "Switched off at the wall / smart power boards" and p.standby_devices > 0,
        lambda p: p.with_(standby_habit="Switched off at the wall / smart power boards"),
        _fixed("smart_power_board", 2), "Two smart power boards",
    ),
    # --- Insulation ---------------------------------------------------------
    Action(
        "ceiling_insulation", "Install or top up ceiling insulation to R4-R6", "Insulation", "Moderate", "Medium", False,
        "The ceiling is where the most heat is lost in winter and gained in summer. Use a licensed installer and keep "
        "insulation clear of downlights and wiring.",
        lambda p: p.has_ceiling_space and p.ceiling_insulation != "Good (R3.5 or more)",
        lambda p: p.with_(ceiling_insulation="Good (R3.5 or more)"),
        _per("ceiling_insulation_m2", _ceiling_area), "Per m² of ceiling",
    ),
    Action(
        "underfloor_insulation", "Insulate under the raised timber floor", "Insulation", "Moderate", "Medium", False,
        "Bulk insulation or foil-faced boards between joists reduce cold floors in winter.",
        lambda p: p.floor_type == "Raised floor, not insulated",
        lambda p: p.with_(floor_type="Raised floor, insulated"),
        _per("underfloor_insulation_m2", lambda p: p.floor_area_m2), "Per m² of floor",
    ),
    Action(
        "wall_insulation", "Insulate external walls (blow-in or during renovation)", "Insulation", "Deep retrofit", "High", False,
        "Cavity or blow-in wall insulation is most cost-effective when walls are opened up for renovation.",
        lambda p: p.dwelling != "Apartment / unit" and p.wall_insulation != "Yes",
        lambda p: p.with_(wall_insulation="Yes"),
        _per("wall_insulation_m2", lambda p: p.floor_area_m2), "Per m² (wall area taken as floor area)",
    ),
    Action(
        "glazing", "Add secondary glazing or upgrade to double glazing", "Insulation", "Deep retrofit", "High", False,
        "Secondary glazing (an extra pane fitted inside the existing window) is a cheaper retrofit than replacing windows.",
        lambda p: HEATS_OR_COOLS(p) and p.glazing == "Single glazing",
        lambda p: p.with_(glazing="Double glazing (most windows)"),
        _per("secondary_glazing_per_window", lambda p: p.n_windows), "Secondary glazing, per window",
    ),
    # --- Other appliances ---------------------------------------------------
    Action(
        "second_fridge", "Turn off the second fridge when it isn't needed", "Other appliances", "Quick win", "Low", True,
        "Old second fridges in garages are among the most expensive appliances to run.",
        lambda p: p.second_fridge,
        lambda p: p.with_(second_fridge=False),
        _free, "No cost",
    ),
    Action(
        "fridge", "Replace the 15+ year old fridge with an efficient model", "Other appliances", "Moderate", "Medium", True,
        "Look for a high star rating on the Energy Rating label; best done when the old fridge needs replacing.",
        lambda p: p.fridge_age == "Over 15 years",
        lambda p: p.with_(fridge_age="Under 5 years"),
        _fixed("fridge_new"), "New 4+ star fridge",
    ),
    Action(
        "dryer", "Line-dry more, and choose a heat pump dryer next time", "Other appliances", "Moderate", "Medium", True,
        "Heat pump dryers use about half the energy of vented dryers; line drying is free.",
        lambda p: p.dryer_type == "Vented / condenser dryer" and p.dryer_loads_week >= 1,
        lambda p: p.with_(dryer_type="Heat pump dryer"),
        _fixed("heat_pump_dryer"), "Heat pump dryer",
    ),
    Action(
        "pool_pump", "Fit a variable-speed pool pump and reduce run hours", "Other appliances", "Moderate", "Medium", False,
        "Variable-speed pumps use up to 70% less energy than single-speed pumps.",
        lambda p: p.pool_pump == "Single-speed pump",
        lambda p: p.with_(pool_pump="Variable-speed pump"),
        _fixed("variable_speed_pool_pump"), "Installed pump",
    ),
    Action(
        "induction", "Swap the gas cooktop for induction", "Other appliances", "Deep retrofit", "Medium", False,
        "Induction is fast and efficient and improves indoor air quality. On its own the saving is small (or negative); "
        "the payoff comes when it is your last gas appliance and you can drop the gas supply charge.",
        lambda p: p.cooking == "Gas",
        lambda p: p.with_(cooking="Induction"),
        _fixed("induction_cooktop"), "Installed cooktop",
    ),
]

ACTIONS_BY_ID = {a.id: a for a in ACTIONS}


def applicable_actions(p: HouseholdProfile) -> list[Action]:
    return [a for a in ACTIONS if a.applies(p)]


def apply_actions(p: HouseholdProfile, actions: list[Action]) -> HouseholdProfile:
    for a in actions:
        if a.applies(p):
            p = a.apply(p)
    return p


def evaluate_action(p: HouseholdProfile, action: Action) -> ActionResult:
    before = summarise(p)
    after = summarise(action.apply(p))
    lo, hi = action.cost(p)
    return ActionResult(
        action=action,
        annual_saving=before.total_cost - after.total_cost,
        elec_kwh_saved=before.elec_kwh - after.elec_kwh,
        gas_mj_saved=before.gas_mj - after.gas_mj,
        co2_kg_saved=before.co2_kg - after.co2_kg,
        cost_low=lo,
        cost_high=hi,
    )


def rank_actions(p: HouseholdProfile) -> list[ActionResult]:
    """Evaluate each applicable action on its own and order them into a plan."""
    results = [evaluate_action(p, a) for a in applicable_actions(p)]
    timing_order = {"Do now": 0, "Plan next": 1, "Consider at replacement / renovation": 2}
    return sorted(results, key=lambda r: (timing_order[r.timing], -r.annual_saving))
