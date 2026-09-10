#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère le blog MadrassaNET à partir de ses sources Markdown.

    python3 tools/build-blog.py             # génère tout
    python3 tools/build-blog.py --inventaire  # liste les articles, n'écrit rien

Entrée  : blog/_articles/*.md      un article par fichier (cf. ARCHITECTURE_BLOG.md)
          blog/_pages/*.md         pages du blog hors flux (rédaction…)
          blog/_auteurs.json       les signatures

Sortie  : blog/<slug>/index.html             les articles
          blog/index.html + blog/page/N/     la liste, paginée
          blog/rubrique/<r>/index.html       une page par rubrique
          blog/videos/index.html             les articles qui portent une vidéo
          blog/feed.xml                      flux RSS 2.0
          sitemap.xml                        bloc BLOG regénéré, avec lastmod
          sitemap-video.xml                  dès qu'une vidéo est déclarée
          llms.txt                           inventaire pour les assistants IA

RÈGLE — bibliothèque standard uniquement. Publier un article ne doit pas
dépendre d'un `pip install` : le jour où la chaîne casse, on ne publie plus.
Les deux autres scripts de tools/ ont des dépendances parce qu'ils tournent
trois fois par an ; celui-ci tourne à chaque publication.

RÈGLE — les liens des pages générées sont absolus (« /blog/… »). Ces pages
vivent à quatre profondeurs (blog/, blog/<slug>/, blog/page/2/,
blog/rubrique/<r>/) : un lien relatif y serait faux une fois sur deux.

RÈGLE — rien de ce qui est généré ne s'édite à la main. Toute correction se
fait dans la source Markdown, puis on relance le script.
"""
import html
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ARTICLES = os.path.join(ROOT, "blog", "_articles")
SRC_PAGES = os.path.join(ROOT, "blog", "_pages")
OUT_BLOG = os.path.join(ROOT, "blog")

SITE = "https://www.madrassanet.com"
MARQUE = "MadrassaNET"
PITCH = ("La solution complète de gestion scolaire pour écoles coraniques, "
         "madrasas et associations.")
PAR_PAGE = 9
MOTS_PAR_MINUTE = 200

# Le positionnement du blog, arrêté dans LIGNE_EDITORIALE.md §1. Une seule
# source pour la page d'accueil du blog, les flux et les métadonnées.
POSITIONNEMENT = ("Un média pratique pour les écoles associatives et les structures "
                  "éducatives : réglementation, sécurité, accueil des enfants, gestion "
                  "quotidienne et outils numériques.")

# Les quatre rubriques de LIGNE_EDITORIALE.md §2. L'ordre est celui d'affichage.
# « degrade » sert aux bannières et aux vignettes : une identité visuelle par
# rubrique, plutôt qu'un dégradé au hasard par article.
RUBRIQUES = {
    "conformite": {
        "nom": "Conformité",
        "titre": "Conformité des écoles associatives : statut, déclarations, contrôles",
        "description": ("Statut juridique de l'activité, déclarations, contrôles, RGPD, "
                        "assurances et subventions : ce que la règle demande à une école "
                        "associative, et comment y répondre."),
        "chapeau": ("Sous quel régime se trouve votre activité, ce qu'il faut déclarer, "
                    "à qui, et quels documents produire le jour où on vous les demande."),
        "emoji": "📑",
        "degrade": ("#1A237E", "#303F9F", "#00796B"),
    },
    "securite": {
        "nom": "Sécurité",
        "titre": "Sécurité et accueil des mineurs : locaux, encadrement, évacuation",
        "description": ("Locaux et ERP, exercices d'évacuation, taux d'encadrement, "
                        "protection des mineurs et gestion des urgences dans une école "
                        "associative."),
        "chapeau": ("Accueillir des enfants engage la responsabilité de l'association. "
                    "Voici ce que la sécurité demande, dans l'ordre où l'on peut s'en occuper."),
        "emoji": "🛡️",
        "degrade": ("#00695C", "#00897B", "#3949AB"),
    },
    "gestion": {
        "nom": "Gestion",
        "titre": "Gérer une école associative au quotidien : inscriptions, présences, paiements",
        "description": ("Inscriptions, présences, paiements, bulletins, réinscriptions et "
                        "trésorerie : les méthodes qui tiennent quand l'équipe est bénévole."),
        "chapeau": ("Tenir la maison sans y passer ses soirées : les méthodes qui marchent "
                    "quand l'équipe est bénévole et que la rentrée arrive."),
        "emoji": "🗂️",
        "degrade": ("#283593", "#3949AB", "#009688"),
    },
    "outils": {
        "nom": "Outils",
        "titre": "Outils numériques pour écoles coraniques et madrasas : comparatifs et guides",
        "description": ("Comparatifs, critères de choix d'un logiciel, passage du papier au "
                        "numérique et modèles à télécharger pour les écoles associatives."),
        "chapeau": ("Comparatifs, critères de choix et passage du papier au numérique — "
                    "y compris quand la réponse est « votre tableur suffit »."),
        "emoji": "🧰",
        "degrade": ("#303F9F", "#3F51B5", "#26A69A"),
    },
}

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]
JOURS_RFC = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MOIS_RFC = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FINE = "\u202f"   # espace fine insécable : devant ; ! ?
NBSP = "\u00a0"   # espace insécable : deux-points, guillemets français


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def erreur(message):
    """Un article mal formé arrête la génération : mieux vaut ne rien publier
    qu'un article aux métadonnées fausses, qu'on ne verra pas passer."""
    sys.stderr.write("ERREUR : %s\n" % message)
    sys.exit(1)


def slugifier(texte):
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = re.sub(r"[^a-zA-Z0-9]+", "-", texte).strip("-").lower()
    return texte or "section"


def date_fr(iso):
    """2026-09-10 → « 10 septembre 2026 »."""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return "%d %s %d" % (d.day, MOIS_FR[d.month - 1], d.year)


def date_rfc822(iso):
    """Format exigé par RSS 2.0. Heure fixée à 8 h, heure de Paris (+0200) :
    l'heure exacte de publication n'a aucun intérêt et rendrait le flux instable."""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return "%s, %02d %s %d 08:00:00 +0200" % (
        JOURS_RFC[d.weekday()], d.day, MOIS_RFC[d.month - 1], d.year)


def e(texte):
    """Échappement pour un contenu d'attribut ou de texte."""
    return html.escape(texte or "", quote=True)


# ---------------------------------------------------------------------------
# Lecture des sources
# ---------------------------------------------------------------------------

CLES_LISTE = {"chapitres", "articles_lies", "mots_cles"}


def lire_source(chemin):
    """Découpe un fichier source en (métadonnées, corps Markdown).

    Les métadonnées sont un bloc « clé: valeur » entre deux lignes « --- ».
    Une clé sans valeur suivie de lignes indentées donne une liste :

        chapitres:
          00:00 Pourquoi la question se pose
          01:12 Les trois régimes possibles
    """
    with open(chemin, encoding="utf-8") as f:
        brut = f.read()

    if not brut.startswith("---"):
        erreur("%s : le fichier doit commencer par un bloc « --- »." % chemin)

    fin = brut.find("\n---", 3)
    if fin == -1:
        erreur("%s : bloc de métadonnées non refermé par « --- »." % chemin)

    entete = brut[3:fin].strip("\n")
    corps = brut[fin + 4:].lstrip("\n")

    meta = {}
    courante = None
    for ligne in entete.split("\n"):
        if not ligne.strip() or ligne.strip().startswith("#"):
            continue
        if ligne[0] in " \t":
            if courante is None:
                erreur("%s : ligne indentée sans clé — « %s »" % (chemin, ligne.strip()))
            meta[courante].append(ligne.strip())
            continue
        if ":" not in ligne:
            erreur("%s : métadonnée sans « : » — « %s »" % (chemin, ligne.strip()))
        cle, valeur = ligne.split(":", 1)
        cle, valeur = cle.strip(), valeur.strip()
        if not valeur:
            meta[cle] = []
            courante = cle
        else:
            if cle in CLES_LISTE:
                meta[cle] = [v.strip() for v in valeur.split(",") if v.strip()]
            else:
                meta[cle] = valeur
            courante = None
    return meta, corps


def compter_mots(corps):
    """Mots du corps, hors blocs HTML bruts et hors balisage."""
    texte = re.sub(r"^::: html.*?^:::", " ", corps, flags=re.S | re.M)
    texte = re.sub(r"<[^>]+>", " ", texte)
    texte = re.sub(r"[#*|>`:\-\[\]()]", " ", texte)
    return len([m for m in texte.split() if any(c.isalnum() for c in m)])


# ---------------------------------------------------------------------------
# Rendu Markdown
# ---------------------------------------------------------------------------
# Sous-ensemble volontairement réduit : titres, paragraphes, listes, tableaux,
# liens, gras, italique, code — plus les conteneurs « ::: » de la charte du
# site. Tout ce qui sort de ce cadre passe par un bloc « ::: html », qui n'est
# ni échappé ni retouché : c'est ainsi que les schémas SVG des articles
# existants ont été conservés tels quels.

SENTINELLE = "\x00%d\x00"

# Conteneurs sans corps : ils marquent un emplacement dans le texte.
MARQUEURS = {"video"}


def typographie(t):
    """Typographie française : apostrophe courbe et espaces insécables.

    Ce n'est pas de la coquetterie : une ligne qui casse entre le dernier mot
    et son point d'interrogation se voit, et un titre d'article se partage.
    """
    t = t.replace("'", "’")
    t = re.sub(r" +([;!?])", FINE + r"\1", t)
    t = re.sub(r" +:", NBSP + ":", t)
    t = re.sub(r"« +", "«" + NBSP, t)
    t = re.sub(r" +»", NBSP + "»", t)
    return t


def rendre_inline(t):
    """Rend le balisage de niveau ligne. Le code et les URL sont mis à l'abri
    avant tout traitement : une URL ne doit jamais recevoir de typographie."""
    jetons = []

    def garder(fragment):
        jetons.append(fragment)
        return SENTINELLE % (len(jetons) - 1)

    t = re.sub(r"`([^`]+)`",
               lambda m: garder("<code>%s</code>" % html.escape(m.group(1))), t)

    def lien(m):
        texte, url = m.group(1), m.group(2)
        return garder('<a href="%s">%s</a>'
                      % (html.escape(url, quote=True), rendre_inline(texte)))

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lien, t)

    t = html.escape(t, quote=False)
    t = re.sub(r"&amp;([a-zA-Z][a-zA-Z0-9]{1,10}|#\d{2,5});", r"&\1;", t)

    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = typographie(t)

    for n, fragment in enumerate(jetons):
        t = t.replace(SENTINELLE % n, fragment)
    return t


def lire_attributs(reste):
    """« titre="X" lien="Y" » → dict."""
    return dict(re.findall(r'([a-z_]+)="([^"]*)"', reste))


def est_debut_de_bloc(ligne):
    return (not ligne.strip()
            or ligne.startswith(("#", ":::", "|", "- ", "* ", "> "))
            or re.match(r"^\d+\. ", ligne) is not None)


def rendre_blocs(lignes, ctx, profondeur=0):
    out = []
    i = 0
    while i < len(lignes):
        ligne = lignes[i]

        if not ligne.strip():
            i += 1
            continue

        # --- conteneurs « ::: nom attributs » -----------------------------
        if ligne.startswith(":::"):
            entete = ligne[3:].strip()
            nom = entete.split(" ")[0] if entete else ""
            attrs = lire_attributs(entete)
            i += 1
            if nom in MARQUEURS:
                # « ::: video » est un marqueur de position, pas un conteneur :
                # il n'a pas de corps et rien à refermer.
                out.append(rendre_conteneur(nom, attrs, [], ctx, profondeur))
                continue
            corps = []
            ferme = False
            while i < len(lignes):
                if lignes[i].rstrip() == ":::":
                    ferme = True
                    i += 1
                    break
                corps.append(lignes[i])
                i += 1
            if not ferme:
                erreur("%s : bloc « ::: %s » non refermé. Chaque conteneur se "
                       "termine par une ligne « ::: » seule."
                       % (ctx["article"].get("_fichier", "?"), nom))
            out.append(rendre_conteneur(nom, attrs, corps, ctx, profondeur))
            continue

        # --- titres -------------------------------------------------------
        m = re.match(r"^(#{2,4}) +(.*)$", ligne)
        if m:
            niveau = len(m.group(1))
            texte = m.group(2).strip()
            ident = slugifier(texte)
            if niveau == 2:
                ctx["sommaire"].append((ident, texte))
                out.append('<h2 id="%s">%s</h2>' % (ident, rendre_inline(texte)))
            else:
                out.append("<h%d>%s</h%d>" % (niveau, rendre_inline(texte), niveau))
            i += 1
            continue

        # --- tableau ------------------------------------------------------
        if ligne.startswith("|"):
            rangs = []
            while i < len(lignes) and lignes[i].startswith("|"):
                rangs.append(lignes[i])
                i += 1
            out.append(rendre_tableau(rangs))
            continue

        # --- listes -------------------------------------------------------
        if ligne.startswith(("- ", "* ")) or re.match(r"^\d+\. ", ligne):
            ordonnee = re.match(r"^\d+\. ", ligne) is not None
            items = []
            while i < len(lignes):
                courante = lignes[i]
                if courante.startswith(("- ", "* ")) or re.match(r"^\d+\. ", courante):
                    items.append(re.sub(r"^(?:[-*] |\d+\. )", "", courante).strip())
                elif courante.startswith("  ") and items:
                    items[-1] += " " + courante.strip()
                else:
                    break
                i += 1
            balise = "ol" if ordonnee else "ul"
            corps = "\n".join("  <li>%s</li>" % rendre_inline(it) for it in items)
            out.append("<%s>\n%s\n</%s>" % (balise, corps, balise))
            continue

        # --- citation -----------------------------------------------------
        if ligne.startswith("> "):
            citation = []
            while i < len(lignes) and lignes[i].startswith("> "):
                citation.append(lignes[i][2:].strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>"
                       % rendre_inline(" ".join(citation)))
            continue

        # --- paragraphe ---------------------------------------------------
        para = []
        while i < len(lignes) and not est_debut_de_bloc(lignes[i]):
            para.append(lignes[i].strip())
            i += 1
        out.append("<p>%s</p>" % rendre_inline(" ".join(para)))

    marge = "  " * profondeur
    return "\n".join(marge + bloc.replace("\n", "\n" + marge) for bloc in out)


def rendre_tableau(rangs):
    cellules = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rangs]
    if len(cellules) >= 2 and all(set(c) <= set("-: ") for c in cellules[1]):
        entete, corps = cellules[0], cellules[2:]
    else:
        entete, corps = None, cellules
    out = ["<table>"]
    if entete:
        out.append("  <thead>")
        out.append("    <tr>%s</tr>"
                   % "".join("<th>%s</th>" % rendre_inline(c) for c in entete))
        out.append("  </thead>")
    out.append("  <tbody>")
    for rang in corps:
        out.append("    <tr>%s</tr>"
                   % "".join("<td>%s</td>" % rendre_inline(c) for c in rang))
    out.append("  </tbody>")
    out.append("</table>")
    return "\n".join(out)


def rendre_conteneur(nom, attrs, corps, ctx, profondeur):
    """Les blocs « ::: » de la charte. Un nom inconnu arrête la génération :
    une faute de frappe ne doit pas se traduire par un bloc absent de la page."""

    if nom == "html":
        return "\n".join(corps)

    if nom in ("encadre", "attention"):
        classe = "alert-box warning" if nom == "attention" else "alert-box"
        return '<div class="%s">\n%s\n</div>' % (
            classe, rendre_blocs(corps, ctx, profondeur + 1))

    if nom == "figure":
        legende = attrs.get("legende", "")
        interne = "\n".join("  " + l for l in corps)
        bloc = ['<figure class="article-figure">', interne]
        if legende:
            bloc.append("  <figcaption>%s</figcaption>" % rendre_inline(legende))
        bloc.append("</figure>")
        return "\n".join(bloc)

    if nom == "cta":
        titre = attrs.get("titre", "Voir MadrassaNET en action")
        lien = attrs.get("lien", "/#contact")
        libelle = attrs.get("libelle", "Voir une démonstration →")
        return ('<div class="article-cta">\n'
                '  <div>\n'
                '    <h3>%s</h3>\n'
                '%s\n'
                '  </div>\n'
                '  <a href="%s" class="btn-lp primary">%s</a>\n'
                '</div>' % (rendre_inline(titre),
                            rendre_blocs(corps, ctx, profondeur + 2),
                            e(lien), rendre_inline(libelle)))

    if nom == "sources":
        ctx["a_sources"] = True
        verifie = ctx["article"].get("verifie_le")
        titre = "Sources"
        if verifie:
            titre += " <span class=\"sources-date\">— vérifiées le %s</span>" % date_fr(verifie)
        return ('<section class="article-sources">\n'
                '  <h2 id="sources">%s</h2>\n'
                '%s\n'
                '</section>' % (titre, rendre_blocs(corps, ctx, profondeur + 1)))

    if nom == "faq":
        return rendre_faq(corps, ctx, profondeur)

    if nom == "transcription":
        ctx["a_transcription"] = True
        return ('<details class="transcription">\n'
                '  <summary>Transcription de la vidéo</summary>\n'
                '  <div class="transcription-corps">\n'
                '%s\n'
                '  </div>\n'
                '</details>' % rendre_blocs(corps, ctx, profondeur + 2))

    if nom == "video":
        ctx["video_placee"] = True
        return rendre_video(ctx["article"])

    erreur("bloc « ::: %s » inconnu dans %s. Blocs disponibles : html, encadre, "
           "attention, figure, cta, sources, faq, transcription, video."
           % (nom, ctx["article"].get("_fichier", "?")))


def rendre_faq(corps, ctx, profondeur):
    """« #### Question » puis la réponse. Alimente aussi le JSON-LD FAQPage :
    c'est ce balisage que les assistants IA citent le plus volontiers."""
    paires = []
    question, reponse = None, []
    for ligne in corps:
        m = re.match(r"^#{3,4} +(.*)$", ligne)
        if m:
            if question:
                paires.append((question, reponse))
            question, reponse = m.group(1).strip(), []
        elif question is not None:
            reponse.append(ligne)
    if question:
        paires.append((question, reponse))
    if not paires:
        erreur("bloc « ::: faq » vide dans %s : chaque question commence par « #### »."
               % ctx["article"].get("_fichier", "?"))

    out = ['<section class="article-faq">', '  <h2 id="questions-frequentes">Questions fréquentes</h2>']
    for q, r in paires:
        rendu = rendre_blocs(r, ctx, 0)
        ctx["faq"].append((q, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", rendu)).strip()))
        out.append('  <details>')
        out.append('    <summary>%s</summary>' % rendre_inline(q))
        out.append('    <div>%s</div>' % rendu)
        out.append('  </details>')
    out.append('</section>')
    return "\n".join(out)


def rendre_video(a):
    """Façade cliquable : rien n'est demandé à YouTube avant le clic du lecteur.

    C'est ce qui permet de publier des vidéos sans bandeau de consentement, et
    accessoirement ce qui évite de payer 900 Ko de lecteur sur chaque article.
    """
    ident = a["video"]
    titre = a.get("video_titre") or a["titre"]
    miniature = a.get("video_miniature") or ("https://i.ytimg.com/vi/%s/maxresdefault.jpg" % ident)
    chapitres = a.get("chapitres") or []

    out = ['<div class="video-embed" data-video="%s">' % e(ident),
           '  <button type="button" class="video-embed-play" aria-label="Lire la vidéo : %s"'
           ' data-track="Video - Lecture" data-track-video="%s" data-track-article="%s">'
           % (e(titre), e(ident), e(a["slug"])),
           '    <img src="%s" alt="" width="1280" height="720" loading="lazy" decoding="async">' % e(miniature),
           '    <span class="video-embed-icon" aria-hidden="true"></span>',
           '    <span class="video-embed-titre">%s</span>' % e(titre),
           '  </button>',
           '</div>']

    if chapitres:
        out.append('<ol class="video-chapitres">')
        for c in chapitres:
            m = re.match(r"^((?:\d+:)?\d+:\d+) +(.*)$", c.strip())
            if not m:
                erreur("chapitre mal formé : « %s » (attendu « 01:12 Titre »)." % c)
            horodatage, libelle = m.group(1), m.group(2)
            out.append('  <li><button type="button" data-t="%d">'
                       '<span class="chapitre-t">%s</span> %s</button></li>'
                       % (en_secondes(horodatage), horodatage, rendre_inline(libelle)))
        out.append('</ol>')

    out.append('<p class="video-note">La vidéo se charge depuis YouTube au moment où '
               'vous cliquez : aucune donnée ne lui est transmise avant.</p>')
    return "\n".join(out)


def en_secondes(horodatage):
    parts = [int(p) for p in horodatage.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


# ---------------------------------------------------------------------------
# Gabarits
# ---------------------------------------------------------------------------
# Les gabarits sont des fonctions Python et non des fichiers de template :
# aucun moteur à installer, et les conditions (vidéo, pagination, rubrique) se
# lisent dans le même langage que le reste. Le prix à payer est du HTML dans
# du Python ; il se lit très bien tant qu'on n'y met pas de logique.

def entete(titre, description, canonical, og_image, og_type="website",
           jsonld=None, og_titre=None, og_description=None, alt_image=None,
           scripts=()):
    ld = ""
    if jsonld:
        ld = ('  <script type="application/ld+json">\n%s\n  </script>\n'
              % json.dumps(jsonld, ensure_ascii=False, indent=2))
    image = og_image if og_image.startswith("http") else SITE + og_image
    alt = alt_image or og_titre or titre
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>%(titre)s</title>
  <meta name="description" content="%(description)s">
  <link rel="canonical" href="%(canonical)s">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="%(og_titre)s">
  <meta property="og:description" content="%(og_description)s">
  <meta property="og:type" content="%(og_type)s">
  <meta property="og:url" content="%(canonical)s">
  <meta property="og:site_name" content="MadrassaNET">
  <meta property="og:locale" content="fr_FR">
  <meta property="og:image" content="%(image)s">
  <meta property="og:image:secure_url" content="%(image)s">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="%(alt)s">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="%(image)s">
  <meta name="twitter:image:alt" content="%(alt)s">
  <link rel="stylesheet" href="/styles.css">
  <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
  <link rel="alternate" type="application/rss+xml" title="Blog MadrassaNET" href="/blog/feed.xml">
%(ld)s  <script src="/assets/analytics.js" defer></script>
%(scripts)s</head>
<body>
""" % {"titre": e(titre), "description": e(description), "canonical": e(canonical),
       "og_titre": e(og_titre or titre), "og_description": e(og_description or description),
       "og_type": og_type, "image": e(image), "alt": e(alt), "ld": ld,
       "scripts": "".join('  <script src="%s" defer></script>\n' % src for src in scripts)}


def nav():
    return """<nav class="nav">
  <a href="/" class="nav-brand">
    <span class="nav-brand-icon"><img src="/assets/logo-mark.svg" alt="" width="22" height="22"></span>
    MadrassaNET
  </a>
  <div class="nav-links">
    <a href="/">Accueil</a>
    <a href="/#fonctionnalites">Fonctionnalités</a>
    <a href="/tarifs/">Tarifs</a>
    <a href="/blog/" aria-current="page">Blog</a>
    <a href="/#contact" class="nav-cta">Demander une démo →</a>
  </div>
</nav>
"""


def fil_ariane(niveaux):
    """niveaux : [(libellé, url ou None pour le niveau courant), …]"""
    morceaux = []
    for libelle, url in niveaux:
        if url:
            morceaux.append('<a href="%s">%s</a>' % (e(url), e(libelle)))
        else:
            morceaux.append("<span>%s</span>" % e(libelle))
    return ('<nav class="breadcrumb" aria-label="Fil d\'Ariane">\n  %s\n</nav>\n'
            % " › ".join(morceaux))


def pied():
    return """<footer class="footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="footer-logo"><span class="fi"><img src="/assets/logo-mark.svg" alt="" width="20" height="20"></span> MadrassaNET</div>
        <p>%(pitch)s</p>
      </div>
      <div class="footer-col">
        <h4>Solutions</h4>
        <ul>
          <li><a href="/madrasa/">Gestion de madrasa</a></li>
          <li><a href="/association-scolaire/">Association scolaire</a></li>
          <li><a href="/ecole-arabe/">École de langue arabe</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Le blog</h4>
        <ul>
%(rubriques)s
        </ul>
      </div>
      <div class="footer-col">
        <h4>Ressources</h4>
        <ul>
          <li><a href="/tarifs/">Tarifs</a></li>
          <li><a href="/templates/">Modèles à télécharger</a></li>
          <li><a href="/support/">Support</a></li>
          <li><a href="/blog/feed.xml">Flux RSS</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2025 MadrassaNET. Tous droits réservés.</span>
      <a href="/blog/redaction/" style="color:rgba(255,255,255,.8)">La rédaction et nos sources</a>
    </div>
  </div>
</footer>

</body>
</html>
""" % {"pitch": PITCH,
       "rubriques": "\n".join(
           '          <li><a href="/blog/rubrique/%s/">%s</a></li>' % (slug, r["nom"])
           for slug, r in RUBRIQUES.items() if slug in RUBRIQUES_ACTIVES)}


def appel_bas_de_page():
    return """<section class="lp-section alt subpage-cta">
  <div class="section-inner">
    <h2>Envie de voir MadrassaNET en action ?</h2>
    <p>Demandez une démonstration gratuite, adaptée à votre école coranique, madrasa ou association.</p>
    <div class="lp-actions" style="justify-content:center;">
      <a href="/#contact" class="btn-lp primary">📩 Nous contacter</a>
      <a href="/tarifs/" class="btn-lp ghost">Voir les tarifs</a>
    </div>
  </div>
</section>
"""


def banniere_svg(a, ident):
    """Bannière d'article : dégradé de la rubrique, émoji et titre de l'article.

    Générée plutôt que dessinée : neuf articles écrits à la main avaient neuf
    dégradés sans logique. Un dégradé par rubrique se reconnaît d'un article
    à l'autre.
    """
    r = RUBRIQUES[a["rubrique"]]
    c1, c2, c3 = r["degrade"]
    titre = a.get("banniere_titre") or r["nom"]
    sous_titre = a.get("banniere_sous_titre") or ""
    emoji = a.get("banniere_emoji") or r["emoji"]
    return """<div class="article-banner">
  <svg viewBox="0 0 1100 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%(alt)s">
    <defs><linearGradient id="bn-%(id)s" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%(c1)s"/><stop offset="0.55" stop-color="%(c2)s"/><stop offset="1" stop-color="%(c3)s"/></linearGradient></defs>
    <rect width="1100" height="300" fill="url(#bn-%(id)s)"/>
    <circle cx="940" cy="70" r="150" fill="#fff" opacity="0.05"/>
    <circle cx="170" cy="285" r="130" fill="#00BFA5" opacity="0.10"/>
    <text x="80" y="175" font-size="110">%(emoji)s</text>
    <text x="230" y="%(y1)d" font-family="Inter, sans-serif" font-size="40" font-weight="800" fill="#fff">%(titre)s</text>%(sous)s
  </svg>
</div>
""" % {"alt": e("%s — %s" % (titre, sous_titre) if sous_titre else titre),
       "id": ident, "c1": c1, "c2": c2, "c3": c3, "emoji": emoji,
       "titre": e(titre), "y1": 150 if sous_titre else 170,
       "sous": ('\n    <text x="230" y="200" font-family="Inter, sans-serif" '
                'font-size="24" font-weight="500" fill="#80DEEA">%s</text>' % e(sous_titre)
                if sous_titre else "")}


def vignette_svg(a, ident):
    r = RUBRIQUES[a["rubrique"]]
    c1, _, c3 = r["degrade"]
    emoji = a.get("banniere_emoji") or r["emoji"]
    return ('<svg viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%s">'
            '<defs><linearGradient id="vg-%s" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>'
            '<rect width="400" height="180" fill="url(#vg-%s)"/>'
            '<circle cx="335" cy="45" r="72" fill="#fff" opacity="0.06"/>'
            '<text x="40" y="108" font-size="54">%s</text>'
            '<rect x="120" y="80" width="150" height="12" rx="6" fill="#fff" opacity="0.85"/>'
            '<rect x="120" y="102" width="105" height="10" rx="5" fill="#fff" opacity="0.5"/>'
            '</svg>' % (e(r["nom"]), ident, c1, c3, ident, emoji))


def carte(a):
    """Carte d'article, utilisée par l'index, les rubriques et la page vidéos."""
    marqueur = ('<span class="blog-card-video" title="Cet article contient une vidéo">'
                '▶ Vidéo</span>' if a.get("video") else "")
    return """      <a class="blog-card" href="%(url)s">
        <span class="blog-card-media">
          %(svg)s
        </span>
        <div class="blog-card-body">
          <span class="blog-tag">%(rubrique)s</span>%(video)s
          <h3>%(titre)s</h3>
          <p>%(resume)s</p>
          <div class="blog-meta">
            <time datetime="%(iso)s">%(date)s</time>
            <span>%(minutes)d min de lecture</span>
          </div>
          <div class="blog-read">Lire l'article →</div>
        </div>
      </a>
""" % {"url": a["url"], "svg": vignette_svg(a, a["slug"]),
       "rubrique": e(RUBRIQUES[a["rubrique"]]["nom"]), "video": marqueur,
       "titre": rendre_inline(a["titre"]), "resume": rendre_inline(a.get("resume") or a["description"]),
       "iso": a["publie_le"], "date": date_fr(a["publie_le"]), "minutes": a["minutes"]}


# ---------------------------------------------------------------------------
# Page article
# ---------------------------------------------------------------------------

def choisir_lies(a, tous):
    """Trois articles à lire ensuite. Explicites si « articles_lies » est
    renseigné, sinon la même rubrique d'abord, complétée par les plus récents.

    Automatique parce qu'un maillage tenu à la main ne l'est pas : sur les neuf
    articles écrits avant ce générateur, aucun ne pointait vers les deux
    derniers publiés.
    """
    par_slug = {x["slug"]: x for x in tous}
    choisis = []
    for slug in a.get("articles_lies") or []:
        if slug not in par_slug:
            erreur("%s : « articles_lies » cite « %s », qui n'existe pas." % (a["_fichier"], slug))
        choisis.append(par_slug[slug])

    candidats = [x for x in tous if x["slug"] != a["slug"]]
    for filtre in (lambda x: x["rubrique"] == a["rubrique"], lambda x: True):
        for x in candidats:
            if len(choisis) >= 3:
                break
            if filtre(x) and x not in choisis:
                choisis.append(x)
    return choisis[:3]


def jsonld_article(a, auteur):
    url = SITE + a["url"]
    rubrique = RUBRIQUES[a["rubrique"]]
    image = a["og_image"] if a["og_image"].startswith("http") else SITE + a["og_image"]

    signature = {"@type": auteur["type"], "name": auteur["nom"]}
    if auteur.get("url"):
        signature["url"] = (auteur["url"] if auteur["url"].startswith("http")
                            else SITE + auteur["url"])

    article = {
        "@type": "Article",
        "headline": a["titre"],
        "description": a["description"],
        "image": image,
        "datePublished": a["publie_le"],
        "dateModified": a.get("modifie_le") or a["publie_le"],
        "author": signature,
        "publisher": {
            "@type": "Organization",
            "name": MARQUE,
            "url": SITE + "/",
            "logo": {"@type": "ImageObject", "url": SITE + "/assets/og/logo-512.png"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "articleSection": rubrique["nom"],
        "inLanguage": "fr-FR",
        "isAccessibleForFree": True,
        "wordCount": a["mots"],
        "timeRequired": "PT%dM" % a["minutes"],
    }
    if a.get("mots_cles"):
        article["keywords"] = ", ".join(a["mots_cles"])

    graphe = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
                {"@type": "ListItem", "position": 3, "name": rubrique["nom"],
                 "item": "%s/blog/rubrique/%s/" % (SITE, a["rubrique"])},
                {"@type": "ListItem", "position": 4, "name": a.get("titre_court") or a["titre"],
                 "item": url},
            ],
        },
        article,
    ]

    if a.get("video"):
        video = {
            "@type": "VideoObject",
            "name": a.get("video_titre") or a["titre"],
            "description": a.get("video_description") or a["description"],
            "thumbnailUrl": [a.get("video_miniature")
                             or "https://i.ytimg.com/vi/%s/maxresdefault.jpg" % a["video"]],
            "uploadDate": a.get("video_publie_le") or a["publie_le"],
            "embedUrl": "https://www.youtube-nocookie.com/embed/%s" % a["video"],
            "contentUrl": "https://www.youtube.com/watch?v=%s" % a["video"],
            "inLanguage": "fr-FR",
            "publisher": article["publisher"],
        }
        if a.get("video_duree"):
            video["duration"] = a["video_duree"]
        if a.get("chapitres"):
            video["hasPart"] = [
                {"@type": "Clip", "name": re.sub(r"^(?:\d+:)?\d+:\d+ +", "", c),
                 "startOffset": en_secondes(re.match(r"^((?:\d+:)?\d+:\d+)", c.strip()).group(1)),
                 "url": "%s#video" % url}
                for c in a["chapitres"]]
        graphe.append(video)

    if a["faq"]:
        graphe.append({
            "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": r}}
                           for q, r in a["faq"]],
        })

    return {"@context": "https://schema.org", "@graph": graphe}


def page_article(a, tous, auteurs):
    auteur = auteurs[a["auteur"]]
    rubrique = RUBRIQUES[a["rubrique"]]
    url = SITE + a["url"]

    meta = ['<span>Par %s</span>' % (
        '<a href="%s">%s</a>' % (e(auteur["url"]), e(auteur["nom"]))
        if auteur.get("url") else e(auteur["nom"]))]
    meta.append('<span><time datetime="%s">%s</time></span>'
                % (a["publie_le"], date_fr(a["publie_le"])))
    if a.get("modifie_le") and a["modifie_le"] != a["publie_le"]:
        meta.append('<span class="article-maj">Mis à jour le <time datetime="%s">%s</time></span>'
                    % (a["modifie_le"], date_fr(a["modifie_le"])))
    meta.append("<span>%d min de lecture</span>" % a["minutes"])

    sommaire = ""
    if a["sommaire"] and len(a["titres"]) >= 5:
        liens = "\n".join('    <li><a href="#%s">%s</a></li>' % (i, rendre_inline(t))
                          for i, t in a["titres"])
        sommaire = ('<nav class="article-sommaire" aria-label="Sommaire">\n'
                    '  <h2>Dans cet article</h2>\n  <ol>\n%s\n  </ol>\n</nav>\n' % liens)

    lies = "\n".join(
        '      <a class="related-card" href="%s"><span>%s</span><h3>%s</h3></a>'
        % (x["url"], e(RUBRIQUES[x["rubrique"]]["nom"]),
           rendre_inline(x.get("titre_court") or x["titre"]))
        for x in choisir_lies(a, tous))

    return "".join([
        entete(a["titre_seo"], a["description"], url, a["og_image"], "article",
               jsonld_article(a, auteur), a.get("og_titre") or a["titre"],
               a.get("og_description") or a["description"], a.get("og_image_alt"),
               scripts=("/assets/blog.js",) if a.get("video") else ()),
        nav(),
        banniere_svg(a, a["slug"]),
        fil_ariane([("Accueil", "/"), ("Blog", "/blog/"),
                    (rubrique["nom"], "/blog/rubrique/%s/" % a["rubrique"]),
                    (a.get("titre_court") or a["titre"], None)]),
        '\n<article>\n',
        '  <div class="article-head">\n',
        '    <a class="blog-tag" href="/blog/rubrique/%s/">%s</a>\n' % (a["rubrique"], e(rubrique["nom"])),
        "    <h1>%s</h1>\n" % rendre_inline(a["titre"]),
        '    <div class="article-meta">\n      %s\n    </div>\n'
        % '<span class="dot"></span>'.join(meta),
        '    <p class="article-lead">%s</p>\n' % rendre_inline(a["chapeau"]),
        "  </div>\n\n",
        '  <div class="prose">\n',
        sommaire,
        a["html"],
        "\n  </div>\n\n",
        '  <div class="article-related">\n    <h2>À lire aussi</h2>\n'
        '    <div class="related-grid">\n%s\n    </div>\n  </div>\n' % lies,
        "</article>\n\n",
        pied(),
    ])


# ---------------------------------------------------------------------------
# Pages de liste, flux, sitemaps
# ---------------------------------------------------------------------------

def barre_rubriques(active):
    liens = ['<a href="/blog/"%s>Tout</a>' % (' class="active"' if active == "tout" else "")]
    for slug, r in RUBRIQUES.items():
        if slug not in RUBRIQUES_ACTIVES:
            continue
        liens.append('<a href="/blog/rubrique/%s/"%s>%s %s</a>'
                     % (slug, ' class="active"' if active == slug else "",
                        r["emoji"], e(r["nom"])))
    if AVEC_VIDEOS:
        liens.append('<a href="/blog/videos/"%s>▶ Vidéos</a>'
                     % (' class="active"' if active == "videos" else ""))
    return ('<nav class="rubriques" aria-label="Rubriques du blog">\n  <div class="rubriques-inner">\n    %s\n  </div>\n</nav>\n'
            % "\n    ".join(liens))


def barre_pagination(base, page, total):
    if total <= 1:
        return ""
    def lien(n):
        return base if n == 1 else "%spage/%d/" % (base, n)
    out = ['<nav class="pagination" aria-label="Pagination des articles">']
    out.append('  <a href="%s" rel="prev" class="%s">← Plus récents</a>'
               % (lien(page - 1) if page > 1 else "#", "" if page > 1 else "desactive"))
    out.append('  <span>Page %d sur %d</span>' % (page, total))
    out.append('  <a href="%s" rel="next" class="%s">Plus anciens →</a>'
               % (lien(page + 1) if page < total else "#", "" if page < total else "desactive"))
    out.append("</nav>")
    return "\n".join(out) + "\n"


def page_liste(titre_seo, description, canonical, etiquette, h1, chapeau, articles,
               og_image, active, fil, base=None, page=1, total=1, jsonld=None,
               og_titre=None, og_description=None):
    cartes = "\n".join(carte(a) for a in articles) or (
        '      <p>Aucun article dans cette rubrique pour le moment.</p>')
    return "".join([
        entete(titre_seo, description, canonical, og_image, "website", jsonld,
               og_titre, og_description),
        nav(),
        '<header class="page-hero">\n  <div class="page-hero-inner">\n'
        '    <span class="lp-hero-tag">%s</span>\n    <h1>%s</h1>\n    <p>%s</p>\n'
        "  </div>\n</header>\n\n" % (e(etiquette), rendre_inline(h1), rendre_inline(chapeau)),
        fil_ariane(fil),
        barre_rubriques(active),
        '\n<section class="lp-section">\n  <div class="section-inner">\n    <div class="blog-grid">\n\n',
        cartes,
        "\n    </div>\n",
        barre_pagination(base or "/blog/", page, total) if base else "",
        "  </div>\n</section>\n\n",
        appel_bas_de_page(),
        pied(),
    ])


def page_generique(p, corps_html):
    """Les pages du blog qui ne sont pas des articles : /blog/redaction/ par
    exemple. Même habillage, pas de JSON-LD Article, absentes du flux."""
    return "".join([
        entete(p["titre_seo"], p["description"], SITE + p["url"], p["og_image"], "website",
               {"@context": "https://schema.org", "@type": "WebPage",
                "name": p["titre"], "description": p["description"],
                "url": SITE + p["url"], "inLanguage": "fr-FR",
                "isPartOf": {"@type": "Blog", "name": "Blog MadrassaNET",
                             "url": SITE + "/blog/"}}),
        nav(),
        '<header class="page-hero">\n  <div class="page-hero-inner">\n'
        '    <span class="lp-hero-tag">%s</span>\n    <h1>%s</h1>\n    <p>%s</p>\n'
        "  </div>\n</header>\n\n" % (e(p.get("etiquette", "📌 Le blog")),
                                     rendre_inline(p["titre"]), rendre_inline(p["chapeau"])),
        fil_ariane([("Accueil", "/"), ("Blog", "/blog/"), (p["titre_court"], None)]),
        '\n<div class="prose">\n', corps_html, "\n</div>\n\n",
        appel_bas_de_page(),
        pied(),
    ])


def page_404(articles):
    """La page d'erreur est générée ici parce qu'elle a besoin de la même barre
    de navigation et du même pied de page que le reste : la recopier à la main
    revenait à la voir vieillir toute seule.

    GitHub Pages sert 404.html pour toute URL inconnue du domaine.
    """
    recents = "\n".join(carte(a) for a in articles[:3])
    return "".join([
        entete("Page introuvable | MadrassaNET",
               "Cette page n'existe pas ou plus. Voici par où reprendre : le blog, "
               "les tarifs et le centre d'aide de MadrassaNET.",
               SITE + "/404.html", "/assets/og/blog.png").replace(
            '<meta name="robots" content="index, follow">',
            '<meta name="robots" content="noindex, follow">'),
        nav(),
        '<section class="erreur-404">\n'
        '  <div class="code">404</div>\n'
        '  <h1>Cette page n\'existe pas, ou plus</h1>\n'
        "  <p>Le lien est peut-être incomplet, ou l'article a changé d'adresse. "
        'Le sommaire du blog et le centre d\'aide sont les deux endroits où '
        "retrouver ce que vous cherchiez.</p>\n"
        '  <div class="lp-actions" style="justify-content:center;">\n'
        '    <a href="/blog/" class="btn-lp primary">Aller au blog</a>\n'
        '    <a href="/support/" class="btn-lp outline">Centre d\'aide</a>\n'
        "  </div>\n</section>\n\n",
        barre_rubriques(""),
        '\n<section class="lp-section">\n  <div class="section-inner">\n'
        "    <h2>Les derniers articles</h2>\n"
        '    <div class="blog-grid">\n\n%s\n    </div>\n  </div>\n</section>\n\n' % recents,
        pied(),
    ])


def ecrire_robots(avec_video):
    """robots.txt : le script ne gère que la liste des sitemaps, entre marqueurs.
    Une ligne « Sitemap: » qui pointe vers un fichier absent est une erreur que
    personne ne remarque — autant qu'elle suive la réalité toute seule."""
    chemin = os.path.join(ROOT, "robots.txt")
    with open(chemin, encoding="utf-8") as f:
        contenu = f.read()
    debut, fin = "# SITEMAPS:DEBUT", "# SITEMAPS:FIN"
    if debut not in contenu or fin not in contenu:
        erreur("robots.txt doit contenir les marqueurs %s et %s." % (debut, fin))
    lignes = ["Sitemap: %s/sitemap.xml" % SITE]
    if avec_video:
        lignes.append("Sitemap: %s/sitemap-video.xml" % SITE)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("%s%s\n%s\n%s%s" % (contenu.split(debut)[0], debut,
                                     "\n".join(lignes), fin, contenu.split(fin)[1]))


def absolutiser(html_article):
    """Dans un flux RSS, un lien « /blog/x/ » ne mène nulle part."""
    html_article = re.sub(r'href="/', 'href="%s/' % SITE, html_article)
    return re.sub(r'src="/', 'src="%s/' % SITE, html_article)


def flux_rss(articles):
    items = []
    for a in articles[:15]:
        items.append("""  <item>
    <title>%(titre)s</title>
    <link>%(url)s</link>
    <guid isPermaLink="true">%(url)s</guid>
    <pubDate>%(date)s</pubDate>
    <category>%(rubrique)s</category>
    <description>%(chapeau)s</description>
    <content:encoded><![CDATA[%(corps)s]]></content:encoded>
  </item>""" % {"titre": e(a["titre"]), "url": SITE + a["url"],
                "date": date_rfc822(a["publie_le"]),
                "rubrique": e(RUBRIQUES[a["rubrique"]]["nom"]),
                "chapeau": e(a["chapeau"]),
                "corps": absolutiser(a["html"])})

    maj = date_rfc822(articles[0]["publie_le"]) if articles else date_rfc822(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel>
  <title>Blog MadrassaNET</title>
  <link>%(site)s/blog/</link>
  <atom:link href="%(site)s/blog/feed.xml" rel="self" type="application/rss+xml"/>
  <description>%(desc)s</description>
  <language>fr-FR</language>
  <lastBuildDate>%(maj)s</lastBuildDate>
  <image>
    <url>%(site)s/assets/og/blog.png</url>
    <title>Blog MadrassaNET</title>
    <link>%(site)s/blog/</link>
  </image>
%(items)s
</channel>
</rss>
""" % {"site": SITE, "desc": e(POSITIONNEMENT), "maj": maj, "items": "\n".join(items)}


def bloc_sitemap(articles, pages, nb_pages):
    """Le bloc que le script régénère dans sitemap.xml. Les pages hors blog
    restent tenues à la main : elles changent trois fois par an."""
    out = []

    def url(loc, lastmod, changefreq, priority):
        out.append("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n"
                   "    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n  </url>"
                   % (loc, lastmod, changefreq, priority))

    dernier = max([a.get("modifie_le") or a["publie_le"] for a in articles] or ["2026-09-10"])
    url(SITE + "/blog/", dernier, "weekly", "0.7")
    for n in range(2, nb_pages + 1):
        url("%s/blog/page/%d/" % (SITE, n), dernier, "weekly", "0.4")
    for slug in RUBRIQUES:
        dans = [a for a in articles if a["rubrique"] == slug]
        if dans:
            url("%s/blog/rubrique/%s/" % (SITE, slug),
                max(a.get("modifie_le") or a["publie_le"] for a in dans), "weekly", "0.6")
    if any(a.get("video") for a in articles):
        url(SITE + "/blog/videos/", dernier, "weekly", "0.6")
    for a in articles:
        url(SITE + a["url"], a.get("modifie_le") or a["publie_le"], "monthly", "0.6")
    for p in pages:
        url(SITE + p["url"], p.get("modifie_le") or p["publie_le"], "yearly", "0.4")
    return "\n".join(out)


def ecrire_sitemap(articles, pages, nb_pages):
    chemin = os.path.join(ROOT, "sitemap.xml")
    with open(chemin, encoding="utf-8") as f:
        contenu = f.read()
    debut, fin = "<!-- BLOG:DEBUT -->", "<!-- BLOG:FIN -->"
    if debut not in contenu or fin not in contenu:
        erreur("sitemap.xml doit contenir les marqueurs %s et %s autour du bloc du blog."
               % (debut, fin))
    avant = contenu.split(debut)[0]
    apres = contenu.split(fin)[1]
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("%s%s\n%s\n%s%s" % (avant, debut, bloc_sitemap(articles, pages, nb_pages),
                                    fin, apres))


def sitemap_video(articles):
    videos = [a for a in articles if a.get("video")]
    if not videos:
        return None
    items = []
    for a in videos:
        items.append("""  <url>
    <loc>%(url)s</loc>
    <video:video>
      <video:thumbnail_loc>%(miniature)s</video:thumbnail_loc>
      <video:title>%(titre)s</video:title>
      <video:description>%(desc)s</video:description>
      <video:player_loc>%(embed)s</video:player_loc>
      <video:publication_date>%(date)s</video:publication_date>
      <video:family_friendly>yes</video:family_friendly>
      <video:live>no</video:live>
    </video:video>
  </url>""" % {"url": SITE + a["url"],
               "miniature": e(a.get("video_miniature")
                              or "https://i.ytimg.com/vi/%s/maxresdefault.jpg" % a["video"]),
               "titre": e(a.get("video_titre") or a["titre"]),
               "desc": e(a.get("video_description") or a["description"]),
               "embed": "https://www.youtube-nocookie.com/embed/%s" % e(a["video"]),
               "date": (a.get("video_publie_le") or a["publie_le"]) + "T08:00:00+02:00"}
        )
    return ("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
%s
</urlset>
""" % "\n".join(items))


def fichier_llms(articles):
    """llms.txt — chantier §8.2-5 du plan marketing. Une part croissante des
    « quel logiciel pour gérer une école coranique ? » se pose à un assistant,
    qui ne lira pas le JavaScript de la page : autant lui donner le plan."""
    lignes = ["# MadrassaNET", "", "> %s" % PITCH.rstrip("."), "",
              "MadrassaNET est un logiciel de gestion scolaire pour écoles coraniques, "
              "madrasas, écoles de langue arabe et associations scolaires. Tarif public : "
              "1 € par élève et par an. Interface française et arabe, bulletins bilingues, "
              "présences, paiements, réinscriptions.", "",
              "## Pages principales", "",
              "- [Accueil](%s/): présentation du produit et formulaire de contact" % SITE,
              "- [Tarifs](%s/tarifs/): les trois niveaux d'abonnement, gratuité pour les associations en difficulté" % SITE,
              "- [Gestion de madrasa](%s/madrasa/): la solution pour une madrasa" % SITE,
              "- [Association scolaire](%s/association-scolaire/): la solution pour une association loi 1901" % SITE,
              "- [École de langue arabe](%s/ecole-arabe/): la solution pour une école de langue" % SITE,
              "- [Modèles à télécharger](%s/templates/): feuilles d'appel, bulletins, modèles de gestion" % SITE,
              "- [Support](%s/support/): centre d'aide et questions fréquentes" % SITE,
              "", "## Blog", "",
              "%s" % POSITIONNEMENT, ""]
    for slug, r in RUBRIQUES.items():
        dans = [a for a in articles if a["rubrique"] == slug]
        if not dans:
            continue
        lignes.append("### %s" % r["nom"])
        lignes.append("")
        for a in dans:
            lignes.append("- [%s](%s%s): %s" % (a["titre"], SITE, a["url"], a["description"]))
        lignes.append("")
    lignes += ["## Mentions", "",
               "- Les articles de conformité citent leurs sources publiques et ne constituent "
               "pas un conseil juridique.",
               "- [La rédaction et ses sources](%s/blog/redaction/)" % SITE,
               "- [Flux RSS du blog](%s/blog/feed.xml)" % SITE, ""]
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# Chaîne de génération
# ---------------------------------------------------------------------------

AVERTISSEMENTS = []

# Rubriques qui comptent au moins un article publié. Renseigné par main() avant
# toute écriture : une rubrique vide ne doit apparaître dans aucune navigation,
# sinon le menu propose un 404.
RUBRIQUES_ACTIVES = set()
AVEC_VIDEOS = False


def avertir(message):
    AVERTISSEMENTS.append(message)


def charger_auteurs():
    """Les signatures. Un auteur nommé est un signal de crédibilité que Google
    attend sur des sujets réglementaires ; « l'équipe » est le repli, pas la cible."""
    chemin = os.path.join(ROOT, "blog", "_auteurs.json")
    if not os.path.exists(chemin):
        erreur("blog/_auteurs.json est absent.")
    with open(chemin, encoding="utf-8") as f:
        auteurs = json.load(f)
    auteurs = {k: v for k, v in auteurs.items() if not k.startswith("_")}
    for cle, a in auteurs.items():
        for champ in ("nom", "type"):
            if champ not in a:
                erreur("blog/_auteurs.json : « %s » n'a pas de champ « %s »." % (cle, champ))
    return auteurs


def preparer(meta, corps, fichier, auteurs):
    slug = meta.get("slug") or os.path.basename(fichier)[:-3]
    a = dict(meta)
    a["_fichier"] = fichier
    a["slug"] = slug
    a["url"] = "/blog/%s/" % slug

    for champ in ("titre", "description", "chapeau", "rubrique", "publie_le"):
        if not a.get(champ):
            erreur("%s : métadonnée obligatoire manquante — « %s »." % (fichier, champ))

    if a["rubrique"] not in RUBRIQUES:
        erreur("%s : rubrique « %s » inconnue. Attendu : %s."
               % (fichier, a["rubrique"], ", ".join(RUBRIQUES)))
    for champ in ("publie_le", "modifie_le", "verifie_le", "video_publie_le"):
        if a.get(champ):
            try:
                datetime.strptime(a[champ], "%Y-%m-%d")
            except ValueError:
                erreur("%s : « %s » doit être une date AAAA-MM-JJ, reçu « %s »."
                       % (fichier, champ, a[champ]))

    a["auteur"] = a.get("auteur", "equipe")
    if a["auteur"] not in auteurs:
        erreur("%s : auteur « %s » absent de blog/_auteurs.json." % (fichier, a["auteur"]))

    a["titre_seo"] = a.get("titre_seo") or "%s | %s" % (a["titre"], MARQUE)
    a["og_image"] = a.get("og_image") or "/assets/og/blog.png"
    a["sommaire"] = a.get("sommaire", "oui") != "non"
    a["mots"] = compter_mots(corps)
    a["minutes"] = max(1, round(a["mots"] / MOTS_PAR_MINUTE))

    if len(a["titre"]) > 110:
        avertir("%s : le titre fait %d caractères ; au-delà de 110, Google le réécrit."
                % (slug, len(a["titre"])))
    if not 70 <= len(a["description"]) <= 165:
        avertir("%s : la meta description fait %d caractères (viser 70 à 165)."
                % (slug, len(a["description"])))
    chemin_og = os.path.join(ROOT, a["og_image"].lstrip("/"))
    if not a["og_image"].startswith("http") and not os.path.exists(chemin_og):
        avertir("%s : l'image de partage %s n'existe pas — ajoutez-la dans "
                "tools/generate-og-images.py." % (slug, a["og_image"]))

    ctx = {"article": a, "faq": [], "sommaire": [], "video_placee": False,
           "a_sources": False, "a_transcription": False}
    html_corps = rendre_blocs(corps.split("\n"), ctx, 1)

    if a.get("video") and not ctx["video_placee"]:
        html_corps = "  " + rendre_video(a).replace("\n", "\n  ") + "\n" + html_corps
        avertir("%s : vidéo déclarée sans bloc « ::: video » ; le lecteur a été "
                "placé en tête d'article." % slug)
    if a.get("video") and not ctx["a_transcription"]:
        avertir("%s : vidéo sans bloc « ::: transcription ». C'est la transcription "
                "qui fait indexer le contenu de la vidéo." % slug)
    if a["rubrique"] in ("conformite", "securite"):
        if not ctx["a_sources"]:
            avertir("%s : article de %s sans bloc « ::: sources » (LIGNE_EDITORIALE §4.2)."
                    % (slug, RUBRIQUES[a["rubrique"]]["nom"]))
        if "conseil juridique" not in corps:
            avertir("%s : article de %s sans la mention « ceci n'est pas un conseil "
                    "juridique » (LIGNE_EDITORIALE §4.3)." % (slug, RUBRIQUES[a["rubrique"]]["nom"]))
        if not a.get("verifie_le"):
            avertir("%s : article de %s sans « verifie_le » : la date de vérification "
                    "des sources est ce qui empêche un article juste de devenir faux."
                    % (slug, RUBRIQUES[a["rubrique"]]["nom"]))

    a["html"] = html_corps
    a["faq"] = ctx["faq"]
    a["titres"] = ctx["sommaire"]
    return a


def nettoyer(pages_total, rubriques_actives, avec_videos):
    """Supprime ce que le générateur avait produit et qui n'a plus de raison
    d'être : une page 3 après un regroupement d'articles, une rubrique vidée,
    le sitemap vidéo du jour où la dernière vidéo est retirée.

    Ne touche QUE ces emplacements-là, jamais un dossier d'article : une URL
    d'article qui disparaît demande une redirection, donc une décision. Le
    générateur se contente alors d'avertir.
    """
    retires = []

    def retirer(relatif):
        chemin = os.path.join(ROOT, relatif)
        if not os.path.exists(chemin):
            return
        if os.path.isdir(chemin):
            for racine, dossiers, fichiers in os.walk(chemin, topdown=False):
                for f in fichiers:
                    os.remove(os.path.join(racine, f))
                for d in dossiers:
                    os.rmdir(os.path.join(racine, d))
            os.rmdir(chemin)
        else:
            os.remove(chemin)
        retires.append(relatif)

    dossier_pages = os.path.join(OUT_BLOG, "page")
    if os.path.isdir(dossier_pages):
        for nom in os.listdir(dossier_pages):
            if not nom.isdigit() or int(nom) > pages_total:
                retirer("blog/page/%s" % nom)
        if not os.listdir(dossier_pages):
            retirer("blog/page")

    dossier_rubriques = os.path.join(OUT_BLOG, "rubrique")
    if os.path.isdir(dossier_rubriques):
        for nom in os.listdir(dossier_rubriques):
            if nom not in rubriques_actives:
                retirer("blog/rubrique/%s" % nom)

    if not avec_videos:
        retirer("blog/videos")
        retirer("sitemap-video.xml")

    return retires


def ecrire(chemin_relatif, contenu):
    chemin = os.path.join(ROOT, chemin_relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    return chemin_relatif


def main():
    inventaire_seul = "--inventaire" in sys.argv
    auteurs = charger_auteurs()

    if not os.path.isdir(SRC_ARTICLES):
        erreur("blog/_articles/ est absent : aucune source à générer.")

    articles, brouillons = [], []
    for nom in sorted(os.listdir(SRC_ARTICLES)):
        if not nom.endswith(".md"):
            continue
        meta, corps = lire_source(os.path.join(SRC_ARTICLES, nom))
        if meta.get("brouillon") == "oui":
            brouillons.append(nom)
            continue
        articles.append(preparer(meta, corps, "blog/_articles/" + nom, auteurs))

    articles.sort(key=lambda a: (a["publie_le"], a["slug"]), reverse=True)

    pages = []
    if os.path.isdir(SRC_PAGES):
        for nom in sorted(os.listdir(SRC_PAGES)):
            if not nom.endswith(".md"):
                continue
            meta, corps = lire_source(os.path.join(SRC_PAGES, nom))
            p = dict(meta)
            p["slug"] = p.get("slug") or nom[:-3]
            p["url"] = "/blog/%s/" % p["slug"]
            p["titre_seo"] = p.get("titre_seo") or "%s | %s" % (p["titre"], MARQUE)
            p["titre_court"] = p.get("titre_court") or p["titre"]
            p["og_image"] = p.get("og_image") or "/assets/og/blog.png"
            p["publie_le"] = p.get("publie_le") or "2026-09-10"
            ctx = {"article": p, "faq": [], "sommaire": [], "video_placee": False,
                   "a_sources": False, "a_transcription": False}
            p["html"] = rendre_blocs(corps.split("\n"), ctx, 1)
            pages.append(p)

    if inventaire_seul:
        print("%-52s %-12s %-12s %6s %5s" % ("slug", "rubrique", "publié", "mots", "min"))
        for a in articles:
            print("%-52s %-12s %-12s %6d %5d"
                  % (a["slug"], a["rubrique"], a["publie_le"], a["mots"], a["minutes"]))
        for nom in brouillons:
            print("%-52s %s" % (nom[:-3], "— BROUILLON, non généré"))
        for m in AVERTISSEMENTS:
            print("  ⚠ %s" % m)
        return

    global RUBRIQUES_ACTIVES, AVEC_VIDEOS
    RUBRIQUES_ACTIVES = {a["rubrique"] for a in articles}
    AVEC_VIDEOS = any(a.get("video") for a in articles)
    for slug, r in RUBRIQUES.items():
        if slug not in RUBRIQUES_ACTIVES:
            avertir("rubrique « %s » sans aucun article : ni page ni lien de menu. "
                    "Le prochain sujet du backlog (LIGNE_EDITORIALE §6) la remplira."
                    % r["nom"])

    retires = nettoyer(max(1, (len(articles) + PAR_PAGE - 1) // PAR_PAGE),
                       RUBRIQUES_ACTIVES, AVEC_VIDEOS)

    ecrits = []

    # Articles
    for a in articles:
        ecrits.append(ecrire("blog/%s/index.html" % a["slug"], page_article(a, articles, auteurs)))

    # Pages hors flux
    for p in pages:
        ecrits.append(ecrire("blog/%s/index.html" % p["slug"], page_generique(p, p["html"])))

    # Index paginé
    pages_total = max(1, (len(articles) + PAR_PAGE - 1) // PAR_PAGE)
    for n in range(1, pages_total + 1):
        tranche = articles[(n - 1) * PAR_PAGE: n * PAR_PAGE]
        suffixe = "" if n == 1 else " — page %d" % n
        canonical = SITE + ("/blog/" if n == 1 else "/blog/page/%d/" % n)
        jsonld = None
        if n == 1:
            jsonld = {
                "@context": "https://schema.org",
                "@graph": [
                    {"@type": "Blog", "name": "Blog MadrassaNET", "url": SITE + "/blog/",
                     "description": POSITIONNEMENT, "inLanguage": "fr-FR",
                     "publisher": {"@type": "Organization", "name": MARQUE, "url": SITE + "/"},
                     "blogPost": [{"@type": "BlogPosting", "headline": a["titre"],
                                   "url": SITE + a["url"], "datePublished": a["publie_le"]}
                                  for a in articles[:PAR_PAGE]]},
                    {"@type": "BreadcrumbList", "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "Accueil", "item": SITE + "/"},
                        {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"}]},
                ]}
        contenu = page_liste(
            "Réglementation, sécurité et gestion des écoles associatives — le blog | MadrassaNET" + suffixe,
            "Réglementation, sécurité, accueil des enfants, gestion quotidienne et outils "
            "numériques : le média pratique des écoles associatives et des structures éducatives.",
            canonical, "📚 Le blog",
            "Réglementation, sécurité et gestion des écoles associatives",
            "Un média pratique pour les écoles associatives et les structures éducatives : ce que "
            "dit la règle, comment s'y conformer, et comment tenir la maison au quotidien. Écrit "
            "pour les directeurs, secrétaires et bénévoles.",
            tranche, "/assets/og/blog.png", "tout",
            [("Accueil", "/"), ("Blog", None)] if n == 1
            else [("Accueil", "/"), ("Blog", "/blog/"), ("Page %d" % n, None)],
            base="/blog/", page=n, total=pages_total, jsonld=jsonld,
            og_titre="Le blog MadrassaNET — réglementation, sécurité et gestion des écoles associatives" + suffixe,
            og_description="Ce que dit la règle, comment s'y conformer, et comment tenir la maison au quotidien.")
        ecrits.append(ecrire("blog/index.html" if n == 1 else "blog/page/%d/index.html" % n, contenu))

    # Rubriques
    for slug, r in RUBRIQUES.items():
        dans = [a for a in articles if a["rubrique"] == slug]
        if not dans:
            continue
        ecrits.append(ecrire("blog/rubrique/%s/index.html" % slug, page_liste(
            "%s | %s" % (r["titre"], MARQUE), r["description"],
            "%s/blog/rubrique/%s/" % (SITE, slug),
            "%s %s" % (r["emoji"], r["nom"]), r["titre"], r["chapeau"],
            dans, "/assets/og/blog.png", slug,
            [("Accueil", "/"), ("Blog", "/blog/"), (r["nom"], None)])))

    # Page vidéos
    avec_video = [a for a in articles if a.get("video")]
    if avec_video:
        ecrits.append(ecrire("blog/videos/index.html", page_liste(
            "Vidéos : gérer une école coranique ou une madrasa pas à pas | MadrassaNET",
            "Démonstrations et tutoriels en vidéo pour les écoles coraniques, madrasas et "
            "associations scolaires : appel, bulletins, paiements, réinscriptions.",
            SITE + "/blog/videos/", "▶ Vidéos",
            "Les articles en vidéo",
            "Chaque vidéo est accompagnée de son article et de sa transcription : à regarder, "
            "ou à lire si vous êtes pressé.",
            avec_video, "/assets/og/blog.png", "videos",
            [("Accueil", "/"), ("Blog", "/blog/"), ("Vidéos", None)])))

    # Flux, sitemaps, llms.txt
    ecrits.append(ecrire("blog/feed.xml", flux_rss(articles)))
    ecrire_sitemap(articles, pages, pages_total)
    ecrits.append("sitemap.xml (bloc BLOG)")
    sv = sitemap_video(articles)
    if sv:
        ecrits.append(ecrire("sitemap-video.xml", sv))
    ecrits.append(ecrire("llms.txt", fichier_llms(articles)))
    ecrits.append(ecrire("404.html", page_404(articles)))
    ecrire_robots(bool(sv))
    ecrits.append("robots.txt (bloc SITEMAPS)")

    # Dossiers générés qui n'ont plus de source : renommage ou suppression
    connus = {a["slug"] for a in articles} | {p["slug"] for p in pages} | {"page", "rubrique", "videos"}
    for nom in sorted(os.listdir(OUT_BLOG)):
        chemin = os.path.join(OUT_BLOG, nom)
        if os.path.isdir(chemin) and not nom.startswith("_") and nom not in connus:
            avertir("blog/%s/ n'a plus de source dans blog/_articles/ : dossier à supprimer "
                    "à la main (une URL qui disparaît doit être redirigée, pas oubliée)." % nom)

    print("%d articles, %d pages, %d fichiers écrits." % (len(articles), len(pages), len(ecrits)))
    for r in retires:
        print("  · retiré (plus de source) : %s" % r)
    for nom in brouillons:
        print("  · brouillon ignoré : %s" % nom)
    if AVERTISSEMENTS:
        print("\n%d point(s) à regarder :" % len(AVERTISSEMENTS))
        for m in AVERTISSEMENTS:
            print("  ⚠ %s" % m)


if __name__ == "__main__":
    main()
