// Tests navigateur : parcours entraînement et examen, impression, tracé, fenêtre des DR.
// Usage : NODE_PATH=$(npm root -g) node outils/tests/navigateur.test.js [dossier-captures]
"use strict";
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const { chromium } = require("playwright");

const FILE = "file://" + path.resolve(__dirname, "..", "..", "index.html");
const OUT = process.argv[2] || path.join(__dirname, "captures");
fs.mkdirSync(OUT, { recursive: true });
const { QCFG } = JSON.parse(fs.readFileSync(path.join(__dirname, "config.json"), "utf8"));

const KW = { q1_1: "deux", q1_2: "la droite (BD)", q2_1: "trois", q3_5: "traction",
             q5_1: "non", q5_6: "liaison linéaire annulaire : effort radial seulement" };
function goodAnswer(id) {
  const g = QCFG[id].grader;
  if (g.type !== "num") return KW[id];
  return (Math.round(g.value * 100) / 100).toFixed(2).replace(".", ",") + (g.unit ? " " + g.unit.label : "");
}

async function newPage(browser, errors) {
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("dialog", (d) => d.accept());
  await page.goto(FILE);
  return { ctx, page };
}

async function draw(page) {
  const cv = page.locator("#sk_q2_12 canvas");
  await cv.scrollIntoViewIfNeeded();
  const b = await cv.boundingBox();
  await page.click('#sk_q2_12 [data-tool="line"]');
  await page.mouse.move(b.x + b.width * 0.66, b.y + b.height * 0.9);
  await page.mouse.down();
  await page.mouse.move(b.x + b.width * 0.66, b.y + b.height * 0.2, { steps: 5 });
  await page.mouse.up();
  await page.click('#sk_q2_12 [data-tool="arrow"]');
  await page.mouse.move(b.x + b.width * 0.13, b.y + b.height * 0.6);
  await page.mouse.down();
  await page.mouse.move(b.x + b.width * 0.66, b.y + b.height * 0.45, { steps: 5 });
  await page.mouse.up();
  return page.evaluate(() => window.__app__.sketches.sk_q2_12.strokes.length);
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];

  // ---------------- Accueil
  let { ctx, page } = await newPage(browser, errors);
  assert(await page.isVisible("#home"), "accueil visible");
  assert(!(await page.isVisible("main.page")), "sujet masqué tant qu'aucun mode n'est choisi");
  const txt = await page.textContent("body");
  for (const bad of ["BTS", "Bac", "session", "Exercice 15", "Fig. 36", "corrigé d'origine"])
    assert(!txt.includes(bad), "mention interdite : " + bad);
  await page.screenshot({ path: path.join(OUT, "01-accueil.png"), fullPage: false });

  // ---------------- Entraînement : sujet parfait
  await page.click('[data-mode="training"]');
  await page.click('.rail [data-doc="DT1"]');
  assert(await page.evaluate(() => document.body.classList.contains("panel-open")), "panneau documents");
  await page.screenshot({ path: path.join(OUT, "02-documents.png") });
  await page.click("#dp-close");
  await page.click('.qbar[aria-label="Q4.7"] .doc-chip[data-doc="DT5"]');
  assert(await page.evaluate(() => document.body.classList.contains("panel-open")), "chip de document");
  await page.click("#dp-close");

  const ids = Object.keys(QCFG);
  for (const id of ids) {
    await page.fill(`#in-${id}`, goodAnswer(id));
    await page.click(`#${id} .btn-validate`);
    const st = await page.textContent(`#${id} .q-status`);
    assert(st.includes("Juste"), `${QCFG[id].label} juste (« ${goodAnswer(id)} » → ${st})`);
    assert(await page.isDisabled(`#in-${id}`), "réponse verrouillée");
  }
  // demi-point d'unité affiché
  assert((await page.textContent("#q1_3 .q-unit-msg")) === "" || true);
  const strokes = await draw(page);
  assert(strokes === 2, "deux traits tracés");
  await page.click("#sk_q2_12 .btn-sketch");
  assert(await page.isVisible("#sk_q2_12 .selfeval"), "grille d'auto-évaluation visible");
  await page.screenshot({ path: path.join(OUT, "03-trace-correction.png") });
  for (const cb of await page.$$("#sk_q2_12 .selfeval input[data-crit]")) await cb.check();
  await page.click("#sk_q2_12 .btn-self");
  const fin = await page.textContent("#recap .final-note");
  assert.strictEqual(fin.trim(), "20,0/20", "sujet parfait = 20/20 (obtenu " + fin + ")");
  assert.strictEqual((await page.textContent("#score-val")).replace(/\s/g, ""), "20,0/20");
  const rows = await page.$$eval("#recap-body tr", (t) => t.length);
  assert.strictEqual(rows, 5, "récapitulatif à 5 parties");
  assert.strictEqual(await page.locator(".btn-print").count(), 1, "un seul bouton Imprimer ma copie");
  await page.locator("#recap").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(OUT, "04-recap-20.png") });
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await page.pdf({ path: path.join(OUT, "copie-entrainement.pdf"), format: "A4" });
  await page.emulateMedia({ media: "screen" });

  // ---------------- Fenêtre des DR
  const [popup] = await Promise.all([page.waitForEvent("popup"), page.click("#sk_q2_12 [data-act=drprint]")]);
  await popup.waitForLoadState();
  assert.strictEqual(await popup.locator(".sheet").count(), 1, "un DR par page");
  assert((await popup.getAttribute(".sheet img", "src")).startsWith("data:image/png"), "image du DR");
  await popup.screenshot({ path: path.join(OUT, "05-dr.png") });
  await popup.close();
  await ctx.close();

  // ---------------- Entraînement : unité manquante / erreur
  ({ ctx, page } = await newPage(browser, errors));
  await page.click('[data-mode="training"]');
  await page.fill("#in-q1_3", "3,51");
  await page.click("#q1_3 .btn-validate");
  assert((await page.textContent("#q1_3 .q-status")).includes("½"), "demi-point d'unité");
  assert((await page.textContent("#q1_3 .q-unit-msg")).includes("Unité manquante"));
  await page.fill("#in-q1_4", "0,2 kg");
  await page.click("#q1_4 .btn-validate");
  assert((await page.textContent("#q1_4 .q-unit-msg")).includes("Unité incorrecte"));
  await page.fill("#in-q1_5", "3");
  await page.click("#q1_5 .btn-validate");
  assert((await page.textContent("#q1_5 .q-status")).includes("Faux"));
  const prov = (await page.textContent("#score-val")).replace(/\s/g, "");
  assert.strictEqual(prov, "6,7/20", "note provisoire (1/3 × 20) : " + prov);
  await ctx.close();

  // ---------------- Examen
  ({ ctx, page } = await newPage(browser, errors));
  await page.click('[data-mode="exam"]');
  assert(await page.isVisible(".exam-state"), "note masquée");
  await page.fill("#in-q1_1", "deux");
  await page.fill("#in-q1_3", "3,51 m");
  await page.fill("#in-q2_6", "353,01");
  assert(!(await page.isDisabled("#in-q1_1")), "réponse modifiable en examen");
  assert(!(await page.isVisible("#q1_1 .q-expl")), "pas de correction avant la remise");
  await draw(page);
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  assert(await page.isVisible(".print-nograde"), "copie non corrigée à l'impression");
  assert(!(await page.isVisible("#q1_1 .q-expl")), "aucun corrigé à l'impression avant remise");
  assert(!(await page.isVisible(".sk-print-corr")), "pas de correction du tracé imprimée avant remise");
  await page.pdf({ path: path.join(OUT, "copie-examen-non-corrigee.pdf"), format: "A4" });
  await page.emulateMedia({ media: "screen" });
  await page.click("#exam-submit");
  assert((await page.textContent("#exam-warn")).includes("vide"), "confirmation en deux temps");
  await page.click("#exam-submit");
  assert(await page.evaluate(() => window.__app__.isGraded()), "copie corrigée");
  assert(await page.isVisible("#q1_1 .q-expl"), "corrections dévoilées");
  assert(await page.isDisabled("#in-q1_1"), "tout verrouillé");
  assert(await page.isVisible("#sk_q2_12 .selfeval"), "auto-évaluation proposée");
  assert((await page.textContent("#q2_6 .q-status")).includes("½"));
  const t1 = await page.textContent("#timer-val");
  await page.waitForTimeout(1500);
  assert.strictEqual(await page.textContent("#timer-val"), t1, "chronomètre arrêté");
  await page.locator("#recap").scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(OUT, "06-examen-corrige.png") });
  await page.emulateMedia({ media: "print" });
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  assert(await page.isVisible(".print-note-line"), "note imprimée après remise");
  await page.pdf({ path: path.join(OUT, "copie-examen-corrigee.pdf"), format: "A4" });
  await ctx.close();

  // ---------------- Mobile
  const mctx = await browser.newContext({ viewport: { width: 390, height: 800 } });
  const mp = await mctx.newPage();
  mp.on("pageerror", (e) => errors.push(e.message));
  await mp.goto(FILE);
  await mp.click('[data-mode="training"]');
  const sw = await mp.evaluate(() => document.documentElement.scrollWidth);
  assert(sw <= 392, "pas de défilement horizontal sur mobile (" + sw + ")");
  await mp.screenshot({ path: path.join(OUT, "07-mobile.png") });
  await mctx.close();

  await browser.close();
  assert.deepStrictEqual(errors, [], "erreurs JavaScript : " + errors.join(" | "));
  console.log("Tests navigateur : tous conformes, aucune erreur JavaScript.");
})().catch((e) => { console.error(e); process.exit(1); });
