/* ============================================================================
 * MadrassaNET — mesure d'audience, consentement et objectifs de conversion
 * ----------------------------------------------------------------------------
 * Un seul fichier, inclus par toutes les pages du site :
 *     <script src="/assets/analytics.js" defer></script>
 *
 * POUR ACTIVER LA MESURE  → renseigner l'identifiant du fournisseur choisi
 * POUR CHANGER D'OUTIL    → CONFIG.provider ('umami' | 'ga4' | 'plausible' | 'none')
 * POUR TOUT DÉSACTIVER    → CONFIG.provider = 'none'
 *
 * Le fournisseur par défaut est **Umami** : gratuit jusqu'à 100 000 événements
 * par mois, sans cookie — donc sans bandeau de consentement — et c'est le même
 * logiciel que la version auto-hébergée. Le jour où l'on héberge sa propre
 * instance, seule CONFIG.umamiScript change ; les objectifs, les attributs
 * data-track et les pages restent identiques.
 *
 * Trois objectifs sont suivis (cf. MARKETING.md) :
 *   • « Contact - Demande envoyee »   soumission réussie du formulaire
 *   • « Ressource - Telechargement »  téléchargement d'un modèle
 *   • « Demo - Rendez-vous »          clic sur le lien de prise de rendez-vous
 *
 * ── LE CONSENTEMENT, ET POURQUOI IL EST ICI ────────────────────────────────
 * Google Analytics dépose des cookies et transmet des données à un tiers : il
 * exige donc un consentement préalable, libre et révocable. Ce fichier ne se
 * contente pas de l'afficher, il le fait respecter : tant que le visiteur n'a
 * pas accepté, AUCUNE requête n'est envoyée à Google — le script gtag n'est
 * même pas chargé. Un refus n'est pas redemandé à la page suivante.
 *
 * Ce n'est pas du zèle : ce site vend la conformité RGPD à des écoles. Une
 * mesure d'audience posée en douce y coûterait plus que ce qu'elle rapporte.
 *
 * Le bandeau ne s'affiche que pour les fournisseurs qui en ont besoin
 * (cf. CONSENTEMENT_REQUIS). Repasser à Plausible le fait disparaître tout
 * seul, sans rien changer aux pages.
 * ========================================================================== */
(function () {
  'use strict';

  var CONFIG = {
    // 'umami' | 'ga4' | 'plausible' | 'none'
    provider: 'umami',

    // Umami : l'identifiant du site, donné à la création dans le tableau de
    // bord (une chaîne de la forme '0a1b2c3d-...'). Tant qu'il est vide, rien
    // n'est chargé et rien n'est envoyé.
    umamiWebsiteId: 'bf12a351-1617-44b0-9dc7-98de0356e5f9',
    // Umami Cloud aujourd'hui ; remplacer par l'URL de sa propre instance
    // (ex. 'https://stats.madrassanet.com/script.js') le jour venu.
    umamiScript: 'https://cloud.umami.is/script.js',

    // GA4 : l'identifiant de flux de données, de la forme 'G-XXXXXXXXXX'.
    // Attention : GA4 dépose des cookies, donc le bandeau de consentement
    // s'affiche automatiquement et une partie des visiteurs refusera.
    ga4MeasurementId: '',

    // Plausible : le domaine déclaré dans le tableau de bord, SANS le www.
    domain: 'madrassanet.com',
    plausibleScript: 'https://plausible.io/js/script.file-downloads.outbound-links.js',

    // Ne rien envoyer depuis un poste de développement.
    ignoreLocalhost: true
  };

  /* Fournisseurs qui déposent des cookies ou appellent un tiers, et qui
   * demandent donc un consentement préalable. */
  var CONSENTEMENT_REQUIS = { umami: false, ga4: true, plausible: false, none: false };

  /* Clé de stockage du choix. Incrémenter la version reposera la question à
   * tout le monde : à faire uniquement si les finalités changent. */
  var CLE_CONSENTEMENT = 'mn_consentement_v1';

  var isLocal = location.protocol === 'file:' ||
    /^(localhost|127\.|0\.0\.0\.0|\[::1\]|192\.168\.)/.test(location.hostname);

  function estConfigure() {
    if (CONFIG.provider === 'umami') { return !!CONFIG.umamiWebsiteId; }
    if (CONFIG.provider === 'ga4') { return !!CONFIG.ga4MeasurementId; }
    if (CONFIG.provider === 'umami') {
      var u = document.createElement('script');
      u.defer = true;
      u.src = CONFIG.umamiScript;
      u.setAttribute('data-website-id', CONFIG.umamiWebsiteId);
      // Aucun attribut de plus : ni cookie, ni identifiant persistant, ni
      // stockage local. Rien à mémoriser côté visiteur, donc rien à lui
      // demander — c'est ce qui permet de se passer de bandeau.
      u.addEventListener('load', viderAttente);
      document.head.appendChild(u);
      return;
    }

    if (CONFIG.provider === 'plausible') { return !!CONFIG.domain; }
    return false;
  }

  var configure = estConfigure();

  var active = configure && !(CONFIG.ignoreLocalhost && isLocal);
  var besoinConsentement = !!CONSENTEMENT_REQUIS[CONFIG.provider];

  var charge = false;
  var enAttente = [];   // événements survenus avant la réponse au bandeau

  /* ── Mémoire du choix ──────────────────────────────────────────────────── */

  function lireChoix() {
    try {
      return localStorage.getItem(CLE_CONSENTEMENT);
    } catch (e) {
      // Navigation privée ou stockage refusé : on considère qu'il n'y a pas
      // de choix, et on ne mesure donc pas.
      return null;
    }
  }

  function ecrireChoix(valeur) {
    try {
      localStorage.setItem(CLE_CONSENTEMENT, valeur);
    } catch (e) { /* sans conséquence : la mesure restera simplement inactive */ }
  }

  /* ── Chargement du fournisseur ─────────────────────────────────────────── */

  function loadProvider() {
    if (!active || charge) { return; }
    charge = true;

    if (CONFIG.provider === 'umami') {
      var u = document.createElement('script');
      u.defer = true;
      u.src = CONFIG.umamiScript;
      u.setAttribute('data-website-id', CONFIG.umamiWebsiteId);
      // Aucun attribut de plus : ni cookie, ni identifiant persistant, ni
      // stockage local. Rien à mémoriser côté visiteur, donc rien à lui
      // demander — c'est ce qui permet de se passer de bandeau.
      u.addEventListener('load', viderAttente);
      document.head.appendChild(u);
      return;
    }

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

    if (CONFIG.provider === 'ga4') {
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

      // Consent Mode v2 : le consentement est accordé explicitement, jamais par
      // défaut. Utile le jour où Google Ads ou Search Ads sont branchés.
      window.gtag('consent', 'default', {
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        analytics_storage: 'denied',
        wait_for_update: 500
      });
      window.gtag('consent', 'update', { analytics_storage: 'granted' });

      window.gtag('js', new Date());
      window.gtag('config', CONFIG.ga4MeasurementId, {
        anonymize_ip: true,
        allow_google_signals: false,      // pas de publicité, pas de données démographiques
        allow_ad_personalization_signals: false
      });

      var g = document.createElement('script');
      g.async = true;
      g.src = 'https://www.googletagmanager.com/gtag/js?id=' +
        encodeURIComponent(CONFIG.ga4MeasurementId);
      document.head.appendChild(g);
    }
  }

  /** Vrai si la mesure peut tourner : configurée, et consentie si nécessaire. */
  function autorisee() {
    if (!active) { return false; }
    return besoinConsentement ? lireChoix() === 'accepte' : true;
  }

  /* ── API commune : mnTrack('Nom de l objectif', { cle: 'valeur' }) ─────── */

  function mnTrack(name, props) {
    if (!name) { return; }

    if (!autorisee()) {
      // Un objectif atteint avant la réponse au bandeau n'est pas perdu : il
      // part si le visiteur accepte, et disparaît avec la page s'il refuse.
      if (active && besoinConsentement && lireChoix() === null) {
        enAttente.push([name, props || null]);
        return;
      }
      if (window.console && console.debug) {
        console.debug('[mesure inactive]', name, props || {});
      }
      return;
    }

    try {
      if (CONFIG.provider === 'umami') {
        if (window.umami && window.umami.track) {
          window.umami.track(name, props || undefined);
        } else {
          enAttente.push([name, props || null]);   // script pas encore chargé
        }
      } else if (CONFIG.provider === 'plausible' && window.plausible) {
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

  function viderAttente() {
    var file = enAttente.splice(0, enAttente.length);
    for (var i = 0; i < file.length; i++) {
      mnTrack(file[i][0], file[i][1]);
    }
  }

  /* ── Le bandeau ────────────────────────────────────────────────────────── */

  function fermerBandeau() {
    var b = document.querySelector('.bandeau-consentement');
    if (b && b.parentNode) { b.parentNode.removeChild(b); }
  }

  function repondre(valeur) {
    ecrireChoix(valeur);
    fermerBandeau();
    if (valeur === 'accepte') {
      loadProvider();
      viderAttente();
    } else {
      enAttente.length = 0;
    }
    majLienReglages();
  }

  function afficherBandeau() {
    if (document.querySelector('.bandeau-consentement')) { return; }

    var b = document.createElement('div');
    b.className = 'bandeau-consentement';
    b.setAttribute('role', 'dialog');
    b.setAttribute('aria-label', 'Mesure d’audience');
    b.innerHTML =
      '<div class="bandeau-consentement-inner">' +
        '<p>' +
          '<strong>Nous aimerions mesurer l’audience de ce site.</strong> ' +
          'Google Analytics nous dit quelles pages vous sont utiles ; il dépose ' +
          'pour cela des cookies sur votre appareil. Rien n’est déposé ni ' +
          'envoyé sans votre accord, et refuser ne change rien au site. ' +
          '<a href="/privacy/">Notre politique de confidentialité</a>' +
        '</p>' +
        '<div class="bandeau-consentement-actions">' +
          '<button type="button" class="btn-consentement refus" data-consentement="refuse">Refuser</button>' +
          '<button type="button" class="btn-consentement accord" data-consentement="accepte">Accepter</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(b);

    var premier = b.querySelector('button');
    if (premier) { premier.focus(); }
  }

  /* Lien de révocation, ajouté au pied de page de toutes les pages sans avoir
   * à les modifier une par une. Le RGPD demande un consentement révocable
   * aussi facilement qu'il a été donné. */
  function majLienReglages() {
    var pied = document.querySelector('.footer-bottom');
    if (!pied || !besoinConsentement || !configure) { return; }

    var lien = pied.querySelector('.lien-consentement');
    if (!lien) {
      lien = document.createElement('a');
      lien.className = 'lien-consentement';
      lien.href = '#';
      lien.addEventListener('click', function (evt) {
        evt.preventDefault();
        afficherBandeau();
      });
      pied.appendChild(lien);
    }
    lien.textContent = lireChoix() === 'accepte'
      ? 'Mesure d’audience : acceptée'
      : 'Mesure d’audience : refusée';
  }

  /** Rouvre le bandeau. Exposé pour un lien écrit en dur dans une page. */
  window.mnConsentement = function () { afficherBandeau(); };

  /* ── Suivi déclaratif : <a data-track="Nom" data-track-fichier="x"> ─────
   * Évite d'écrire du JavaScript dans chaque page : il suffit de poser les
   * attributs sur le lien ou le bouton concerné.
   * ---------------------------------------------------------------------- */
  function onClick(evt) {
    var cible = evt.target && evt.target.closest ? evt.target : null;
    if (!cible) { return; }

    var choix = cible.closest('[data-consentement]');
    if (choix) {
      repondre(choix.getAttribute('data-consentement'));
      return;
    }

    var el = cible.closest('[data-track]');
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
   *
   * sessionStorage, pas de cookie, pas d'envoi à un tiers : c'est de la
   * mémoire de formulaire, elle ne dépend donc pas du consentement.
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

  /* ── Démarrage ─────────────────────────────────────────────────────────── */

  function demarrer() {
    if (!besoinConsentement) {
      loadProvider();
    } else if (active) {
      var choix = lireChoix();
      if (choix === 'accepte') {
        loadProvider();
      } else if (choix === null) {
        afficherBandeau();
      }
      majLienReglages();
    }
  }

  captureCampaign();
  document.addEventListener('click', onClick, true);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
