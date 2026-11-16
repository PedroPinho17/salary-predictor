# Salary Predictor

🇵🇹 [Português](#-português) · 🇬🇧 [English](#-english)

---

## 🇵🇹 Português

Prevê o salário anual (USD) de um programador na Europa, com base no país, anos de experiência, tipo de função, formação e linguagens que usa.

Treinado com o [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/) (9 684 respostas de 19 países europeus).

### Resultados

Erro médio absoluto (MAE) em validação cruzada com 5 partições (média ± desvio padrão):

| Modelo | Erro médio |
|---|---|
| Base (mediana) | 34 808 ± 778 $/ano |
| Random Forest | 26 233 ± 569 $/ano (25% melhor que a base) |
| Gradient Boosting | **25 938 ± 477 $/ano** |

No survey, os dois modelos estão praticamente empatados (a diferença é menor que o desvio entre partições). Os fatores com mais peso são o **país** e os **anos de experiência**. O notebook [`01-explorar`](notebooks/01-explorar.ipynb) tem também uma Regressão Linear (28 364 $/ano numa única divisão treino/teste).

Para reproduzir: `uv run python -m salary_predictor.train --compare`

### Teste com ofertas reais (Radar)

O modelo foi testado com 22 ofertas portuguesas com salário, recolhidas pelo Radar, o meu assistente de procura de emprego (ITJobs e Landing.jobs).

| Modelo | Erro médio | Previsão vs. real |
|---|---|---|
| Random Forest | 11 005 €/ano | 93% |
| Gradient Boosting | 14 707 €/ano | 78% |

> ⚠️ Estes números foram obtidos com uma versão anterior do `compare_radar`, que detetava mal as linguagens nas descrições ("Java" contava em ofertas de JavaScript, "Go" em "Google", etc.). Falta voltar a correr `compare_radar --compare` com a versão corrigida.

Com base nisto, o modelo guardado por defeito é o **Random Forest**. Mas 22 ofertas, com anos de experiência deduzidos do título, são uma amostra demasiado pequena para separar dois modelos que empatam no survey. É uma escolha provisória até haver mais ofertas.

Acerta melhor em funções comuns (DevOps, Java, testes, ERP) e quando o título indica a senioridade. Falha mais em funções raras ou bem pagas (ex.: "SQL Bridge Engineer") e em funções que não são de programação.

### Dados

| Ficheiro | O que é |
|---|---|
| `data/results.csv.gz` | Respostas do Stack Overflow Developer Survey 2025, comprimidas (16 MB; o CSV original tem 141 MB e passa o limite de 100 MB do GitHub). O pandas lê o `.gz` diretamente, não é preciso descomprimir. |
| `models/salary_model.joblib` | Modelo Random Forest já treinado, pronto a usar. |
| Base de dados do Radar (PostgreSQL) | Ofertas de emprego reais, usadas só pelo `compare_radar`. **Não está no repositório**: é acedida através de `DATABASE_URL`. |

Os dados do survey são publicados pela Stack Overflow sob a licença [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).

### Tecnologias

Python 3.13, pandas, scikit-learn, FastAPI, PostgreSQL (psycopg), pytest, Jupyter, uv

### Como correr

1. Instala o [uv](https://docs.astral.sh/uv/) e depois as dependências: `uv sync`
2. Prevê (usa o modelo incluído): `uv run salary-predictor --years 2`
3. API: `uv run uvicorn salary_predictor.api:app --reload` e abre http://127.0.0.1:8000/docs
4. Treinar de novo (opcional): `uv run python -m salary_predictor.train` (`--model gb` para Gradient Boosting, `--compare` para avaliar todos)
5. Testes: `uv run pytest` (usam um modelo sintético e não precisam do survey nem do modelo treinado)
6. Comparar com o Radar: `uv run python -m salary_predictor.compare_radar [--compare]`. Precisa de `DATABASE_URL` no ambiente ou num `.env`, por exemplo:
   ```
   DATABASE_URL=postgresql://utilizador:password@localhost:5432/radar
   ```
   Para usar o `.env` de outro projeto: `RADAR_ENV_FILE=../radar-app/apps/api/.env`

### Exemplo

```json
POST /predict
{ "country": "Portugal", "years": 2 }

→ { "salario_anual_usd": 29945, "salario_mensal_usd": 2495 }
```

Endpoints: `GET /health`, `GET /options`, `POST /predict`, `POST /estimate`.

`GET /options` lista os valores aceites para país, função, formação, trabalho remoto e linguagens. Valores desconhecidos (ex.: `"portugal"` em minúsculas) dão erro 422 em vez de uma previsão silenciosamente errada.

### Limitações

- O survey só tem programadores e não inclui empresa, setor nem cidade, por isso funções raras ou fora da programação ficam mal estimadas.
- As ofertas não dizem os anos de experiência: o `compare_radar` deduz pelo título (Junior = 1, Senior/Lead = 7, resto = 3).
- Ofertas com salário abaixo de 6 000 €/ano são excluídas da comparação por serem provavelmente valores mensais.
- A conversão de USD para EUR usa uma taxa fixa aproximada (0,87).
- O teste com o Radar tem só 22 ofertas, é uma amostra pequena.

---

## 🇬🇧 English

Predicts the annual salary (USD) of a software developer in Europe, based on country, years of experience, role, education and the programming languages they use.

Trained on the [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/) (9,684 responses from 19 European countries).

### Results

Mean absolute error (MAE) with 5-fold cross-validation (mean ± standard deviation):

| Model | Mean error |
|---|---|
| Baseline (median) | 34,808 ± 778 $/year |
| Random Forest | 26,233 ± 569 $/year (25% better than baseline) |
| Gradient Boosting | **25,938 ± 477 $/year** |

On the survey the two models are practically tied (the difference is smaller than the spread between folds). The strongest factors are **country** and **years of experience**. The [`01-explorar`](notebooks/01-explorar.ipynb) notebook also includes a Linear Regression (28,364 $/year on a single train/test split).

To reproduce: `uv run python -m salary_predictor.train --compare`

### Test on real job offers (Radar)

The model was tested on 22 Portuguese job offers with a published salary, collected by Radar, my job-search assistant (ITJobs and Landing.jobs).

| Model | Mean error | Predicted vs. actual |
|---|---|---|
| Random Forest | 11,005 €/year | 93% |
| Gradient Boosting | 14,707 €/year | 78% |

> ⚠️ These numbers come from an earlier version of `compare_radar`, which detected languages in job descriptions poorly ("Java" matched JavaScript offers, "Go" matched "Google", etc.). `compare_radar --compare` still needs to be re-run with the fixed version.

Based on this, the default saved model is **Random Forest**. However, 22 offers, with years of experience inferred from the job title, is too small a sample to separate two models that tie on the survey. It is a provisional choice until more offers are available.

It does best on common roles (DevOps, Java, QA, ERP) and when the title states seniority. It does worst on rare or highly paid roles (e.g. "SQL Bridge Engineer") and on non-programming roles.

### Data

| File | What it is |
|---|---|
| `data/results.csv.gz` | Stack Overflow Developer Survey 2025 responses, compressed (16 MB; the original CSV is 141 MB, over GitHub's 100 MB limit). pandas reads the `.gz` directly, no need to decompress. |
| `models/salary_model.joblib` | Pre-trained Random Forest model, ready to use. |
| Radar database (PostgreSQL) | Real job offers, used only by `compare_radar`. **Not included in the repository**: accessed through `DATABASE_URL`. |

The survey data is published by Stack Overflow under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).

### Tech stack

Python 3.13, pandas, scikit-learn, FastAPI, PostgreSQL (psycopg), pytest, Jupyter, uv

### Getting started

1. Install [uv](https://docs.astral.sh/uv/), then the dependencies: `uv sync`
2. Predict (uses the bundled model): `uv run salary-predictor --years 2`
3. API: `uv run uvicorn salary_predictor.api:app --reload` and open http://127.0.0.1:8000/docs
4. Retrain (optional): `uv run python -m salary_predictor.train` (`--model gb` for Gradient Boosting, `--compare` to evaluate all)
5. Tests: `uv run pytest` (they use a synthetic model and need neither the survey nor the trained model)
6. Compare against Radar: `uv run python -m salary_predictor.compare_radar [--compare]`. Requires `DATABASE_URL` in the environment or in a `.env` file, e.g.:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/radar
   ```
   To use another project's `.env`: `RADAR_ENV_FILE=../radar-app/apps/api/.env`

### Example

```json
POST /predict
{ "country": "Portugal", "years": 2 }

→ { "salario_anual_usd": 29945, "salario_mensal_usd": 2495 }
```

Endpoints: `GET /health`, `GET /options`, `POST /predict`, `POST /estimate`.

`GET /options` lists the accepted values for country, role, education, remote work and languages. Unknown values (e.g. lowercase `"portugal"`) return a 422 error instead of a silently wrong prediction.

### Limitations

- The survey only covers developers and has no company, industry or city, so rare or non-programming roles are poorly estimated.
- Job offers don't state years of experience: `compare_radar` infers it from the title (Junior = 1, Senior/Lead = 7, otherwise 3).
- Offers below 6,000 €/year are excluded from the comparison since they are probably monthly figures.
- USD to EUR conversion uses a fixed approximate rate (0.87).
- The Radar test has only 22 offers, which is a small sample.

---

Pedro Pinho
