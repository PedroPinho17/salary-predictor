# Salary Predictor

<p align="right"><b>English</b> · <a href="README.pt-PT.md">Português</a></p>

Predicts the annual salary of a software developer in Europe or the United States from their country, years of experience, role, education and the programming languages they use.

A machine-learning model trained on the [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/) (14,602 responses from 19 European countries and the US), with a web interface, a REST API, and a check against real job offers stored in PostgreSQL.

<p align="center">
  <img src="docs/media/demo.gif" alt="Demo: changing country, experience, role and languages and watching the estimate update" width="900">
</p>
<p align="center"><sub>Demo at 1.5× speed · <a href="docs/media/demo.mp4">full-quality video</a></sub></p>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-data-150458?logo=pandas&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-psycopg-4169E1?logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-no%20framework-F7DF1E?logo=javascript&logoColor=black)
![pytest](https://img.shields.io/badge/tests-67%20passing-0A9EDC?logo=pytest&logoColor=white)

## Features

- **Web interface**: fill in your profile and the estimate updates instantly, with a chart of how the salary grows with experience. Portuguese and English, € or $, dark mode, works on mobile.
- **Salary prediction**: annual and monthly salary (USD) for any combination of country, experience, role, education, remote work and languages.
- **Two models, compared fairly**: Random Forest and Gradient Boosting, evaluated against a per-country median baseline with 5-fold cross-validation, with the error reported separately for Europe and the US.
- **REST API**: FastAPI with interactive docs. `POST /predict` for a developer profile, `POST /estimate` for a job offer (title, CV skills and location, result in €).
- **Strict validation**: unknown values (e.g. lowercase `"portugal"`) return a 422 with the reason instead of a silently wrong prediction. `GET /options` lists every accepted value.
- **Location-aware estimates**: the offer's location picks the country: "Lisboa" → Portugal, "Remote (USA)" → United States, "Berlin" → Germany. Remote offers with no country ("Anywhere", "Europe", "EMEA") get the median across European countries.
- **Real-world check**: `compare_radar` reads job offers with published salaries from the Radar PostgreSQL database and measures how far off the model is.
- **CLI**: `salary-predictor --years 2` for a quick prediction in the terminal.
- **Ready to run**: the survey data and the trained model are included in the repository.

## Screenshots

| Light mode (Portuguese) | Dark mode (English) |
| --- | --- |
| ![Web interface in light mode](docs/media/app.png) | ![Web interface in dark mode](docs/media/app-dark.png) |

<p align="center"><img src="docs/media/app-mobile.png" alt="Web interface on a phone" width="300"></p>

## Results

Mean absolute error (MAE) with 5-fold cross-validation, reported separately for each region because US salaries are on a much higher scale:

| Model | Europe | United States |
|---|---|---|
| Baseline (median per country) | 31,221 ± 432 $/year | 55,905 ± 1,223 $/year |
| Random Forest | 26,139 ± 378 $/year (16% better) | 45,325 ± 689 $/year (19% better) |
| Gradient Boosting | **25,328 ± 281 $/year** | **44,321 ± 826 $/year** |

<p align="center"><img src="docs/media/mae.png" alt="Cross-validation error per model" width="720"></p>

The two models are close (Gradient Boosting is slightly ahead). The strongest factors are **country** and **years of experience**:

| By country (5 years of experience) | By years of experience |
| --- | --- |
| ![Predicted salary by country](docs/media/by-country.png) | ![Predicted salary vs. years of experience](docs/media/by-experience.png) |

<sub>Charts generated with the bundled model for a full-stack developer with the default stack (JavaScript, TypeScript, Python, Java, SQL).</sub>

**Adding the US didn't hurt Europe.** Before adding the US data, I compared both versions on the same European test folds: Random Forest stayed at ~26,100 $/year (26,120 Europe-only vs 26,139 with the US), and Gradient Boosting improved slightly (25,847 → 25,328).

The [`01-explorar`](notebooks/01-explorar.ipynb) notebook has the exploratory analysis, plus a Linear Regression (28,364 $/year on a single train/test split).

### Test on real job offers (Radar)

The model was tested on 22 job offers with a published salary, collected by Radar, my job-search assistant (ITJobs and Landing.jobs).

| Model | Mean error | Predicted vs. actual |
|---|---|---|
| Random Forest | 11,005 €/year | 93% |
| Gradient Boosting | 14,707 €/year | 78% |

> ⚠️ These numbers come from an earlier version: a Europe-only model, every offer treated as Portuguese, and poor language detection in descriptions ("Java" matched JavaScript offers, "Go" matched "Google", etc.). `compare_radar --compare` still needs to be re-run with the current version.

Based on this, the default saved model is **Random Forest**. 22 offers, with years of experience inferred from the title, is too small a sample to separate two models this close, so it is a provisional choice.

It does best on common roles (DevOps, Java, QA, ERP) and when the title states seniority. It does worst on rare or highly paid roles (e.g. "SQL Bridge Engineer") and on non-programming roles.

## Architecture

```mermaid
flowchart LR
    S[(Survey 2025<br/>results.csv.gz)] --> T[train.py<br/>clean + Europe & US]
    T --> P[Pipeline<br/>OneHotEncoder → Random Forest<br/>on log salary]
    P --> M[(salary_model.joblib)]
    M --> C[CLI]
    M --> A[FastAPI]
    A -- / page + /predict /curve --> U[Browser<br/>HTML + CSS + JS]
    RA[Radar] -->|"/estimate: title, skills, location"| A
    R[(Radar<br/>PostgreSQL)] -- job offers --> CR[compare_radar.py]
    M --> CR
    CR --> E[Error vs. real salaries]
```

**Training:** `survey → drop missing values and outliers (< 5k or > 400k $) → 19 European countries + US → features (country, experience, education, remote work, role, 9 languages as 0/1) → model trained on log(salary)`

### Design decisions

| Decision | Why |
| --- | --- |
| Train on `log(salary)` | Salaries have a long right tail. Predicting the log keeps a few very high salaries from dominating the error. |
| `min_frequency=20` in the encoder | Rare categories are grouped together instead of becoming columns with a handful of examples. |
| Per-country median baseline | A model is only useful if it beats "predict the median salary of your country". A global median would be too easy to beat once US salaries are in the data. |
| Train on Europe and the US together | The US data lets remote US offers get US salaries. Measured on the same folds, it didn't make European predictions worse. |
| Error reported per region | A single MAE would mix two salary scales and hide how the model does in Europe. |
| Remote with no country → European median | "Anywhere" or "Europe" doesn't say which salary applies. The median across the 19 European countries is a neutral middle ground; unknown locations fall back to Portugal, where Radar mostly searches. |
| Cross-validation instead of one split | 5 folds give a mean and a spread, which shows how close the two models really are. |
| Reject unknown values with 422 | The encoder would silently ignore an unknown category and still return a number. An explicit error is safer. |
| Shared `features.py` | Training, CLI, API and `compare_radar` build features the same way, so they can't drift apart. |
| Plain HTML/CSS/JS served by FastAPI | One form doesn't need React or a build step. One command starts the whole app, and the page only offers values the model knows (from `GET /options`). |
| `/curve` endpoint | The chart needs 31 predictions. One request with one `model.predict` call is much faster than 31 requests. |
| Tests with a synthetic model | Tests run in under 2 seconds and don't need the survey, the trained model or the database. |

## Data

| File | What it is |
|---|---|
| `data/results.csv.gz` | Stack Overflow Developer Survey 2025 responses, compressed (16 MB; the original CSV is 141 MB, over GitHub's 100 MB limit). pandas reads the `.gz` directly. |
| `models/salary_model.joblib` | Pre-trained Random Forest model, ready to use. |
| Radar database (PostgreSQL) | Real job offers, used only by `compare_radar`. **Not included**: accessed through `DATABASE_URL`. |

The survey data is published by Stack Overflow under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML, CSS, JavaScript (no framework), hand-drawn SVG chart |
| Model | scikit-learn (Random Forest, HistGradientBoosting), pandas, NumPy |
| API | FastAPI, Pydantic, Uvicorn |
| Data | Stack Overflow Survey (CSV), PostgreSQL via psycopg |
| Analysis | Jupyter, matplotlib |
| Tooling | uv, pytest, Python 3.13 |

## Getting started

1. Install [uv](https://docs.astral.sh/uv/), then the dependencies: `uv sync`
2. Start the app: `uv run uvicorn salary_predictor.api:app --reload`
   - Web interface: http://127.0.0.1:8000
   - API docs: http://127.0.0.1:8000/docs
3. Or predict in the terminal: `uv run salary-predictor --years 2`
4. Retrain (optional): `uv run python -m salary_predictor.train` (`--model gb` for Gradient Boosting, `--compare` to evaluate all)
5. Tests: `uv run pytest`
6. Compare against Radar: `uv run python -m salary_predictor.compare_radar [--compare]`. Requires `DATABASE_URL` in the environment or in a `.env` file:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/radar
   ```
   To use another project's `.env`: `RADAR_ENV_FILE=../radar-app/apps/api/.env`

## API

| Endpoint | What it does |
| --- | --- |
| `GET /health` | Health check |
| `GET /options` | Accepted values for country, role, education, remote work and languages |
| `POST /predict` | Annual and monthly salary (USD) for a developer profile |
| `POST /curve` | Predicted salary from 0 to 30 years of experience, for the chart |
| `GET /meta` | USD→EUR rate and the model's mean error per region |
| `POST /estimate` | Annual salary (€) for a job offer, from its title, your skills and its location |

```json
POST /predict
{ "country": "Portugal", "years": 2 }

→ { "salario_anual_usd": 29529, "salario_mensal_usd": 2461 }

POST /estimate
{ "title": "Senior Backend Engineer", "location": "Remoto (USA)" }

→ { "salario_anual_eur": 124000, "base": "United States of America" }
```

`base` says which country the estimate used, or `"Europe"` for remote offers with no country.

| Prediction for a back-end developer in Germany | Unknown values are rejected with a clear error |
| --- | --- |
| ![POST /predict returning the annual and monthly salary](docs/media/predict.png) | ![POST /predict returning a 422 for an unknown country](docs/media/validation.png) |

## Limitations

- The survey only covers developers and has no company, industry or city, so rare or non-programming roles are poorly estimated.
- Only 19 European countries and the US are covered. Offers elsewhere are estimated as Portugal (unknown location) or the European median (several countries).
- The location is matched against a list of country and city names; an unusual spelling falls back to Portugal.
- Job offers don't state years of experience: `compare_radar` infers it from the title (Junior = 1, Senior/Lead = 7, otherwise 3).
- Offers below 6,000 €/year are excluded from the comparison since they are probably monthly figures.
- USD to EUR conversion uses a fixed approximate rate (0.87).
- The Radar test has only 22 offers, which is a small sample.

## Author

**Pedro Pinho** · [GitHub](https://github.com/PedroPinho17)
