import pytest

from energy_advisor import assumptions as A
from energy_advisor.actions import ACTIONS, ACTIONS_BY_ID, applicable_actions, evaluate_action, rank_actions
from energy_advisor.baseline import END_USES, calibrate, summarise
from energy_advisor.checks import SEVEN_CHECKS, run_checks
from energy_advisor.demos import DEMO_HOMES
from energy_advisor.export import action_plan_df, assumptions_df, scenarios_df
from energy_advisor.profile import HouseholdProfile
from energy_advisor.scenarios import standard_scenarios

DEFAULT = HouseholdProfile()

VIC_RENTER = HouseholdProfile(
    state="VIC", climate=A.DEFAULT_CLIMATE["VIC"], people=2, dwelling="Apartment / unit", floor_area_m2=70,
    owner=False, heating_system="Electric heaters (fan, oil, panel, radiant)", cooling_system="Fans only",
    ceiling_insulation="Not applicable (apartment below another)", floor_type="Upper-level apartment",
    window_covering="None or thin blinds", n_windows=4, **{k: v for k, v in A.STATE_TARIFFS["VIC"].items()},
)

NSW_GAS_HOUSE = HouseholdProfile(
    heating_system="Gas ducted heating", hot_water="Gas storage tank", cooking="Gas", conditioned_share="Whole home",
    ceiling_insulation="None", draughts="Many noticeable draughts", heat_setpoint=23,
)

QLD_SOLAR = HouseholdProfile(
    state="QLD", climate=A.DEFAULT_CLIMATE["QLD"], pv_kw=6.6, pool_pump="Single-speed pump",
    **{k: v for k, v in A.STATE_TARIFFS["QLD"].items()},
)

PROFILES = [DEFAULT, VIC_RENTER, NSW_GAS_HOUSE, QLD_SOLAR]


@pytest.mark.parametrize("p", PROFILES)
def test_baseline_is_plausible(p):
    s = summarise(p)
    assert set(s.end_uses) == set(END_USES)
    assert all(u.elec_kwh >= 0 and u.gas_mj >= 0 for u in s.end_uses.values())
    assert 1500 < s.elec_kwh + s.gas_mj / 3.6 < 40000
    assert s.total_cost > 0
    assert s.import_kwh <= s.elec_kwh


def test_gas_supply_only_when_gas_used():
    assert summarise(DEFAULT).gas_supply_cost == 0
    assert summarise(NSW_GAS_HOUSE).gas_supply_cost > 0


def test_full_electrification_removes_gas_supply_charge():
    p = NSW_GAS_HOUSE
    for aid in ("hvac_upgrade", "hw_heat_pump", "induction"):
        p = ACTIONS_BY_ID[aid].apply(p)
    s = summarise(p)
    assert s.gas_mj == 0 and s.gas_supply_cost == 0


@pytest.mark.parametrize("p", PROFILES)
def test_actions_save_money_and_never_increase_use(p):
    # Fuel switches can cost slightly more on their own while gas stays connected.
    for a in applicable_actions(p):
        if a.id == "induction":
            continue
        r = evaluate_action(p, a)
        assert r.annual_saving >= -0.01, a.id
        assert r.cost_low <= r.cost_high


def test_applied_action_no_longer_applies():
    for a in ACTIONS:
        for p in PROFILES:
            if a.applies(p):
                assert not a.applies(a.apply(p)), a.id


@pytest.mark.parametrize("p", PROFILES)
def test_scenarios_ordered_and_bounded(p):
    scs = {s.name: s for s in standard_scenarios(p)}
    base = scs["Current home"].summary.total_cost
    quick = scs["Quick wins"].summary.total_cost
    moderate = scs["Moderate upgrades"].summary.total_cost
    deep = scs["Deep retrofit"].summary.total_cost
    assert base >= quick >= moderate >= deep - 0.01
    assert all(s.summary.elec_kwh >= 0 for s in scs.values())


def test_combined_saving_not_more_than_sum_of_parts():
    p = NSW_GAS_HOUSE
    deep = next(s for s in standard_scenarios(p) if s.name == "Deep retrofit")
    combined = summarise(p).total_cost - deep.summary.total_cost
    individual = sum(r.annual_saving for r in rank_actions(p))
    assert combined <= individual + 0.01


def test_renter_scenario_excludes_landlord_actions():
    rf = next(s for s in standard_scenarios(VIC_RENTER) if s.name == "Renter-friendly")
    assert rf.actions and all(a.renter_friendly for a in rf.actions)


def test_seven_checks():
    checks = run_checks(NSW_GAS_HOUSE)
    assert [c.name for c in checks] == SEVEN_CHECKS
    by = {c.name: c for c in checks}
    assert by["Insulation"].status != "Good"
    assert by["Draughts"].status == "Priority"
    assert all(0 <= c.score <= 100 for c in checks)


def test_thermostat_effect():
    warm = summarise(DEFAULT.with_(heat_setpoint=22)).end_uses["Heating"].elec_kwh
    std = summarise(DEFAULT.with_(heat_setpoint=20)).end_uses["Heating"].elec_kwh
    assert warm == pytest.approx(std * 1.2 / 1.0)


def test_calibration_matches_bill():
    target_kwh = 8000
    cal = calibrate(DEFAULT, target_kwh / 4, 91, None, 91)
    s = summarise(DEFAULT.with_(calib_elec=cal.calib_elec))
    assert s.import_kwh == pytest.approx(target_kwh / 4 / 91 * 365, rel=0.01)


def test_calibration_with_solar():
    cal = calibrate(QLD_SOLAR, 1000, 91, None, 91)
    s = summarise(QLD_SOLAR.with_(calib_elec=cal.calib_elec))
    assert s.import_kwh == pytest.approx(1000 / 91 * 365, rel=0.01)


def test_time_of_use_rate():
    p = DEFAULT.with_(tariff_type="Time of use", peak_c_kwh=50, shoulder_c_kwh=30, offpeak_c_kwh=20, peak_share=0.5, shoulder_share=0.3)
    assert p.elec_rate_c_kwh == pytest.approx(0.5 * 50 + 0.3 * 30 + 0.2 * 20)


@pytest.mark.parametrize("p", PROFILES)
def test_exports_build(p):
    assert not action_plan_df(rank_actions(p), p.owner).empty
    assert not scenarios_df(standard_scenarios(p)).empty
    assert not assumptions_df(p).empty


def test_demo_homes_use_valid_options():
    for home in DEMO_HOMES.values():
        assert home["climate"] in A.CLIMATE_ZONES
        assert home["heating_system"] in A.HEATING_SYSTEMS
        assert home["cooling_system"] in A.COOLING_SYSTEMS
        assert home["hot_water"] in A.HOT_WATER_SYSTEMS
        assert home["ceiling_insulation"] in A.CEILING_INSULATION_FACTOR
        assert home["draughts"] in A.DRAUGHT_FACTOR
        assert home["window_covering"] in A.WINDOW_COVERING_FACTOR
        assert home["standby_habit"] in A.STANDBY_HABIT_FACTOR
        assert home["cooking"] in A.COOKING
