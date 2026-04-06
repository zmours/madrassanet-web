# MadrassaNET – Site Vitrine Statique

Site web statique requis pour la soumission de l'application sur l'App Store et Google Play.

## Structure

```
madrassanet-web/
├── index.html              ← Landing page / vitrine
├── styles.css              ← CSS partagé
├── privacy/
│   └── index.html          ← Politique de confidentialité (RGPD)
├── terms/
│   └── index.html          ← Conditions Générales d'Utilisation
├── legal/
│   └── index.html          ← Mentions légales
├── support/
│   └── index.html          ← Centre d'aide & FAQ
├── delete-account/
│   └── index.html          ← Procédure de suppression de compte
└── templates/
    └── index.html          ← Modèles Excel à télécharger
    └── files/              ← Placer ici les .xlsx et .pdf
```

## URLs pour les stores

| Store | Champ | URL |
|---|---|---|
| App Store | Privacy Policy URL | `https://madrassanet.app/privacy/` |
| App Store | Support URL | `https://madrassanet.app/support/` |
| App Store | Marketing URL | `https://madrassanet.app/` |
| App Store | Account deletion | `https://madrassanet.app/delete-account/` |
| Google Play | Privacy Policy | `https://madrassanet.app/privacy/` |
| Google Play | Support URL | `https://madrassanet.app/support/` |

> ⚠️ Remplacez `https://madrassanet.app` par votre vrai domaine.

## Déploiement

### Option 1 – GitHub Pages (gratuit, recommandé)
```bash
# Dans votre repo GitHub, activez GitHub Pages depuis:
# Settings → Pages → Source: Deploy from a branch
# Branch: main  Folder: /madrassanet-web

# L'URL sera : https://<username>.github.io/<repo>/
```

### Option 2 – Netlify (gratuit, domaine personnalisé facile)
```bash
# Connectez votre repo GitHub à Netlify
# Base directory : madrassanet-web
# Build command : (vide)
# Publish directory : madrassanet-web
```

### Option 3 – Vercel (gratuit)
```bash
cd madrassanet-web
npx vercel
```

### Option 4 – Hébergement statique simple (nginx, Apache)
```nginx
server {
    listen 443 ssl;
    server_name madrassanet.app;
    root /var/www/madrassanet-web;
    index index.html;
    location / { try_files $uri $uri/ $uri.html =404; }
}
```

## Checklist avant soumission App Store

- [ ] Remplacer `https://madrassanet.app` par le vrai domaine dans tous les fichiers
- [ ] Compléter les informations `[À compléter]` dans `legal/index.html`
- [ ] Ajouter le favicon dans `assets/favicon.ico`
- [ ] Placer les fichiers `.xlsx` dans `templates/files/`
- [ ] Vérifier que toutes les URLs sont accessibles publiquement
- [ ] Tester sur mobile (responsive)
- [ ] Vérifier `app.config.ts` : `privacyPolicyUrl` et `supportUrl` mis à jour

## Checklist avant soumission Google Play

- [ ] Privacy Policy URL accessible
- [ ] Support email mentionné (`support@madrassanet.app`)
- [ ] Remplir la section "Data Safety" dans la Play Console (se baser sur `privacy/index.html`)
