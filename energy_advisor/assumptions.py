"""All modelling assumptions in one place.

Every number used by the calculators lives here so it can be shown to users on
the Assumptions tab and adjusted in one spot. Values are *indicative* Australian
figures intended for comparison between options, not for billing accuracy.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tariffs by state / territory (indicative 2025-26 residential, GST inclusive)
# Sources: AER Default Market Offer, Victorian Default Offer, Synergy (WA),
# Aurora (TAS), Jacana/Power and Water (NT) published standing offers, rounded.
# Users should overwrite these with the rates printed on their own bill.
# ---------------------------------------------------------------------------
STATE_TARIFFS: dict[str, dict[str, float]] = {
    "NSW": {"elec_c_kwh": 37.0, "supply_c_day": 110.0, "fit_c_kwh": 5.0, "peak_c_kwh": 55.0, "shoulder_c_kwh": 35.0, "offpeak_c_kwh": 25.0, "gas_c_mj": 4.0, "gas_supply_c_day": 80.0},
    "VIC": {"elec_c_kwh": 30.0, "supply_c_day": 115.0, "fit_c_kwh": 4.0, "peak_c_kwh": 40.0, "shoulder_c_kwh": 30.0, "offpeak_c_kwh": 22.0, "gas_c_mj": 3.6, "gas_supply_c_day": 105.0},
    "QLD": {"elec_c_kwh": 33.0, "supply_c_day": 120.0, "fit_c_kwh": 5.0, "peak_c_kwh": 48.0, "shoulder_c_kwh": 30.0, "offpeak_c_kwh": 22.0, "gas_c_mj": 4.5, "gas_supply_c_day": 75.0},
    "SA": {"elec_c_kwh": 45.0, "supply_c_day": 120.0, "fit_c_kwh": 4.0, "peak_c_kwh": 60.0, "shoulder_c_kwh": 30.0, "offpeak_c_kwh": 32.0, "gas_c_mj": 4.8, "gas_supply_c_day": 85.0},
    "WA": {"elec_c_kwh": 31.0, "supply_c_day": 116.0, "fit_c_kwh": 2.5, "peak_c_kwh": 56.0, "shoulder_c_kwh": 31.0, "offpeak_c_kwh": 15.0, "gas_c_mj": 4.0, "gas_supply_c_day": 60.0},
    "TAS": {"elec_c_kwh": 30.0, "supply_c_day": 120.0, "fit_c_kwh": 9.0, "peak_c_kwh": 38.0, "shoulder_c_kwh": 30.0, "offpeak_c_kwh": 18.0, "gas_c_mj": 5.0, "gas_supply_c_day": 80.0},
    "ACT": {"elec_c_kwh": 30.0, "supply_c_day": 95.0, "fit_c_kwh": 5.0, "peak_c_kwh": 40.0, "shoulder_c_kwh": 30.0, "offpeak_c_kwh": 20.0, "gas_c_mj": 3.7, "gas_supply_c_day": 85.0},
    "NT": {"elec_c_kwh": 30.0, "supply_c_day": 70.0, "fit_c_kwh": 9.0, "peak_c_kwh": 38.0, "shoulder_c_kwh": 30.0, "offpeak_c_kwh": 21.0, "gas_c_mj": 4.5, "gas_supply_c_day": 70.0},
}

STATE_NAMES = {
    "NSW": "New South Wales",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "SA": "South Australia",
    "WA": "Western Australia",
    "TAS": "Tasmania",
    "ACT": "Australian Capital Territory",
    "NT": "Northern Territory",
}

# Grid electricity emissions, kg CO2-e per kWh consumed (scope 2 + 3, indicative,
# National Greenhouse Accounts Factors). ACT draws from the NSW grid.
GRID_EMISSIONS_KG_KWH = {"NSW": 0.73, "VIC": 0.88, "QLD": 0.80, "SA": 0.25, "WA": 0.55, "TAS": 0.20, "ACT": 0.73, "NT": 0.58}

# Natural gas combustion + upstream, kg CO2-e per MJ (~55 kg/GJ).
GAS_EMISSIONS_KG_MJ = 0.055

# Typical rooftop solar yield, kWh per kW of panels per day (annual average).
SOLAR_YIELD_KWH_KW_DAY = {"NSW": 3.9, "VIC": 3.6, "QLD": 4.2, "SA": 4.1, "WA": 4.4, "TAS": 3.3, "ACT": 4.0, "NT": 4.6}

# Share of solar generation used in the home rather than exported.
SOLAR_SELF_CONSUMPTION = {"no_battery": 0.30, "battery": 0.65}
# Self-consumed solar can never exceed this share of household consumption.
SOLAR_MAX_SHARE_OF_LOAD = 0.60

# ---------------------------------------------------------------------------
# Climate zones (simplified from NatHERS / BCA zones)
# heat/cool = thermal energy needed per m2 of conditioned floor area per year
# for an average (~1990s, partly insulated) home at 20 C heating / 25 C cooling.
# ---------------------------------------------------------------------------
CLIMATE_ZONES: dict[str, dict[str, float | str]] = {
    "Hot humid (e.g. Darwin, Cairns, Townsville)": {"heat_kwh_m2": 2.0, "cool_kwh_m2": 65.0, "short": "Hot humid"},
    "Hot dry (e.g. Alice Springs, Kalgoorlie)": {"heat_kwh_m2": 20.0, "cool_kwh_m2": 50.0, "short": "Hot dry"},
    "Warm temperate (e.g. Brisbane, Perth, Sydney west)": {"heat_kwh_m2": 18.0, "cool_kwh_m2": 25.0, "short": "Warm temperate"},
    "Mild temperate (e.g. Sydney, Adelaide)": {"heat_kwh_m2": 35.0, "cool_kwh_m2": 14.0, "short": "Mild temperate"},
    "Cool temperate (e.g. Melbourne, Canberra, Hobart)": {"heat_kwh_m2": 70.0, "cool_kwh_m2": 6.0, "short": "Cool temperate"},
    "Alpine / very cold (e.g. Ballarat, Cooma)": {"heat_kwh_m2": 105.0, "cool_kwh_m2": 2.0, "short": "Alpine"},
}

DEFAULT_CLIMATE = {
    "NSW": "Mild temperate (e.g. Sydney, Adelaide)",
    "VIC": "Cool temperate (e.g. Melbourne, Canberra, Hobart)",
    "QLD": "Warm temperate (e.g. Brisbane, Perth, Sydney west)",
    "SA": "Mild temperate (e.g. Sydney, Adelaide)",
    "WA": "Warm temperate (e.g. Brisbane, Perth, Sydney west)",
    "TAS": "Cool temperate (e.g. Melbourne, Canberra, Hobart)",
    "ACT": "Cool temperate (e.g. Melbourne, Canberra, Hobart)",
    "NT": "Hot humid (e.g. Darwin, Cairns, Townsville)",
}

# ---------------------------------------------------------------------------
# Building fabric multipliers on heating/cooling thermal load
# ---------------------------------------------------------------------------
DWELLING_FACTOR = {"Detached house": 1.00, "Townhouse / semi-detached": 0.85, "Apartment / unit": 0.70}
AGE_FACTOR = {"Before 1990": 1.20, "1990-2005": 1.00, "2006 or later (5-7 star)": 0.75}
CONDITIONED_SHARE = {"One or two rooms": 0.30, "Main living areas": 0.50, "Whole home": 0.90}

CEILING_INSULATION_FACTOR = {"None": 1.30, "Thin or old (under R2.5)": 1.15, "Unsure": 1.15, "Good (R3.5 or more)": 1.00, "Not applicable (apartment below another)": 1.00}
WALL_INSULATION_FACTOR = {"No": 1.10, "Unsure": 1.07, "Yes": 1.00}
FLOOR_INSULATION_FACTOR = {"Concrete slab": 1.00, "Raised floor, not insulated": 1.08, "Raised floor, insulated": 1.00, "Upper-level apartment": 1.00}
DRAUGHT_FACTOR = {"Many noticeable draughts": 1.15, "A few draughts": 1.10, "Well sealed": 1.00}
WINDOW_COVERING_FACTOR = {"None or thin blinds": 1.10, "Curtains or blinds, no pelmets": 1.05, "Heavy close-fitting curtains / cellular blinds with pelmets": 1.00}
GLAZING_FACTOR = {"Single glazing": 1.00, "Double glazing (most windows)": 0.90}
CURTAIN_HABIT_FACTOR = {"Yes, routinely": 1.00, "Sometimes": 1.04, "Rarely": 1.08}

# Each degree warmer (heating) or cooler (cooling) than the recommended set point
# adds roughly 10% to running costs (energy.gov.au / YourHome guidance).
THERMOSTAT_PER_DEGREE = 0.10
RECOMMENDED_HEAT_SETPOINT = 20
RECOMMENDED_COOL_SETPOINT = 25

# ---------------------------------------------------------------------------
# Heating and cooling equipment: (fuel, efficiency as delivered heat / input)
# ---------------------------------------------------------------------------
HEATING_SYSTEMS: dict[str, tuple[str, float]] = {
    "Reverse-cycle split system (under 10 years)": ("elec", 3.8),
    "Reverse-cycle split system (10+ years)": ("elec", 2.8),
    "Ducted reverse-cycle": ("elec", 3.2),
    "Gas ducted heating": ("gas", 0.70),
    "Gas space heater": ("gas", 0.80),
    "Electric heaters (fan, oil, panel, radiant)": ("elec", 1.00),
    "Wood heater": ("none", 1.0),
    "No heating": ("none", 1.0),
}
COOLING_SYSTEMS: dict[str, tuple[str, float]] = {
    "Reverse-cycle split system (under 10 years)": ("elec", 4.0),
    "Reverse-cycle split system (10+ years)": ("elec", 3.0),
    "Ducted reverse-cycle": ("elec", 3.2),
    "Evaporative cooler": ("elec", 8.0),
    "Portable / window air conditioner": ("elec", 2.2),
    "Fans only": ("elec", 15.0),
    "No cooling": ("none", 1.0),
}
EFFICIENT_RC = "Reverse-cycle split system (under 10 years)"

# ---------------------------------------------------------------------------
# Hot water
# ---------------------------------------------------------------------------
SHOWER_FLOW_LPM = {"Older / standard showerhead (~12 L/min)": 12.0, "Water-efficient 3-star showerhead (~7.5 L/min)": 7.5}
HOT_SHARE_OF_SHOWER = 0.50  # ~40 C at the rose: half 60 C tank water, half cold
OTHER_HOT_WATER_L_PERSON_DAY = 10.0  # basins, kitchen, laundry
WATER_HEAT_KWH_PER_L = 0.0523  # 4.186 kJ/kg.K x 45 K rise / 3600
# (fuel, efficiency incl. standing losses; solar types include a solar fraction)
HOT_WATER_SYSTEMS: dict[str, tuple[str, float]] = {
    "Electric storage tank": ("elec", 0.80),
    "Gas storage tank": ("gas", 0.60),
    "Gas instantaneous / continuous flow": ("gas", 0.80),
    "Heat pump": ("elec", 3.20),
    "Solar, electric boosted": ("elec", 0.80 / 0.40),
    "Solar, gas boosted": ("gas", 0.70 / 0.40),
}
EFFICIENT_SHOWER_MINUTES = 4

# ---------------------------------------------------------------------------
# Lighting, standby and appliances
# ---------------------------------------------------------------------------
LED_WATTS = 7.0
NON_LED_WATTS = 40.0  # typical mix of halogen downlights, incandescent and CFL
LIGHT_HOURS_PER_DAY = 3.0
LIGHT_HABIT_FACTOR = {"Usually switched off": 1.00, "Sometimes left on": 1.15, "Often left on": 1.30}

STANDBY_WATTS_PER_DEVICE = 4.0
STANDBY_HABIT_FACTOR = {"Most things left on standby": 1.00, "Some things switched off": 0.60, "Switched off at the wall / smart power boards": 0.25}

FRIDGE_KWH = {"Under 5 years": 330.0, "5-15 years": 450.0, "Over 15 years": 750.0}
SECOND_FRIDGE_KWH = 550.0
DRYER_KWH_PER_LOAD = {"Vented / condenser dryer": 3.0, "Heat pump dryer": 1.3}
POOL_PUMP_KW = {"No pool": 0.0, "Single-speed pump": 1.1, "Variable-speed pump": 0.35}
COOKING = {"Electric (coil / ceramic)": ("elec", 450.0), "Induction": ("elec", 380.0), "Gas": ("gas", 2400.0)}
COOKING_PER_PERSON_SCALE = 0.25  # +25% per person above 2, -25% per person below

OTHER_APPLIANCES_BASE_KWH = 500.0
OTHER_APPLIANCES_PER_PERSON_KWH = 350.0

# Bill-calibration factor is clipped to keep a bad bill entry from distorting results.
CALIBRATION_RANGE = (0.4, 2.5)

# ---------------------------------------------------------------------------
# Upgrade costs (indicative installed AUD, before rebates unless stated)
# ---------------------------------------------------------------------------
COSTS = {
    "split_system_each": (2200, 4000),
    "heat_pump_hot_water": (3000, 5500),  # after STC discount, before state rebates
    "led_per_light": (8, 30),
    "curtains_per_window": (150, 450),
    "pelmet_per_window": (60, 160),
    "draught_sealing_diy": (100, 500),
    "draught_sealing_pro": (500, 1500),
    "showerhead": (30, 120),
    "smart_power_board": (60, 160),
    "ceiling_insulation_m2": (15, 30),
    "underfloor_insulation_m2": (25, 45),
    "wall_insulation_m2": (35, 70),
    "double_glazing_per_window": (700, 1500),
    "secondary_glazing_per_window": (300, 700),
    "fridge_new": (1100, 2000),
    "heat_pump_dryer": (900, 1700),
    "variable_speed_pool_pump": (900, 1800),
    "induction_cooktop": (1200, 3000),
}

GAS_DISCONNECT_NOTE = (
    "If every gas appliance is replaced, the gas daily supply charge is removed. "
    "Disconnection or abolishment fees ($0-$1,000) are not included."
)

SOURCES = [
    ("Australian Energy Regulator - Default Market Offer", "https://www.aer.gov.au/industry/registers/resources/reviews/default-market-offer-prices-2025-26"),
    ("Essential Services Commission - Victorian Default Offer", "https://www.esc.vic.gov.au/electricity-and-gas/prices-tariffs-and-benchmarks/victorian-default-offer"),
    ("energy.gov.au - Household energy saving tips", "https://www.energy.gov.au/households"),
    ("YourHome - Australia's guide to environmentally sustainable homes", "https://www.yourhome.gov.au/"),
    ("DCCEEW - National Greenhouse Accounts Factors", "https://www.dcceew.gov.au/climate-change/publications/national-greenhouse-accounts-factors"),
    ("Energy Rating (appliance energy labels)", "https://www.energyrating.gov.au/"),
    ("Clean Energy Regulator - Small-scale Renewable Energy Scheme", "https://cer.gov.au/schemes/small-scale-renewable-energy-scheme"),
]

STATE_REBATE_PROGRAMS = {
    "NSW": "NSW Energy Savings Scheme / Peak Demand Reduction Scheme (energy.nsw.gov.au)",
    "VIC": "Victorian Energy Upgrades and Solar Victoria (energy.vic.gov.au, solar.vic.gov.au)",
    "QLD": "Queensland energy rebates and Peak Smart programs (qld.gov.au)",
    "SA": "Retailer Energy Productivity Scheme (sa.gov.au)",
    "WA": "WA Residential Battery Scheme and energy rebates (wa.gov.au)",
    "TAS": "Energy Saver Loan Scheme (recfit.tas.gov.au)",
    "ACT": "Home Energy Support and Sustainable Household Scheme (climatechoices.act.gov.au)",
    "NT": "Home and Business Battery Scheme (nt.gov.au)",
}
