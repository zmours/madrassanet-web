/* ============================================================================
 * MadrassaNET — pages de liste du blog
 * ----------------------------------------------------------------------------
 * Chargé par l'index, les pages de rubrique et la page vidéos.
 *
 * Deux fonctions, et rien d'autre :
 *
 *   1. LE BADGE « NOUVEAU », posé ici et pas dans le HTML généré. Une
 *      fraîcheur calculée à la génération se périme en silence, et forcerait
 *      à regénérer toutes les pages chaque semaine pour rester juste.
 *
 *   2. LA RECHERCHE, sur tous les articles et pas seulement sur la page
 *      affichée. L'index n'est téléchargé qu'au premier caractère saisi : un
 *      lecteur qui ne cherche rien ne paie rien. Le champ est masqué dans le
 *      HTML et révélé ici — un champ de recherche qui ne cherche pas est pire
 *      que pas de champ du tout.
 *
 * Aucune dépendance, et la page reste entièrement utilisable sans ce fichier.
 * ========================================================================== */
(function () {
  'use strict';

  var JOURS_NOUVEAU = 45;
  var INDEX_URL = '/blog/articles.json';

  /* ── 1. Badge « Nouveau » ──────────────────────────────────────────────── */

  function marquerNouveautes(racine) {
    var limite = Date.now() - JOURS_NOUVEAU * 86400000;
    var cartes = (racine || document).querySelectorAll('.blog-card');

    for (var i = 0; i < cartes.length; i++) {
      var t = cartes[i].querySelector('time[datetime]');
      if (!t || cartes[i].querySelector('.badge-nouveau')) { continue; }
      if (new Date(t.getAttribute('datetime')).getTime() < limite) { continue; }

      var badges = cartes[i].querySelector('.blog-card-badges');
      if (!badges) { continue; }
      var b = document.createElement('span');
      b.className = 'badge-nouveau';
      b.textContent = 'Nouveau';
      badges.insertBefore(b, badges.firstChild);
    }
  }

  /* ── 2. Recherche ──────────────────────────────────────────────────────── */

  var champ = document.getElementById('blog-q');
  var zone = document.querySelector('.blog-recherche');
  var resultats = document.querySelector('.blog-resultats');
  var contenu = document.querySelector('.blog-contenu');
  var etat = document.querySelector('.blog-recherche-etat');
  var vider = document.querySelector('.blog-recherche-vider');

  var index = null;
  var chargement = null;
  var minuteur = null;

  /** Minuscules et sans accents : « présences » doit répondre à « presence ». */
  function normaliser(t) {
    return (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  /* Pluriel : « écoles coraniques » doit trouver « école coranique ». On coupe
   * le s ou le x final des mots assez longs pour que ce soit sans risque —
   * c'est grossier, mais c'est ce qui sépare une recherche utilisable d'une
   * recherche qui ne trouve rien une fois sur deux. */
  function radical(mot) {
    return mot.length > 4 && /[sx]$/.test(mot) ? mot.slice(0, -1) : mot;
  }

  function chargerIndex() {
    if (index) { return Promise.resolve(index); }
    if (!chargement) {
      chargement = fetch(INDEX_URL)
        .then(function (r) { return r.ok ? r.json() : { articles: [] }; })
        .then(function (donnees) {
          index = (donnees.articles || []).map(function (a) {
            a.recherche = normaliser(a.mots);
            a.vedetteN = normaliser(a.vedette);
            return a;
          });
          return index;
        })
        .catch(function () { index = []; return index; });
    }
    return chargement;
  }

  function afficherTout() {
    resultats.hidden = true;
    resultats.innerHTML = '';
    contenu.hidden = false;
    etat.textContent = '';
    if (vider) { vider.hidden = true; }
  }

  function afficher(termes) {
    var mots = normaliser(termes).split(/\s+/).filter(Boolean).map(radical);

    /* Un mot du titre pèse trois fois un mot croisé dans un paragraphe. Sans
     * cela, chercher « présences » classe l'article sur les présences après
     * trois articles qui se contentent de mentionner le mot. */
    var trouves = [];
    for (var n = 0; n < index.length; n++) {
      var a = index[n], score = 0, complet = true;
      for (var i = 0; i < mots.length; i++) {
        if (a.recherche.indexOf(mots[i]) === -1) { complet = false; break; }
        score += a.vedetteN.indexOf(mots[i]) !== -1 ? 3 : 1;
        score += Math.min(a.recherche.split(mots[i]).length - 1, 5) * 0.2;
      }
      if (complet) { trouves.push({ a: a, score: score, rang: n }); }
    }
    // À score égal, le plus récent d'abord : l'index est déjà trié par date.
    trouves.sort(function (x, y) { return y.score - x.score || x.rang - y.rang; });
    trouves = trouves.map(function (t) { return t.a; });

    contenu.hidden = true;
    resultats.hidden = false;

    if (!trouves.length) {
      resultats.innerHTML =
        '<p class="blog-vide">Aucun article ne correspond à « ' +
        termes.replace(/[<&]/g, '') + ' ». ' +
        '<a href="/blog/">Voir tous les articles</a></p>';
      etat.textContent = 'Aucun résultat';
      return;
    }

    resultats.innerHTML = '<div class="blog-grid">' +
      trouves.map(function (a) { return a.carte; }).join('') + '</div>';
    etat.textContent = trouves.length > 1
      ? trouves.length + ' articles trouvés'
      : '1 article trouvé';
    marquerNouveautes(resultats);
  }

  function chercher() {
    var termes = champ.value.trim();
    if (vider) { vider.hidden = !termes; }
    if (termes.length < 2) { afficherTout(); return; }
    chargerIndex().then(function () { afficher(termes); });
  }

  function activerRecherche() {
    if (!champ || !zone || !resultats || !contenu) { return; }
    zone.hidden = false;

    champ.addEventListener('input', function () {
      clearTimeout(minuteur);
      minuteur = setTimeout(chercher, 130);
    });
    champ.addEventListener('keydown', function (evt) {
      if (evt.key === 'Escape') { champ.value = ''; chercher(); }
    });
    // Un formulaire n'est pas nécessaire : la recherche est instantanée.
    champ.addEventListener('search', chercher);
    if (vider) {
      vider.addEventListener('click', function () {
        champ.value = '';
        champ.focus();
        chercher();
      });
    }
  }

  function demarrer() {
    marquerNouveautes(document);
    activerRecherche();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
