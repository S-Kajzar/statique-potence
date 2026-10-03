#!/usr/bin/env python3
"""Découpe les documents dans le scan potence-source.jpg (nettoyage du verso
par niveaux de gris, effacement des numéros de figure, PNG quantifié).
Coordonnées exprimées sur un aperçu de 1000 px de large (facteur K)."""
import os, subprocess
ICI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
SRC = os.path.join(ICI, "potence-source.jpg")
K = 2271 / 1000

def r(v): return int(round(v * K))

DECOUPES = {
    # nom: (x0, y0, x1, y1, [rectangles à blanchir en coordonnées absolues])
    "ensemble": (100, 30, 908, 447, [(770, 222, 908, 262), (820, 420, 910, 450), (295, 412, 470, 450)]),
    "schema":   (680, 30, 908, 192, []),
    "palan":    (780, 450, 925, 748, [(780, 600, 806, 712)]),
    "tirant":   (295, 412, 778, 592, [(560, 478, 655, 507), (600, 412, 750, 452), (295, 560, 460, 592)]),
    "fleche":   (255, 560, 800, 812, [(555, 596, 645, 624), (560, 560, 700, 593), (700, 560, 800, 602)]),
    "colonne":  (70, 476, 248, 825, []),
}
for nom, (x0, y0, x1, y1, blancs) in DECOUPES.items():
    args = ["convert", SRC, "-colorspace", "Gray", "-level", "35%,72%",
            "-crop", f"{r(x1 - x0)}x{r(y1 - y0)}+{r(x0)}+{r(y0)}", "+repage",
            "-fill", "white", "-stroke", "none"]
    for (a, b, c, d) in blancs:
        args += ["-draw", f"rectangle {r(a - x0)},{r(b - y0)} {r(c - x0)},{r(d - y0)}"]
    args += ["-resize", "1600x>", "-colors", "16", "-depth", "8", "-define", "png:compression-level=9",
             os.path.join(ICI, nom + ".png")]
    subprocess.run(args, check=True)
    print(nom, subprocess.run(["identify", "-format", "%wx%h %b", os.path.join(ICI, nom + ".png")],
                              capture_output=True, text=True).stdout)
