# 🏡 Energy Efficient Home_AU

A lite, one-page **home-energy advisor for Australian households**, built with Streamlit.

Answer about 20 quick questions, or load a **demo home**, and get:

- **Seven checks**: heating & cooling, lighting, curtains & blinds, draughts, hot water, standby power and insulation, each rated *Good / Could improve / Priority* with an indicative saving
- **A personalised action plan**: actions grouped as *Do now*, *Plan next* and *Consider at replacement*, with annual savings, upfront cost ranges, payback and a renter/landlord flag
- **A scenario comparison**: current home vs quick wins, renter-friendly (for tenants), moderate upgrades and deep retrofit, showing bill, energy and emissions side by side
- **Charts**: check scores, where the money goes, and the scenario comparison
- **CSV export** of the action plan, the scenarios and every assumption

## Demo homes

Pick one from **"Try a demo home"** at the top of the page:

| Demo | What it shows |
|---|---|
| Sydney family house | Old reverse-cycle system and an electric storage hot water tank: hot water is the big win |
| Melbourne renter flat | Plug-in heaters and draughts: what a tenant can do without the landlord |
| Brisbane solar home | An efficient home with 6.6 kW of solar: modest remaining savings |
| Canberra gas house | Gas heating and hot water with no insulation: the electrification case, including dropping the gas supply charge |

## How the numbers work (transparent and indicative)

- **Heating/cooling** = climate-zone load (kWh per m²) × area heated × home type, age, insulation, draught and curtain factors × ~10% per °C of thermostat setting, ÷ equipment efficiency
- **Hot water** is calculated from people, shower length and showerhead flow. **Lighting, standby and appliances** use typical wattages.
- **Bills** = grid electricity × your rate + supply charges − solar exports × feed-in + gas × rate + gas supply charge (removed once no gas appliances remain)
- **Emissions** use state grid factors from the National Greenhouse Accounts Factors
- **Actions** are modelled as changes to your answers, and the whole model is re-run. Scenarios therefore never double count overlapping savings.
- **Payback** = mid-range cost ÷ annual saving, with no rebates, inflation or discounting

Every constant is in [`energy_advisor/assumptions.py`](energy_advisor/assumptions.py) and is shown in the app. Tariffs are pre-filled with indicative 2025–26 standing-offer rates for each state, and users can overwrite them with the rates on their own bill.

> Results are indicative estimates. They are not a substitute for a professional home energy assessment.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the tests:

```bash
pip install pytest
python -m pytest
```

## Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**.
3. Repository: `arminbaghaei/Energy-Efficient-Home_AU`, branch: `main`, main file: `streamlit_app.py`.
4. Under **Advanced settings**, choose Python 3.12 or later, then click **Deploy**.

## Project layout

```
streamlit_app.py            # the one-page lite app
energy_advisor/
  assumptions.py            # every number used, with sources
  profile.py                # HouseholdProfile: all answers in one record
  baseline.py               # end-use energy, bills, emissions
  actions.py                # catalogue of actions (as changes to the profile)
  checks.py                 # the seven checks
  scenarios.py              # quick wins / moderate / deep / renter packages
  charts.py                 # Plotly charts
  export.py                 # CSV tables
  inputs.py, demos.py       # questionnaire widgets and demo homes
tests/test_calculations.py  # model tests
```

## Licence

MIT
