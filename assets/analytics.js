/* ============================================================================
 * MadrassaNET — mesure d'audience et objectifs de conversion
 * ----------------------------------------------------------------------------
 * Un seul fichier, inclus par toutes les pages du site :
 *     <script src="/assets/analytics.js" defer></script>
 *
 * POUR ACTIVER LA MESURE  → renseigner CONFIG.provider et CONFIG.domain
 * POUR CHANGER D'OUTIL    → une seule ligne à modifier (CONFIG.provider)
 * POUR TOUT DÉSACTIVER    → CONFIG.provider = 'none'
 *
 * Trois objectifs sont suivis (cf. docs MARKETING.md) :
 *   • « Contact - Demande envoyée »   soumission réussie du formulaire
 *   • « Modele - Telechargement »     téléchargement d'un modèle
 *   • « Demo - Rendez-vous »          clic sur le lien de prise de rendez-vous
 *
 * Aucun cookie n'est posé par la variante Plausible : pas de bandeau à afficher.
 * ========================================================================== */
(function () {
  'use strict';

  var CONFIG = {
    // 'plausible' | 'ga4' | 'none'
    provider: 'plausible',

    // Plausible : le domaine déclaré dans le tableau de bord, SANS le www.
    domain: 'madrassanet.com',
    plausibleScript: 'https://plausible.io/js/script.file-downloads.outbound-links.js',

    // GA4 : à renseigner uniquement si provider === 'ga4' (ex. 'G-XXXXXXXXXX')
    ga4MeasurementId: '',

    // Ne rien envoyer depuis un poste de développement.
    ignoreLocalhost: true
  };

  var isLocal = location.protocol === 'file:' ||
    /^(localhost|127\.|0\.0\.0\.0|\[::1\]|192\.168\.)/.test(location.hostname);

  var active = CONFIG.provider !== 'none' && !(CONFIG.ignoreLocalhost && isLocal);

  /* ── Chargement du fournisseur ─────────────────────────────────────────── */
  function loadProvider() {
    if (!active) { return; }

    if (CONFIG.provider === 'plausible') {
      // File d'attente : permet d'appeler plausible() avant la fin du chargement.
      window.plausible = window.plausible || function () {
        (window.plausible.q = window.plausible.q || []).push(arguments);
      };
      var s = document.createElement('script');
      s.defer = true;
      s.setAttribute('data-domain', CONFIG.domain);
      s.src = CONFIG.plausibleScript;
      document.head.appendChild(s);
      return;
    }

    if (CONFIG.provider === 'ga4' && CONFIG.ga4MeasurementId) {
      window.dataLayer = window.dataLayer || [];
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
      window.gtag('config', CONFIG.ga4MeasurementId);
      var g = document.createElement('script');
      g.async = true;
      g.src = 'https://www.googletagmanager.com/gtag/js?id=' +
        encodeURIComponent(CONFIG.ga4MeasurementId);
      document.head.appendChild(g);
    }
  }

  /* ── API commune : mnTrack('Nom de l objectif', { cle: 'valeur' }) ─────── */
  function mnTrack(name, props) {
    if (!name) { return; }
    if (!active) {
      if (window.console && console.debug) {
        console.debug('[analytics inactif]', name, props || {});
      }
      return;
    }
    try {
      if (CONFIG.provider === 'plausible' && window.plausible) {
        window.plausible(name, props ? { props: props } : undefined);
      } else if (CONFIG.provider === 'ga4' && window.gtag) {
        // GA4 n'accepte ni espaces ni accents dans les noms d'événements.
        var safe = name.toLowerCase()
          .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
          .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
        window.gtag('event', safe, props || {});
      }
    } catch (e) { /* la mesure ne doit jamais casser une page */ }
  }
  window.mnTrack = mnTrack;

  /* ── Suivi déclaratif : <a data-track="Nom" data-track-fichier="x"> ─────
   * Évite d'écrire du JavaScript dans chaque page : il suffit de poser les
   * attributs sur le lien ou le bouton concerné.
   * ---------------------------------------------------------------------- */
  function onClick(evt) {
    var el = evt.target && evt.target.closest ? evt.target.closest('[data-track]') : null;
    if (!el) { return; }
    var name = el.getAttribute('data-track');
    var props = {};
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i];
      if (a.name.indexOf('data-track-') === 0 && a.name !== 'data-track') {
        props[a.name.slice('data-track-'.length)] = a.value;
      }
    }
    mnTrack(name, Object.keys(props).length ? props : null);
  }

  /* ── Conservation de la campagne d'origine ────────────────────────────────
   * Les UTM sont perdus dès la deuxième page. On les mémorise pour la durée
   * de la visite afin de pouvoir les rattacher à une demande de contact.
   * ---------------------------------------------------------------------- */
  function captureCampaign() {
    try {
      var qs = new URLSearchParams(location.search);
      var keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
      var found = {};
      var any = false;
      keys.forEach(function (k) {
        var v = qs.get(k);
        if (v) { found[k] = v; any = true; }
      });
      if (any) {
        found.landing = location.pathname;
        found.at = new Date().toISOString();
        sessionStorage.setItem('mn_campaign', JSON.stringify(found));
      }
    } catch (e) { /* navigation privée, stockage refusé : sans conséquence */ }
  }

  /** Renvoie la campagne d'origine de la visite, ou null. */
  window.mnCampaign = function () {
    try {
      var raw = sessionStorage.getItem('mn_campaign');
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  };

  /** Résumé court « source/medium/campagne », à joindre à un formulaire. */
  window.mnCampaignLabel = function () {
    var c = window.mnCampaign();
    if (!c) { return 'direct'; }
    return [c.utm_source || '?', c.utm_medium || '?', c.utm_campaign || '?'].join('/');
  };

  loadProvider();
  captureCampaign();
  document.addEventListener('click', onClick, true);
})();
