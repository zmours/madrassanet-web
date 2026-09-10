# Ligne éditoriale du blog MadrassaNET

Décidé le 10/09/2026. Ce document cadre ce qu'on écrit, ce qu'on n'écrit pas, et dans quel ordre.
Il complète le plan marketing (`madrasssnet/docs/PLAN_MARKETING_MADRASSANET.md`), dont il applique
le §8 (SEO) et reprend les personas du §2.1.

---

## 1. Le positionnement, en une phrase

> **Un média pratique pour les écoles associatives et les structures éducatives : réglementation,
> sécurité, accueil des enfants, gestion quotidienne et outils numériques.**

À utiliser telle quelle dans la page d'accueil du blog, les bios sociales et les présentations.

### Les trois fonctions du blog

| Fonction | Traduction concrète dans un article |
|---|---|
| **Informer** des règles applicables | Chaque affirmation juridique cite son texte, avec un lien vers Légifrance ou un site public |
| **Aider à identifier et corriger** les points faibles | Chaque article se termine par une action réalisable cette semaine, pas par un constat |
| **Présenter l'outil** comme moyen de prévention | L'outil apparaît là où l'administration demande une preuve — jamais avant |

### Ce que ce blog n'est pas

- **Pas un média sur les fermetures.** La fermeture administrative est un cas limite, pas un sujet
  de rubrique. On écrit sur ce qui l'évite : le statut, la déclaration, les locaux, le registre.
  Un blog qui vit des fermetures parle à des gens inquiets ; un blog qui vit de la conformité
  parle à des gens qui s'organisent. Le second lectorat achète un logiciel, le premier lit et part.
- **Pas un média politique.** Aucun commentaire sur les intentions de l'État, aucune plainte sur
  la pression réglementaire, aucun vocabulaire de victimisation. On énonce la règle et le moyen de
  s'y conformer. C'est ce qui rend le blog citable par un maire, un SDJES ou une fédération — et
  donc utile à ses lecteurs.
- **Pas un blog produit.** Un article qui ne serait pas utile à une école utilisant un tableur
  n'a pas sa place ici.

---

## 2. Les quatre rubriques

Les rubriques sont les `blog-tag` affichés sur les cartes. Les quatre nouvelles remplacent les
étiquettes hétérogènes actuelles (`École coranique`, `Présences`, `Productivité`…) au fil des
republications ; les anciens articles peuvent être re-étiquetés sans être réécrits.

| Rubrique | Ce qu'elle couvre | Persona visé |
|---|---|---|
| **Conformité** | Statut juridique de l'activité, déclarations, contrôles, RGPD, assurances, subventions | Président / directeur |
| **Sécurité** | Locaux (ERP), évacuation, encadrement, protection des mineurs, urgences | Président / directeur |
| **Gestion** | Inscriptions, présences, paiements, bulletins, réinscriptions, trésorerie | Trésorier / secrétaire |
| **Outils** | Comparatifs, choix d'un logiciel, passage du papier au numérique, modèles à télécharger | Enseignant bénévole, trésorier |

**Répartition cible : une moitié Conformité + Sécurité, une moitié Gestion + Outils.** La première
moitié amène l'audience nouvelle (personne ne cherche « logiciel de gestion » avant d'avoir un
problème), la seconde convertit.

---

## 3. Le lecteur que l'on ajoute

Aux trois personas du plan marketing s'ajoute celui que ce positionnement fait venir :

> **Le responsable qui vient de recevoir un courrier.** Une demande de la mairie sur les locaux,
> un questionnaire du SDJES, une visite annoncée. Il cherche à 23 h, sur son téléphone, une réponse
> à une question précise. Il ne veut pas un dossier de vingt pages : il veut savoir si son activité
> est concernée, et quoi produire.

C'est pour lui qu'on écrit les articles de conformité : réponse en tête d'article, détail ensuite.

---

## 4. Les sept règles de rédaction

1. **Une affirmation juridique = une source.** Lien vers Légifrance, service-public.fr,
   education.gouv.fr, jeunes.gouv.fr ou une fiche préfectorale. Si la source n'est pas trouvée,
   l'affirmation ne s'écrit pas. Un média de conformité qui se trompe sur le droit perd sa
   crédibilité d'un coup — et ses lecteurs prennent des décisions avec.
2. **Un bloc « Sources » en fin d'article**, avec la date de dernière vérification. Le droit bouge :
   sans date, un article juste devient un article faux sans que personne ne s'en aperçoive.
3. **La mention « ceci n'est pas un conseil juridique »**, systématique sur les articles de
   conformité, avec le renvoi vers l'interlocuteur compétent (SDJES, mairie, rectorat, CNIL).
4. **Ton factuel, jamais alarmiste.** Pas de « attention, vous risquez la fermeture ! ». On écrit
   « voici la règle, voici comment y répondre ». La peur fait cliquer une fois et fuir ensuite.
5. **La réponse d'abord.** Les trois premières lignes disent si le lecteur est concerné. Le
   raisonnement vient après. Personne ne lit un article de conformité par plaisir.
6. **Une action par section.** Chaque `h2` doit permettre de faire quelque chose, ou d'écarter un
   cas. Sinon la section est de la documentation, pas du contenu.
7. **L'outil en fin de parcours.** Le produit apparaît une fois par article, au moment où
   l'administration réclame une preuve (liste d'inscrits, registre de présences, liste des
   encadrants). Un `article-cta` suffit : la valeur de l'article doit tenir sans lui.

### Sur les sujets sensibles

Le lectorat est majoritairement composé d'associations musulmanes, dans un contexte de contrôles
renforcés. Deux réflexes :

- **Traiter la règle, pas la communauté.** Un article sur les taux d'encadrement s'applique aussi
  au catéchisme et au club de foot : l'écrire ainsi, avec les mêmes mots que l'administration.
- **Ne jamais laisser croire qu'un contournement existe.** Le blog documente les régimes et leurs
  seuils ; il n'aide pas à rester sous un seuil. C'est aussi la position la plus utile au lecteur.

---

## 5. Publier un article — les fichiers à toucher

Aucune génération, aucun CMS : chaque article est un dossier avec un `index.html`.

1. `blog/<slug>/index.html` — copier la structure d'un article existant. À adapter : `title`,
   `meta description`, `canonical`, les trois blocs `og:`, le `BreadcrumbList` (3 niveaux), le
   `Article` du JSON-LD (`headline`, `datePublished`, `dateModified`), la bannière SVG, le
   `blog-tag`, le `h1`, l'`article-meta` (date + temps de lecture), l'`article-lead`.
2. `blog/index.html` — ajouter la carte `blog-card` **en tête de grille** (les plus récents
   d'abord), avec un dégradé et un émoji distincts des cartes voisines.
3. `sitemap.xml` — une entrée `<url>`, `changefreq: monthly`, `priority: 0.6` comme les autres
   articles.
4. **Maillage** : trois `related-card` en fin d'article, et au moins un article existant modifié
   pour pointer vers le nouveau. Un article sans lien entrant ne sera pas lu.

Conventions : slug en minuscules sans accent, contenant la requête cible ; `lang="fr"` ;
`article-meta` avec la date en français (« 10 septembre 2026 ») ; temps de lecture réaliste
(≈ 200 mots/minute).

---

## 6. Backlog priorisé

Priorité = intention de recherche × facilité de rédaction. « Requête cible » est la formulation
qu'on cherche à occuper ; elle doit apparaître dans le `title`, le `h1` et le slug.

| # | Article | Rubrique | Requête cible | État |
|---|---|---|---|---|
| 1 | Faut-il déclarer son école coranique comme accueil collectif de mineurs ? | Conformité | `école coranique déclaration accueil collectif de mineurs` | **publié le 10/09/2026** |
| 2 | Votre salle de cours est un ERP : ce que la mairie peut vous demander | Sécurité | `local association ERP type R obligations` | à écrire |
| 3 | Contrôle du SDJES ou de la mairie : les six documents à pouvoir sortir en dix minutes | Conformité | `contrôle association accueil mineurs documents` | à écrire |
| 4 | Taux d'encadrement et qualification des animateurs : composer une équipe conforme | Sécurité | `taux encadrement accueil de loisirs BAFA` | à écrire |
| 5 | Le dossier d'inscription minimal : autorisations, urgences, droit à l'image | Conformité | `dossier inscription association enfant autorisation parentale` | à écrire |
| 6 | Vérifier les antécédents judiciaires de vos encadrants : pourquoi et comment | Sécurité | `vérification antécédents judiciaires animateur bénévole` | à écrire |
| 7 | École à temps plein : le régime des établissements privés hors contrat | Conformité | `ouvrir école privée hors contrat déclaration` | à écrire |
| 8 | Assurance de l'association : ce qui doit être couvert quand on accueille des enfants | Conformité | `assurance association accueil enfants responsabilité civile` | à écrire |
| 9 | Exercice d'évacuation et registre de sécurité : le mode opératoire | Sécurité | `exercice évacuation registre sécurité ERP association` | à écrire |
| 10 | Contrat d'engagement républicain : ce que ça change pour une subvention | Conformité | `contrat engagement républicain association subvention` | à écrire |
| 11 | Alternative à Excel pour gérer ses élèves | Outils | `alternative Excel gestion élèves` | prévu au plan §8.1 |
| 12 | Gérer les adhérents d'une association loi 1901 | Gestion | `logiciel gestion association loi 1901 adhérents` | prévu au plan §8.1 |

Les huit articles existants restent en ligne et alimentent les rubriques **Gestion** et **Outils**.
Deux méritent une mise à jour une fois la rubrique Conformité installée : `rgpd-donnees-eleves-madrasa`
(ajouter le lien vers l'article 5) et `logiciel-gratuit-ou-payant-ecole-coranique` (relier à la page
tarifs).

**Rythme : deux articles par mois**, conformément au §8.2 du plan marketing. Un de conformité ou
sécurité, un de gestion ou outils. Ne pas publier deux articles de conformité de suite : le blog
deviendrait anxiogène.

---

## 7. Ce qu'on mesure

Trois indicateurs suffisent, une fois la mesure d'audience activée (voir `MARKETING.md`) :

- **Position moyenne sur les 12 requêtes cibles** du plan §8.1, plus celles du tableau ci-dessus.
- **Taux de clic vers `tarifs/`** depuis les articles : c'est le seul signe qu'un article de
  conformité amène bien un décideur, et pas seulement un curieux.
- **Téléchargements de ressources** depuis les articles : le meilleur article de conformité est
  celui qui donne envie de récupérer un modèle.

Si un article de conformité génère du trafic mais aucun clic vers l'offre, ce n'est pas un échec :
c'est de la notoriété. Si aucun n'en génère au bout de six mois, la rubrique est mal ciblée.
