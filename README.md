# Salary Predictor

<p align="right"><b>English</b> · <a href="README.pt-PT.md">Português</a></p>

Predicts the annual salary of a software developer in Europe from their country, years of experience, role, education and the programming languages they use.

A machine-learning model trained on the [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/) (9,684 responses from 19 European countries), served through a REST API and checked against real Portuguese job offers stored in PostgreSQL.

<p align="center">
  <img src="docs/media/demo.gif" alt="Demo: calling the API from the interactive docs to predict salaries" width="900">
</p>
<p align="center"><sub>Demo at 2× speed · <a href="docs/media/demo.mp4">full-quality video</a> · interactive API docs at <code>/docs</code></sub></p>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-data-150458?logo=pandas&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-psycopg-4169E1?logo=postgresql&logoColor=white)
![pytest](https://img.shields.io/badge/tests-31%20passing-0A9EDC?logo=pytest&logoColor=white)

## Features

- **Salary prediction**: annual and monthly salary (USD) for any combination of country, experience, role, education, remote work and languages.
- **Two models, compared fairly**: Random Forest and Gradient Boosting, evaluated against a median baseline with 5-fold cross-validation.
- **REST API**: FastAPI with interactive docs. `POST /predict` for a developer profile, `POST /estimate` for a job offer (title + CV skills, result in €).
- **Strict validation**: unknown values (e.g. lowercase `"portugal"`) return a 422 with the reason instead of a silently wrong prediction. `GET /options` lists every accepted value.
- **Real-world check**: `compare_radar` reads job offers with published salaries from the Radar PostgreSQL database and measures how far off the model is.
- **CLI**: `salary-predictor --years 2` for a quick prediction in the terminal.
- **Ready to run**: the survey data and the trained model are included in the repository.

## Screenshots

| Prediction for a back-end developer in Germany | Unknown values are rejected with a clear error |
| --- | --- |
| ![POST /predict returning the annual and monthly salary](docs/media/predict.png) | ![POST /predict returning a 422 for an unknown country](docs/media/validation.png) |

## Results

Mean absolute error (MAE) with 5-fold cross-validation:

| Model | Mean error |
|---|---|
| Baseline (median) | 34,808 ± 778 $/year |
| Random Forest | 26,233 ± 569 $/year (25% better than baseline) |
| Gradient Boosting | **25,938 ± 477 $/year** |

<p align="center"><img src="docs/media/mae.png" alt="Cross-validation error per model" width="720"></p>

On the survey the two models are practically tied (the difference is smaller than the spread between folds). The strongest factors are **country** and **years of experience**:

| By country (5 years of experience) | By years of experience |
| --- | --- |
| ![Predicted salary by country](docs/media/by-country.png) | ![Predicted salary vs. years of experience](docs/media/by-experience.png) |

<sub>Charts generated with the bundled model for a full-stack developer with the default stack (JavaScript, TypeScript, Python, Java, SQL).</sub>

The [`01-explorar`](notebooks/01-explorar.ipynb) notebook has the exploratory analysis, plus a Linear Regression (28,364 $/year on a single train/test split).

### Test on real job offers (Radar)

The model was tested on 22 Portuguese job offers with a published salary, collected by Radar, my job-search assistant (ITJobs and Landing.jobs).

| Model | Mean error | Predicted vs. actual |
|---|---|---|
| Random Forest | 11,005 €/year | 93% |
| Gradient Boosting | 14,707 €/year | 78% |

> ⚠️ These numbers come from an earlier version of `compare_radar`, which detected languages in job descriptions poorly ("Java" matched JavaScript offers, "Go" matched "Google", etc.). `compare_radar --compare` still needs to be re-run with the fixed version.

Based on this, the default saved model is **Random Forest**. 22 offers, with years of experience inferred from the title, is too small a sample to separate two models that tie on the survey, so it is a provisional choice.

It does best on common roles (DevOps, Java, QA, ERP) and when the title states seniority. It does worst on rare or highly paid roles (e.g. "SQL Bridge Engineer") and on non-programming roles.

## Architecture

```mermaid
flowchart LR
    S[(Survey 2025<br/>results.csv.gz)] --> T[train.py<br/>clean + filter Europe]
    T --> P[Pipeline<br/>OneHotEncoder → Random Forest<br/>on log salary]
    P --> M[(salary_model.joblib)]
    M --> C[CLI]
    M --> A[FastAPI]
    A -- /predict /estimate --> U[Client / browser]
    R[(Radar<br/>PostgreSQL)] -- job offers --> CR[compare_radar.py]
    M --> CR
    CR --> E[Error vs. real salaries]
```

**Training:** `survey → drop missing values and outliers (< 5k or > 400k $) → 19 European countries → features (country, experience, education, remote work, role, 9 languages as 0/1) → model trained on log(salary)`

### Design decisions

| Decision | Why |
| --- | --- |
| Train on `log(salary)` | Salaries have a long right tail. Predicting the log keeps a few very high salaries from dominating the error. |
| `min_frequency=20` in the encoder | Rare categories are grouped together instead of becoming columns with a handful of examples. |
| Median baseline | A model is only useful if it beats "always predict the median". It does, by 25%. |
| Cross-validation instead of one split | 5 folds give a mean and a spread, which shows the two models are really tied. |
| Reject unknown values with 422 | The encoder would silently ignore an unknown category and still return a number. An explicit error is safer. |
| Shared `features.py` | Training, CLI, API and `compare_radar` build features the same way, so they can't drift apart. |
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
| Model | scikit-learn (Random Forest, HistGradientBoosting), pandas, NumPy |
| API | FastAPI, Pydantic, Uvicorn |
| Data | Stack Overflow Survey (CSV), PostgreSQL via psycopg |
| Analysis | Jupyter, matplotlib |
| Tooling | uv, pytest, Python 3.13 |

## Getting started

1. Install [uv](https://docs.astral.sh/uv/), then the dependencies: `uv sync`
2. Predict (uses the bundled model): `uv run salary-predictor --years 2`
3. API: `uv run uvicorn salary_predictor.api:app --reload` and open http://127.0.0.1:8000/docs
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
| `POST /estimate` | Annual salary (€) for a job offer in Portugal, from its title and your skills |

```json
POST /predict
{ "country": "Portugal", "years": 2 }

→ { "salario_anual_usd": 29945, "salario_mensal_usd": 2495 }
```

## Limitations

- The survey only covers developers and has no company, industry or city, so rare or non-programming roles are poorly estimated.
- Job offers don't state years of experience: `compare_radar` infers it from the title (Junior = 1, Senior/Lead = 7, otherwise 3).
- Offers below 6,000 €/year are excluded from the comparison since they are probably monthly figures.
- USD to EUR conversion uses a fixed approximate rate (0.87).
- The Radar test has only 22 offers, which is a small sample.

## Author

**Pedro Pinho** · [GitHub](https://github.com/PedroPinho17)
