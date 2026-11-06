#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les images de partage (Open Graph) du site.

    python3 tools/generate-og-images.py

Sortie : assets/og/*.png — 1200 × 630, moins de 300 Ko chacune.

POURQUOI CE FORMAT. WhatsApp, Facebook, LinkedIn et iMessage ne savent pas
afficher un SVG, et rognent tout ce qui s'éloigne du ratio 1,91:1. Une capture
d'écran de l'application, elle, devient illisible à la taille d'une vignette de
conversation. D'où ces cartes : du texte assez gros pour être lu sur un
téléphone, aux dimensions exactes attendues par les aperçus.

POURQUOI CENTRÉ (refonte du 30/10/2026). WhatsApp affiche le plus souvent un
grand aperçu au format 1,91:1, mais certaines versions réduisent l'image à une
petite vignette carrée découpée au centre. Tout est donc centré : dans ce carré
restent le logo et le cœur du titre, là où l'ancien gabarit, aligné à gauche,
perdait la marque et le début de la phrase.

RÈGLE : une carte par page qui mérite d'être partagée telle quelle. Le titre de
la carte n'est pas le titre SEO — il est plus court, il tient en trois lignes,
et il doit se comprendre sans contexte. Les mots entre *astérisques* passent
en ambre.

Les polices sont celles du site (Bricolage Grotesque, Instrument Sans, licence
OFL), rangées dans tools/polices/ pour que l'image soit la même sur toutes les
machines.
"""
import os
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "og")
POLICES = os.path.join(ROOT, "tools", "polices")
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 630

# Palette reprise de styles.css et de l'accueil
NUIT = (10, 16, 48)          # #0A1030
NUIT_2 = (24, 33, 90)        # #18215A
LUMIERE = (246, 185, 59)     # #F6B93B
LAGON = (61, 214, 195)       # #3DD6C3
CLAIR = (238, 240, 251)      # #EEF0FB
BRUME = (167, 174, 211)      # #A7AED3
MARQUE = (57, 73, 171)       # #3949AB, la pastille du logo

# La couleur d'accent de chaque rubrique du blog (cf. RUBRIQUES de build-blog.py)
ACCENTS = {
    "École en ligne": LUMIERE,
    "Conformité": (143, 155, 255),
    "Sécurité": (255, 138, 101),
    "Gestion": LAGON,
    "Outils": (197, 155, 255),
}


def police(famille, graisse, taille):
    f = ImageFont.truetype(os.path.join(POLICES, famille + ".ttf"), taille)
    f.set_variation_by_name(graisse)
    return f


def fond():
    """Dégradé nuit, halo ambre en haut à droite, halo lagon en bas à gauche."""
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(0, W, 2):
            t = (x / W * 0.6) + (y / H * 0.4)
            c = tuple(int(NUIT[i] + (NUIT_2[i] - NUIT[i]) * t) for i in range(3))
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
    # L'ambre seul, flouté sur le bleu nuit, vire au brun : il est posé sur un
    # halo indigo, plus petit et plus discret que lui.
    halos = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(halos)
    d.ellipse([W - 520, -380, W + 260, 340], fill=(88, 103, 232, 92))
    d.ellipse([W - 300, -200, W + 60, 160], fill=LUMIERE + (34,))
    d.ellipse([-300, H - 230, 330, H + 330], fill=LAGON + (52,))
    halos = halos.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), halos)
    # Deux orbites fines autour du halo ambre, comme sur les vignettes du blog
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(o)
    for r, a in ((190, 46), (300, 26)):
        od.ellipse([W - 120 - r, 60 - r, W - 120 + r, 60 + r], outline=LUMIERE + (a,), width=2)
    return Image.alpha_composite(img, o)


# Géométrie du « M » de la marque, dans un carré de 64 (identique à
# assets/logo.svg — toute retouche doit être reportée dans les deux).
M_POLY = [(17, 45), (17, 21), (18.8, 20.9), (32, 38), (45.2, 20.9), (47, 21), (47, 45),
          (40.4, 45), (40.4, 32.4), (33.7, 41), (30.3, 41), (23.6, 32.4), (23.6, 45)]


def logo(d, x, y, s, pastille, lettre, point):
    """Marque MadrassaNET : pastille arrondie, « M », point."""
    k = s / 64.0
    d.rounded_rectangle([x, y, x + s, y + s], radius=15 * k, fill=pastille)
    d.polygon([(x + px * k, y + py * k) for px, py in M_POLY], fill=lettre)
    r = 3.2 * k
    d.ellipse([x + 32 * k - r, y + 52 * k - r, x + 32 * k + r, y + 52 * k + r], fill=point)


def mots(titre):
    """[(mot, en_ambre)] : les mots entre *astérisques* passent en ambre."""
    out = []
    for m in re.finditer(r"\*([^*]+)\*|([^*]+)", titre):
        ambre = m.group(1) is not None
        for mot in (m.group(1) or m.group(2)).split():
            out.append((mot, ambre))
    return out


def couper(d, liste, f, largeur):
    lignes, courante = [], []
    for mot, ambre in liste:
        essai = " ".join(m for m, _ in courante + [(mot, ambre)])
        if courante and d.textlength(essai, font=f) > largeur:
            lignes.append(courante)
            courante = [(mot, ambre)]
        else:
            courante.append((mot, ambre))
    if courante:
        lignes.append(courante)
    return lignes


def centre(d, y, texte, f, couleur):
    d.text(((W - d.textlength(texte, font=f)) / 2, y), texte, font=f, fill=couleur)


def carte(nom, titre, sous_titre, etiquette=None):
    img = fond()
    d = ImageDraw.Draw(img)

    # Marque, centrée
    f_marque = police("BricolageGrotesque", "ExtraBold", 34)
    l_marque = d.textlength("MadrassaNET", font=f_marque)
    x0 = (W - (52 + 16 + l_marque)) / 2
    logo(d, x0, 46, 52, MARQUE, CLAIR, (128, 222, 234))
    d.text((x0 + 68, 52), "Madrassa", font=f_marque, fill=CLAIR)
    d.text((x0 + 68 + d.textlength("Madrassa", font=f_marque), 52), "NET", font=f_marque, fill=LAGON)

    # Étiquette : pastille de couleur + texte, centrées
    haut = 168
    if etiquette:
        accent = ACCENTS.get(etiquette, LUMIERE)
        f_et = police("InstrumentSans", "Bold", 22)
        texte = etiquette.upper()
        l = d.textlength(texte, font=f_et) + 4 * len(texte)   # interlettrage approché
        x = (W - (l + 22)) / 2
        d.ellipse([x, haut + 9, x + 12, haut + 21], fill=accent)
        cx = x + 22
        for c in texte:
            d.text((cx, haut), c, font=f_et, fill=accent)
            cx += d.textlength(c, font=f_et) + 4
        haut += 56
    else:
        haut += 14

    # Titre : on réduit le corps jusqu'à tenir en trois lignes, dans une
    # colonne de 940 px. Un « \n » dans le titre impose le retour à la ligne,
    # pour qu'un groupe de mots en ambre ne soit pas coupé en deux.
    # Moins de lignes vaut mieux qu'un corps plus grand : on prend la plus
    # grande taille où chaque morceau tient sur sa ligne, sinon la plus grande
    # qui tient en trois lignes.
    parties = titre.split("\n")
    essais = []
    for taille in (76, 70, 64, 58, 52):
        f = police("BricolageGrotesque", "ExtraBold", taille)
        essais.append((taille, f, [l for partie in parties for l in couper(d, mots(partie), f, 940)]))
    taille, f, lignes = next((x for x in essais if len(x[2]) == len(parties)),
                             next((x for x in essais if len(x[2]) <= 3), essais[-1]))
    pas = int(taille * 1.1)
    f_st = police("InstrumentSans", "Medium", 30)
    lignes_st = couper(d, [(m, False) for m in sous_titre.split()], f_st, 980)[:2] if sous_titre else []
    # Le bloc titre + sous-titre est centré entre l'étiquette et l'adresse.
    hauteur = len(lignes) * pas + (18 + 42 * len(lignes_st) if lignes_st else 0)
    y = haut + max(0, (H - 100 - haut - hauteur) // 2)
    espace = d.textlength(" ", font=f)
    for ligne in lignes:
        largeur = sum(d.textlength(m, font=f) for m, _ in ligne) + espace * (len(ligne) - 1)
        x = (W - largeur) / 2
        for mot, ambre in ligne:
            d.text((x, y), mot, font=f, fill=LUMIERE if ambre else (255, 255, 255))
            x += d.textlength(mot, font=f) + espace
        y += pas

    # Sous-titre
    if lignes_st:
        y += 18
        for ligne in lignes_st:
            centre(d, y, " ".join(m for m, _ in ligne), f_st, BRUME)
            y += 42

    # Pied : l'adresse, centrée
    f_url = police("InstrumentSans", "SemiBold", 24)
    centre(d, H - 62, "www.madrassanet.com", f_url, CLAIR)

    chemin = os.path.join(OUT, nom + ".png")
    img.convert("RGB").save(chemin, "PNG", optimize=True)
    return chemin, os.path.getsize(chemin)


# nom, titre de la carte, sous-titre, étiquette
CARTES = [
    ("default", "Gérez votre école.\nPassez *en ligne* à votre rythme.",
     "Appel, bulletins, inscriptions et paiements, et la visio quand il le faut", None),
    ("ecole-en-ligne", "Ouvrez votre école\n*en ligne,* à votre nom",
     "Cours en direct, rediffusions, inscriptions et paiement en ligne", "École en ligne"),
    ("soutien-scolaire", "Le logiciel des centres\nde *soutien scolaire*",
     "Groupes par niveau, suivi des parents, devoirs et cours en direct", "Soutien scolaire"),
    ("tarifs", "Un prix clair,\n*sans frais cachés*",
     "Gestion de l'école : 1 € par élève et par an · École en ligne : sur devis", "Tarifs"),
    ("blog", "Des guides pratiques\npour les *écoles associatives*",
     "Réglementation, sécurité, gestion et école en ligne", "Le blog"),
    ("madrasa", "Gérer votre madrasa\n*sans paperasse*",
     "Inscriptions par familles, appel sur mobile, bulletins bilingues", "Madrasa"),
    ("association-scolaire", "Le logiciel des\n*associations scolaires*",
     "Droits par rôle, réinscriptions, paiements des familles", "Association"),
    ("ecole-arabe", "Le logiciel des écoles\nde *langue arabe*",
     "Interface en arabe, français et anglais, de droite à gauche", "École de langue"),
    ("bulletins", "Des bulletins PDF\n*en deux clics*",
     "En français ou en arabe, prêts à imprimer", "Fonctionnalités"),
    ("presences", "L'appel en 30 secondes,\n*depuis le téléphone*",
     "Présences, retards et absences notifiées aux familles", "Fonctionnalités"),
    ("finances", "Qui a payé,\n*qui doit quoi*",
     "Paiements des familles par carte ou virement, relances", "Fonctionnalités"),
    ("templates", "Modèles gratuits\n*pour votre école*",
     "Feuille d'appel, suivi des paiements, bulletin type", "Ressources"),
    # Articles du blog : l'étiquette est la rubrique, qui donne sa couleur
    ("blog-acm", "Faut-il déclarer votre école comme\n*accueil collectif de mineurs ?*",
     "Les seuils, les cas de bascule et la déclaration au SDJES", "Conformité"),
    ("blog-rgpd", "RGPD et\n*données des élèves*",
     "Vos obligations, expliquées simplement", "Conformité"),
    ("blog-reinscriptions", "Organiser les réinscriptions\n*sans y passer des semaines*",
     "Une méthode en quatre temps pour la rentrée", "Gestion"),
    ("blog-appel", "Faire l'appel *sans papier*",
     "Passer au pointage mobile en 4 étapes", "Gestion"),
    ("blog-paiements", "Gérer les paiements\n*des familles*",
     "Cotisations, relances et reçus sans y passer ses soirées", "Gestion"),
    ("blog-choisir", "Choisir un logiciel de gestion\n*pour sa madrasa*",
     "Les 8 critères à vérifier avant de signer", "Outils"),
    ("blog-gratuit-payant", "Logiciel gratuit ou payant :\n*que choisir ?*",
     "Le vrai coût = licence + temps + risque", "Outils"),
    ("blog-bulletins", "Des bulletins clairs\n*en arabe et en français*",
     "Bonnes pratiques en contexte bilingue", "Gestion"),
    ("blog-automatiser", "Les 10 tâches\n*à automatiser* dans une école",
     "Gagner des heures chaque semaine", "Outils"),
]


# assets/og/logo-512.png (publisher.logo des données structurées) n'est plus
# généré ici : la refonte du 30/10/2026 ne touche pas au logo.

if __name__ == "__main__":
    total = 0
    for nom, titre, sous_titre, etiquette in CARTES:
        chemin, taille = carte(nom, titre, sous_titre, etiquette)
        total += taille
        alerte = "  ⚠ plus de 300 Ko : WhatsApp risque de l'ignorer" if taille > 300 * 1024 else ""
        print("%-28s %6d Ko%s" % (os.path.basename(chemin), round(taille / 1024), alerte))
    print("---\n%d images, %d Ko au total" % (len(CARTES), round(total / 1024)))
