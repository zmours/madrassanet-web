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

RÈGLE : une carte par page qui mérite d'être partagée telle quelle. Le titre de
la carte n'est pas le titre SEO — il est plus court, il tient en trois lignes,
et il doit se comprendre sans contexte.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "og")
os.makedirs(OUT, exist_ok=True)

W, H = 1200, 630

# Palette reprise de styles.css
INDIGO_DARK = (26, 35, 126)     # #1A237E
INDIGO = (48, 63, 159)          # #303F9F
TEAL = (0, 121, 107)            # #00796B
CYAN_LIGHT = (128, 222, 234)    # #80DEEA
WHITE = (255, 255, 255)

# Le site utilise Inter, absent de la plupart des machines : on retombe sur la
# même pile que le CSS (system-ui), qui a des métriques proches.
FONT_CANDIDATES = {
    "bold": [
        "/Library/Fonts/Inter-Bold.ttf",
        os.path.expanduser("~/Library/Fonts/Inter-Bold.ttf"),
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "regular": [
        "/Library/Fonts/Inter-Regular.ttf",
        os.path.expanduser("~/Library/Fonts/Inter-Regular.ttf"),
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


def font(weight, size):
    for path in FONT_CANDIDATES[weight]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit("Aucune police utilisable trouvée — installez Inter ou DejaVu.")


def background():
    """Dégradé diagonal indigo → teal, avec deux voiles circulaires."""
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(0, W, 2):
            t = (x / W * 0.65) + (y / H * 0.35)
            if t < 0.5:
                k = t / 0.5
                c = tuple(int(INDIGO_DARK[i] + (INDIGO[i] - INDIGO_DARK[i]) * k) for i in range(3))
            else:
                k = (t - 0.5) / 0.5
                c = tuple(int(INDIGO[i] + (TEAL[i] - INDIGO[i]) * k) for i in range(3))
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(veil)
    d.ellipse([W - 260, -220, W + 260, 300], fill=(255, 255, 255, 16))
    d.ellipse([-200, H - 240, 300, H + 260], fill=(0, 191, 165, 28))
    return Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")


# Géométrie du « M » de la marque, dans un carré de 64 (identique à
# assets/logo.svg — toute retouche doit être reportée dans les deux).
M_POLY = [(17, 45), (17, 21), (18.8, 20.9), (32, 38), (45.2, 20.9), (47, 21), (47, 45),
          (40.4, 45), (40.4, 32.4), (33.7, 41), (30.3, 41), (23.6, 32.4), (23.6, 45)]


def logo(d, x, y, s, badge, letter, dot):
    """Marque MadrassaNET : pastille arrondie, « M », point."""
    k = s / 64.0
    d.rounded_rectangle([x, y, x + s, y + s], radius=15 * k, fill=badge)
    d.polygon([(x + px * k, y + py * k) for px, py in M_POLY], fill=letter)
    r = 3.2 * k
    d.ellipse([x + 32 * k - r, y + 52 * k - r, x + 32 * k + r, y + 52 * k + r], fill=dot)


def wrap(d, text, fnt, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if d.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def card(name, title, subtitle, pill=None):
    img = background()
    d = ImageDraw.Draw(img)
    margin = 78

    # Marque
    logo(d, margin, 56, 56, WHITE, INDIGO_DARK, TEAL)
    d.text((margin + 74, 66), "MadrassaNET", font=font("bold", 34), fill=WHITE)

    # Étiquette de rubrique
    top = 190
    if pill:
        f = font("bold", 22)
        tw = d.textlength(pill.upper(), font=f)
        d.rounded_rectangle([margin, 152, margin + tw + 40, 152 + 42], radius=21,
                            fill=(255, 255, 255, 255) if False else (255, 255, 255, 40),
                            outline=(255, 255, 255, 90), width=2)
        d.text((margin + 20, 161), pill.upper(), font=f, fill=CYAN_LIGHT)
        top = 226

    # Titre : on réduit le corps jusqu'à tenir en trois lignes
    for size in (66, 60, 54, 48, 44):
        f = font("bold", size)
        lines = wrap(d, title, f, W - margin * 2 - 20)
        if len(lines) <= 3:
            break
    y = top
    for line in lines:
        d.text((margin, y), line, font=f, fill=WHITE)
        y += int(size * 1.22)

    # Sous-titre
    if subtitle:
        fs = font("regular", 30)
        for line in wrap(d, subtitle, fs, W - margin * 2 - 20)[:2]:
            y += 12
            d.text((margin, y), line, font=fs, fill=CYAN_LIGHT)
            y += 40

    # Pied
    d.line([(margin, H - 96), (W - margin, H - 96)], fill=(255, 255, 255, 60), width=1)
    fp = font("bold", 26)
    d.text((margin, H - 72), "www.madrassanet.com", font=fp, fill=WHITE)
    fr = font("regular", 26)
    right = "FR · EN · AR"
    d.text((W - margin - d.textlength(right, font=fr), H - 72), right, font=fr, fill=CYAN_LIGHT)

    path = os.path.join(OUT, name + ".png")
    img.save(path, "PNG", optimize=True)
    return path, os.path.getsize(path)


# name, titre de la carte, sous-titre, étiquette
CARDS = [
    ("default", "Le logiciel des écoles coraniques, madrasas et associations",
     "Élèves, présences, bulletins et paiements — 1 € par élève et par an", None),
    ("tarifs", "1 € par élève et par an, tous modules inclus",
     "Abonnement annuel, sans frais de mise en service", "Tarifs"),
    ("blog", "Réglementation, sécurité et gestion des écoles associatives",
     "Le média pratique des structures éducatives", "Le blog"),
    ("madrasa", "Gérer votre madrasa sans paperasse",
     "Inscriptions par familles, présences, bulletins bilingues", "Solutions"),
    ("association-scolaire", "Le logiciel des associations scolaires",
     "Droits par rôle, finances, réinscriptions, RGPD", "Solutions"),
    ("ecole-arabe", "Le logiciel des écoles de langue arabe",
     "Interface complète en arabe, français et anglais", "Solutions"),
    ("bulletins", "Des bulletins PDF en deux clics",
     "Bilingues arabe-français, illimités, prêts à imprimer", "Fonctionnalités"),
    ("presences", "L'appel en 30 secondes, depuis le téléphone",
     "Présences, retards et absences justifiées", "Fonctionnalités"),
    ("finances", "Qui a payé, qui doit quoi",
     "Cotisations, relances et reçus automatiques", "Fonctionnalités"),
    ("templates", "Modèles gratuits pour votre école",
     "Feuille d'appel, suivi des paiements, bulletin type", "Ressources"),
    # Articles du blog
    ("blog-acm", "Faut-il déclarer votre école comme accueil collectif de mineurs ?",
     "Les seuils, les cas de bascule et la déclaration au SDJES", "Conformité"),
    ("blog-rgpd", "RGPD et données des élèves",
     "Vos obligations, expliquées simplement", "Conformité"),
    ("blog-reinscriptions", "Organiser les réinscriptions sans y passer des semaines",
     "Une méthode en quatre temps pour la rentrée", "Gestion"),
    ("blog-appel", "Faire l'appel sans papier",
     "Passer au pointage mobile en 4 étapes", "Gestion"),
    ("blog-paiements", "Gérer les paiements des familles",
     "Cotisations, relances et reçus sans y passer ses soirées", "Gestion"),
    ("blog-choisir", "Choisir un logiciel de gestion pour sa madrasa",
     "Les 8 critères à vérifier avant de signer", "Outils"),
    ("blog-gratuit-payant", "Logiciel gratuit ou payant : que choisir ?",
     "Le vrai coût = licence + temps + risque", "Outils"),
    ("blog-bulletins", "Des bulletins clairs en arabe et en français",
     "Bonnes pratiques en contexte bilingue", "Gestion"),
    ("blog-automatiser", "Les 10 tâches à automatiser dans une école",
     "Gagner des heures chaque semaine", "Outils"),
]

def logo_png():
    """Logo carré 512 px — publisher.logo des données structurées."""
    k = 512 / 64.0
    # même dégradé que assets/logo.svg, sinon la marque n'est pas la même
    # selon qu'on la voit dans un onglet ou dans un résultat de recherche
    grad = Image.new("RGB", (512, 512))
    gp = grad.load()
    for y in range(512):
        for x in range(512):
            t = (x + y) / 1022.0
            gp[x, y] = tuple(int(INDIGO[i] + (TEAL[i] - INDIGO[i]) * t) for i in range(3))
    mask = Image.new("L", (512, 512), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 511, 511], radius=15 * k, fill=255)
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.polygon([(px * k, py * k) for px, py in M_POLY], fill=WHITE)
    r = 3.2 * k
    d.ellipse([32 * k - r, 52 * k - r, 32 * k + r, 52 * k + r], fill=CYAN_LIGHT)
    path = os.path.join(OUT, "logo-512.png")
    img.save(path, "PNG", optimize=True)
    return path, os.path.getsize(path)


if __name__ == "__main__":
    total = 0
    path, size = logo_png()
    total += size
    print("%-28s %6d Ko" % (os.path.basename(path), round(size / 1024)))
    for name, title, subtitle, pill in CARDS:
        path, size = card(name, title, subtitle, pill)
        total += size
        print("%-28s %6d Ko" % (os.path.basename(path), round(size / 1024)))
    print("---\n%d images, %d Ko au total" % (len(CARDS) + 1, round(total / 1024)))
