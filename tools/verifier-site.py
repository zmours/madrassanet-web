#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifie le site généré avant de le commiter.

    python3 tools/verifier-site.py      # 0 si tout va bien, 1 sinon

Ce que ce script attrape, et qu'un coup d'œil ne voit pas :

  • un JSON-LD invalide — invisible à l'écran, mais Google le rejette en bloc ;
  • un XML cassé dans sitemap.xml ou le flux RSS ;
  • une balise mal refermée, ou un titre glissé dans un <span> (interdit) ;
  • une page sans <title>, sans canonical, ou avec deux <h1> ;
  • un lien interne ou une URL de sitemap qui ne mène nulle part.

À lancer après `python3 tools/build-blog.py`, et avant chaque commit. Aucune
dépendance : bibliothèque standard uniquement.
"""
import json, os, re, sys
from html.parser import HTMLParser
from xml.dom import minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDES = {"meta", "link", "img", "br", "hr", "input", "source", "path", "rect",
         "circle", "line", "polygon", "polyline", "stop", "use", "ellipse", "col"}
soucis = []

class Balises(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile = []
        self.erreurs = []
    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "h4", "p", "div", "ul", "ol", "table") and "span" in self.pile:
            self.erreurs.append("<%s> à l'intérieur d'un <span> (ligne %d) — un span ne "
                                "peut contenir que du texte" % (tag, self.getpos()[0]))
        if tag not in VIDES:
            self.pile.append(tag)
    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        if not self.pile:
            self.erreurs.append("</%s> sans ouverture (ligne %d)" % (tag, self.getpos()[0]))
        elif self.pile[-1] != tag:
            self.erreurs.append("</%s> alors que <%s> est ouvert (ligne %d)"
                                % (tag, self.pile[-1], self.getpos()[0]))
            if tag in self.pile:
                while self.pile and self.pile.pop() != tag:
                    pass
        else:
            self.pile.pop()

# Toutes les pages du site, générées ou écrites à la main. Les contrôles de
# structure ont longtemps porté sur les seules pages générées : une balise <a>
# jamais refermée dans delete-account/ est ainsi passée inaperçue, et avalait
# le texte qui la suivait — 290 px de débordement sur un téléphone.
pages = []
for racine, _, fichiers in os.walk(ROOT):
    if "/.git" in racine or "_articles" in racine or "_pages" in racine:
        continue
    pages += [os.path.join(racine, f) for f in fichiers if f.endswith(".html")]

for p in sorted(pages):
    rel = os.path.relpath(p, ROOT)
    s = open(p, encoding="utf-8").read()

    for bloc in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(bloc)
        except Exception as ex:
            soucis.append("%s : JSON-LD invalide — %s" % (rel, ex))

    b = Balises()
    b.feed(s)
    if b.pile:
        soucis.append("%s : balises non refermées — %s" % (rel, b.pile))
    for er in b.erreurs:
        soucis.append("%s : %s" % (rel, er))

    if s.count("<h1") > 1:
        soucis.append("%s : %d <h1> (un seul attendu)" % (rel, s.count("<h1")))
    if "<title>" not in s:
        soucis.append("%s : <title> manquant" % rel)
    if rel.startswith("blog/") and 'rel="canonical"' not in s:
        soucis.append("%s : canonical manquant" % rel)

# XML
for x in ("sitemap.xml", "blog/feed.xml"):
    try:
        minidom.parse(os.path.join(ROOT, x))
    except Exception as ex:
        soucis.append("%s : XML invalide — %s" % (x, ex))

# Liens internes de tout le site
def cible_existe(u):
    u = u.split("#")[0].split("?")[0]
    if not u.startswith("/") or u.startswith("//"):
        return True
    chemin = os.path.join(ROOT, u.lstrip("/"))
    if u.endswith("/"):
        return os.path.exists(os.path.join(chemin, "index.html"))
    return os.path.exists(chemin)

for p in sorted(set(pages)):
    rel = os.path.relpath(p, ROOT)
    s = open(p, encoding="utf-8").read()
    for u in set(re.findall(r'(?:href|src)="([^"]+)"', s)):
        if not cible_existe(u):
            soucis.append("%s : lien mort → %s" % (rel, u))

# Sitemap : chaque URL doit exister
doc = minidom.parse(os.path.join(ROOT, "sitemap.xml"))
for loc in doc.getElementsByTagName("loc"):
    u = loc.firstChild.data.replace("https://www.madrassanet.com", "")
    if not cible_existe(u):
        soucis.append("sitemap.xml : URL déclarée mais absente → %s" % u)

print("%d page(s) vérifiée(s)" % len(set(pages)))
if soucis:
    print("\n%d problème(s) :" % len(soucis))
    for x in sorted(set(soucis)):
        print("  ✗ %s" % x)
    sys.exit(1)
print("Aucun problème.")
