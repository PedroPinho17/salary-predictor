# Salary Predictor

<p align="right"><a href="README.md">English</a> · <b>Português</b></p>

Prevê o salário anual de um programador na Europa ou nos Estados Unidos a partir do país, anos de experiência, função, formação e linguagens que usa.

Um modelo de machine learning treinado com o [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/) (14 602 respostas de 19 países europeus e dos EUA), com uma interface web, uma API REST e um teste com ofertas de emprego reais guardadas em PostgreSQL.

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
![pytest](https://img.shields.io/badge/testes-67%20a%20passar-0A9EDC?logo=pytest&logoColor=white)

## Funcionalidades

- **Interface web**: preenches o perfil e a estimativa atualiza na hora, com um gráfico da evolução do salário com a experiência. Português e inglês, € ou $, modo escuro, funciona no telemóvel.
- **Previsão de salário**: salário anual e mensal (USD) para qualquer combinação de país, experiência, função, formação, trabalho remoto e linguagens.
- **Dois modelos, comparados de forma justa**: Random Forest e Gradient Boosting, avaliados contra uma base (mediana de cada país) com validação cruzada de 5 partições, com o erro da Europa e dos EUA medido em separado.
- **API REST**: FastAPI com documentação interativa. `POST /predict` para um perfil, `POST /estimate` para uma oferta de emprego (título, skills do CV e localização, resultado em €).
- **Validação rigorosa**: valores desconhecidos (ex.: `"portugal"` em minúsculas) dão erro 422 com o motivo, em vez de uma previsão silenciosamente errada. `GET /options` lista todos os valores aceites.
- **Estimativa conforme a localização**: a localização da oferta escolhe o país: "Lisboa" → Portugal, "Remoto (USA)" → EUA, "Berlin" → Alemanha. Ofertas remotas sem país ("Anywhere", "Europe", "EMEA") recebem a mediana dos países europeus.
- **Teste com o mundo real**: o `compare_radar` lê ofertas com salário da base de dados PostgreSQL do Radar e mede o erro do modelo.
- **Linha de comandos**: `salary-predictor --years 2` para uma previsão rápida no terminal.
- **Pronto a usar**: os dados do survey e o modelo treinado estão incluídos no repositório.

## Capturas de ecrã

| Modo claro (português) | Modo escuro (inglês) |
| --- | --- |
| ![Interface web em modo claro](docs/media/app.png) | ![Interface web em modo escuro](docs/media/app-dark.png) |

<p align="center"><img src="docs/media/app-mobile.png" alt="Interface web no telemóvel" width="300"></p>

## Resultados

Erro médio absoluto (MAE) em validação cruzada com 5 partições, separado por região porque os salários dos EUA estão numa escala muito mais alta:

| Modelo | Europa | Estados Unidos |
|---|---|---|
| Base (mediana de cada país) | 31 221 ± 432 $/ano | 55 905 ± 1 223 $/ano |
| Random Forest | 26 139 ± 378 $/ano (16% melhor) | 45 325 ± 689 $/ano (19% melhor) |
| Gradient Boosting | **25 328 ± 281 $/ano** | **44 321 ± 826 $/ano** |

<p align="center"><img src="docs/media/mae.png" alt="Erro em validação cruzada por modelo" width="720"></p>

Os dois modelos estão próximos (o Gradient Boosting fica ligeiramente à frente). Os fatores com mais peso são o **país** e os **anos de experiência**:

| Por país (5 anos de experiência) | Por anos de experiência |
| --- | --- |
| ![Salário previsto por país](docs/media/by-country.png) | ![Salário previsto vs. anos de experiência](docs/media/by-experience.png) |

<sub>Gráficos gerados com o modelo incluído, para um programador full-stack com a stack por omissão (JavaScript, TypeScript, Python, Java, SQL).</sub>

**Juntar os EUA não piorou a Europa.** Antes de juntar os dados dos EUA, comparei as duas versões nas mesmas partições de teste europeias: o Random Forest ficou nos ~26 100 $/ano (26 120 só com a Europa vs 26 139 com os EUA) e o Gradient Boosting melhorou ligeiramente (25 847 → 25 328).

O notebook [`01-explorar`](notebooks/01-explorar.ipynb) tem a análise exploratória e também uma Regressão Linear (28 364 $/ano numa única divisão treino/teste).

### Teste com ofertas reais (Radar)

O modelo foi testado com 22 ofertas com salário, recolhidas pelo Radar, o meu assistente de procura de emprego (ITJobs e Landing.jobs).

| Modelo | Erro médio | Previsão vs. real |
|---|---|---|
| Random Forest | **11 589 €/ano** | **94%** |
| Gradient Boosting | 15 053 €/ano | 81% |

<sub>"Previsão vs. real" é a mediana de previsto ÷ real: 100% quer dizer sem desvio sistemático; abaixo de 100% o modelo subestima.</sub>

No survey o Gradient Boosting fica ligeiramente à frente, mas nas ofertas reais o Random Forest é claramente melhor: erra menos e quase não tem desvio, enquanto o Gradient Boosting subestima a maioria das ofertas. Por isso o modelo guardado por defeito é o **Random Forest**. 22 ofertas, com anos de experiência deduzidos do título, continuam a ser uma amostra pequena, por isso a comparação vai ser repetida à medida que o Radar recolhe mais ofertas.

Acerta melhor em funções comuns (DevOps, Java, testes, consultoria ERP, engenharia de plataformas/IA) e quando o título indica a senioridade. Falha mais em funções bem pagas ou especializadas que o título não revela (ex.: "SQL Bridge Engineer", "Data Scientist", "iOS Developer") e sobrestima funções mal pagas fora da programação (ex.: técnico de laboratório).

## Arquitetura

```mermaid
flowchart LR
    S[(Survey 2025<br/>results.csv.gz)] --> T[train.py<br/>limpeza + Europa e EUA]
    T --> P[Pipeline<br/>OneHotEncoder → Random Forest<br/>sobre log do salário]
    P --> M[(salary_model.joblib)]
    M --> C[CLI]
    M --> A[FastAPI]
    A -- página / + /predict /curve --> U[Browser<br/>HTML + CSS + JS]
    RA[Radar] -->|"/estimate: título, skills, localização"| A
    R[(Radar<br/>PostgreSQL)] -- ofertas --> CR[compare_radar.py]
    M --> CR
    CR --> E[Erro vs. salários reais]
```

**Treino:** `survey → remove valores em falta e outliers (< 5k ou > 400k $) → 19 países europeus + EUA → features (país, experiência, formação, trabalho remoto, função, 9 linguagens como 0/1) → modelo treinado sobre log(salário)`

### Decisões de design

| Decisão | Porquê |
| --- | --- |
| Treinar sobre `log(salário)` | Os salários têm cauda longa à direita. Prever o log evita que meia dúzia de salários muito altos dominem o erro. |
| `min_frequency=20` no encoder | Categorias raras são agrupadas em vez de virarem colunas com meia dúzia de exemplos. |
| Base com a mediana de cada país | Um modelo só é útil se for melhor que "prever a mediana do teu país". Uma mediana global seria fácil demais de bater com os salários dos EUA nos dados. |
| Treinar com a Europa e os EUA juntos | Os dados dos EUA permitem dar salários americanos às ofertas remotas americanas. Medido nas mesmas partições, não piorou as previsões europeias. |
| Erro medido por região | Um só MAE misturaria duas escalas de salários e esconderia como o modelo se porta na Europa. |
| Remoto sem país → mediana europeia | "Anywhere" ou "Europe" não diz que salário se aplica. A mediana dos 19 países europeus é um meio-termo neutro; localizações desconhecidas ficam em Portugal, onde o Radar procura sobretudo. |
| Validação cruzada em vez de uma só divisão | 5 partições dão uma média e um desvio, o que mostra quão próximos os dois modelos estão. |
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
| `GET /meta` | Taxa USD→EUR e erro médio do modelo por região |
| `POST /estimate` | Salário anual (€) para uma oferta, a partir do título, das tuas skills e da localização |

```json
POST /predict
{ "country": "Portugal", "years": 2 }

→ { "salario_anual_usd": 29529, "salario_mensal_usd": 2461 }

POST /estimate
{ "title": "Senior Backend Engineer", "location": "Remoto (USA)" }

→ { "salario_anual_eur": 124000, "base": "United States of America" }
```

`base` diz que país foi usado na estimativa, ou `"Europe"` para ofertas remotas sem país.

| Previsão para um back-end developer na Alemanha | Valores desconhecidos são rejeitados com um erro claro |
| --- | --- |
| ![POST /predict a devolver o salário anual e mensal](docs/media/predict.png) | ![POST /predict a devolver 422 para um país desconhecido](docs/media/validation.png) |

## Limitações

- O survey só tem programadores e não inclui empresa, setor nem cidade, por isso funções raras ou fora da programação ficam mal estimadas.
- Só cobre 19 países europeus e os EUA. Ofertas de outros sítios são estimadas como Portugal (localização desconhecida) ou com a mediana europeia (vários países).
- A localização é comparada com uma lista de nomes de países e cidades; uma grafia invulgar cai em Portugal.
- As ofertas não dizem os anos de experiência: o `compare_radar` deduz pelo título (Junior = 1, Senior/Lead = 7, resto = 3).
- Ofertas com salário abaixo de 6 000 €/ano são excluídas da comparação por serem provavelmente valores mensais.
- A conversão de USD para EUR usa uma taxa fixa aproximada (0,87).
- O teste com o Radar tem só 22 ofertas, é uma amostra pequena.

## Autor

**Pedro Pinho** · [GitHub](https://github.com/PedroPinho17)
