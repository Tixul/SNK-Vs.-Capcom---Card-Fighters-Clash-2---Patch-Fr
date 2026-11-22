# Card Fighters 2 Expand Edition — notes techniques (ROM, texte, police, affichage, images)

Tout ce qui suit a été mesuré sur la ROM japonaise (2 Mio, CRC32 `CCBCFDA7`, en-tête `CARD FIGHT 2`,
logiciel 0x0116). Adresses **fichier** sauf mention ; la cartouche est vue en CPU 0x200000 (fichier 0 =
CPU 0x200000) ; la 2e puce de la ROM traduite (fichier 0x200000) est vue en CPU 0x800000.

## Chaîne de construction
`tools/build.py` : ROM japonaise (contrôlée, `tools/rom_jp.py`) → ROM de 4 Mio → code ajouté (`vwf.bin`)
et police en 2e puce → détournements de l'afficheur → images (plaques, boutons, bandeaux, bulles, titre,
logo, tutoriel, duel, enseigne) → choix Oui/Non → clavier du nom → noms des cartes → textes traduits
encodés en 2e puce, pointeurs de la table réécrits → patch IPS **depuis la ROM japonaise**, revérifié.

## Texte
- Table maîtresse de pointeurs 32 bits (CPU) : **0xE0000-0xE61A8**, 6 250 entrées, 3 206 utilisées
  (FFFFFFFF = vide), lue en 0x2067FF. Textes japonais 0xE61A8-0xFE248. Une traduction anglaise amateur
  garde la même table au même endroit (même index).
- Afficheur 0x205FE2 (texte pointé par XIZ). Octet ≥ 0x20 = glyphe ; `0p xx` (p = 1..7) = glyphe
  p×256+xx ; `00` fin ; `0B` ligne ; `08 xx` locuteur (visage et nom) ; `17 xx` ; `09` `0A` `0C` `0D`
  (attentes, choix Oui/Non) ; `10`-`1F` variables (`10`/`11` noms des joueurs, `12` carte, `13` capacité,
  `14` deck, `15` paquet, `18` nombre).
- `0E` = menu : `0E N b c d` puis N × (x, y, 4 octets de navigation, libellé jusqu'à `0B`), puis la suite.
  Les fenêtres de menu ont la largeur japonaise exacte : un libellé plus large est coupé.
- Police japonaise (2 bpp, 16 octets par glyphe) : **0x8D00C + code × 16**. 0x20-0x5F ≈ ASCII sans
  minuscules (0x40 = espace, écrit `@` dans les fichiers), kana 0x60-0xFF, kanji 0x100-0x1DF et
  0x260-0x2B6 (`tools/kanji.txt`, transcrits à l'œil ; 0x280 est un signe « = »), icônes 0x1E5-0x1FF,
  boutons 0x200-0x20B, chiffres et lettres grasses 0x230-0x25A.
- L'afficheur clôt la ligne dès que la 18e tuile est ouverte : largeur sûre d'une ligne = **136 px**.
  Boîte de dialogue = 3 lignes.
- Lexique des règles (3100-3199) : le jeu coupe ses pages au nombre de tuiles ; le build les coupe aux mots.
- Choix Oui/Non (`0C`) : chaînes codées en dur 0x206199 / 0x2061A7, lues par `lda XIZ` en 0x206163 /
  0x206173 → chaînes traduites en 2e puce, adresses réécrites.

## Code ajouté (tools/asm/vwf.asm, 2e puce)
- 0x800000 : sauts (INIT, VWF, MONOCALL, objet du clavier) ; police 1 bpp 0x800400, largeurs 0x800C00,
  table d'expansion 1 bit → 2 bits 0x800D00 ; textes traduits dès 0x801000 ; tuiles d'images ajoutées
  dès le fichier 0x380000.
- Chasse variable : `call VWF ; jr +5` aux 5 sites `ld WA,QWA ; call 2459CC ; inc H ; inc L`
  (0x2060A8, 0x206181, 0x2063D0, 0x206456, 0x2065A5) ; `call INIT` en 0x205FE8 (position remise à 0).
  Glyphes ≥ 0x100 (icônes) et `@` occupent une tuile entière (alignement sur la grille). Les nombres
  (0x20661D) restent en chasse fixe. Variables du code en RAM 0x5FF0-0x5FFF (zone jamais utilisée).
- Chasse fixe forcée : grille du clavier (0x247979, objet 0x24789A) et champ du nom (0x25097B).
- La police 2 bpp d'origine est aussi réécrite (minuscules et accents à la place des kana, chasse fixe)
  pour les routines d'affichage non converties.

## Saisie du nom
Clavier (0x47A56, 0x47B3C) : page 1 = majuscules et accents, page 2 = minuscules, page 3 = page d'origine ;
tables ゛ ゜ vidées. Bandeau « NAME » (4 tuiles en 0x9F3C2) → « NOM ».

## Cartes
424 enregistrements de 64 octets en **0x806E4** : nom (16 octets), nom de capacité (16), caractéristiques.
Champs de 15 caractères + 00. Le nom s'affiche sur la face de la carte (55 px) et dans la liste (8 tuiles).
Textes de capacité : index 2001 + carte ; textes d'ambiance : 2501 + carte.

## Images
Méthode : vider la VRAM de l'écran voulu, puis chercher les 16 octets de chaque tuile dans la ROM (les
images sont stockées non compressées). Une tuile partagée par plusieurs images n'est modifiée que si
toutes ses copies doivent l'être.
- Décors (`tools/decors.py`) : répertoire 0x104044, enregistrements de 16 octets (carte, tuiles,
  largeur, hauteur, nombre de tuiles) ; tuiles chargées en VRAM 0x118+. Les plaques de lieu sont peintes
  dans le décor (rangées 1-2, colonnes 1-8) : `tools/plaques.py` les repeint ; si des tuiles manquent,
  le bloc de tuiles est recopié en 2e puce et l'enregistrement mis à jour.
- Table d'images 0x9AC40 (enregistrements de 10 octets) : boutons 11×2, bulles 12×4 (0xCF1D9 + k × 0x300),
  plaques de noms 6×2, plaques de lieu autonomes 8×2.
- Bandeaux : table 0x97C00-0x98070 (pointeur, nombre, largeur, hauteur, carte). Certains bandeaux
  partagent 2 octets (dernière ligne de l'un = première du suivant).
- Écran titre : cartes des plans 1 et 2 en 0x94243 / 0x9453F (20 × 19 mots), bloc de 248 tuiles en
  0xA60B3 (VRAM 0x10 + n) ; des sprites (bloc 0xC31CB) complètent le « ズ » d'origine. Le logo français
  est livré fini dans `tools/data/logo_fr.bin`.
- Tutoriel (7 étapes) et début de duel (« 先攻 / 後攻 ») : chaque case de l'image → adresse(s) de sa tuile
  (`tools/data/tuto_cases.json`, `duel_cases.json`).
- « HP » des plaques de duel (0xD68ED) et du terrain (0xBBB59) → « PV ». Enseigne « ジョイジョイ » de la
  carte de la ville (0xAAC22, 3 tuiles, fond couleur 3, encre couleur 1) → « JOYJOY ».

## Sauvegarde
Écrite dans la cartouche à partir de 0x1F8000 (1re puce) ; la traduction ne la déplace pas, et les outils
ignorent ce bloc en contrôlant la ROM.

## Menu de débogage
Le jeu contient le « COF DEBUG MENU » des développeurs (visionneuses de cartes et de textes, tests de
boutique, de don, de duel…), que la cartouche n'appelle pas. Le patch ne l'active pas.
