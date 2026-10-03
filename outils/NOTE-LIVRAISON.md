# Note de livraison : potence à tirant sur mur

`index.html` est maintenant **généré** par `outils/construire.py` à partir du gabarit `outils/gabarit-exercice-interactif.html`. Le bloc `<style>`, le moteur `Grading` et le moteur applicatif sont repris tels quels. Seuls les paramètres propres au sujet sont remplacés : `CONSEIL_MIN`, `DECOR`, `DR_NAMES`, et le texte d'en-tête de la fenêtre des DR (voir plus bas).

```
python3 outils/construire.py                                   # régénère index.html
node outils/tests/grading.test.js                              # 371 cas du moteur de correction
NODE_PATH=$(npm root -g) node outils/tests/navigateur.test.js  # parcours Playwright
```

## Structure

| Partie | Durée | Poids | Points | Contenu |
|---|---|---|---|---|
| 1. Lire la figure et modéliser | 25 min | 20,8 % | 11 | Q1.1 à Q1.11 |
| 2. Isolement de la flèche (3) | 35 min | 29,2 % | 16 | Q2.1 à Q2.11 et le tracé Q2.12 (5 critères) |
| 3. Le tirant (2) | 10 min | 8,3 % | 5 | Q3.1 à Q3.5 |
| 4. Isolement de la colonne (1) | 30 min | 25,0 % | 12 | Q4.1 à Q4.12 |
| 5. Vérification globale | 20 min | 16,7 % | 6 | Q5.1 à Q5.6 |

Au total : 45 questions et 1 tracé, pour une durée conseillée de 2 h.

Les documents sont DP1 (présentation et schéma cinématique), DT1 (vue d'ensemble cotée), DT2 (palan), DT3 (tirant), DT4 (flèche isolée) et DT5 (colonne isolée).

Ils sont découpés par `outils/decouper.py` dans le scan haute définition `outils/images/potence-source.jpg` (2 271 × 1 907 px). Le traitement est le suivant :
- passage en niveaux de gris ;
- rehaussement des niveaux (35 % → 72 %), ce qui fait disparaître le texte du verso visible par transparence ;
- effacement des numéros de figure ;
- export en PNG quantifié à 16 niveaux, sur 1 600 px de large au plus.

Les images pèsent environ 145 Ko au total. Le fond du tracé (DR1) est la flèche isolée à pleine résolution (1 238 × 572 px). La correction est recalée sur ce fond : A (72 ; 353), M (932 ; 353), B (1 099 ; 296), et le point de concours I tombe à (932 ; 243,5), exactement sur la droite BD imprimée.

## Erreur corrigée dans l'ancienne version de la page (importante)

L'ancien `index.html` affirmait que les cotes 240 et 450 étaient prises **depuis la face du mur**. Il en déduisait que A était sur l'axe de la colonne, donc FA = (0 ; 0,26), et il signalait comme « erreur du corrigé d'origine » l'emploi de FA = (0,24 ; 0,26).

Une **lecture visuelle** de la vue d'ensemble et de la colonne isolée montre le contraire : ces deux cotes partent du **trait d'axe vertical EF** de la colonne. A est donc décalé de 240 mm et D de 450 mm par rapport à cet axe.

Conséquences, toutes recalculées :

| Grandeur | Ancienne page | Corrigé d'origine | Valeur retenue |
|---|---|---|---|
| FA | (0 ; 0,26) | (0,24 ; 0,26) | **(0,24 ; 0,26)** |
| FD | (0,21 ; 1,47) | (0,45 ; 1,21) | **(0,45 ; 1,47)** |
| M<sub>F</sub>(A<sub>3/1</sub>) | 300,21 daN·m | 265,02 daN·m | **264,93 daN·m** |
| M<sub>F</sub>(D<sub>2/1</sub>) | −1 770,21 daN·m | −1 556,4 daN·m | **−1 854,93 daN·m** |
| M<sub>F</sub>(E<sub>4/1</sub>) | 1 470 daN·m | 1 291,38 daN·m | **1 590 daN·m** |
| E<sub>4/1 x</sub> | −849,71 daN | 746,5 daN | **−919,08 daN** |
| F<sub>5/1 x</sub> | 849,71 daN | — | **919,08 daN** |
| ‖F<sub>5/1</sub>‖ | 985,91 daN | — | **1 046,28 daN** |

La « vérification globale » de l'ancienne page prenait 2,94 m comme bras de levier de P par rapport à F. Or F est à 0,24 m à gauche de A, ce qui donne 3,18 m. Ce bras de levier erroné expliquait la concordance trompeuse avec 849,71 daN. Avec 3,18 m, l'isolement global donne exactement −1 590 / 1,73 = −919,08 daN, ce qui confirme l'isolement de la colonne au centième près.

## Erreurs relevées dans le corrigé d'origine et arbitrage

- **FD<sub>y</sub> = 1,21 m** : c'est la hauteur de D au-dessus de A, alors que le moment est pris en F. Il faut 1,21 + 0,26 = 1,47 m. C'est la cause de l'écart 746,5 → 919,08 daN. Cette erreur est conservée comme piège pédagogique en Q4.8 et Q5.5.
- Le **signe** est perdu dans la division finale (1 291,38 / 1,73 au lieu de −1 291,38 / 1,73).
- **F<sub>5/1 y</sub> = 500 N** : c'est une erreur d'unité, il faut lire 500 daN.
- FA = (0,24 ; 0,26) est **correct** dans le corrigé d'origine (voir ci-dessus).

## Coquilles du document source

- Les numéros de figure (« Fig. 36-a » à « Fig. 36-e »), la légende d'origine et le titre « Exercice 15 » ont été retirés, pour ne laisser aucune référence à la source.
- Le schéma cinématique regroupe le bâti sous l'annotation « 0 + 5 + 6 ». Le support supérieur (4) n'y figure pas, et le palan (6) n'appartient pas au bâti : on attendrait plutôt « 0 + 4 + 5 ». C'est probablement une coquille du source ; elle est signalée ici et laissée telle quelle.
- La première version de la page utilisait une image basse définition en couleur. Sur cette image, l'action du palan sur la flèche isolée était notée « M<sub>0/3</sub> ». Le scan haute définition porte bien « M<sub>6/3</sub> = P ». L'étiquette d'origine est donc conservée, sans retouche.

## Décisions d'interprétation et de tolérance

- Les **longueurs** sont arrondies au centième, avec une tolérance de ± 0,005 m (± 0,006 m pour y<sub>D</sub> et FD<sub>y</sub>, qui dépendent de tan 73°).
- Les **forces et moments** sont arrondis au centième, avec une tolérance relative de 0,5 % annoncée dans la consigne. Elle couvre les arrondis intermédiaires : par exemple c = 4,16 au lieu de 4,1642 donne B<sub>2/3 y</sub> = 353,37 daN.
- Les **unités** valent un demi-point. Une valeur convertie avec la bonne unité est acceptée pour la totalité des points : mm pour m, N pour daN, N·m pour daN·m. Sans unité, une valeur convertie ne rapporte rien, car elle est ambiguë.
- tan 73° et k sont des nombres sans unité, notés sur la valeur seule. Le coefficient c est une longueur (m).
- Pour la liaison en E, le terme « glissière » de l'ancienne page a été remplacé par **pivot glissant** (ou linéaire annulaire), car une glissière interdirait la rotation de la colonne. La correction accepte les deux noms, ainsi que toute formulation indiquant le coulissement, l'effort radial ou l'absence d'effort vertical.
- Les durées conseillées ne figurent pas dans le source. Elles ont été fixées à 2 h au total et réparties selon le volume de travail de chaque partie.

## Questions reformulées, découpées ou ajoutées

- La numérotation passe de Q1–Q42 à Qp.n, et tous les renvois internes ont été mis à jour.
- **Q1.7** est reformulée : les cotes partent de l'axe EF (et non du mur).
- **Q1.10 et Q1.11** découpent l'ancienne Q10 en deux : x<sub>F</sub> = −0,24 m, puis y<sub>F</sub> = −0,26 m. L'ancienne réponse « abscisse de F nulle » était fausse.
- **Q2.12 (ajoutée)** est un tracé de vérification graphique sur la flèche isolée (DR1) : concours des trois forces au point I, puis direction de A<sub>1/3</sub> (≈ 7,3°). La grille d'auto-évaluation compte 5 critères. La correction n'apparaît qu'après validation de Q2.9 et Q2.10.
- **Q5.1 (ajoutée, oui/non)** demande si la cote 2 940 peut servir de bras de levier en F.
- **Q5.2 (ajoutée)** demande FM<sub>x</sub> = 3,18 m.
- La figure SVG de la colonne isolée (partie 4) a été redessinée avec A décalé de l'axe EF et les cotes 240 et 450 prises depuis cet axe.
- Toutes les mentions « corrigé d'origine » ont été retirées de la page élève. Les écarts sont documentés ici seulement.

## Écart au gabarit (signalé)

- L'en-tête de la fenêtre « Imprimer les DR » disait « Quatre pages, une par document ». Ce texte est codé en dur dans le moteur et ne convient pas pour un seul DR. Il a été remplacé par « Une page par document réponse, à imprimer en A4 paysage. ».
- Aucune autre ligne du moteur n'a été modifiée.

## Vérifications effectuées

- **Moteur de correction** : 371 cas conformes. Ils couvrent, pour chaque question, la réponse juste, la réponse sans unité, une unité fausse, une valeur fausse, le signe opposé et une valeur convertie, ainsi que les cas limites : accents, majuscules, virgule ou point, signe moins typographique, notation scientifique, fautes de frappe et formulations alternatives.
- **Tests Playwright** :
  - aucune mention de la source sur la page ;
  - un sujet entièrement juste donne 20,0/20 ;
  - demi-point d'unité : messages « Unité manquante » et « Unité incorrecte » ;
  - en mode examen, ni correction ni note avant la remise, même à l'impression (« Copie non corrigée ») ;
  - confirmation de la remise en deux temps, puis tout est verrouillé et le chronomètre s'arrête ;
  - fenêtre des DR avec une page ;
  - panneau des documents et boutons de document des en-têtes de question ;
  - pas de défilement horizontal à 390 px ;
  - aucune erreur JavaScript.
