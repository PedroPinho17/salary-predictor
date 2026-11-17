# Salary Predictor

<p align="right"><a href="README.md">English</a> · <b>Português</b></p>

Prevê o salário anual de um programador na Europa a partir do país, anos de experiência, função, formação e linguagens que usa.

Um modelo de machine learning treinado com o [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/) (9 684 respostas de 19 países europeus), com uma interface web, uma API REST e um teste com ofertas de emprego reais em Portugal guardadas em PostgreSQL.

<p align="center">
  <img src="docs/media/demo.gif" alt="Demo: mudar país, experiência, função e linguagens e ver a estimativa a atualizar" width="900">
</p>
<p align="center"><sub>Demo a 1,5× · <a href="docs/media/demo.mp4">vídeo em qualidade total</a></sub></p>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-data-150458?logo=pandas&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-psycopg-4169E1?logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-sem%20framework-F7DF1E?logo=javascript&logoColor=black)
![pytest](https://img.shields.io/badge/testes-36%20a%20passar-0A9EDC?logo=pytest&logoColor=white)

## Funcionalidades

- **Interface web**: preenches o perfil e a estimativa atualiza na hora, com um gráfico da evolução do salário com a experiência. Português e inglês, € ou $, modo escuro, funciona no telemóvel.
- **Previsão de salário**: salário anual e mensal (USD) para qualquer combinação de país, experiência, função, formação, trabalho remoto e linguagens.
- **Dois modelos, comparados de forma justa**: Random Forest e Gradient Boosting, avaliados contra uma base (mediana) com validação cruzada de 5 partições.
- **API REST**: FastAPI com documentação interativa. `POST /predict` para um perfil, `POST /estimate` para uma oferta de emprego (título + skills do CV, resultado em €).
- **Validação rigorosa**: valores desconhecidos (ex.: `"portugal"` em minúsculas) dão erro 422 com o motivo, em vez de uma previsão silenciosamente errada. `GET /options` lista todos os valores aceites.
- **Teste com o mundo real**: o `compare_radar` lê ofertas com salário da base de dados PostgreSQL do Radar e mede o erro do modelo.
- **Linha de comandos**: `salary-predictor --years 2` para uma previsão rápida no terminal.
- **Pronto a usar**: os dados do survey e o modelo treinado estão incluídos no repositório.

## Capturas de ecrã

| Modo claro (português) | Modo escuro (inglês) |
| --- | --- |
| ![Interface web em modo claro](docs/media/app.png) | ![Interface web em modo escuro](docs/media/app-dark.png) |

<p align="center"><img src="docs/media/app-mobile.png" alt="Interface web no telemóvel" width="300"></p>

## Resultados

Erro médio absoluto (MAE) em validação cruzada com 5 partições:

| Modelo | Erro médio |
|---|---|
| Base (mediana) | 34 808 ± 778 $/ano |
| Random Forest | 26 233 ± 569 $/ano (25% melhor que a base) |
| Gradient Boosting | **25 938 ± 477 $/ano** |

<p align="center"><img src="docs/media/mae.png" alt="Erro em validação cruzada por modelo" width="720"></p>

No survey, os dois modelos estão praticamente empatados (a diferença é menor que o desvio entre partições). Os fatores com mais peso são o **país** e os **anos de experiência**:

| Por país (5 anos de experiência) | Por anos de experiência |
| --- | --- |
| ![Salário previsto por país](docs/media/by-country.png) | ![Salário previsto vs. anos de experiência](docs/media/by-experience.png) |

<sub>Gráficos gerados com o modelo incluído, para um programador full-stack com a stack por omissão (JavaScript, TypeScript, Python, Java, SQL).</sub>

O notebook [`01-explorar`](notebooks/01-explorar.ipynb) tem a análise exploratória e também uma Regressão Linear (28 364 $/ano numa única divisão treino/teste).

### Teste com ofertas reais (Radar)

O modelo foi testado com 22 ofertas portuguesas com salário, recolhidas pelo Radar, o meu assistente de procura de emprego (ITJobs e Landing.jobs).

| Modelo | Erro médio | Previsão vs. real |
|---|---|---|
| Random Forest | 11 005 €/ano | 93% |
| Gradient Boosting | 14 707 €/ano | 78% |

> ⚠️ Estes números foram obtidos com uma versão anterior do `compare_radar`, que detetava mal as linguagens nas descrições ("Java" contava em ofertas de JavaScript, "Go" em "Google", etc.). Falta voltar a correr `compare_radar --compare` com a versão corrigida.

Com base nisto, o modelo guardado por defeito é o **Random Forest**. 22 ofertas, com anos de experiência deduzidos do título, são uma amostra demasiado pequena para separar dois modelos que empatam no survey, por isso é uma escolha provisória.

Acerta melhor em funções comuns (DevOps, Java, testes, ERP) e quando o título indica a senioridade. Falha mais em funções raras ou bem pagas (ex.: "SQL Bridge Engineer") e em funções que não são de programação.

## Arquitetura

```mermaid
flowchart LR
    S[(Survey 2025<br/>results.csv.gz)] --> T[train.py<br/>limpeza + filtro Europa]
    T --> P[Pipeline<br/>OneHotEncoder → Random Forest<br/>sobre log do salário]
    P --> M[(salary_model.joblib)]
    M --> C[CLI]
    M --> A[FastAPI]
    A -- página / + /predict /curve --> U[Browser<br/>HTML + CSS + JS]
    A -- /predict /estimate --> X[Outros clientes]
    R[(Radar<br/>PostgreSQL)] -- ofertas --> CR[compare_radar.py]
    M --> CR
    CR --> E[Erro vs. salários reais]
```

**Treino:** `survey → remove valores em falta e outliers (< 5k ou > 400k $) → 19 países europeus → features (país, experiência, formação, trabalho remoto, função, 9 linguagens como 0/1) → modelo treinado sobre log(salário)`

### Decisões de design

| Decisão | Porquê |
| --- | --- |
| Treinar sobre `log(salário)` | Os salários têm cauda longa à direita. Prever o log evita que meia dúzia de salários muito altos dominem o erro. |
| `min_frequency=20` no encoder | Categorias raras são agrupadas em vez de virarem colunas com meia dúzia de exemplos. |
| Base com a mediana | Um modelo só é útil se for melhor que "prever sempre a mediana". É, por 25%. |
| Validação cruzada em vez de uma só divisão | 5 partições dão uma média e um desvio, o que mostra que os dois modelos estão mesmo empatados. |
| Rejeitar valores desconhecidos com 422 | O encoder ignoraria em silêncio uma categoria desconhecida e devolvia na mesma um número. Um erro explícito é mais seguro. |
| `features.py` partilhado | Treino, CLI, API e `compare_radar` constroem as features da mesma forma, por isso não ficam dessincronizados. |
| HTML/CSS/JS simples servido pelo FastAPI | Um formulário não precisa de React nem de build. Um só comando arranca tudo, e a página só oferece valores que o modelo conhece (vêm de `GET /options`). |
| Endpoint `/curve` | O gráfico precisa de 31 previsões. Um pedido com uma só chamada a `model.predict` é muito mais rápido que 31 pedidos. |
| Testes com um modelo sintético | Os testes correm em menos de 2 segundos e não precisam do survey, do modelo treinado nem da base de dados. |

## Dados

| Ficheiro | O que é |
|---|---|
| `data/results.csv.gz` | Respostas do Stack Overflow Developer Survey 2025, comprimidas (16 MB; o CSV original tem 141 MB e passa o limite de 100 MB do GitHub). O pandas lê o `.gz` diretamente. |
| `models/salary_model.joblib` | Modelo Random Forest já treinado, pronto a usar. |
| Base de dados do Radar (PostgreSQL) | Ofertas de emprego reais, usadas só pelo `compare_radar`. **Não está incluída**: é acedida através de `DATABASE_URL`. |

Os dados do survey são publicados pela Stack Overflow sob a licença [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/).

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Frontend | HTML, CSS, JavaScript (sem framework), gráfico SVG feito à mão |
| Modelo | scikit-learn (Random Forest, HistGradientBoosting), pandas, NumPy |
| API | FastAPI, Pydantic, Uvicorn |
| Dados | Stack Overflow Survey (CSV), PostgreSQL com psycopg |
| Análise | Jupyter, matplotlib |
| Ferramentas | uv, pytest, Python 3.13 |

## Como correr

1. Instala o [uv](https://docs.astral.sh/uv/) e depois as dependências: `uv sync`
2. Arranca a aplicação: `uv run uvicorn salary_predictor.api:app --reload`
   - Interface web: http://127.0.0.1:8000
   - Documentação da API: http://127.0.0.1:8000/docs
3. Ou prevê no terminal: `uv run salary-predictor --years 2`
4. Treinar de novo (opcional): `uv run python -m salary_predictor.train` (`--model gb` para Gradient Boosting, `--compare` para avaliar todos)
5. Testes: `uv run pytest`
6. Comparar com o Radar: `uv run python -m salary_predictor.compare_radar [--compare]`. Precisa de `DATABASE_URL` no ambiente ou num `.env`:
   ```
   DATABASE_URL=postgresql://utilizador:password@localhost:5432/radar
   ```
   Para usar o `.env` de outro projeto: `RADAR_ENV_FILE=../radar-app/apps/api/.env`

## API

| Endpoint | O que faz |
| --- | --- |
| `GET /health` | Verifica se a API está a correr |
| `GET /options` | Valores aceites para país, função, formação, trabalho remoto e linguagens |
| `POST /predict` | Salário anual e mensal (USD) para um perfil |
| `POST /curve` | Salário previsto de 0 a 30 anos de experiência, para o gráfico |
| `GET /meta` | Taxa USD→EUR e erro médio do modelo |
| `POST /estimate` | Salário anual (€) para uma oferta em Portugal, a partir do título e das tuas skills |

```json
POST /predict
{ "country": "Portugal", "years": 2 }

→ { "salario_anual_usd": 29945, "salario_mensal_usd": 2495 }
```

| Previsão para um back-end developer na Alemanha | Valores desconhecidos são rejeitados com um erro claro |
| --- | --- |
| ![POST /predict a devolver o salário anual e mensal](docs/media/predict.png) | ![POST /predict a devolver 422 para um país desconhecido](docs/media/validation.png) |

## Limitações

- O survey só tem programadores e não inclui empresa, setor nem cidade, por isso funções raras ou fora da programação ficam mal estimadas.
- As ofertas não dizem os anos de experiência: o `compare_radar` deduz pelo título (Junior = 1, Senior/Lead = 7, resto = 3).
- Ofertas com salário abaixo de 6 000 €/ano são excluídas da comparação por serem provavelmente valores mensais.
- A conversão de USD para EUR usa uma taxa fixa aproximada (0,87).
- O teste com o Radar tem só 22 ofertas, é uma amostra pequena.

## Autor

**Pedro Pinho** · [GitHub](https://github.com/PedroPinho17)
