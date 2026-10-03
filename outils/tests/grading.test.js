// Tests du moteur de correction sur la configuration réelle du sujet.
// Usage : node outils/tests/grading.test.js
"use strict";
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const html = fs.readFileSync(path.join(__dirname, "..", "..", "index.html"), "utf8");
const src = html.slice(html.indexOf("/*GRADING-START*/"), html.indexOf("/*GRADING-END*/"));
const Grading = new Function("module", src + "\nreturn Grading;")(undefined);
const { QCFG } = JSON.parse(fs.readFileSync(path.join(__dirname, "config.json"), "utf8"));

let n = 0, fails = 0;
function expect(id, answer, score) {
  n++;
  const r = Grading.grade(answer, QCFG[id].grader);
  const got = r.invalid ? "invalid" : r.score;
  if (got !== score) { fails++; console.log(`ÉCHEC ${QCFG[id].label} « ${answer} » : attendu ${score}, obtenu ${got}`); }
}
const fr2 = (v) => v.toFixed(2).replace(".", ",");

// --- toutes les questions numériques : juste, sans unité, unité fausse, valeur fausse, convertie
const OTHER = { "m": "kg", "daN": "kg", "daN·m": "daN" };
const CONV = { "m": ["mm", 1000], "daN": ["N", 10], "daN·m": ["N.m", 10] };
for (const [id, q] of Object.entries(QCFG)) {
  const g = q.grader;
  if (g.type !== "num") continue;
  const v = Math.round(g.value * 100) / 100;
  if (g.unit) {
    const u = g.unit.label;
    expect(id, `${fr2(v)} ${u}`, 1);
    expect(id, `${v.toFixed(2)}${u}`, 1);
    expect(id, fr2(v), 0.5);
    expect(id, `${fr2(v)} ${OTHER[u]}`, 0.5);
    expect(id, `${fr2(v * 1.1 + 1)} ${u}`, 0);
    expect(id, `${fr2(-v - (v === 0 ? 5 : 0))} ${u}`, v === 0 ? 0 : 0);
    const [cu, f] = CONV[u];
    expect(id, `${fr2(v * f)} ${cu}`, 1);
    expect(id, fr2(v * f) === fr2(v) ? `${fr2(v)}` : `${fr2(v * f)}`, v === 0 ? 0.5 : 0);
  } else {
    expect(id, fr2(v), 1);
    expect(id, v.toFixed(2), 1);
    expect(id, fr2(-v), 0);
  }
}

// --- cas limites ciblés
expect("q1_3", "x_B = 3,51 m", 1);
expect("q1_3", "3510 mm", 1);
expect("q1_3", "3510", 0);
expect("q1_3", "3,51 mètres", 1);
expect("q1_3", "3.51 M", 1);
expect("q1_7", "0,45 m", 0);
expect("q1_10", "-0,24 m", 1);
expect("q1_10", "−0,24 m", 1);
expect("q1_10", "0 m", 0);
expect("q1_10", "0,24 m", 0);
expect("q2_2", "-500 daN", 1);
expect("q2_2", "500 daN", 0);
expect("q2_2", "−5000 N", 1);
expect("q2_3", "-1470 daN.m", 1);
expect("q2_3", "-1 470 daN·m", 1);
expect("q2_3", "-1470 m.daN", 1);
expect("q2_3", "-1470 daN", 0.5);
expect("q2_3", "-14700 N·m", 1);
expect("q2_4", "-3,27", 1);
expect("q2_4", "3,27", 0);
expect("q2_6", "353,37 daN", 1);   // arrondis intermédiaires (c = 4,16)
expect("q2_6", "353 daN", 1);
expect("q2_6", "360 daN", 0);
expect("q2_6", "3,5301e2 daN", 1);
expect("q2_10", "146,63 daN", 1);
expect("q4_5", "0 daN", 1);
expect("q4_5", "0", 0.5);
expect("q4_5", "0 N", 1);
expect("q4_7", "300,21 daN.m", 0);  // FA pris vertical : erreur de lecture de la cote 240
expect("q4_8", "-1856,2 daN.m", 1);
expect("q4_10", "-919,08 daN", 1);
expect("q4_10", "-849,71 daN", 0);
expect("q4_10", "-746,27 daN", 0);
expect("q4_10", "919,08 daN", 0);
expect("q5_2", "2,94 m", 0);
expect("q5_5", "1,21 m", 0);

expect("q1_1", "2", 1);
expect("q1_1", "deux forces", 1);
expect("q1_1", "Deux : B3/2 et D1/2", 1);
expect("q1_1", "3", 0);
expect("q1_1", "trois", 0);
expect("q1_2", "(BD)", 1);
expect("q1_2", "la droite BD", 1);
expect("q1_2", "droite (DB)", 1);
expect("q1_2", "selon l'axe du tirant", 1);
expect("q1_2", "perpendiculaire à BD", 0);
expect("q1_2", "verticale", 0);
expect("q2_1", "3", 1);
expect("q2_1", "trois actions", 1);
expect("q2_1", "Trois : A1/3, B2/3 et M6/3", 1);
expect("q2_1", "2", 0);
expect("q3_5", "traction", 1);
expect("q3_5", "Traction", 1);
expect("q3_5", "tracion", 1);
expect("q3_5", "il est tendu", 1);
expect("q3_5", "compression", 0);
expect("q3_5", "flexion", 0);
expect("q5_1", "non", 1);
expect("q5_1", "Non, il faut 3,18 m", 1);
expect("q5_1", "oui", 0);
expect("q5_1", "peut-être", "invalid");
expect("q5_6", "liaison linéaire annulaire", 1);
expect("q5_6", "Lineaire annulaire d'axe y", 1);
expect("q5_6", "pivot glissant", 1);
expect("q5_6", "la colonne peut coulisser verticalement dans le support", 1);
expect("q5_6", "le support ne transmet aucun effort vertical", 1);
expect("q5_6", "effort radial uniquement", 1);
expect("q5_6", "c'est un encastrement", 0);
expect("q5_6", "parce que", 0);

console.log(`${n - fails} / ${n} cas conformes`);
process.exit(fails ? 1 : 0);
