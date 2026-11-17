// Salary Predictor — interface web.
// Lê os valores aceites de GET /options, pede a previsão a POST /predict e a curva a POST /curve
// sempre que um campo muda. Sem frameworks nem build.

// ---------- Textos (PT / EN) ----------
const TEXT = {
  pt: {
    title: "Quanto deverias ganhar?",
    subtitle: "Estimativa do salário anual de um programador na Europa, com um modelo treinado em 9 684 respostas do Stack Overflow Developer Survey 2025.",
    profile: "O teu perfil", country: "País", experience: "Experiência profissional",
    role: "Função", education: "Formação", remote: "Modelo de trabalho", languages: "Linguagens que usas",
    estimate: "Salário estimado", perYear: "/ ano", perMonth: "/ mês (12 meses)",
    margin: (v) => `Erro médio do modelo: ± ${v} por ano`,
    curveTitle: "Evolução com a experiência", you: "tu",
    years: (n) => (n === 1 ? "1 ano" : `${n} anos`), yearsShort: (n) => `${n}a`,
    note: "Valores brutos anuais. O survey não inclui empresa, setor nem cidade, por isso usa a estimativa como referência, não como valor exato.",
    footer: "Feito por Pedro Pinho", apiDocs: "Documentação da API", theme: "Mudar tema",
    error: "Não foi possível obter a estimativa. A API está a correr?",
  },
  en: {
    title: "How much should you earn?",
    subtitle: "Annual salary estimate for a software developer in Europe, from a model trained on 9,684 responses to the Stack Overflow Developer Survey 2025.",
    profile: "Your profile", country: "Country", experience: "Professional experience",
    role: "Role", education: "Education", remote: "Work arrangement", languages: "Languages you use",
    estimate: "Estimated salary", perYear: "/ year", perMonth: "/ month (12 months)",
    margin: (v) => `Model's mean error: ± ${v} per year`,
    curveTitle: "Growth with experience", you: "you",
    years: (n) => (n === 1 ? "1 year" : `${n} years`), yearsShort: (n) => `${n}y`,
    note: "Gross annual figures. The survey has no company, industry or city, so treat the estimate as a reference, not an exact value.",
    footer: "Made by Pedro Pinho", apiDocs: "API docs", theme: "Toggle theme",
    error: "Couldn't get an estimate. Is the API running?",
  },
};

// Nomes curtos para os valores do survey: [PT, EN]. A ordem das chaves é a ordem nas listas.
// Valores que não estejam aqui aparecem tal como vêm da API.
const LABELS = {
  Country: {
    "Austria": ["Áustria", "Austria"], "Belgium": ["Bélgica", "Belgium"],
    "Czech Republic": ["Chéquia", "Czech Republic"], "Denmark": ["Dinamarca", "Denmark"],
    "Finland": ["Finlândia", "Finland"], "France": ["França", "France"],
    "Germany": ["Alemanha", "Germany"], "Greece": ["Grécia", "Greece"],
    "Ireland": ["Irlanda", "Ireland"], "Italy": ["Itália", "Italy"],
    "Netherlands": ["Países Baixos", "Netherlands"], "Norway": ["Noruega", "Norway"],
    "Poland": ["Polónia", "Poland"], "Portugal": ["Portugal", "Portugal"],
    "Romania": ["Roménia", "Romania"], "Spain": ["Espanha", "Spain"],
    "Sweden": ["Suécia", "Sweden"], "Switzerland": ["Suíça", "Switzerland"],
    "United Kingdom of Great Britain and Northern Ireland": ["Reino Unido", "United Kingdom"],
  },
  EdLevel: {
    "Desconhecido": ["Prefiro não indicar", "Prefer not to say"],
    "Primary/elementary school": ["Ensino básico", "Primary school"],
    "Secondary school (e.g. American high school, German Realschule or Gymnasium, etc.)": ["Ensino secundário", "Secondary school"],
    "Some college/university study without earning a degree": ["Universidade, sem concluir", "Some college, no degree"],
    "Associate degree (A.A., A.S., etc.)": ["Curso técnico superior", "Associate degree"],
    "Bachelor’s degree (B.A., B.S., B.Eng., etc.)": ["Licenciatura", "Bachelor's degree"],
    "Master’s degree (M.A., M.S., M.Eng., MBA, etc.)": ["Mestrado", "Master's degree"],
    "Professional degree (JD, MD, Ph.D, Ed.D, etc.)": ["Doutoramento", "Doctorate"],
    "Other (please specify):": ["Outra", "Other"],
  },
  RemoteWork: {
    "Desconhecido": ["Prefiro não indicar", "Prefer not to say"],
    "Remote": ["Remoto", "Remote"],
    "Hybrid (some in-person, leans heavy to flexibility)": ["Híbrido, mais remoto", "Hybrid, mostly remote"],
    "Hybrid (some remote, leans heavy to in-person)": ["Híbrido, mais presencial", "Hybrid, mostly in-office"],
    "In-person": ["Presencial", "In-office"],
    "Your choice (very flexible, you can come in when you want or just as needed)": ["Flexível, à escolha", "Flexible, your choice"],
  },
  DevType: {
    "Developer, full-stack": ["Full-stack developer", "Full-stack developer"],
    "Developer, back-end": ["Back-end developer", "Back-end developer"],
    "Developer, front-end": ["Front-end developer", "Front-end developer"],
    "Developer, mobile": ["Mobile developer", "Mobile developer"],
    "Developer, desktop or enterprise applications": ["Aplicações desktop / empresariais", "Desktop / enterprise developer"],
    "Developer, embedded applications or devices": ["Sistemas embebidos", "Embedded developer"],
    "Developer, game or graphics": ["Jogos / gráficos", "Game / graphics developer"],
    "Developer, QA or test": ["QA / testes", "QA / test developer"],
    "Developer, AI apps or physical AI": ["Aplicações de IA", "AI apps developer"],
    "AI/ML engineer": ["Engenheiro de IA / ML", "AI / ML engineer"],
    "Data engineer": ["Engenheiro de dados", "Data engineer"],
    "Data scientist": ["Data scientist", "Data scientist"],
    "Data or business analyst": ["Analista de dados / negócio", "Data / business analyst"],
    "Database administrator or engineer": ["Administrador de bases de dados", "Database administrator"],
    "DevOps engineer or professional": ["DevOps", "DevOps engineer"],
    "Cloud infrastructure engineer": ["Engenheiro de cloud", "Cloud infrastructure engineer"],
    "System administrator": ["Administrador de sistemas", "System administrator"],
    "Cybersecurity or InfoSec professional": ["Cibersegurança", "Cybersecurity"],
    "Architect, software or solutions": ["Arquiteto de software", "Software / solutions architect"],
    "Engineering manager": ["Engineering manager", "Engineering manager"],
    "Product manager": ["Product manager", "Product manager"],
    "Project manager": ["Gestor de projeto", "Project manager"],
    "UX, Research Ops or UI design professional": ["UX / UI designer", "UX / UI designer"],
    "Support engineer or analyst": ["Suporte técnico", "Support engineer"],
    "Applied scientist": ["Cientista aplicado", "Applied scientist"],
    "Academic researcher": ["Investigador académico", "Academic researcher"],
    "Financial analyst or engineer": ["Analista financeiro", "Financial analyst"],
    "Founder, technology or otherwise": ["Fundador", "Founder"],
    "Senior executive (C-suite, VP, etc.)": ["Executivo (C-level, VP)", "Senior executive (C-suite, VP)"],
    "Student": ["Estudante", "Student"],
    "Other (please specify):": ["Outra", "Other"],
  },
};
const HIDDEN = new Set(["Retired"]); // não faz sentido estimar salário para reformados
const DEFAULTS = { country: "Portugal", years: 3, dev_type: "Developer, full-stack",
                   ed_level: "Desconhecido", remote_work: "Desconhecido" };

// ---------- Estado ----------
const $ = (s) => document.querySelector(s);
const form = $("#form");
const state = {
  lang: pick("lang", ["pt", "en"], navigator.language?.startsWith("pt") ? "pt" : "en"),
  currency: pick("currency", ["EUR", "USD"], "EUR"),
  options: null, meta: { usd_para_eur: 0.87, mae_usd: 26233 },
  langs: new Set(["JavaScript", "TypeScript", "Python", "Java", "SQL"]),
  result: null, curve: null, shown: 0,
};

function pick(key, allowed, fallback) {
  try { const v = localStorage.getItem(key); if (allowed.includes(v)) return v; } catch {}
  return fallback;
}
function save(key, value) { try { localStorage.setItem(key, value); } catch {} }
const t = () => TEXT[state.lang];

// ---------- Formatação ----------
function money(usd, { compact = false } = {}) {
  const value = state.currency === "EUR" ? usd * state.meta.usd_para_eur : usd;
  const locale = state.lang === "pt" ? "pt-PT" : "en-GB";
  if (compact) {
    return new Intl.NumberFormat(locale, { style: "currency", currency: state.currency,
      notation: "compact", maximumFractionDigits: 0 }).format(value);
  }
  // Arredonda às centenas: mais precisão que isto seria fingir exatidão
  // useGrouping "always": em pt-PT, sem isto, 2900 € não leva espaço mas 35 100 € leva
  return new Intl.NumberFormat(locale, { style: "currency", currency: state.currency,
    maximumFractionDigits: 0, useGrouping: "always" }).format(Math.round(value / 100) * 100);
}
const label = (col, value) => LABELS[col]?.[value]?.[state.lang === "pt" ? 0 : 1] ?? value;

// ---------- Construção do formulário ----------
function fillSelect(name, col) {
  const select = form.elements[name];
  const current = select.value || DEFAULTS[name];
  const known = Object.keys(LABELS[col] ?? {});
  const values = state.options[col].filter((v) => !HIDDEN.has(v));
  // Países por ordem alfabética do nome traduzido; o resto pela ordem definida em LABELS
  values.sort(col === "Country"
    ? (a, b) => label(col, a).localeCompare(label(col, b), state.lang)
    : (a, b) => (known.indexOf(a) + 1 || 999) - (known.indexOf(b) + 1 || 999));
  select.replaceChildren(...values.map((v) => new Option(label(col, v), v)));
  select.value = values.includes(current) ? current : values[0];
}

function buildChips() {
  $("#langs").replaceChildren(...state.options.langs.map((lang) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip"; b.textContent = lang;
    b.setAttribute("aria-pressed", state.langs.has(lang));
    b.addEventListener("click", () => {
      state.langs.has(lang) ? state.langs.delete(lang) : state.langs.add(lang);
      b.setAttribute("aria-pressed", state.langs.has(lang));
      update();
    });
    return b;
  }));
}

function applyText() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const v = t()[el.dataset.i18n];
    if (typeof v === "string") el.textContent = v;
  });
  document.querySelectorAll("[data-i18n-title]").forEach((el) => {
    el.title = el.ariaLabel = t()[el.dataset.i18nTitle];
  });
  document.querySelectorAll("[data-lang]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.lang === state.lang));
  document.querySelectorAll("[data-currency]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.currency === state.currency));
  if (state.options) {
    fillSelect("country", "Country"); fillSelect("dev_type", "DevType");
    fillSelect("ed_level", "EdLevel"); fillSelect("remote_work", "RemoteWork");
  }
  $("#years-out").textContent = t().years(+form.elements.years.value);
  render();
}

// ---------- Pedidos à API ----------
let controller;
let timer;
function profile() {
  const f = form.elements;
  return { country: f.country.value, years: +f.years.value, dev_type: f.dev_type.value,
           ed_level: f.ed_level.value, remote_work: f.remote_work.value, langs: [...state.langs] };
}

function update() {
  $("#years-out").textContent = t().years(+form.elements.years.value);
  clearTimeout(timer);
  timer = setTimeout(load, 120); // espera o utilizador parar de arrastar o seletor
}

async function post(path, body, signal) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(body), signal });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

async function load() {
  controller?.abort(); // cancela o pedido anterior se ainda estiver a decorrer
  controller = new AbortController();
  const body = profile();
  $(".result").classList.add("loading");
  try {
    const [result, curve] = await Promise.all([
      post("/predict", body, controller.signal),
      post("/curve", body, controller.signal),
    ]);
    state.result = result; state.curve = curve;
    $("#error").hidden = true;
    render(true);
  } catch (e) {
    if (e.name === "AbortError") return;
    $("#error").textContent = t().error; $("#error").hidden = false;
  } finally {
    $(".result").classList.remove("loading");
  }
}

// ---------- Resultado ----------
function render(animate = false) {
  if (!state.result) return;
  const target = state.result.salario_anual_usd;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (animate && !reduce && state.shown) countTo(state.shown, target);
  else paintAmount(target);
  state.shown = target;
  $("#margin").textContent = t().margin(money(state.meta.mae_usd));
  drawChart();
}

function paintAmount(usd) {
  $("#annual").textContent = money(usd);
  $("#monthly").textContent = money(usd / 12);
}

let raf;
function countTo(from, to) {
  cancelAnimationFrame(raf);
  const start = performance.now(), dur = 350;
  const step = (now) => {
    const k = Math.min(1, (now - start) / dur), ease = 1 - (1 - k) ** 3;
    paintAmount(from + (to - from) * ease);
    if (k < 1) raf = requestAnimationFrame(step);
  };
  raf = requestAnimationFrame(step);
}

// ---------- Gráfico (SVG feito à mão) ----------
const SVG = "http://www.w3.org/2000/svg";
function el(name, attrs, parent) {
  const n = document.createElementNS(SVG, name);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  parent?.appendChild(n);
  return n;
}

// Passo "redondo" para o eixo (1, 2, 2.5 ou 5 × potência de 10), para ~4 linhas de grelha
function niceStep(max) {
  const raw = max / 4, p = 10 ** Math.floor(Math.log10(raw));
  return p * [1, 2, 2.5, 5, 10].find((m) => m * p >= raw);
}

function drawChart() {
  const box = $("#chart");
  if (!state.curve) return;
  const { anos, salario_anual_usd: ys } = state.curve;
  const rate = state.currency === "EUR" ? state.meta.usd_para_eur : 1;
  // Largura real do contentor: assim o texto do gráfico tem sempre o mesmo tamanho
  const W = Math.max(280, box.clientWidth), H = W < 420 ? 190 : 220, L = 52, R = 10, T = 12, B = 26;
  const step = niceStep(Math.max(...ys) * rate);
  const maxY = Math.ceil((Math.max(...ys) * rate * 1.05) / step) * step;
  const x = (a) => L + (a / anos.at(-1)) * (W - L - R);
  const y = (v) => T + (1 - (v * rate) / maxY) * (H - T - B);

  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": t().curveTitle });
  for (let v = 0; v <= maxY + 1e-6; v += step) {
    const yy = y(v / rate);
    el("line", { class: "gridline", x1: L, x2: W - R, y1: yy, y2: yy }, svg);
    el("text", { class: "tick", x: L - 8, y: yy + 4, "text-anchor": "end" }, svg).textContent =
      money(v / rate, { compact: true });
  }
  for (const a of (W < 420 ? [0, 10, 20, 30] : [0, 5, 10, 15, 20, 25, 30])) {
    el("text", { class: "tick", x: x(a), y: H - 6, "text-anchor": "middle" }, svg).textContent = t().yearsShort(a);
  }
  const pts = anos.map((a, i) => `${x(a).toFixed(1)},${y(ys[i]).toFixed(1)}`);
  el("path", { class: "area", d: `M${x(0)},${H - B} L${pts.join(" L")} L${x(anos.at(-1))},${H - B} Z` }, svg);
  el("path", { class: "line", d: `M${pts.join(" L")}` }, svg);

  // Ponto "tu" nos anos escolhidos
  const yrs = +form.elements.years.value;
  const i = anos.indexOf(yrs);
  if (i >= 0) {
    el("line", { class: "you-line", x1: x(yrs), x2: x(yrs), y1: y(ys[i]), y2: H - B }, svg);
    el("circle", { class: "you", cx: x(yrs), cy: y(ys[i]), r: 6 }, svg);
  }

  // Tooltip ao passar o rato
  const hover = el("circle", { class: "hover-dot", r: 4, visibility: "hidden" }, svg);
  const tip = document.createElement("div");
  tip.className = "tooltip"; tip.hidden = true;
  svg.addEventListener("pointermove", (ev) => {
    const rect = svg.getBoundingClientRect();
    const px = ((ev.clientX - rect.left) / rect.width) * W;
    const a = Math.max(0, Math.min(anos.at(-1), Math.round(((px - L) / (W - L - R)) * anos.at(-1))));
    const j = anos.indexOf(a);
    hover.setAttribute("cx", x(a)); hover.setAttribute("cy", y(ys[j])); hover.setAttribute("visibility", "visible");
    tip.hidden = false;
    tip.textContent = `${t().years(a)} · ${money(ys[j])}`;
    tip.style.left = `${(x(a) / W) * 100}%`;
    tip.style.top = `${(y(ys[j]) / H) * rect.height}px`;
  });
  svg.addEventListener("pointerleave", () => { hover.setAttribute("visibility", "hidden"); tip.hidden = true; });

  box.replaceChildren(svg, tip);
}

// ---------- Eventos ----------
form.addEventListener("input", update);
form.addEventListener("submit", (e) => e.preventDefault());
document.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => {
  state.lang = b.dataset.lang; save("lang", state.lang); applyText();
}));
document.querySelectorAll("[data-currency]").forEach((b) => b.addEventListener("click", () => {
  state.currency = b.dataset.currency; save("currency", state.currency); applyText();
}));
$("#theme").addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.dataset.theme
    ? root.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  save("theme", root.dataset.theme);
});

// Redesenha o gráfico quando a largura muda (rodar o telemóvel, redimensionar a janela)
let lastWidth = 0;
new ResizeObserver(([entry]) => {
  const w = Math.round(entry.contentRect.width);
  if (w !== lastWidth) { lastWidth = w; drawChart(); }
}).observe($("#chart"));

// ---------- Arranque ----------
(async function init() {
  form.elements.years.value = DEFAULTS.years;
  applyText();
  try {
    const [options, meta] = await Promise.all([
      fetch("/options").then((r) => r.json()),
      fetch("/meta").then((r) => r.json()),
    ]);
    state.options = options; state.meta = meta;
    buildChips();
    applyText();
    load();
  } catch {
    $("#error").textContent = t().error; $("#error").hidden = false;
  }
})();
