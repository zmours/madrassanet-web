# Mesure d'audience, objectifs et ressources téléchargeables

Ce document décrit ce qui a été mis en place sur la vitrine pour le **lot 0** du plan
marketing (`madrasssnet/docs/PLAN_MARKETING_MADRASSANET.md` §3), et ce qu'il reste à
brancher côté comptes SaaS.

---

## ⏳ TODO — la mesure est allumée, il reste le relevé de départ

**Mise à jour du 10/09/2026.** L'attente décidée le 07/09/2026 est levée : l'outil est choisi
(**Umami Cloud** — gratuit, sans cookie donc sans bandeau, et même logiciel que la future
instance auto-hébergée), le site est créé et son identifiant est en place dans
`CONFIG.umamiWebsiteId`. **La mesure compte dès le prochain déploiement.**

Le jour de la bascule vers une instance propre, seule `CONFIG.umamiScript` change ; ni les
pages, ni les objectifs, ni les attributs `data-track` ne bougent.

- [x] ~~Choisir l'outil de mesure~~ → **Umami Cloud**, le 10/09/2026
- [x] ~~Créer le site et coller l'identifiant~~ → fait le 10/09/2026
- [ ] **Vérifier que les trois objectifs remontent** dans l'onglet *Events* d'Umami, aux noms
      exacts du §2 étape 2 (envoyer le formulaire, télécharger un modèle, cliquer sur la prise
      de rendez-vous **depuis un vrai navigateur**, pas depuis `localhost` où la mesure est
      volontairement inactive).
- [ ] **Search Console** : propriété, `sitemap.xml`, et **relever les positions actuelles des
      12 requêtes cibles**. → §2 étape 3
      ⚠️ Ce relevé est le point zéro. Il est perdu pour de bon si on ne le fait pas :
      chaque semaine d'attente est une semaine d'historique qui n'existera jamais.
- [ ] **Renseigner les 3 constantes** de `index.html` : `BOOKING_URL` (cal.com, gratuit,
      5 min), `TOUR_VIDEO_URL` (après le lot 1), `BREVO_FORM_URL`. → §4

**Ce que ce report coûte, pour le savoir :** l'arbitrage prévu en fin de semaine 4 du plan
(§13) — « le SEO rapporte-t-il déjà, faut-il écrire plus d'articles ou pousser YouTube ? » —
reste sans réponse tant que la mesure n'est pas allumée. Les lots suivants avancent donc à
l'estime plutôt que sur des chiffres. Ce n'est pas bloquant, c'est juste moins précis.

**Ce que ce report ne coûte pas :** rien n'est cassé, aucun lien mort n'est publié (les
boutons non configurés restent masqués), et les trois ressources téléchargeables fonctionnent
déjà.

---

## 1. Ce qui est en place

| Élément | Fichier | État |
|---|---|---|
| Mesure d'audience centralisée | [`assets/analytics.js`](assets/analytics.js) | Posée sur **toutes les pages**, **active** (Umami Cloud, depuis le 10/09/2026) |
| Consentement (bandeau + révocation) | idem | Prêt, et **inutile avec Umami** : il ne s'affiche que pour un outil à cookies |
| Trois objectifs de conversion | idem | Branchés |
| Conservation de la campagne d'origine (UTM) | idem | Branchée |
| Attribution rattachée aux demandes de contact | `index.html` | Branchée, **sans modification du back** |
| Écran de confirmation enrichi après envoi | `index.html` | En place |
| Trois ressources téléchargeables | [`templates/files/`](templates/files/) | Produites |
| Page de téléchargement | [`templates/index.html`](templates/index.html) | Refaite |
| Générateur des ressources | [`tools/generate-templates.py`](tools/generate-templates.py) | `python3 tools/generate-templates.py` |

---

## 2. Activer la mesure — 3 étapes, ~15 minutes

Rien n'est envoyé aujourd'hui : `assets/analytics.js` charge le fournisseur mais le compte
n'existe pas encore. Aucune donnée n'est perdue côté visiteur, mais **rien n'est compté**
jusqu'à ce que ces étapes soient faites.

### Étape 1 — Créer le compte

**Umami Cloud** (décision du 10/09/2026), pour trois raisons : gratuit jusqu'à
100 000 événements par mois, aucun cookie donc **aucun bandeau de consentement**, et c'est le
**même logiciel** que la version auto-hébergée — la migration vers sa propre instance ne demandera
pas de réinstrumenter le site.

1. Créer un compte sur [cloud.umami.is](https://cloud.umami.is/)
2. **Add website**, domaine `www.madrassanet.com`
3. Copier le *Website ID* et le coller dans `CONFIG.umamiWebsiteId` (`assets/analytics.js`)
4. Recharger une page du site : la visite doit apparaître dans le tableau de bord

✅ **Fait le 10/09/2026** — identifiant `bf12a351-…` en place. Rien d'autre à faire : le script
est déjà sur toutes les pages et sait quoi envoyer.

**Le jour où l'on héberge sa propre instance** : remplacer `CONFIG.umamiScript` par l'URL du
script de l'instance (par exemple `https://stats.madrassanet.com/script.js`) et l'identifiant du
site. Aucune autre ligne à toucher.

**Les autres options, et ce qu'elles coûtent.** `assets/analytics.js` accepte `plausible`
(~9 €/mois, sans cookie) et `ga4` (gratuit) — une ligne à changer dans les deux cas.

> ⚠️ **Ce que GA4 coûte vraiment.** Pas d'abonnement, mais des cookies : le bandeau de
> consentement s'affiche alors automatiquement (le code le gère, `privacy/` §10 le prévoit), et
> **entre 30 et 50 % des visiteurs refusent** — les chiffres sont amputés d'autant. Sur un site
> qui vend la conformité RGPD à des écoles, demander l'autorisation d'envoyer les visiteurs chez
> Google est aussi un signal. À garder pour le jour où Google Ads devient utile.
>
> **Si vous basculez sur GA4, une chose à ne pas oublier** : `privacy/` §10.2 affirme aujourd'hui
> que le site ne dépose aucun cookie. C'est vrai avec Umami ; ce serait faux avec GA4. Cette
> phrase-là doit être corrigée en même temps que `CONFIG.provider`, et la configuration GA4 doit
> être passée en conservation 14 mois, Google signals désactivé (le code le demande déjà via
> `allow_google_signals: false`).

### Étape 2 — Déclarer les trois objectifs

Dans Umami, les événements personnalisés apparaissent seuls dans **Events** dès qu'ils se
produisent : il n'y a rien à déclarer à l'avance. Ce qui suit est la liste de ce que le code
envoie — à retrouver telle quelle dans le tableau de bord (et à déclarer comme objectifs si l'on
passe un jour à Plausible ou GA4). Les noms sont sans accents pour rester compatibles avec GA4 :

| Nom de l'objectif | Se déclenche quand | Propriété jointe |
|---|---|---|
| `Contact - Demande envoyee` | Le formulaire de contact est accepté par l'API | `objet` (Demande de démo, Tarifs…) |
| `Ressource - Telechargement` | Une ressource est téléchargée | `fichier` |
| `Demo - Rendez-vous` | Clic sur le bouton de prise de rendez-vous | — |

Objectifs secondaires : `Video - Visite guidee`, `Demo - Demande depuis ressources`,
`Ressource - Depuis confirmation`, et depuis le 10/09/2026 **`Video - Lecture`** — émis par le
lecteur des articles de blog, avec l'identifiant de la vidéo et le slug de l'article
(cf. `blog/ARCHITECTURE_BLOG.md` §5).

### Étape 3 — Search Console

1. Créer la propriété sur `https://www.madrassanet.com`
2. Soumettre `https://www.madrassanet.com/sitemap.xml`
3. **Noter les positions actuelles des 12 requêtes cibles** (§8.1 du plan) : c'est le point
   zéro, et il n'existera plus si on ne le relève pas maintenant.

> ⚠️ **Le premier arbitrage du plan dépend de cette étape.** Il est possible que les 8 articles
> de blog rapportent déjà des visiteurs ; dans ce cas la bonne décision sera d'en écrire
> davantage plutôt que d'ouvrir des comptes sociaux. Sans ce relevé, la question reste sans
> réponse.

---

## 3. La convention d'UTM — à respecter sans exception

**Aucun lien publié quelque part ne doit être nu.** Sans UTM, un visiteur venu d'un post
LinkedIn est indistinguable d'un visiteur venu de Google : tout l'intérêt de la mesure
disparaît.

```
https://www.madrassanet.com/<page>/?utm_source=<réseau>&utm_medium=<type>&utm_campaign=<campagne>&utm_content=<contenu précis>
```

| Paramètre | Valeurs admises | Exemple |
|---|---|---|
| `utm_source` | `linkedin`, `facebook`, `youtube`, `groupe-fb`, `whatsapp`, `email`, `appvizer`, `capterra` | `linkedin` |
| `utm_medium` | `social`, `video`, `email`, `annuaire`, `signature`, `pdf` | `social` |
| `utm_campaign` | La campagne, en minuscules avec des tirets | `rentree2026`, `notoriete`, `rgpd` |
| `utm_content` | **Le contenu précis** : c'est lui qui dit *quel post* a marché | `post-rgpd-2026-09-10` |

Exemples réels :

```
# Post LinkedIn du mercredi sur le RGPD
.../blog/rgpd-donnees-eleves-madrasa/?utm_source=linkedin&utm_medium=social&utm_campaign=notoriete&utm_content=post-rgpd-5-obligations

# Description d'une vidéo YouTube
.../templates/?utm_source=youtube&utm_medium=video&utm_campaign=tutoriels&utm_content=video-03-import-excel

# Réponse dans un groupe Facebook
.../templates/?utm_source=groupe-fb&utm_medium=social&utm_campaign=entraide&utm_content=feuille-appel
```

### Ce que la convention permet, concrètement

`assets/analytics.js` mémorise la campagne pour la durée de la visite, et
`index.html` **joint son résumé au message de la demande de contact** :

```
Bonjour, nous avons 180 élèves le samedi matin.

---
Origine : linkedin/social/rentree2026
```

L'email de notification reçu par les super-admins porte donc l'origine du prospect,
**sans aucune modification du backend**. C'est le moyen le plus simple de savoir quel contenu
produit des demandes de démo.

---

## 4. Ce qu'il reste à brancher

Trois constantes en tête du script de `index.html` (chercher `BOOKING_URL`). **Tant qu'elles
sont vides, les boutons correspondants restent masqués** : aucun lien mort n'est publié.

| Constante | À renseigner avec | Effet |
|---|---|---|
| `BOOKING_URL` | Un lien **cal.com** (gratuit), créneaux de 30 min | Affiche « Réserver un créneau » sur l'écran de confirmation. À reporter aussi dans la bio LinkedIn et sur la page tarifs |
| `TOUR_VIDEO_URL` | La vidéo n°1 « MadrassaNET en 3 minutes » (lot 1) | Affiche « La visite guidée en 3 minutes » |
| `BREVO_FORM_URL` | L'URL d'un formulaire **Brevo** (gratuit à ce volume) | Inscrit le prospect dans Brevo, qui envoie **l'accusé de réception immédiat** puis la séquence de relance. Textes prêts dans `madrasssnet/docs/MARKETING_EMAILS_MADRASSANET.md` |

Vérifier au passage que `BREVO_FIELDS` correspond aux noms d'attributs réellement définis
dans Brevo (`EMAIL`, `NOM`, `ECOLE`, `ORIGINE`).

> **Pourquoi Brevo et pas le backend ?** Aujourd'hui `ContactRequestService` notifie les
> super-admins mais **n'envoie rien au prospect**. Passer par Brevo évite de toucher au
> back et apporte en plus la séquence de relance. Si l'on préfère un accusé de réception
> envoyé par l'application elle-même, c'est une quinzaine de lignes dans
> `ContactRequestService.createFromPublicForm` — mais c'est du développement, hors périmètre
> de ce lot.

---

## 5. Les ressources téléchargeables

Trois documents, dans `templates/files/`, tous produits par
`python3 tools/generate-templates.py` :

| Fichier | Ce que c'est | Requête visée |
|---|---|---|
| `feuille-presence-trimestre.pdf` | Feuille d'appel A4 paysage, 20 élèves × 12 semaines, une page | « feuille d'appel à imprimer école » |
| `checklist-rentree-ecole-associative.pdf` | Rétroplanning mai → octobre, 33 points à cocher, une page | « organiser la rentrée école coranique » |
| `modele-bulletin-bilingue.xlsx` | Bulletin FR/AR, moyenne pondérée automatique, RTL correct | « bulletin scolaire arabe modèle » |

### 🚫 La règle : ne jamais publier un document qui recopie le produit

Un quatrième fichier existait — un modèle d'import des élèves reprenant les colonnes de
`StudentImportService.TEMPLATE_COLUMNS`. **Il a été retiré le 07/09/2026**, pour deux raisons
qui valent pour tout futur ajout :

1. **Il devient faux tout seul.** Dès que les colonnes d'import changent côté backend, le
   fichier déjà téléchargé par un prospect ne s'importe plus. Le document travaille alors
   contre vous : la première expérience du produit est un échec d'import.
2. **L'application le fait déjà, et mieux.** `StudentController` →
   `generateImportTemplate(tenantId)` génère le modèle à la demande, toujours à jour et
   **adapté aux classes de l'établissement** — ce qu'un fichier statique ne peut pas faire.

**Le critère à appliquer avant d'ajouter une ressource ici** : est-ce que ce document reflète
une structure interne du produit (colonnes, schéma, écrans, paramètres) ? Si oui, il n'a pas sa
place sur la vitrine — il appartient à l'application. Les trois documents conservés ne
dépendent d'aucun code : ils restent valables tant qu'une école a une rentrée à préparer.

### Choix assumés

- **Téléchargement libre, sans formulaire.** Un bénévole méfiant abandonne devant un mur
  d'email ; et un PDF qui circule dans un groupe WhatsApp travaille pendant des mois. La
  capture d'email se fait par le formulaire de contact et par Brevo, pas en péage.
- **Chaque fichier porte la marque, l'URL et le prix en pied de page.** C'est ce qui rend le
  partage utile : le document est la publicité.

## 6. Vérifier que tout fonctionne

```bash
# 1. Servir le site localement
python3 -m http.server 8899

# 2. Les ressources répondent bien
for f in feuille-presence-trimestre.pdf checklist-rentree-ecole-associative.pdf \
         modele-bulletin-bilingue.xlsx; do
  curl -s -o /dev/null -w "$f %{http_code}\n" "http://localhost:8899/templates/files/$f"
done

# 3. Le script de mesure est bien inclus partout (doit afficher 29)
grep -rl "assets/analytics.js" --include="*.html" . | wc -l

# 4. Le script de mesure lui-même, hors navigateur (16 contrôles)
node tools/test-analytics.js
```

> Sur `localhost`, la mesure est **volontairement inactive**
> (`CONFIG.ignoreLocalhost`) : les objectifs sont alors écrits dans la console du
> navigateur avec le préfixe `[mesure inactive]`, ce qui permet de vérifier le
> déclenchement sans polluer les statistiques.

Le nombre de pages augmente à chaque article publié : `python3 tools/build-blog.py` pose le
script sur les pages qu'il génère, il n'y a jamais à l'ajouter à la main.
