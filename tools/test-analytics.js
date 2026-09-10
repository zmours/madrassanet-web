/* ============================================================================
 * MadrassaNET — test du script de mesure, hors navigateur
 * ----------------------------------------------------------------------------
 *     node tools/test-analytics.js
 *
 * POURQUOI CE FICHIER. Le consentement est la partie du site qu'on ne peut pas
 * se permettre de casser : une régression y enverrait des données à un tiers
 * sans accord. Un DOM minimal suffit à vérifier l'essentiel — qu'aucune requête
 * ne part avant un « oui », qu'un « non » n'est pas redemandé, et qu'un
 * objectif atteint avant la réponse n'est pas perdu.
 *
 * Aucune dépendance : ni navigateur, ni npm install.
 * ========================================================================== */
const fs = require('fs');
const path = require('path');
const SRC = path.join(__dirname, '..', 'assets', 'analytics.js');

function faireDom(stockage) {
  const ecoute = {};
  const ajoutes = [];
  const elements = [];
  function creerElement(tag) {
    const el = {
      tagName: tag, attributs: {}, enfants: [], className: '', innerHTML: '',
      textContent: '', style: {},
      setAttribute(k, v) { this.attributs[k] = v; },
      getAttribute(k) { return this.attributs[k] ?? null; },
      appendChild(c) { this.enfants.push(c); return c; },
      addEventListener(t, f) { (this.ecoute = this.ecoute || {})[t] = f; },
      querySelector() { return null; },
      querySelectorAll() { return []; },
      closest() { return null; },
      focus() {},
    };
    elements.push(el);
    return el;
  }
  const body = creerElement('body');
  const doc = {
    readyState: 'complete',
    head: { appendChild(s) { ajoutes.push(s); return s; } },
    body,
    createElement: creerElement,
    querySelector(sel) {
      if (sel === '.bandeau-consentement') {
        return body.enfants.find((e) => e.className === 'bandeau-consentement') || null;
      }
      if (sel === '.footer-bottom') { return doc._pied; }
      return null;
    },
    addEventListener(t, f) { ecoute[t] = f; },
  };
  doc._pied = creerElement('div');
  doc._pied.querySelector = () => null;
  const g = {
    document: doc,
    location: { protocol: 'https:', hostname: 'www.madrassanet.com', search: '', pathname: '/blog/' },
    localStorage: {
      _d: { ...stockage },
      getItem(k) { return k in this._d ? this._d[k] : null; },
      setItem(k, v) { this._d[k] = v; },
    },
    sessionStorage: { _d: {}, getItem(k) { return this._d[k] ?? null; }, setItem(k, v) { this._d[k] = v; } },
    URLSearchParams,
    console,
    Date,
  };
  g.window = g;
  return { g, doc, ajoutes, body, ecoute };
}

function lancer(provider, identifiant, stockage) {
  let src = fs.readFileSync(SRC, 'utf8');
  // Le test force le fournisseur. Si la ligne change de forme, il faut le
  // savoir : sans cette garde, tous les cas tourneraient sur le fournisseur
  // par défaut et passeraient pour de mauvaises raisons.
  const avant = src;
  src = src.replace(/provider: '[a-z0-9]+'/, `provider: '${provider}'`);
  if (src === avant && !avant.includes(`provider: '${provider}'`)) {
    throw new Error('impossible de forcer CONFIG.provider dans analytics.js');
  }
  // On écrase la valeur configurée, quelle qu'elle soit : le test doit dire la
  // même chose avant et après qu'un identifiant réel a été collé dans le fichier.
  src = src.replace(/umamiWebsiteId: '[^']*'/, `umamiWebsiteId: '${identifiant}'`)
           .replace(/ga4MeasurementId: '[^']*'/, `ga4MeasurementId: '${identifiant}'`);
  const { g, doc, ajoutes, body, ecoute } = faireDom(stockage);
  const vm = require('vm');
  vm.createContext(g);
  vm.runInContext(src, g);
  if (ecoute.DOMContentLoaded) ecoute.DOMContentLoaded();
  return { g, doc, ajoutes, body, ecoute };
}

function verifier(titre, cas) {
  try {
    cas();
    console.log('  ok   ' + titre);
  } catch (e) {
    console.log('  ÉCHEC ' + titre + ' → ' + e.message);
    process.exitCode = 1;
  }
}

const assert = require('assert');

console.log('Umami configuré :');
{
  const r = lancer('umami', '0a1b-test', {});
  verifier('script umami chargé', () => assert.strictEqual(r.ajoutes.length, 1));
  verifier('identifiant transmis', () =>
    assert.strictEqual(r.ajoutes[0].attributs['data-website-id'], '0a1b-test'));
  verifier('aucun bandeau affiché', () => assert.strictEqual(r.body.enfants.length, 0));
  verifier('événement mis en file avant chargement', () => {
    r.g.mnTrack('Demo - Rendez-vous');            // umami pas encore prêt
    const recus = [];
    r.g.umami = { track: (n) => recus.push(n) };
    r.ajoutes[0].ecoute.load();                    // le script finit de charger
    assert.deepStrictEqual(recus, ['Demo - Rendez-vous']);
  });
}

console.log('Umami non configuré (identifiant vide) :');
{
  const r = lancer('umami', '', {});
  verifier('rien chargé', () => assert.strictEqual(r.ajoutes.length, 0));
  verifier('mnTrack ne casse pas', () => r.g.mnTrack('Contact - Demande envoyee'));
}

console.log('GA4 sans choix enregistré :');
{
  const r = lancer('ga4', 'G-TEST123', {});
  verifier('rien envoyé à Google', () => assert.strictEqual(r.ajoutes.length, 0));
  verifier('bandeau affiché', () => assert.strictEqual(r.body.enfants[0].className, 'bandeau-consentement'));
  verifier('deux boutons, refus et accord', () => {
    const h = r.body.enfants[0].innerHTML;
    assert.ok(h.includes('data-consentement="refuse"') && h.includes('data-consentement="accepte"'));
  });
}

console.log('GA4 après refus :');
{
  const r = lancer('ga4', 'G-TEST123', { mn_consentement_v1: 'refuse' });
  verifier('rien chargé', () => assert.strictEqual(r.ajoutes.length, 0));
  verifier('bandeau non réaffiché', () => assert.strictEqual(r.body.enfants.length, 0));
  verifier('mnTrack silencieux', () => r.g.mnTrack('Demo - Rendez-vous'));
}

console.log('GA4 après acceptation :');
{
  const r = lancer('ga4', 'G-TEST123', { mn_consentement_v1: 'accepte' });
  verifier('gtag chargé', () => assert.ok(r.ajoutes.some((s) => (s.src || '').includes('googletagmanager'))));
  verifier('consentement par défaut refusé puis accordé', () => {
    const c = r.g.dataLayer.filter((a) => a[0] === 'consent');
    assert.strictEqual(c[0][1], 'default');
    assert.strictEqual(c[0][2].analytics_storage, 'denied');
    assert.strictEqual(c[1][1], 'update');
    assert.strictEqual(c[1][2].analytics_storage, 'granted');
  });
  verifier('nom d événement normalisé pour GA4', () => {
    r.g.gtag = (...a) => r.g.dataLayer.push(a);
    r.g.mnTrack('Contact - Demande envoyee');
    const ev = r.g.dataLayer.filter((a) => a[0] === 'event').pop();
    assert.strictEqual(ev[1], 'contact_demande_envoyee');
  });
}

console.log('Plausible (sans consentement requis) :');
{
  const r = lancer('plausible', '', {});
  verifier('script chargé sans bandeau', () => {
    assert.ok(r.ajoutes.some((s) => (s.src || '').includes('plausible')));
    assert.strictEqual(r.body.enfants.length, 0);
  });
}
