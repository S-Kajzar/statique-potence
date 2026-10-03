#!/usr/bin/env python3
"""Génère ../index.html à partir du gabarit et du contenu du sujet.

Le bloc <style>, le moteur Grading et le moteur applicatif sont repris tels
quels depuis gabarit-exercice-interactif.html ; seuls les paramètres propres
au sujet (CONSEIL_MIN, DECOR, DR_NAMES, texte de la fenêtre des DR) sont
remplacés. Usage : python3 outils/construire.py
"""
import base64
import json
import math
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "index.html")
GABARIT = open(os.path.join(ICI, "gabarit-exercice-interactif.html"), encoding="utf-8").read()


def img(nom):
    mime = "image/png" if nom.endswith(".png") else "image/jpeg"
    with open(os.path.join(ICI, "images", nom), "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def idim(nom):
    """Largeur et hauteur d'une image PNG (en-tête IHDR) ou JPEG (marqueurs SOF)."""
    with open(os.path.join(ICI, "images", nom), "rb") as f:
        d = f.read()
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")
    i = 2
    while i < len(d):
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if m in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(d[i + 7:i + 9], "big"), int.from_bytes(d[i + 5:i + 7], "big")
        i += 2 + int.from_bytes(d[i + 2:i + 4], "big")
    raise ValueError(nom)


# ===================================================================
#  Résultats de référence (recalculés, voir NOTE-LIVRAISON.md)
# ===================================================================
TAN = math.tan(math.radians(73))
XB, YB, XM, XD = 3.51, 0.20, 2.94, 0.21
DY = (XB - XD) / TAN
YD = YB + DY
K = -TAN
C = XB - YB * K
BY = 1470 / C
BX = K * BY
NB = math.hypot(BX, BY)
AX, AY = -BX, 500 - BY
NA = math.hypot(AX, AY)
MFA = 0.24 * (-AY) - 0.26 * (-AX)
FDY = YD + 0.26
MFD = 0.45 * (-BY) - FDY * (-BX)
MFE = -(MFA + MFD)
EX = -MFE / 1.73
FX, FY = -(-AX - BX + EX), 500.0
NF = math.hypot(FX, FY)


def fr(x, d=2):
    s = f"{abs(x):,.{d}f}".replace(",", " ").replace(".", ",")
    return ("−" if x < 0 else "") + s


def V(l, sub=""):
    return f'<span class="vec">{l}</span>' + (f"<sub>{sub}</sub>" if sub else "")


def calc(*lignes):
    return "<p><code>" + "<br>".join(lignes) + "</code></p>"


# ===================================================================
#  Unités
# ===================================================================
U_M = {"label": "m", "accept": ["m", "metre", "metres", "meter", "meters"]}
U_MM = {"label": "mm", "accept": ["mm", "millimetre", "millimetres"]}
U_DAN = {"label": "daN", "accept": ["dan", "decanewton", "decanewtons"]}
U_N = {"label": "N", "accept": ["n", "newton", "newtons"]}
U_DANM = {"label": "daN·m", "accept": ["danm", "mdan", "decanewtonmetre", "decanewtonmetres",
                                         "decanewtonsmetre", "decanewtonsmetres", "metredecanewton"]}
U_NM = {"label": "N·m", "accept": ["nm", "mn", "newtonmetre", "newtonmetres", "newtonsmetre", "newtonsmetres"]}

CONV = {"m": (U_M, U_MM, 1000), "daN": (U_DAN, U_N, 10), "daN·m": (U_DANM, U_NM, 10)}

H_UNIT = "Arrondir au centième. Saisis la valeur <strong>avec son unité</strong> : l'unité vaut la moitié des points de la question."
H_FORCE = ("Arrondir au centième (une tolérance de 0,5 % couvre les arrondis intermédiaires). "
           "Saisis la valeur <strong>avec son unité</strong> : l'unité vaut la moitié des points de la question.")
H_SANS = "Arrondir au centième. Nombre sans unité."


# ===================================================================
#  Contenu du sujet
# ===================================================================
PARTS = [
    {"num": "1", "title": "Lire la figure et modéliser", "minutes": 25, "duration": "25 min"},
    {"num": "2", "title": "Isolement de la flèche (3)", "minutes": 35, "duration": "35 min"},
    {"num": "3", "title": "Le tirant (2) : transmission vers la colonne", "minutes": 10, "duration": "10 min"},
    {"num": "4", "title": "Isolement de la colonne (1)", "minutes": 30, "duration": "30 min"},
    {"num": "5", "title": "Vérification globale et regard critique", "minutes": 20, "duration": "20 min"},
]

QCFG = {}
SKCFG = {}
CONTENU = {p["num"]: [] for p in PARTS}   # blocs HTML par partie


def bloc_q(qid, label, stem, hint, expected, why, docs):
    chips = "".join(f'<button type="button" class="doc-chip" data-doc="{d}" aria-pressed="false">{d}</button>' for d in docs)
    docs_html = f"Documents à consulter : {chips}" if docs else "Aucun document nécessaire"
    return f"""
      <div class="qbar" role="group" aria-label="{label}"><div class="qb-num">{label}</div><div class="qb-docs">{docs_html}</div><div class="qb-ans">Répondre : ci-dessous</div></div>
        <div class="q" id="{qid}" data-q="{qid}">
          <p class="q-stem"><span class="q-num">{label}</span> <strong>{stem}</strong></p>
          <p class="q-hint" id="h-{qid}">{hint}</p>
          <div class="q-row">
            <input type="text" class="q-input" id="in-{qid}" aria-label="Réponse {label}" aria-describedby="h-{qid}" autocomplete="off" autocapitalize="off" spellcheck="false">
            <button type="button" class="btn btn-validate">Valider</button>
            <span class="q-status" aria-live="polite"></span>
            <span class="print-only pstat">Non validée : comptée fausse</span>
          </div>
          <p class="q-msg" role="alert"></p>
          <div class="q-expl" hidden>
            <p class="q-unit-msg" hidden></p>
            <p class="q-expected"><span>Réponse attendue :</span> {expected}</p>
            <div class="q-why">{why}</div>
          </div>
        </div>"""


def _add(part, n, grader, stem, hint, expected, why, docs, pts=1):
    qid = f"q{part}_{n}"
    label = f"Q{part}.{n}"
    QCFG[qid] = {"label": label, "part": part, "pts": pts, "grader": grader}
    CONTENU[part].append(bloc_q(qid, label, stem, hint, expected, why, docs))
    return qid


def num(part, n, stem, value, unit, expected, why, docs, absTol=None, relTol=None, hint=None):
    g = {"type": "num", "value": round(value, 6)}
    if absTol is not None:
        g["absTol"] = absTol
    if relTol is not None:
        g["relTol"] = relTol
    if unit:
        u, u2, f = CONV[unit]
        g["unit"] = u
        var = {"value": round(value * f, 6), "unit": u2, "strictUnit": True}
        if absTol is not None:
            var["absTol"] = round(absTol * f, 6)
        if relTol is not None:
            var["relTol"] = relTol
        g["variants"] = [var]
    if hint is None:
        hint = (H_FORCE if relTol else H_UNIT) if unit else H_SANS
    return _add(part, n, g, stem, hint, expected, why, docs)


def kw(part, n, stem, any_, forbid, expected, why, docs, hint):
    return _add(part, n, {"type": "kw", "any": any_, "forbid": forbid}, stem, hint, expected, why, docs)


def yesno(part, n, stem, value, expected, why, docs):
    return _add(part, n, {"type": "yesno", "value": value}, stem,
                "Commence ta réponse par « oui » ou « non ».", expected, why, docs)


def intro(part, html):
    CONTENU[part].append("\n      " + html)


# ------------------------------------------------------------- Partie 1
intro("1", f"""<p>Avant tout calcul, on met la géométrie au propre dans le repère (A, <var>x</var>, <var>y</var>) et on identifie le solide qui va donner la première information : le tirant.</p>
      <div class="data"><p class="data-title">Données</p><ul class="cols">
        <li>Charge : <var>P</var> = 500 daN, verticale vers le bas, appliquée en <var>M</var>.</li>
        <li>Poids propres des solides négligés.</li>
        <li>Repère direct d'origine <var>A</var> : <var>x</var> horizontal vers l'extérieur du mur, <var>y</var> vertical vers le haut.</li>
        <li>Cotes en millimètres sur les documents ; résultats en m, daN et daN·m.</li>
        <li>Les cotes 240 et 450 sont prises depuis l'<strong>axe vertical EF</strong> de la colonne.</li>
        <li>Le tirant (BD) fait 73° avec la verticale.</li></ul></div>""")

kw("1", 1, "Le tirant BD (2) est articulé en D sur la colonne et en B sur la flèche. Son poids est négligé et aucune autre action ne s'applique sur lui. À combien d'actions mécaniques extérieures est-il soumis ?",
   [[["2", "deux"]]], ["3", "trois", "4", "quatre"], "2 (deux actions, en B et en D)",
   f"<p>Deux actions seulement : {V('B','3/2')} exercée par la flèche en B, et {V('D','1/2')} exercée par la colonne en D.</p>"
   "<p>Le tirant est donc un <strong>solide soumis à deux forces</strong>. Le principe fondamental de la statique impose alors que ces deux forces soient <strong>de même intensité, de sens opposés et portées par la droite (BD)</strong> qui joint leurs points d'application. C'est la seule information exploitable au départ : elle donne la <em>direction</em> de l'action en B, ce qui rend l'isolement de la flèche résoluble.</p>",
   ["DT3"], "Réponds par un nombre, en chiffres ou en lettres.")

kw("1", 2, f"En déduire la droite d'action de l'action mécanique {V('B','2/3')} exercée en B par le tirant (2) sur la flèche (3).",
   [[["bd", "db"]], [["b"], ["d"]], [["axe"], ["tirant"]]], ["perpendiculaire", "normale"], "la droite (BD), axe du tirant",
   f"<p>Puisque (2) est soumis à deux forces, la droite d'action de {V('B','2/3')} est la droite <strong>(BD)</strong>, c'est-à-dire l'axe du tirant.</p>"
   "<p>Sur la figure, cette droite fait <strong>73° avec la verticale</strong>. Le tirant retenant l'extrémité de la flèche, l'action en B sur la flèche est dirigée <strong>de B vers D</strong> : vers le haut et vers le mur.</p>",
   ["DT1", "DT3"], "Nomme la droite support.")

num("1", 3, "Quelle est l'abscisse <var>x</var><sub>B</sub> du point B dans le repère (A, <var>x</var>, <var>y</var>) ?",
    XB, "m", "<var>x</var><sub>B</sub> = 3,51 m",
    "<p>La cote 2 940 mm va de A au point M (crochet du palan), et la cote 570 mm de M à B.</p>"
    + calc("x_B = 2 940 + 570 = 3 510 mm = 3,51 m")
    + "<p>La cote 240 mm ne concerne pas cette distance : elle sépare A de l'axe EF de la colonne, situé de l'autre côté.</p>",
    ["DT1", "DT4"], absTol=0.005)

num("1", 4, "Quelle est l'ordonnée <var>y</var><sub>B</sub> du point B ?",
    YB, "m", "<var>y</var><sub>B</sub> = 0,20 m",
    "<p>L'axe de la flèche passe par A, et l'articulation B est située <strong>200 mm au-dessus</strong> de cet axe (cote verticale à droite de la vue d'ensemble et de la flèche isolée).</p>"
    + calc("y_B = +200 mm = +0,20 m")
    + "<p>Ce petit décalage intervient dans le bras de levier de l'action en B : on ne peut pas traiter la flèche comme une poutre chargée sur un seul axe.</p>",
    ["DT1", "DT4"], absTol=0.005)

num("1", 5, "Quelle est l'abscisse <var>x</var><sub>M</sub> du point M où le palan applique la charge ?",
    XM, "m", "<var>x</var><sub>M</sub> = 2,94 m",
    "<p>Lecture directe de la cote : <strong>2 940 mm</strong> entre A et M.</p>"
    + calc("x_M = 2,94 m ; y_M = 0 (M est sur l'axe de la flèche)"),
    ["DT1", "DT4"], absTol=0.005)

num("1", 6, "Le tirant fait un angle de 73° avec la verticale. Donner la valeur de tan 73°.",
    TAN, None, "tan 73° ≈ 3,27",
    "<p>tan 73° = 3,2709… ≈ 3,27.</p><p>L'angle étant mesuré <strong>depuis la verticale</strong>, la tangente donne le rapport <em>horizontal / vertical</em> :</p>"
    + calc("tan 73° = Δx / Δy")
    + "<p>C'est ce rapport qui reliera les deux composantes de l'action en B.</p>",
    ["DT1"], absTol=0.006)

num("1", 7, "Les cotes 240 et 450 sont toutes deux prises depuis l'axe vertical EF de la colonne : 240 jusqu'à A, 450 jusqu'à D. Quelle est l'abscisse <var>x</var><sub>D</sub> de l'articulation D dans le repère (A, <var>x</var>, <var>y</var>) ?",
    XD, "m", "<var>x</var><sub>D</sub> = 0,21 m",
    "<p>Les deux cotes partent du même trait d'axe EF. L'abscisse de D par rapport à A est donc leur différence :</p>"
    + calc("x_D = 450 − 240 = 210 mm = 0,21 m")
    + "<p><strong>Point de vigilance.</strong> Prendre 0,45 m comme abscisse de D dans le repère d'origine A est une erreur classique : 0,45 m est mesuré depuis l'axe EF, pas depuis A.</p>",
    ["DT1", "DT5"], absTol=0.005)

num("1", 8, "En utilisant l'angle de 73° et les positions de B et de D, calculer l'ordonnée <var>y</var><sub>D</sub> de l'articulation D.",
    YD, "m", "<var>y</var><sub>D</sub> ≈ 1,21 m",
    "<p>Écart horizontal entre D et B :</p>"
    + calc("x_B − x_D = 3,51 − 0,21 = 3,30 m")
    + "<p>Comme l'angle de 73° est pris depuis la verticale, le dénivelé vaut :</p>"
    + calc("Δy = 3,30 / tan 73° = 3,30 / 3,2709 = 1,0089 m", "y_D = y_B + Δy = 0,20 + 1,0089 = 1,2089 ≈ 1,21 m")
    + "<p>D se situe donc à environ 1,21 m <strong>au-dessus de A</strong>, un peu en dessous de E (1,47 m).</p>",
    ["DT1", "DT3"], absTol=0.006)

num("1", 9, "Quelle est la distance FE entre les deux liaisons de la colonne sur le mur ?",
    1.73, "m", "FE = 1,73 m",
    "<p>La cote 1 470 mm est mesurée de E jusqu'à l'axe de la flèche (niveau de A), et la cote 260 mm de ce même axe jusqu'à F, situé <strong>en dessous</strong>.</p>"
    + calc("FE = 1 470 + 260 = 1 730 mm = 1,73 m")
    + "<p>Ces deux cotes s'additionnent parce qu'elles sont prises de part et d'autre de l'axe de la flèche.</p>",
    ["DT1", "DT5"], absTol=0.005)

num("1", 10, "Quelle est l'abscisse <var>x</var><sub>F</sub> du point F dans le repère (A, <var>x</var>, <var>y</var>) ?",
    -0.24, "m", "<var>x</var><sub>F</sub> = −0,24 m",
    "<p>F est sur l'axe EF de la colonne, et A est à <strong>240 mm à droite</strong> de cet axe (côté opposé au mur, vers la charge). F est donc à gauche de A :</p>"
    + calc("x_F = −240 mm = −0,24 m")
    + "<p>A n'est <strong>pas</strong> sur l'axe de la colonne : c'est bien visible sur la vue d'ensemble, où E et F sont alignés sur le trait d'axe vertical alors que l'articulation A est décalée vers la droite. Ce décalage interviendra dans tous les moments pris en F.</p>",
    ["DT1", "DT5"], absTol=0.005)

num("1", 11, "Quelle est l'ordonnée <var>y</var><sub>F</sub> du point F ?",
    -0.26, "m", "<var>y</var><sub>F</sub> = −0,26 m",
    "<p>F est situé <strong>260 mm en dessous</strong> de l'axe de la flèche :</p>"
    + calc("y_F = −0,26 m, donc F(−0,24 ; −0,26) et FA (0,24 ; 0,26)")
    + "<p>Le vecteur FA a donc <strong>deux</strong> composantes non nulles.</p>",
    ["DT1", "DT5"], absTol=0.005)

# ------------------------------------------------------------- Partie 2
intro("2", "<p>La flèche est le seul solide sur lequel une action est entièrement connue (la charge). C'est donc par elle qu'il faut commencer. Le moment en A élimine l'action inconnue en A et laisse une seule inconnue.</p>")

kw("2", 1, "On isole la flèche (3). Combien d'actions mécaniques extérieures s'exercent sur elle ?",
   [[["3", "trois"]]], ["2", "deux", "4", "quatre"], "3 (en A, en B et en M)",
   f"<p>Trois actions : {V('A','1/3')} (colonne en A), {V('B','2/3')} (tirant en B) et {V('M','6/3')} (palan en M).</p>"
   "<p>La flèche est donc un <strong>solide soumis à trois forces</strong> : on connaît entièrement l'une d'elles, la direction d'une deuxième (Q1.2), et rien de la troisième. Le système est résoluble.</p>",
   ["DT4"], "Poids négligé. Réponds par un nombre.")

num("2", 2, f"Le palan (6) est en équilibre sous l'action de la charge et de la flèche. Quelle est la composante suivant <var>y</var> de l'action {V('M','6/3')} exercée par le palan sur la flèche en M ?",
    -500, "daN", "<var>M</var><sub>6/3 y</sub> = −500 daN",
    f"<p>Le palan est soumis au poids de la charge {V('P')} (500 daN vers le bas) et à l'action {V('M','3/6')} de la flèche. Son équilibre impose {V('M','3/6')} = 500 daN vers le haut.</p>"
    "<p>Par le principe des actions réciproques :</p>"
    + calc("M6/3 = −M3/6  →  M6/3 y = −500 daN")
    + "<p>Le palan transmet intégralement la charge à la flèche, vers le bas : d'où le signe négatif. (Le document de la flèche isolée note cette action « = P ».)</p>",
    ["DT2"], absTol=0.5, hint="Attention au signe. Saisis la valeur <strong>avec son unité</strong> : l'unité vaut la moitié des points de la question.")

num("2", 3, f"Calculer le moment en A de l'action {V('M','6/3')}.",
    -1470, "daN·m", "M<sub>A</sub>(M<sub>6/3</sub>) = −1 470 daN·m",
    "<p>Avec AM (2,94 ; 0) et M6/3 (0 ; −500), en comptant positif le sens trigonométrique :</p>"
    + calc("MA(M6/3) = AM_x · M6/3 y − AM_y · M6/3 x", "         = 2,94 × (−500) − 0 × 0 = −1 470 daN·m")
    + "<p>Le signe négatif traduit un moment <strong>horaire</strong> : la charge tend à faire basculer la flèche vers le bas autour de A. Le tirant devra produire le moment opposé.</p>",
    ["DT4"], absTol=1, hint="M<sub>A</sub> = <var>x</var>·F<sub>y</sub> − <var>y</var>·F<sub>x</sub>, sens trigonométrique positif. " + H_UNIT)

num("2", 4, "L'action en B est portée par (BD), dirigée de B vers D. On écrit B<sub>2/3 x</sub> = <var>k</var> · B<sub>2/3 y</sub>. Donner la valeur de <var>k</var>.",
    K, None, "<var>k</var> = tan(−73°) ≈ −3,27",
    "<p>De B vers D, on se déplace de 3,30 m vers le mur (<var>x</var> négatif) et de 1,01 m vers le haut (<var>y</var> positif). Le rapport des composantes est donc :</p>"
    + calc("B2/3 x / B2/3 y = −3,30 / 1,0089 = −3,2709", "k ≈ −3,27")
    + "<p>Écrire <var>k</var> = +3,27 reviendrait à faire pousser le tirant vers l'extérieur du mur, ce qui est impossible pour un tirant.</p>",
    ["DT4"], absTol=0.006, hint="Le tirant monte vers le mur : les deux composantes sont de signes contraires. " + H_SANS)

num("2", 5, f"En reportant cette relation dans le moment en A, on obtient M<sub>A</sub>({V('B','2/3')}) = <var>c</var> · B<sub>2/3 y</sub>. Calculer le coefficient <var>c</var>.",
    C, "m", "<var>c</var> ≈ 4,16 m",
    "<p>Avec AB (3,51 ; 0,20) :</p>"
    + calc("MA(B2/3) = 3,51 × B2/3 y − 0,20 × B2/3 x",
           "         = 3,51 × B2/3 y − 0,20 × (−3,2709 × B2/3 y)",
           "         = (3,51 + 0,6542) × B2/3 y = 4,1642 × B2/3 y")
    + "<p><var>c</var> ≈ 4,16 m (un moment divisé par une force : c'est une longueur). Le bras de levier « utile » du tirant vaut donc 4,16 m et non 3,51 m : le décalage vertical de 200 mm combiné à l'inclinaison ajoute environ 0,65 m.</p>",
    ["DT4"], absTol=0.006)

num("2", 6, "Écrire l'équation des moments en A pour la flèche et en déduire B<sub>2/3 y</sub>.",
    BY, "daN", "B<sub>2/3 y</sub> ≈ 353,01 daN",
    "<p>Équation des moments en A :</p>"
    + calc("MA(A1/3) + MA(M6/3) + MA(B2/3) = 0")
    + "<p>A1/3 passant par A, son moment en A est nul. Il reste :</p>"
    + calc("−1 470 + 4,1642 × B2/3 y = 0", "B2/3 y = 1 470 / 4,1642 = 353,01 daN")
    + "<p>Le choix du point A n'a rien d'arbitraire : c'est le seul point qui élimine d'un coup les deux composantes inconnues de l'action en A.</p>",
    ["DT4"], relTol=0.005)

num("2", 7, "En déduire B<sub>2/3 x</sub>.",
    BX, "daN", "B<sub>2/3 x</sub> ≈ −1 154,65 daN",
    calc("B2/3 x = k × B2/3 y = −3,2709 × 353,01 = −1 154,65 daN")
    + "<p>La composante horizontale est plus de trois fois supérieure à la composante verticale : le tirant, très couché, tire surtout la flèche horizontalement vers le mur.</p>",
    ["DT4"], relTol=0.005)

num("2", 8, f"Calculer l'intensité (la norme) de l'action {V('B','2/3')}.",
    NB, "daN", "‖B<sub>2/3</sub>‖ ≈ 1 207,41 daN",
    calc("‖B2/3‖ = √(1 154,65² + 353,01²) = √1 457 429 ≈ 1 207,41 daN")
    + "<p>Pour lever 500 daN, le tirant encaisse près de 1 207 daN, soit environ 2,4 fois la charge. Plus le tirant se rapproche de l'horizontale, plus l'effort augmente.</p>",
    ["DT4"], relTol=0.005)

num("2", 9, "Appliquer le principe fondamental de la statique en résultante à la flèche et en déduire A<sub>1/3 x</sub>.",
    AX, "daN", "A<sub>1/3 x</sub> ≈ 1 154,65 daN",
    calc("A1/3 + B2/3 + M6/3 = 0")
    + "<p>Projection sur <var>x</var>, M6/3 étant vertical :</p>"
    + calc("A1/3 x = −B2/3 x − M6/3 x = +1 154,65 − 0 = 1 154,65 daN")
    + "<p>La colonne pousse la flèche vers l'extérieur du mur, à l'opposé de la traction du tirant.</p>",
    ["DT4"], relTol=0.005)

num("2", 10, "En déduire A<sub>1/3 y</sub>.",
    AY, "daN", "A<sub>1/3 y</sub> ≈ 146,99 daN",
    calc("A1/3 y = −B2/3 y − M6/3 y = −353,01 + 500 = 146,99 daN")
    + "<p>Le tirant reprend 353 daN des 500 daN de la charge ; les 147 daN restants passent par l'articulation A.</p>",
    ["DT4"], relTol=0.005, absTol=0.5)

num("2", 11, f"Calculer l'intensité de l'action {V('A','1/3')}.",
    NA, "daN", "‖A<sub>1/3</sub>‖ ≈ 1 163,97 daN",
    calc("‖A1/3‖ = √(1 154,65² + 146,99²) ≈ 1 163,97 daN")
    + "<p>L'action en A est presque horizontale : elle fait arctan(146,99 / 1 154,65) ≈ 7,3° avec l'axe <var>x</var>. Le tracé suivant le vérifie graphiquement.</p>",
    ["DT4"], relTol=0.005)

# Tracé : concours des trois forces sur la flèche isolée
SK_ID = "sk_q2_12"
SK_CRIT = [
    f"La droite d'action de {V('M','6/3')}, verticale passant par M, est prolongée au-dessus de la flèche.",
    "Le point de concours I est marqué à l'intersection de cette verticale et de la droite (BD), au-dessus de la flèche.",
    "La droite d'action de l'action en A est tracée de A jusqu'à I.",
    "Cette droite fait un petit angle (environ 7°) au-dessus de l'axe <var>x</var> : elle est presque horizontale.",
    f"La flèche représentant {V('A','1/3')} part de A et pointe vers I (vers l'extérieur du mur et légèrement vers le haut).",
]
SKCFG[SK_ID] = {"bg": "FLECHE", "deps": ["q2_9", "q2_10"], "label": "Q2.12", "part": "2",
                "pts": len(SK_CRIT), "criteria": SK_CRIT}

# ------------------------------------------------------------- Partie 3
intro("3", "<p>Le tirant ne sert ici qu'à transporter l'effort de B jusqu'à D. Deux applications successives du principe des actions réciproques et de l'équilibre d'un solide soumis à deux forces suffisent.</p>")

num("3", 1, f"Donner la composante suivant <var>x</var> de l'action {V('B','3/2')} exercée par la flèche sur le tirant.",
    -BX, "daN", "B<sub>3/2 x</sub> ≈ 1 154,65 daN",
    calc("B3/2 = −B2/3  →  B3/2 x = +1 154,65 daN")
    + "<p>Même droite d'action, même intensité, sens opposé : c'est le principe des actions réciproques.</p>",
    ["DT3"], relTol=0.005)

num("3", 2, f"Donner la composante suivant <var>y</var> de {V('B','3/2')}.",
    -BY, "daN", "B<sub>3/2 y</sub> ≈ −353,01 daN",
    calc("B3/2 y = −B2/3 y = −353,01 daN")
    + "<p>La flèche tire l'extrémité basse du tirant vers le bas et vers l'extérieur.</p>",
    ["DT3"], relTol=0.005)

num("3", 3, "Le tirant étant soumis à deux forces, en déduire D<sub>1/2 x</sub>, action de la colonne sur le tirant en D.",
    BX, "daN", "D<sub>1/2 x</sub> ≈ −1 154,65 daN",
    calc("B3/2 + D1/2 = 0  →  D1/2 = −B3/2", "D1/2 x = −1 154,65 daN")
    + "<p>On retrouve la propriété annoncée en Q1.1 : les deux actions sur le tirant sont exactement opposées.</p>",
    ["DT3"], relTol=0.005)

num("3", 4, "En déduire D<sub>1/2 y</sub>.",
    BY, "daN", "D<sub>1/2 y</sub> ≈ 353,01 daN",
    calc("D1/2 y = −B3/2 y = +353,01 daN")
    + "<p>La colonne retient le haut du tirant vers le haut et vers le mur.</p>",
    ["DT3"], relTol=0.005)

kw("3", 5, "Les deux actions appliquées au tirant sont dirigées vers l'extérieur de celui-ci. À quelle sollicitation le tirant est-il soumis ?",
   [[["traction", "tendu", "tendue", "extension", "tension", "etire", "etiree"]]],
   ["compression", "comprime", "flexion", "cisaillement", "torsion", "flambage", "flambement"],
   "traction (extension)",
   "<p>Le tirant travaille en <strong>traction</strong> (extension).</p>"
   "<p>En B la flèche l'étire vers le bas et l'extérieur, en D la colonne le retient vers le haut et le mur : les deux forces s'éloignent l'une de l'autre, la barre est tendue. C'est ce qui justifie son nom de « tirant » et permet de le dimensionner avec σ = N / S.</p>",
   ["DT3"], "Un seul mot suffit.")

# ------------------------------------------------------------- Partie 4
COLONNE_SVG = None  # construit plus bas

intro("4", "<p>Deux des quatre actions sur la colonne sont maintenant connues. La liaison en E ne peut transmettre qu'un effort horizontal : un moment pris en F livre alors la dernière inconnue.</p>\n      @@COLONNE@@")

num("4", 1, "Donner A<sub>3/1 x</sub>, action de la flèche sur la colonne en A.",
    -AX, "daN", "A<sub>3/1 x</sub> ≈ −1 154,65 daN",
    calc("A3/1 = −A1/3  →  A3/1 x = −1 154,65 daN")
    + "<p>La flèche pousse la colonne vers le mur au niveau de A.</p>",
    ["DT5"], relTol=0.005)

num("4", 2, "Donner A<sub>3/1 y</sub>.",
    -AY, "daN", "A<sub>3/1 y</sub> ≈ −146,99 daN",
    calc("A3/1 y = −A1/3 y = −146,99 daN")
    + "<p>Action dirigée vers le bas, comme on s'y attend pour une charge suspendue.</p>",
    ["DT5"], relTol=0.005, absTol=0.5)

num("4", 3, "Donner D<sub>2/1 x</sub>, action du tirant sur la colonne en D.",
    -BX, "daN", "D<sub>2/1 x</sub> ≈ 1 154,65 daN",
    calc("D2/1 = −D1/2  →  D2/1 x = +1 154,65 daN")
    + "<p>Le tirant tire le haut de la colonne vers l'extérieur du mur : c'est cette action qui crée le basculement que les liaisons E et F doivent reprendre.</p>",
    ["DT5"], relTol=0.005)

num("4", 4, "Donner D<sub>2/1 y</sub>.",
    -BY, "daN", "D<sub>2/1 y</sub> ≈ −353,01 daN",
    calc("D2/1 y = −D1/2 y = −353,01 daN"),
    ["DT5"], relTol=0.005)

num("4", 5, "En E, la colonne est guidée par le support (4) : le contact est cylindrique et laisse la colonne libre de coulisser suivant <var>y</var>. Que vaut E<sub>4/1 y</sub> ?",
    0, "daN", "E<sub>4/1 y</sub> = 0 daN",
    calc("E4/1 y = 0")
    + "<p>Le support supérieur ne bloque pas la translation verticale de la colonne : il ne peut transmettre qu'un effort <strong>radial, donc horizontal</strong>. L'énoncé le confirme en précisant que l'action en E est supposée horizontale.</p>"
    "<p>Toute la charge verticale doit donc redescendre par la liaison inférieure en F.</p>",
    ["DT1", "DT5"], absTol=0.01, hint="Saisis la valeur <strong>avec son unité</strong> : l'unité vaut la moitié des points de la question.")

num("4", 6, "Écrire l'équilibre de la colonne en projection sur <var>y</var> et en déduire F<sub>5/1 y</sub>.",
    FY, "daN", "F<sub>5/1 y</sub> = 500 daN",
    calc("A3/1 y + D2/1 y + E4/1 y + F5/1 y = 0", "−146,99 − 353,01 + 0 + F5/1 y = 0", "F5/1 y = +500 daN")
    + "<p>Le support inférieur reprend <strong>exactement le poids de la charge</strong> : c'est la seule action verticale extérieure à l'ensemble de la potence, et seule la liaison en F peut la reprendre verticalement.</p>",
    ["DT5"], relTol=0.005)

num("4", 7, f"Pour trouver l'action en E, on prend les moments en F. Calculer M<sub>F</sub>({V('A','3/1')}).",
    MFA, "daN·m", f"M<sub>F</sub>(A<sub>3/1</sub>) ≈ {fr(MFA)} daN·m",
    "<p>A est à 0,24 m à droite de l'axe EF et à 0,26 m au-dessus de F : FA (0,24 ; 0,26).</p>"
    + calc("MF(A3/1) = FA_x · A3/1 y − FA_y · A3/1 x",
           "         = 0,24 × (−146,99) − 0,26 × (−1 154,65)",
           "         = −35,28 + 300,21 = +264,93 daN·m")
    + "<p>Oublier la composante horizontale de FA (en croyant A sur l'axe de la colonne) donnerait 300,21 daN·m : c'est une erreur de lecture de la cote 240.</p>",
    ["DT5"], relTol=0.005, hint="FA (0,24 ; 0,26). " + H_FORCE)

num("4", 8, f"Calculer M<sub>F</sub>({V('D','2/1')}).",
    MFD, "daN·m", f"M<sub>F</sub>(D<sub>2/1</sub>) ≈ {fr(MFD)} daN·m",
    "<p>Coordonnées de D par rapport à F :</p>"
    + calc("FD_x = 0,45 m (cote 450 depuis l'axe EF)", "FD_y = 1,2089 + 0,26 = 1,4689 m")
    + calc("MF(D2/1) = FD_x · D2/1 y − FD_y · D2/1 x",
           "         = 0,45 × (−353,01) − 1,4689 × 1 154,65",
           "         = −158,86 − 1 696,07 = −1 854,93 daN·m")
    + "<p><strong>Piège :</strong> 1,21 m est la hauteur de D au-dessus de <em>A</em>. Le moment étant pris en <em>F</em>, situé 0,26 m plus bas, il faut 1,47 m. Utiliser 1,21 m conduirait à E ≈ 746 daN au lieu de 919 daN.</p>",
    ["DT5"], relTol=0.005, hint="D est à 0,45 m de l'axe EF et à 1,21 m au-dessus de A ; F est 0,26 m sous A. " + H_FORCE)

num("4", 9, f"Écrire l'équation des moments en F pour la colonne et en déduire M<sub>F</sub>({V('E','4/1')}).",
    MFE, "daN·m", "M<sub>F</sub>(E<sub>4/1</sub>) = 1 590 daN·m",
    calc("MF(A3/1) + MF(D2/1) + MF(E4/1) + MF(F5/1) = 0")
    + "<p>F5/1 passe par F, son moment y est nul :</p>"
    + calc("MF(E4/1) = −(264,93 − 1 854,93) = +1 590,00 daN·m")
    + "<p>La valeur ronde n'est pas un hasard : elle est exactement opposée au moment de la charge par rapport à F, 500 × 3,18 (voir partie 5). C'est un excellent contrôle intermédiaire.</p>",
    ["DT5"], relTol=0.005)

num("4", 10, "En déduire E<sub>4/1 x</sub>.",
    EX, "daN", f"E<sub>4/1 x</sub> ≈ {fr(EX)} daN",
    "<p>FE est vertical, de longueur 1,73 m, et E4/1 n'a qu'une composante horizontale :</p>"
    + calc("MF(E4/1) = FE_x · E4/1 y − FE_y · E4/1 x = 0 × 0 − 1,73 × E4/1 x",
           "−1,73 × E4/1 x = 1 590", "E4/1 x = −1 590 / 1,73 = −919,08 daN")
    + "<p>Le signe négatif indique que le support supérieur <strong>tire la colonne vers le mur</strong> : la charge tend à faire basculer la potence vers l'extérieur autour de F.</p>",
    ["DT5"], relTol=0.005)

num("4", 11, "Écrire l'équilibre de la colonne en projection sur <var>x</var> et en déduire F<sub>5/1 x</sub>.",
    FX, "daN", f"F<sub>5/1 x</sub> ≈ {fr(FX)} daN",
    calc("A3/1 x + D2/1 x + E4/1 x + F5/1 x = 0", "−1 154,65 + 1 154,65 − 919,08 + F5/1 x = 0", "F5/1 x = +919,08 daN")
    + "<p>Les actions en A et en D se compensent exactement sur <var>x</var>. Il ne reste que le couple E–F pour équilibrer le basculement : deux forces horizontales opposées de 919,08 daN distantes de 1,73 m (919,08 × 1,73 = 1 590 daN·m).</p>",
    ["DT5"], relTol=0.005)

num("4", 12, f"Calculer l'intensité de l'action {V('F','5/1')} exercée par le support inférieur sur la colonne.",
    NF, "daN", f"‖F<sub>5/1</sub>‖ ≈ {fr(NF)} daN",
    calc("‖F5/1‖ = √(919,08² + 500²) = √1 094 707 ≈ 1 046,28 daN")
    + "<p>Le support inférieur (5) est le plus sollicité des deux ancrages : il reprend à la fois la totalité de la charge verticale et une des deux forces du couple de basculement.</p>",
    ["DT5"], relTol=0.005)

# ------------------------------------------------------------- Partie 5
intro("5", "<p>Un isolement bien conduit doit toujours pouvoir se recouper par un second, plus large. On isole maintenant l'ensemble {1 + 2 + 3 + 6} : les seules actions extérieures sont la charge P en M, l'action en E et l'action en F.</p>")

yesno("5", 1, "Pour calculer le moment en F de la charge P, peut-on prendre directement la cote 2 940 comme bras de levier ?",
      False, "Non",
      "<p><strong>Non.</strong> La cote 2 940 est mesurée depuis <em>A</em>. Or le moment est pris en <em>F</em>, qui est sur l'axe EF, 0,24 m à gauche de A. Le bras de levier de P (verticale) par rapport à F est la distance horizontale de F à M, soit 0,24 + 2,94 = 3,18 m.</p>",
      ["DT1"])

num("5", 2, "Quelle est la distance horizontale entre F et M, c'est-à-dire la composante FM<sub><var>x</var></sub> ?",
    3.18, "m", "FM<sub>x</sub> = 3,18 m",
    calc("FM_x = 0,24 + 2,94 = 3,18 m ; FM_y = 0,26 m")
    + "<p>Toutes les coordonnées doivent être exprimées <em>depuis le point où l'on calcule le moment</em>.</p>",
    ["DT1"], absTol=0.005)

num("5", 3, "Calculer le moment en F de la charge P.",
    -1590, "daN·m", "M<sub>F</sub>(P) = −1 590 daN·m",
    calc("MF(P) = FM_x · P_y − FM_y · P_x = 3,18 × (−500) − 0,26 × 0 = −1 590 daN·m")
    + "<p>La composante verticale de FM ne joue aucun rôle puisque P n'a pas de composante horizontale.</p>",
    ["DT1"], absTol=1)

num("5", 4, "En écrivant l'équilibre en moment de cet ensemble en F, retrouver E<sub>4/1 x</sub>.",
    EX, "daN", f"E<sub>4/1 x</sub> ≈ {fr(EX)} daN",
    calc("MF(P) + MF(E4/1) + MF(F5/1) = 0", "−1 590 − 1,73 × E4/1 x + 0 = 0", "E4/1 x = −1 590 / 1,73 = −919,08 daN")
    + "<p><strong>La valeur trouvée en Q4.10 est confirmée.</strong> Ce contrôle est décisif car il ne fait intervenir que des données directement lisibles : la charge, la distance horizontale de F à M (240 + 2 940 mm) et l'entraxe des paliers (1 730 mm). Il ne dépend ni de la position de D, ni de l'angle de 73°.</p>",
    ["DT1"], relTol=0.005)

num("5", 5, "Récapitulatif du point qui fait basculer tout le calcul : quel est le bras de levier vertical FD<sub><var>y</var></sub> à utiliser entre F et D pour le moment en F ?",
    FDY, "m", "FD<sub>y</sub> ≈ 1,47 m",
    calc("FD_y = y_D − y_F = 1,2089 − (−0,26) = 1,4689 ≈ 1,47 m")
    + "<p>Prendre 1,21 m (hauteur de D au-dessus de A) au lieu de 1,47 m donne E ≈ 746 daN, soit une sous-estimation de près de 19 % de l'effort sur l'ancrage supérieur.</p>"
    "<p><strong>Règle à retenir :</strong> lorsqu'on calcule un moment en un point, toutes les coordonnées sont exprimées depuis ce point. Mélanger des cotes prises depuis l'axe EF (240, 450) et depuis A (1 210, 2 940) dans un même produit conduit inévitablement à une erreur.</p>",
    ["DT5"], absTol=0.006)

kw("5", 6, "Justifier en une phrase pourquoi la composante verticale de l'action en E est nulle.",
   [[["pivot"], ["glissant"]], [["lineaire"], ["annulaire"]], [["annulaire"]], [["radial", "radiale", "radiaux"]],
    [["coulisser", "coulisse", "coulissement", "glisser", "glisse", "glissement", "translation"]],
    [["aucun", "aucune", "pas", "ne", "nul", "nulle"], ["effort", "action", "force"], ["vertical", "verticale", "axial", "axiale"]]],
   ["encastrement", "rotule"],
   "le support (4) laisse la colonne coulisser verticalement (pivot glissant / linéaire annulaire) : il ne transmet qu'un effort radial",
   "<p>Le support (4) réalise une <strong>liaison pivot glissant d'axe <var>y</var></strong> (ou linéaire annulaire si le contact est court) : la colonne peut tourner et coulisser verticalement dans ce guidage, qui ne peut donc transmettre qu'un effort radial, c'est-à-dire horizontal.</p>"
   "<p>Une action suivant <var>y</var> en E supposerait un blocage axial que la liaison ne possède pas. C'est pourquoi l'action en E est « supposée horizontale », et c'est aussi ce qui oblige le palier inférieur en F à reprendre seul les 500 daN.</p>",
   ["DT1"], "Nomme la liaison ou décris ce qu'elle laisse libre.")

# ===================================================================
#  Figure SVG de la colonne isolée (positions et bras de levier)
# ===================================================================
def colonne_svg():
    s = 150.0
    ax = 120.0                      # axe EF
    xA, xD = ax + 0.24 * s, ax + 0.45 * s

    def Y(m):
        return 44 + s * (1.47 - m)
    yE, yD, yA, yF = Y(1.47), Y(YD), Y(0), Y(-0.26)
    ink, blue, red, green, yel = "#1C2530", "#1F5FA8", "#B42318", "#1B7A43", "#F2B705"
    o = []
    a = o.append

    def vcote(x, y1, y2, lab):
        a(f'<line x1="{x}" y1="{y1:.1f}" x2="{x}" y2="{y2:.1f}" stroke="{green}" stroke-width="1" marker-start="url(#ch)" marker-end="url(#ch)"/>')
        a(f'<text x="{x + 7}" y="{(y1 + y2) / 2 + 4:.1f}" fill="{green}" font-size="13">{lab}</text>')

    def hcote(y, x1, x2, lab):
        a(f'<line x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" stroke="{green}" stroke-width="1" marker-start="url(#ch)" marker-end="url(#ch)"/>')
        a(f'<text x="{(x1 + x2) / 2:.1f}" y="{y - 6}" fill="{green}" font-size="13" text-anchor="middle">{lab}</text>')

    def leader(x, y, tx, ty, lab):
        a(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{tx}" y2="{ty:.1f}" stroke="{red}" stroke-width="1" stroke-dasharray="3 3"/>')
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{red}"/>')
        a(f'<text x="{tx + 5}" y="{ty + 4:.1f}" fill="{red}" font-size="13.5">{lab}</text>')

    a('<svg viewBox="0 0 640 410" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Colonne (1) isolée : positions de E, D, A et F, points d\'application des quatre actions et bras de levier mesurés depuis F.">')
    a(f'<defs><marker id="ch" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M2,2 L8,5 L2,8 z" fill="{green}"/></marker></defs>')
    a(f'<rect x="{ax - 24}" y="{yE + 12:.1f}" width="{xA - ax + 44:.1f}" height="{yF - yE - 24:.1f}" fill="#FFF3C4" stroke="{ink}" stroke-width="1.2"/>')
    a(f'<line x1="{ax}" y1="24" x2="{ax}" y2="372" stroke="{blue}" stroke-width="0.9" stroke-dasharray="14 3 2 3"/>')
    a(f'<text x="{ax - 4}" y="18" fill="{blue}" font-size="12" text-anchor="middle">axe EF</text>')
    a(f'<line x1="{xA + 20:.1f}" y1="{yD:.1f}" x2="{xD:.1f}" y2="{yD:.1f}" stroke="{ink}" stroke-width="5"/>')
    for (px, py, lab, dx, dy) in [(ax, yE, "E", -18, 4), (xD, yD, "D", 7, -9), (xA, yA, "A", 8, 16), (ax, yF, "F", -18, 5)]:
        a(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.6" fill="#fff" stroke="{ink}" stroke-width="1.8"/>')
        a(f'<text x="{px + dx:.1f}" y="{py + dy:.1f}" font-size="15" font-style="italic" font-weight="700" fill="{ink}">{lab}</text>')
    leader(ax, yE, 236, yE - 4, "E4/1")
    leader(xD, yD, 236, yD - 4, "D2/1")
    leader(xA, yA, 236, yA - 4, "A3/1")
    leader(ax, yF, 236, yF + 18, "F5/1")
    for (x0, y0, x1) in [(xD, yD, 434), (ax, yE, 544), (xA, yA, 344), (ax, yF, 544)]:
        a(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1}" y2="{y0:.1f}" stroke="{green}" stroke-width="0.7" stroke-dasharray="4 3"/>')
    vcote(324, yF, yA, "FA y = 0,26")
    vcote(434, yF, yD, "FD y = 1,47")
    vcote(544, yF, yE, "FE = 1,73")
    for x0, y0 in [(xA, yA), (xD, yD)]:
        a(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0:.1f}" y2="402" stroke="{green}" stroke-width="0.7" stroke-dasharray="4 3"/>')
    hcote(yF + 44, ax, xA, "240")
    hcote(398, ax, xD, "450")
    a('</svg>')
    return "".join(o)


COLONNE_FIG = ('<figure class="fig" style="max-width:640px">' + colonne_svg() +
               "<figcaption>Colonne (1) isolée : points d'application des quatre actions extérieures et bras de levier à utiliser. "
               "Les cotes 240 et 450 partent de l'axe EF ; pour un moment en F, toutes les coordonnées se mesurent depuis F.</figcaption></figure>")
CONTENU["4"][0] = CONTENU["4"][0].replace("@@COLONNE@@", COLONNE_FIG)

# ===================================================================
#  Tracé (bloc HTML)
# ===================================================================
FL_W, FL_H = idim("fleche.png")
FL_SCALE = 1  # coordonnées DECOR = pixels du fond

SK_HTML = f"""
      <div class="qbar" role="group" aria-label="Q2.12"><div class="qb-num">Q2.12</div><div class="qb-docs">Documents à consulter : <button type="button" class="doc-chip" data-doc="DT4" aria-pressed="false">DT4</button></div><div class="qb-ans">Répondre : sur le DR1</div></div>
        <div class="sketch" data-sketch="{SK_ID}" id="{SK_ID}">
          <p class="q-stem"><span class="q-num">Q2.12</span> <strong>Vérification graphique. Sur la flèche isolée (DR1), tracer la droite d'action de {V('M','6/3')} et repérer son point de concours I avec la droite (BD). En déduire la droite d'action de {V('A','1/3')} et représenter son sens.</strong></p>
          <div class="sk-layout">
            <div class="sk-main">
              <div class="sk-toolbar" role="toolbar" aria-label="Outils de tracé Q2.12">
                <button type="button" data-tool="pen" aria-pressed="true">Crayon</button>
                <button type="button" data-tool="line" aria-pressed="false">Ligne</button>
                <button type="button" data-tool="arrow" aria-pressed="false">Flèche</button>
                <button type="button" data-tool="text" aria-pressed="false">Texte</button>
                <button type="button" data-tool="erase" aria-pressed="false">Gomme</button>
                <span class="sep"></span>
                <button type="button" class="sw" data-color="#1F5FA8" aria-label="Couleur bleue" aria-pressed="true" style="background:#1F5FA8"></button>
                <button type="button" class="sw" data-color="#1B7A43" aria-label="Couleur verte" aria-pressed="false" style="background:#1B7A43"></button>
                <button type="button" class="sw" data-color="#1C2530" aria-label="Couleur noire" aria-pressed="false" style="background:#1C2530"></button>
                <span class="sep"></span>
                <span class="tb-group"><span class="tb-lab">Trait</span>
                  <button type="button" data-width="fin" aria-pressed="false">Fin</button>
                  <button type="button" data-width="moyen" aria-pressed="true">Moyen</button>
                  <button type="button" data-width="epais" aria-pressed="false">Épais</button></span>
                <span class="sep"></span>
                <span class="tb-group"><span class="tb-lab">Zoom</span>
                  <button type="button" data-zoom="out" aria-label="Réduire le zoom">−</button>
                  <span class="zoom-val">100 %</span>
                  <button type="button" data-zoom="in" aria-label="Agrandir le zoom">+</button>
                  <button type="button" data-zoom="reset">Ajuster</button></span>
                <span class="sep"></span>
                <button type="button" data-act="undo">Annuler</button>
                <button type="button" data-act="clear">Tout effacer</button>
                <span class="spacer"></span>
                <button type="button" class="btn-drprint" data-act="drprint">Imprimer les DR</button>
                <button type="button" data-act="full" aria-pressed="false">Plein écran</button>
              </div>
              <div class="sk-stage"><img class="sk-bg" src="{img('fleche.png')}" width="{FL_W * FL_SCALE}" height="{FL_H * FL_SCALE}" alt="" hidden>
                <canvas role="img" aria-label="Zone de tracé sur le document réponse DR1 : flèche (3) isolée"></canvas></div>
              <div class="sk-foot">
                <button type="button" class="btn btn-sketch">Valider mon tracé</button>
                <label class="sk-corr-toggle"><input type="checkbox"> Superposer la correction</label>
                <span class="sk-meas" aria-live="polite"></span><span class="q-status" aria-live="polite"></span>
              </div>
              <div class="sk-print-wrap print-only"><p>Tracé de l'élève</p><img class="sk-print sk-print-student" alt="Tracé de l'élève">
                <p>Correction superposée au document réponse</p><img class="sk-print sk-print-corr" alt="Correction du tracé"></div>
              <div class="selfeval" hidden>
                <p class="se-title">Auto-évaluation — {len(SK_CRIT)} points sur les @@PTS2@@ de la partie 2</p>
                <p class="se-lead">Compare ton tracé à la correction, puis coche uniquement ce que ton tracé comporte réellement. Sois honnête : c'est toi qui repères ce qu'il te reste à travailler.</p>
                {"".join(f'<label class="se-item"><input type="checkbox" data-crit="{i}"><span>{c}</span></label>' for i, c in enumerate(SK_CRIT))}
                <div class="se-foot"><button type="button" class="btn btn-self">Valider mon auto-évaluation</button>
                  <span class="se-score" aria-live="polite"></span></div>
                <p class="print-only se-print"></p>
              </div>
            </div>
            <div class="sk-side"><p class="small"><strong>Principe.</strong> Un solide soumis à trois forces non parallèles est en équilibre si leurs droites d'action sont <strong>concourantes</strong> (et si leur somme est nulle).</p>
              <ul class="small"><li>{V('M','6/3')} : connue, verticale, appliquée en M.</li>
                <li>{V('B','2/3')} : direction connue, la droite (BD) déjà tracée.</li>
                <li>{V('A','1/3')} : inconnue, appliquée en A.</li></ul>
              <p class="small">Outil « Ligne » pour les droites d'action, « Flèche » pour le sens, « Texte » pour nommer I.</p></div>
          </div>
          <p class="sk-note sk-note-wrap">La correction se superposera à ton tracé une fois les questions Q2.9 et Q2.10 validées. <span class="sk-wait" aria-live="polite"></span></p>
          <div class="q-expl" hidden><p class="q-expected"><span>Correction du tracé</span></p>
            <p>1. La droite d'action de {V('M','6/3')} est la verticale passant par M.</p>
            <p>2. Elle coupe la droite (BD) en I, à environ 0,37 m au-dessus de l'axe de la flèche (0,20 + 0,57 / tan 73° = 0,374 m).</p>
            <p>3. Les trois droites d'action étant concourantes, celle de {V('A','1/3')} est la droite (AI). Elle fait avec <var>x</var> un angle arctan(0,374 / 2,94) ≈ 7,3°, exactement l'angle obtenu par le calcul en Q2.11 (146,99 / 1 154,65).</p>
            <p>4. {V('A','1/3')} est dirigée de A vers I : la colonne pousse la flèche vers l'extérieur du mur et légèrement vers le haut, ce que confirment les signes de A<sub>1/3 x</sub> et A<sub>1/3 y</sub>.</p></div>
        </div>"""
CONTENU["2"].append(SK_HTML)

# ===================================================================
#  Barème
# ===================================================================
for p in PARTS:
    p["points"] = sum(q["pts"] for q in QCFG.values() if q["part"] == p["num"]) + \
        sum(s["pts"] for s in SKCFG.values() if s["part"] == p["num"])
TOTAL_MIN = sum(p["minutes"] for p in PARTS)
NB_Q = len(QCFG)
NB_SK = len(SKCFG)


def pct(p):
    return f"{p['minutes'] / TOTAL_MIN * 100:.1f}".replace(".", ",")


def duree_txt(m):
    return f"{m // 60} h {m % 60:02d}"


# ===================================================================
#  Décor du tracé (coordonnées du fond déclaré 1080 × 500)
# ===================================================================
# Repères relevés sur fleche.png : A (72 ; 353), M (932 ; 353), B (1099 ; 296)
PX_M = (932 - 72) / 2.94           # pixels par mètre sur le fond
IY = 353 - (YB + (XB - XM) / TAN) * PX_M
PENTE = 1 / TAN                    # pente de (BD) sur le dessin
PENTE_AI = (353 - IY) / (932 - 72)
DECOR_JS = f"""  var DECOR = {{
    FLECHE: {{
      pad: {{ t: 16, r: 16, b: 16, l: 130 }}, rs: 2,
      decorate: function (c) {{
        text(c, "Repère", -116, 250, "#000", 22, "left", "700");
        arrow(c, -100, 353, -30, 353, "#000", 2); arrow(c, -100, 353, -100, 283, "#000", 2);
        vlabel(c, -26, 375, "x", "", "#000", 24); vlabel(c, -90, 285, "y", "", "#000", 24);
      }},
      correction: function (c) {{
        var I = [932, {IY:.1f}];
        line(c, 932, 540, 932, 140, CORR, 2.4, [10, 6]);
        line(c, 1099, 296, 640, 296 - 459 * {PENTE:.4f}, CORR, 2.4);
        line(c, 72, 353, 1080, 353 - 1008 * {PENTE_AI:.4f}, CORR, 2.4, [10, 6]);
        dot(c, I[0], I[1], 7, CORR);
        text(c, "I", I[0] - 34, I[1] - 26, CORR, 34, "left", "800");
        arrow(c, 72, 353, 262, 353 - 190 * {PENTE_AI:.4f}, CORR, 4);
        vlabel(c, 160, 288, "A", "1/3", CORR, 32, "center");
        text(c, "≈ 7°", 300, 290, CORR, 28, "left", "800");
        arrow(c, 1099, 296, 1099 - 120, 296 - 120 * {PENTE:.4f}, CORR, 4);
        vlabel(c, 1010, 200, "B", "2/3", CORR, 30, "center");
        text(c, "Correction", 990, 40, CORR, 28, "left", "800");
      }}
    }}
  }};
"""
DRNAMES_JS = """  var DR_NAMES = {
    FLECHE: { doc: "DR1", q: "Q2.12", t: "Flèche (3) isolée : concours des trois forces", scale: false }
  };
"""

# ===================================================================
#  Assemblage
# ===================================================================
def extraire(debut, fin, texte=GABARIT):
    i = texte.index(debut)
    j = texte.index(fin, i) + len(fin)
    return texte[i:j]


STYLE = extraire("<style>:root", "</style>")
GRADING = extraire("<script>/*GRADING-START*/", "</script>")
APP = extraire("<script>(function () {", "</script>", GABARIT[GABARIT.index("/*GRADING-END*/"):])


def remplacer(src, ancien, nouveau):
    assert src.count(ancien) == 1, ancien[:60]
    return src.replace(ancien, nouveau)


APP = remplacer(APP, "var CONSEIL_MIN = 300;", f"var CONSEIL_MIN = {TOTAL_MIN};")
i = APP.index("  var DECOR = {")
j = APP.index("  function distSeg")
APP = APP[:i] + DECOR_JS + "\n" + APP[j:]
i = APP.index("  var DR_NAMES = {")
j = APP.index("  function printDR")
APP = APP[:i] + DRNAMES_JS + "\n" + APP[j:]
APP = remplacer(APP, "<p>Quatre pages, une par document, à imprimer en A4 paysage à 100 %.</p>",
                "<p>Une page par document réponse, à imprimer en A4 paysage.</p>")

DOCS = [
    ("DP1", "Présentation de la potence", "Dossier présentation", None),
    ("DT1", "Vue d'ensemble cotée", "Dossier technique", "ensemble.png"),
    ("DT2", "Palan (6) isolé", "Dossier technique", "palan.png"),
    ("DT3", "Tirant (2) isolé", "Dossier technique", "tirant.png"),
    ("DT4", "Flèche (3) isolée", "Dossier technique", "fleche.png"),
    ("DT5", "Colonne (1) isolée", "Dossier technique", "colonne.png"),
]
DOC_ALT = {
    "DT1": "Vue d'ensemble cotée de la potence : mur (0), colonne (1), tirant (2), flèche (3), supports (4) et (5), palan (6). Cotes 1 470, 260, 240, 450, 2 940, 570 et 200 mm, angle 73°.",
    "DT2": "Palan (6) isolé : poids P de 500 daN vers le bas en M et action de la flèche M3/6 de 500 daN vers le haut.",
    "DT3": "Tirant (2) isolé, de D à B, incliné de 73° par rapport à la verticale.",
    "DT4": "Flèche (3) isolée : articulation A, point M à 2 940 mm, articulation B à 570 mm plus loin et 200 mm au-dessus de l'axe, droite BD à 73° de la verticale.",
    "DT5": "Colonne (1) isolée : E en haut et F en bas sur l'axe vertical, D à 450 mm de l'axe, A à 240 mm de l'axe ; cotes 1 470 et 260 mm.",
}
DOC_CAP = {
    "DT1": "Cotes en millimètres. Les cotes 240 et 450 partent de l'axe vertical EF de la colonne.",
    "DT2": "Le palan transmet intégralement la charge à la flèche.",
    "DT3": "Le tirant est articulé à ses deux extrémités, D sur la colonne et B sur la flèche.",
    "DT4": "Sur ce document, l'action du palan en M est notée M6/3 = P (500 daN).",
    "DT5": "E et F sont sur l'axe de la colonne ; A et D sont décalés de 240 et 450 mm vers l'extérieur du mur.",
}

PRESENTATION = f"""<div class="doc-text"><h3>Potence à tirant sur mur</h3>
        <p>Une potence de manutention se compose d'une flèche <strong>(3)</strong> articulée en <var>A</var> sur une colonne pivotante <strong>(1)</strong>, et d'un tirant <strong>(2)</strong> articulé en <var>D</var> sur la colonne et en <var>B</var> sur la flèche.</p>
        <p>La colonne est guidée en rotation autour de l'axe vertical <var>EF</var> par deux supports <strong>(4)</strong> et <strong>(5)</strong> fixés au mur <strong>(0)</strong>. Le support supérieur (4) laisse la colonne libre de coulisser verticalement : l'action en <var>E</var> est supposée horizontale.</p>
        <p>Un palan <strong>(6)</strong> suspendu en <var>M</var> soulève une charge de poids {V('P')} = 500 daN. Les poids des solides sont négligés.</p>
        <p><strong>Objectif :</strong> déterminer, pour la position représentée, les actions exercées en <var>A</var>, <var>B</var>, <var>D</var>, <var>E</var> et <var>F</var>, toutes schématisées par des vecteurs-forces passant par ces points.</p></div>
      <img class="doc-img" src="{img('schema.png')}" alt="Schéma cinématique : colonne 1 en liaison avec le mur en E et F, tirant 2 entre D et B, flèche 3 entre A et B." width="{idim('schema.png')[0]}" height="{idim('schema.png')[1]}">
      <p class="doc-cap">Schéma cinématique de la potence.</p>"""

docs_html = []
for key, titre, kind, fichier in DOCS:
    if fichier is None:
        corps = PRESENTATION
    else:
        w, h = idim(fichier)
        corps = (f'<img class="doc-img" src="{img(fichier)}" alt="{DOC_ALT[key]}" width="{w}" height="{h}">'
                 f'\n      <p class="doc-cap">{DOC_CAP[key]}</p>')
    docs_html.append(f'    <section class="doc" id="doc-{key}" data-title="{key} : {titre}" data-kind="{kind}">\n      {corps}\n    </section>')

rail = ['  <button type="button" class="tab" data-doc="DP1" aria-selected="false" title="Présentation">DP1</button>',
        '  <div class="grp" aria-hidden="true"></div>']
rail += [f'  <button type="button" class="tab dt" data-doc="{k}" aria-selected="false" title="{t}">{k}</button>'
         for k, t, kind, f in DOCS if k != "DP1"]
tabs = "".join(f'<button type="button" data-doc="{k}" aria-selected="false">{k}</button>' for k, *_ in DOCS)

parts_html = []
for p in PARTS:
    n = p["num"]
    body = "".join(CONTENU[n]).replace("@@PTS2@@", str(p["points"]))
    parts_html.append(f"""
  <section class="part" id="partie-{n}" aria-labelledby="t-partie-{n}">
    <header class="part-head"><div class="part-num" aria-hidden="true">{n}</div>
      <div><h2 id="t-partie-{n}"><span class="sr-only">Partie {n} : </span>{p['title']}</h2>
        <div class="duree">Durée conseillée : {p['duration']} · Barème : {p['points']} points, soit {pct(p)} % de la note</div></div></header>
    <div class="part-body">{body}
    </div>
  </section>""")

TITRE = "Potence à tirant sur mur"
W1, H1 = idim("ensemble.png")
HERO = img("ensemble.png")

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Fichier généré par outils/construire.py à partir de outils/gabarit-exercice-interactif.html : ne pas modifier à la main. -->
<title>{TITRE} — exercice interactif</title>
<meta name="description" content="Statique du solide : principe fondamental de la statique appliqué à trois isolements successifs (flèche, tirant, colonne), solide soumis à deux et à trois forces, moments, vérification par un isolement global.">
{STYLE}
</head>
<body class="no-mode">

<nav class="rail" aria-label="Dossier de présentation et dossier technique">
{chr(10).join(rail)}
</nav>

<aside id="docpanel" aria-label="Documents du sujet" aria-hidden="true">
  <div class="dp-head">
    <h3 id="dp-title">Documents</h3>
    <button type="button" id="dp-out" aria-label="Réduire">−</button><span id="dp-zoom" class="small">100 %</span>
    <button type="button" id="dp-in" aria-label="Agrandir">+</button>
    <button type="button" id="dp-fit">Ajuster</button>
    <button type="button" id="dp-close">Fermer</button>
  </div>
  <div class="dp-tabs" role="tablist" aria-label="Choisir un document">
    {tabs}
  </div>
  <div class="dp-body">
{chr(10).join(docs_html)}
  </div>
</aside>

<section id="home" aria-labelledby="home-title">
  <div class="home-inner">
    <header class="home-head">
      <h1 id="home-title">{TITRE}</h1>
      <p class="home-sub">Une flèche articulée sur une colonne pivotante, retenue par un tirant incliné, soulève une charge de 500 daN. En isolant successivement la flèche, le tirant puis la colonne, tu détermines les actions mécaniques dans chaque articulation et sur les deux ancrages muraux : {NB_Q} questions et {NB_SK} tracé, à mener dans l'ordre de résolution.</p>
    </header>
    <figure class="home-hero">
      <img src="{HERO}" alt="{DOC_ALT['DT1']}" width="{W1}" height="{H1}">
      <figcaption>La potence et son schéma cinématique : mur (0), colonne (1), tirant (2), flèche (3), supports (4) et (5), palan (6).</figcaption>
    </figure>
    <div class="home-facts">
      <div><b>{len(PARTS)} parties</b><span>flèche, tirant, colonne, puis vérification globale</span></div>
      <div><b>{duree_txt(TOTAL_MIN)}</b><span>durée conseillée, qui fixe la pondération</span></div>
      <div><b>{len(DOCS)} documents</b><span>DP1 et DT1 à DT5 consultables</span></div>
      <div><b>{NB_SK} tracé</b><span>sur document réponse, auto-évalué</span></div>
    </div>
    <h2 class="home-choose">Choisis ton mode de travail</h2>
    <div class="modes">
      <article class="mode-card">
        <div class="mc-head"><span class="mc-tag">Mode 1</span><h3>Mode entraînement</h3></div>
        <p class="mc-lead">Pour apprendre en avançant, question par question.</p>
        <ul><li>Chaque question se valide isolément ; la démarche corrigée s'affiche aussitôt.</li>
          <li>La note pondérée s'actualise en continu dans le bandeau.</li>
          <li>Les documents et le chronomètre restent disponibles, sans contrainte de temps.</li></ul>
        <button type="button" class="btn btn-mode" data-mode="training">Commencer l'entraînement</button>
      </article>
      <article class="mode-card exam">
        <div class="mc-head"><span class="mc-tag">Mode 2</span><h3>Mode examen</h3></div>
        <p class="mc-lead">Pour se placer en conditions d'évaluation.</p>
        <ul><li>Aucune correction et aucune note pendant la composition ; les réponses restent modifiables.</li>
          <li>Le chronomètre tourne, à comparer à la durée conseillée.</li>
          <li>En fin de sujet, le bouton « J'ai fini, je fais corriger ma copie » dévoile d'un coup les corrections, les notes par partie et la note globale.</li></ul>
        <button type="button" class="btn btn-mode" data-mode="exam">Composer en mode examen</button>
      </article>
    </div>
    <p class="home-note small">Le mode se choisit une seule fois : pour en changer, recharge la page. Rien n'est enregistré sur l'ordinateur.</p>
  </div>
</section>

<main class="page">
  <section class="print-only print-summary">
    <p>Élève : <span class="print-nom"></span> | Copie imprimée le <span class="print-date"></span></p>
    <p>Mode : <span class="print-mode"></span> | Temps de rédaction : <strong class="print-time"></strong> (durée conseillée : {duree_txt(TOTAL_MIN)})</p>
    <p class="print-note-line">Note finale pondérée : <strong class="final-note"></strong></p>
    <p class="print-nograde">Copie non corrigée : les corrections et la note n'apparaissent qu'après la remise de la copie en mode examen.</p>
  </section>

  <header class="cartouche">
    <div class="title">
      <h1>{TITRE}</h1>
      <p>{NB_Q} questions notées (unités comprises) et {NB_SK} tracé auto-évalué, répartis en {len(PARTS)} parties pondérées par leur durée.</p></div>
    <div class="nom"><label for="nom-eleve">Nom et prénom</label><input id="nom-eleve" type="text" autocomplete="name"></div>
  </header>

  <div class="consignes">
    <p class="only-training"><strong>Mode entraînement.</strong> Réponds dans chaque champ puis clique sur « Valider » : une réponse validée est définitive et sa correction s'affiche aussitôt.</p>
    <p class="only-exam"><strong>Mode examen.</strong> Compose tout le sujet sans correction ni note : tes réponses restent modifiables jusqu'au bout. Le bouton « J'ai fini, je fais corriger ma copie », en fin de sujet, dévoile d'un coup les corrections, les notes par partie et la note globale.</p>
    <p><strong>Conventions.</strong> Repère direct d'origine <var>A</var> : <var>x</var> horizontal vers l'extérieur du mur, <var>y</var> vertical vers le haut. Un moment est <strong>positif dans le sens trigonométrique</strong> : M<sub>A</sub>(F) = <var>x</var>·F<sub>y</sub> − <var>y</var>·F<sub>x</sub>. Les composantes sont algébriques : n'oublie pas le signe.</p>
    <p><strong>Les unités sont notées.</strong> Pour toute question numérique, la valeur vaut la moitié des points et l'unité l'autre moitié : une valeur juste écrite sans unité, ou avec une unité fausse, ne rapporte qu'un demi-point. Une valeur convertie (mm, N, N·m) avec la bonne unité est acceptée.</p>
    <p>Le dossier de présentation (DP) et le dossier technique (DT) s'ouvrent avec les onglets sur le bord droit, ou avec les boutons des en-têtes de question.</p>
    <p><strong>Le tracé compte aussi.</strong> Quand sa correction s'affiche, tu t'attribues toi-même les points à l'aide d'une grille de critères.</p>
    <p><strong>Barème pondéré par la durée conseillée</strong> : chaque partie est notée sur 20, puis pèse au prorata de son temps. Le récapitulatif de fin de sujet donne le détail partie par partie.</p>
  </div>
{"".join(parts_html)}

  <section class="recap" id="recap" aria-labelledby="t-recap">
    <header class="recap-head"><h2 id="t-recap">Récapitulatif et note finale</h2>
      <p class="small">Les questions non validées comptent comme fausses. Chaque partie est ramenée sur 20, puis pondérée par sa durée conseillée.</p></header>
    <div id="exam-submit-wrap">
      <p class="es-lead">Ta copie n'est pas encore corrigée : aucune réponse n'est verrouillée, tu peux encore revenir sur les questions et le tracé.</p>
      <button type="button" class="btn btn-exam" id="exam-submit">J'ai fini, je fais corriger ma copie</button>
      <p class="es-warn" id="exam-warn" role="alert"></p>
    </div>
    <div id="recap-graded">
      <div class="recap-wrap">
        <table class="t recap-table">
          <thead><tr><th>Partie</th><th>Durée</th><th>Poids</th><th>Points</th><th>Note /20</th><th>Contribution</th></tr></thead>
          <tbody id="recap-body"></tbody>
          <tfoot><tr><th colspan="4">Note globale pondérée</th><th class="final-note"></th><th></th></tr></tfoot>
        </table>
      </div>
      <p class="final-detail small"></p>
    </div>
    <div class="recap-foot" id="recap-foot"><button type="button" class="btn btn-print">Imprimer ma copie</button>
      <span class="small no-print">L'impression reprend tes réponses, les corrections, ton tracé et ce récapitulatif.</span></div>
  </section>
</main>

<footer class="banner" aria-label="Suivi de la composition">
  <div class="score-block"><div class="lab">Note provisoire</div><div class="score" id="score-val">–<small>/20</small></div></div>
  <div class="exam-block"><div class="lab">Mode examen</div><div class="exam-state">Note masquée</div></div>
  <div class="timer-block"><div class="lab">Temps</div><div class="timer" id="timer-val">0:00:00</div></div>
  <div class="count" id="score-count" aria-live="polite"></div>
  <div class="spacer"></div>
  <button type="button" class="btn-docs" id="btn-docs">Documents</button>
</footer>

<!-- CONFIGURATION DU SUJET -->
<script>window.__PARTS__ = {json.dumps(PARTS, ensure_ascii=False)};
window.__QCFG__ = {json.dumps(QCFG, ensure_ascii=False)};
window.__SKCFG__ = {json.dumps(SKCFG, ensure_ascii=False)};</script>
{GRADING}
{APP}
</body>
</html>
"""

with open(SORTIE, "w", encoding="utf-8") as f:
    f.write(HTML)

# Fichier de référence pour les tests
with open(os.path.join(ICI, "tests", "config.json"), "w", encoding="utf-8") as f:
    json.dump({"QCFG": QCFG, "SKCFG": SKCFG, "PARTS": PARTS}, f, ensure_ascii=False, indent=1)

print(f"index.html : {len(HTML) / 1024:.0f} Ko, {NB_Q} questions, {NB_SK} tracé, "
      f"points par partie {[p['points'] for p in PARTS]}, durée {TOTAL_MIN} min")
print(f"E = {EX:.2f} daN, F = ({FX:.2f} ; {FY:.2f}) daN, |F| = {NF:.2f} daN, I_y = {IY:.1f} px")
