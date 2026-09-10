# Architecture du blog

Décidé le 10/09/2026. Ce document explique **comment le blog est fabriqué**. Ce qu'on y écrit et
dans quel ordre est dans [`LIGNE_EDITORIALE.md`](./LIGNE_EDITORIALE.md) ; ce document-ci ne parle
que de mécanique.

---

## 1. Pourquoi un générateur

Le blog était neuf pages HTML écrites à la main. Chacune redupliquait la barre de navigation, le
pied de page et soixante lignes de métadonnées (`og:`, canonical, JSON-LD). Publier demandait de
toucher quatre fichiers ; changer une entrée de menu en demandait neuf. À deux articles par mois,
la même opération en aurait demandé trente-trois au bout d'un an.

Ce n'est pas seulement une question de confort : ce sont les conséquences qui coûtaient cher.

| Ce qui manquait | Pourquoi c'est un problème de référencement |
|---|---|
| Pages de rubrique | Les quatre rubriques de la ligne éditoriale n'existaient que comme étiquettes décoratives. Ce sont elles qui captent la longue traîne et donnent une structure lisible |
| Pagination | Une grille unique qui grossit indéfiniment finit par ne plus être explorée en entier |
| Dates sur les cartes | Aucun signal de fraîcheur en page de liste |
| Flux RSS | Rien à donner à une newsletter, à LinkedIn ou à un agrégateur |
| `lastmod` dans le sitemap | C'est le seul signal de fraîcheur que Google utilise vraiment |
| Maillage automatique | Les trois « à lire aussi » étant écrits à la main, aucun article ne pointait vers les deux derniers publiés |
| Toute mécanique vidéo | Ni lecteur, ni `VideoObject`, ni transcription, ni sitemap vidéo |
| Temps de lecture juste | Les durées affichées étaient saisies à la main, et fausses du double |

Le générateur rend tout cela gratuit et **impossible à oublier**.

---

## 2. Les quatre règles

1. **Bibliothèque standard uniquement.** `tools/build-blog.py` n'importe rien qui ne soit livré
   avec Python. Publier un article ne doit pas dépendre d'un `pip install` : le jour où la chaîne
   casse, on ne publie plus. Les deux autres scripts de `tools/` ont des dépendances parce qu'ils
   tournent trois fois par an ; celui-ci tourne à chaque publication.
2. **Rien de ce qui est généré ne s'édite à la main.** Toute correction se fait dans la source
   Markdown, puis on relance le script. Un `blog/<slug>/index.html` modifié directement sera
   écrasé sans prévenir.
3. **Les liens des pages générées sont absolus** (`/blog/…`). Ces pages vivent à quatre
   profondeurs — `blog/`, `blog/<slug>/`, `blog/page/2/`, `blog/rubrique/<r>/` — et un lien
   relatif y serait faux une fois sur deux. Les pages tenues à la main gardent leurs liens
   relatifs : elles ne bougent pas.
4. **La sortie est commitée.** GitHub Pages sert la branche telle quelle, sans étape de
   construction. Le HTML généré fait donc partie du dépôt, et un commit qui touche une source
   Markdown sans le HTML correspondant ne déploie rien.

---

## 3. Ce qui est source, ce qui est généré

```
blog/
  _articles/<slug>.md     ← SOURCE     un fichier par article
  _pages/<slug>.md        ← SOURCE     pages du blog hors flux (redaction.md)
  _auteurs.json           ← SOURCE     les signatures
  LIGNE_EDITORIALE.md     ← SOURCE     la ligne éditoriale
  ARCHITECTURE_BLOG.md    ← SOURCE     ce document

  <slug>/index.html       ← généré     les articles
  index.html              ← généré     la liste, page 1
  page/<n>/index.html     ← généré     la liste, pages suivantes
  rubrique/<r>/index.html ← généré     une page par rubrique pourvue
  videos/index.html       ← généré     dès qu'un article porte une vidéo
  feed.xml                ← généré     flux RSS 2.0
  articles.json           ← généré     index de la recherche (texte intégral)

404.html                  ← généré     a besoin des mêmes nav et pied de page
llms.txt                  ← généré     inventaire pour les assistants IA
sitemap-video.xml         ← généré     dès qu'un article porte une vidéo
sitemap.xml               ← MIXTE      bloc entre BLOG:DEBUT et BLOG:FIN
robots.txt                ← MIXTE      bloc entre SITEMAPS:DEBUT et SITEMAPS:FIN
styles.css                ← SOURCE     section « BLOG » en fin de fichier
assets/blog.js            ← SOURCE     lecteur vidéo, chargé par les seuls articles vidéo
assets/blog-liste.js      ← SOURCE     recherche et badge « Nouveau » des pages de liste
tools/verifier-site.py    ← SOURCE     contrôle du site généré
```

Les deux fichiers **mixtes** ont un bloc délimité par des marqueurs, régénéré à chaque
construction ; tout ce qui est en dehors reste tenu à la main. C'est ce qui permet au sitemap de
lister les pages hors blog sans que le script ait à les connaître.

Le générateur **supprime** ce qu'il a lui-même produit et qui n'a plus de raison d'être : une
page 3 après regroupement, une rubrique vidée, le sitemap vidéo du jour où la dernière vidéo
disparaît. Il ne supprime **jamais** un dossier d'article : une URL publique qui disparaît demande
une redirection, donc une décision. Dans ce cas il avertit, et c'est à vous de trancher.

---

## 4. Publier un article

```bash
cp blog/_articles/faire-appel-sans-papier.md blog/_articles/mon-nouvel-article.md
# … écrire …
python3 tools/build-blog.py
git add -A && git commit
```

Le nom du fichier donne le slug, donc l'URL. Le script écrit l'article, l'insère dans la liste et
dans sa rubrique, refait la pagination, le flux, les sitemaps et `llms.txt`. **Il n'y a rien
d'autre à mettre à jour.**

`python3 tools/build-blog.py --inventaire` liste les articles avec leur rubrique, leur date et
leur longueur, sans rien écrire.

### Les métadonnées

| Clé | Obligatoire | Rôle |
|---|---|---|
| `titre` | ● | Le `h1`, et le `headline` du JSON-LD |
| `titre_court` | | Fil d'Ariane et cartes « à lire aussi ». À utiliser dès que le titre dépasse une ligne |
| `titre_seo` | | Balise `<title>`. Par défaut : `titre` + ` \| MadrassaNET` |
| `description` | ● | Meta description. **70 à 165 caractères** — au-delà, Google la coupe |
| `resume` | | Texte de la carte en page de liste. Par défaut : la description |
| `chapeau` | ● | Le `article-lead`. Les trois premières lignes doivent dire si le lecteur est concerné |
| `rubrique` | ● | `conformite`, `securite`, `gestion` ou `outils` |
| `auteur` | | Clé de `_auteurs.json`. Par défaut `equipe` |
| `publie_le` | ● | `AAAA-MM-JJ` |
| `modifie_le` | | Affiche « Mis à jour le … » et alimente `dateModified` |
| `verifie_le` | | Date de vérification des sources, affichée dans le bloc Sources |
| `og_image` | | Image de partage. Par défaut `/assets/og/blog.png`. À générer dans `tools/generate-og-images.py` |
| `og_titre`, `og_description`, `og_image_alt` | | Variantes de partage, plus courtes que le SEO |
| `vignette_mot` | | **Le mot en très gros** sur la vignette et la bannière : `ACM`, `RGPD`, `PRÉSENCES`. C'est lui qui identifie l'article dans la grille — le générateur avertit si deux articles affichent le même |
| `vignette_icone` | | L'icône au trait (liste ci-dessous). Par défaut, celle de la rubrique |
| `vignette_image` | | Une **vraie image** (capture, photo) qui remplace la vignette générée, carte et bannière comprises |
| `banniere_sous_titre` | | La ligne sous le mot-clé |
| `banniere_emoji`, `banniere_titre` | | Hérités de l'ancienne composition. `banniere_titre` sert encore de repli quand `vignette_mot` est absent |
| `mots_cles` | | `keywords` du JSON-LD **et poids dans la recherche interne**. À renseigner : l'article sur le pointage ne contenait le mot « présences » nulle part dans ses métadonnées, et la recherche le classait quatrième |
| `articles_lies` | | Trois slugs. Sinon, choisis automatiquement dans la même rubrique |
| `sommaire` | | `non` retire le sommaire. Il n'apparaît qu'à partir de cinq sections |
| `brouillon` | | `oui` : l'article n'est ni généré, ni listé, ni dans le flux |

Le **temps de lecture** n'est pas une métadonnée : il est calculé à 200 mots/minute, comme le
demande la ligne éditoriale.

### Les blocs Markdown

Titres `##`/`###`/`####`, paragraphes, listes `-` et `1.`, tableaux `| a | b |`, `**gras**`,
`*italique*`, `` `code` ``, `[texte](url)`, citations `>`. La typographie française — apostrophes
courbes, espaces insécables — est appliquée à la construction : écrivez avec une apostrophe droite.

Les blocs propres à la charte :

| Bloc | Ce qu'il produit |
|---|---|
| `::: encadre` | Encadré bleu, pour un point à retenir |
| `::: attention` | Encadré orange. C'est là que va la mention « ceci n'est pas un conseil juridique » |
| `::: figure legende="…"` | Une figure avec sa légende ; le corps est du HTML brut (SVG, `img`) |
| `::: cta titre="…" lien="…" libelle="…"` | L'appel à l'action. **Un seul par article**, à l'endroit où l'administration réclame une preuve |
| `::: sources` | Le bloc Sources, avec la date de `verifie_le`. Une liste de liens |
| `::: faq` | Questions dépliables + JSON-LD `FAQPage`. Chaque question commence par `####` |
| `::: video` | Marqueur : place le lecteur ici. Pas de corps, pas de `:::` de fermeture |
| `::: transcription` | Transcription repliée de la vidéo |
| `::: html` | HTML brut, ni échappé ni retouché. Le recours pour tout le reste |

Tous les conteneurs sauf `::: video` se ferment par une ligne `:::` seule.

---

## 5. Publier une vidéo

L'intérêt d'une vidéo pour le référencement n'est pas de poser un lecteur sur la page : c'est
**article + lecteur + chapitres + transcription** à la même URL. La transcription apporte le
contenu textuel qui manque aux articles courts, et c'est ce que Google indexe.

1. **Publier la vidéo sur YouTube** — deuxième moteur de recherche, et l'hébergement est gratuit.
   Description : la phrase de positionnement, le lien vitrine avec UTM, et le sommaire horodaté
   (cf. plan marketing §4.2).
2. **Créer ou compléter l'article jumeau.** Une vidéo sans article ne se référence pas ; un
   article sans vidéo se référence très bien. C'est l'article qui porte la page.
3. **Renseigner les métadonnées** et placer `::: video` :

```
video: 3xK9pQ2mZ1s              # l'identifiant YouTube, pas l'URL
video_titre: Faire l'appel de sa classe en 30 secondes sur téléphone
video_description: …            # par défaut : la description de l'article
video_duree: PT1M12S            # format ISO 8601
video_publie_le: 2026-09-24
video_miniature: /assets/og/video-appel.png   # facultatif
chapitres:
  00:00 Le résultat, tout de suite
  00:18 Ouvrir la classe du jour
  01:02 Ce que voit le bureau
```

4. **Écrire la transcription** dans un bloc `::: transcription`. Le script avertit si elle manque.

Le reste est automatique : `VideoObject` avec ses `Clip` par chapitre, `sitemap-video.xml`, la
ligne correspondante dans `robots.txt`, la page `/blog/videos/`, le badge « Vidéo » sur la carte
et le chargement de `assets/blog.js`.

### Ce que fait le lecteur

Un `<iframe>` YouTube posé dans la page coûte environ 900 Ko et deux cookies tiers **à chaque
visiteur**, y compris à ceux qui ne regarderont pas la vidéo. Ici la page n'affiche qu'une image ;
l'iframe est créé au clic, sur `youtube-nocookie.com`. Aucune donnée n'est transmise à YouTube
avant un geste du visiteur — donc **aucun bandeau de consentement à afficher**. Les chapitres
rechargent le lecteur à leur horodatage.

Par défaut, la miniature est celle de YouTube (`i.ytimg.com`). Pour ne rien demander à un tiers
au chargement, générer une miniature locale et la déclarer dans `video_miniature`.

### Une chose à faire côté mesure

Le bouton de lecture émet l'événement **`Video - Lecture`** (avec l'identifiant de la vidéo et le
slug de l'article) via les attributs `data-track` d'`analytics.js`. Il s'ajoute aux trois objectifs
de `MARKETING.md` §2 étape 2, et doit être déclaré dans Plausible pour être compté.

---

## 6. Les illustrations

Vignette de carte et bannière d'article sont **le même dessin**, à deux tailles : le lecteur qui
clique doit retrouver l'image qu'il a vue. Trois éléments les composent :

| Élément | D'où il vient |
|---|---|
| Le **mot-clé** en très gros | `vignette_mot` — c'est l'identité visuelle de l'article |
| L'**icône au trait** | `vignette_icone`, sinon celle de la rubrique |
| La **teinte** | Le dégradé de la rubrique, sa teinte tournée de ±15° selon le slug |

La rotation de teinte n'est pas un effet de style : sans elle, deux articles d'une même rubrique
ont exactement la même image. Elle est calculée à partir du slug, donc stable d'une génération à
l'autre.

**Pourquoi plus d'émoji.** Le rendu d'un émoji change d'un système à l'autre, il n'est pas
indexable, et sur un article de conformité il fait informel. Les icônes sont des tracés SVG, dans
`ICONES` de `tools/build-blog.py` :

`document`, `carnet`, `cadenas`, `calendrier`, `liste`, `bouclier`, `batiment`, `personnes`,
`eclair`, `monnaie`, `loupe`, `cycle`, `balance`, `tampon`.

Pour en ajouter une : un tracé de plus dans `ICONES`, centré sur (0,0) dans un carré d'environ 56
unités, puis `vignette_icone: <clé>` dans l'article. Une clé inconnue arrête la génération.

**Une vraie image quand elle vaut mieux.** `vignette_image: /assets/blog/appel-mobile.png` remplace
le dessin généré, sur la carte comme sur la bannière. À utiliser dès qu'une capture du produit dit
mieux les choses qu'un dessin — c'est aussi le seul moyen d'exister dans Google Images, qu'un SVG
ne capte pas.

---

## 7. La page de liste

Refondue le 10/09/2026 pour tenir la charge d'un blog qui publie deux fois par mois.

| Élément | Ce qu'il résout |
|---|---|
| **Article à la une** | Le dernier publié prend une grande carte horizontale, sur la première page seulement. Sans mise en avant, la nouveauté se noie dans une grille uniforme et le lecteur régulier ne sait pas s'il a déjà tout lu |
| **Badge « Nouveau »** | Posé par le navigateur sur les articles de moins de 45 jours. Calculé côté client à dessein : une fraîcheur figée dans le HTML se périme en silence, et obligerait à tout regénérer chaque semaine |
| **Compteurs par rubrique** | Dit au lecteur si la rubrique vaut le détour, et nous dit laquelle est en retard sur la répartition cible du §2 de la ligne éditoriale |
| **Recherche instantanée** | Porte sur **tous** les articles, pas seulement la page affichée. Sans accents ni pluriels (« écoles coraniques » trouve « école coranique »), classée par pertinence : un mot du titre pèse trois fois un mot croisé dans un paragraphe |
| **Pagination numérotée** | « Page 2 sur 4 » ne dit pas s'il vaut la peine d'aller plus loin ; une suite de numéros, si |
| **Bloc « Suivre le blog »** | Le flux RSS est le seul canal qui ne dépende de personne — ni d'un réseau social, ni d'une liste d'adresses à constituer |

**La recherche ne coûte rien à qui ne cherche pas.** L'index (`blog/articles.json`, texte
intégral des articles) n'est téléchargé qu'au premier caractère saisi. Le champ lui-même est
écrit avec `hidden` et révélé par `assets/blog-liste.js` : un champ de recherche qui ne cherche
pas est pire que pas de champ du tout, et la page reste entièrement utilisable sans JavaScript.

L'index embarque la carte **déjà rendue** plutôt qu'un gabarit à reconstruire en JavaScript : un
second gabarit divergerait du premier au premier changement de design, et personne ne s'en
apercevrait avant longtemps.

---

## 8. Ce que le script vérifie à chaque construction

Il ne se contente pas de générer : il relit la ligne éditoriale à votre place et affiche une liste
de points à regarder. Il **arrête** la génération sur une erreur de structure (rubrique inconnue,
date mal formée, bloc non refermé, auteur inexistant, article lié inexistant) — mieux vaut ne rien
publier qu'un article aux métadonnées fausses, qu'on ne verra pas passer. Il **avertit** sans
bloquer sur :

- une meta description hors de la fourchette 70–165 caractères, un titre au-delà de 110 ;
- une image de partage déclarée mais absente du dépôt ;
- un article de **Conformité** ou de **Sécurité** sans bloc `::: sources`, sans la mention
  « ceci n'est pas un conseil juridique », ou sans `verifie_le` (§4.2 et §4.3 de la ligne
  éditoriale) ;
- une vidéo sans transcription, ou sans marqueur `::: video` ;
- une rubrique sans aucun article — elle n'apparaît alors dans aucun menu ;
- un dossier d'article généré qui n'a plus de source.

Ces avertissements sont la liste des choses à faire, pas du bruit. Au 10/09/2026 il en reste trois,
et elles sont réelles : l'article RGPD n'a pas de bloc Sources, et la rubrique Sécurité est vide.

---

## 9. Vérifier avant de commiter

```bash
python3 tools/build-blog.py        # doit finir sans erreur
python3 tools/verifier-site.py     # doit afficher « Aucun problème »
python3 -m http.server 8000        # puis ouvrir http://localhost:8000/blog/
```

`verifier-site.py` attrape ce qu'un coup d'œil ne voit pas : un JSON-LD invalide (Google le
rejette en bloc, sans rien afficher), un XML cassé, une balise mal refermée, un titre glissé
dans un `<span>`, une page sans `title` ou sans canonical, deux `h1`, un lien interne ou une URL
de sitemap qui ne mène nulle part.

À regarder sur un article : la bannière, le sommaire, les tableaux, le bloc Sources, les trois
« à lire aussi », et le lecteur vidéo s'il y en a un. À regarder sur `/blog/` : la barre des
rubriques, les dates sur les cartes, la pagination si elle existe.

Deux points que le script ne sait pas voir :

- **Les liens externes.** Une source Légifrance déplacée reste un lien mort. C'est ce que la date
  `verifie_le` sert à faire relire.
- **Le rendu réel.** Rien ne remplace un coup d'œil sur téléphone.

---

## 10. Ce qui reste à faire

| # | Chantier | Pourquoi |
|---|---|---|
| 1 | **Activer la mesure et Search Console** (`MARKETING.md` §TODO) | Tant que ce n'est pas fait, tout travail de référencement est aveugle : on ne saura pas quel article marche |
| 2 | **Reprendre l'article RGPD** : bloc Sources, `verifie_le` | Un article de conformité sans source est le seul type d'article qui peut nuire à la crédibilité du reste |
| 3 | **Écrire le premier article Sécurité** (backlog §6, sujet n° 2 : les locaux et l'ERP) | La rubrique existe dans la ligne éditoriale mais n'a aucun article, donc aucune page |
| 4 | **Deux articles par landing** (`madrasa/`, `association-scolaire/`, `ecole-arabe/`) vers le blog | Chantier §8.2-1 du plan marketing. Aujourd'hui aucune page produit ne renvoie vers un article |
| 5 | **Des images réelles** sur les articles produit | Le champ `vignette_image` existe (§6) ; reste à produire les captures. C'est ce qui ouvrirait le trafic Google Images, qu'un SVG ne capte pas |
| 6 | **Un auteur nommé** sur les articles de conformité | `_auteurs.json` est prêt. C'est le signal d'expertise que Google attend sur les sujets réglementaires — mais c'est une décision, pas une configuration |
