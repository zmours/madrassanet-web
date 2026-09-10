/* ============================================================================
 * MadrassaNET — comportements des articles du blog
 * ----------------------------------------------------------------------------
 * Chargé par tous les articles. Deux choses, et rien d'autre : le lecteur
 * vidéo et l'indice de défilement des tableaux.
 *
 * POURQUOI CE FICHIER. Un <iframe> YouTube posé dans la page coûte environ
 * 900 Ko et deux cookies tiers à chaque lecteur, y compris à ceux qui ne
 * regarderont pas la vidéo. Ici, la page n'affiche qu'une image ; l'iframe
 * n'est créé qu'au clic, sur youtube-nocookie.com. Conséquence pratique :
 * aucune donnée n'est transmise à YouTube avant un geste du visiteur, donc
 * aucun bandeau de consentement à afficher.
 *
 * La mesure passe par les attributs data-track du bouton (cf. analytics.js) :
 * rien à faire ici.
 * ========================================================================== */
(function () {
  'use strict';

  var PERMISSIONS = 'accelerometer; autoplay; clipboard-write; encrypted-media; ' +
                    'gyroscope; picture-in-picture; web-share';

  /** Remplace la façade par le lecteur, éventuellement à un horodatage donné. */
  function charger(conteneur, secondes) {
    var id = conteneur.getAttribute('data-video');
    if (!id) { return; }

    var url = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) +
              '?autoplay=1&rel=0&modestbranding=1&hl=fr';
    if (secondes) { url += '&start=' + secondes; }

    var titre = 'Vidéo';
    var bouton = conteneur.querySelector('.video-embed-play');
    if (bouton) { titre = bouton.getAttribute('aria-label') || titre; }

    var iframe = document.createElement('iframe');
    iframe.src = url;
    iframe.title = titre;
    iframe.setAttribute('allow', PERMISSIONS);
    iframe.setAttribute('allowfullscreen', '');
    iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');

    conteneur.textContent = '';
    conteneur.appendChild(iframe);
    conteneur.setAttribute('data-charge', 'oui');
  }

  /* ── Tableaux qui défilent ────────────────────────────────────────────────
   * Un tableau trop large défile à l'intérieur de son cadre plutôt que de
   * pousser la page entière. Encore faut-il que le lecteur le sache : l'indice
   * n'est posé que sur les tableaux qui débordent RÉELLEMENT, et disparaît une
   * fois la fin atteinte. Un indice affiché à tort serait pire que pas
   * d'indice du tout.
   * ------------------------------------------------------------------------ */
  function suivreTableaux() {
    var cadres = document.querySelectorAll('.table-defilante');

    for (var i = 0; i < cadres.length; i++) {
      (function (cadre) {
        function etat() {
          var deborde = cadre.scrollWidth - cadre.clientWidth > 2;
          var auBout = cadre.scrollLeft + cadre.clientWidth >= cadre.scrollWidth - 2;
          cadre.classList.toggle('defile', deborde && !auBout);

          var indice = cadre.nextElementSibling;
          var estIndice = indice && indice.classList.contains('table-indice');
          if (deborde && !estIndice) {
            indice = document.createElement('p');
            indice.className = 'table-indice';
            indice.textContent = 'Faites glisser le tableau pour voir toutes les colonnes.';
            cadre.parentNode.insertBefore(indice, cadre.nextSibling);
          } else if (!deborde && estIndice) {
            indice.remove();
          }
        }
        etat();
        cadre.addEventListener('scroll', etat, { passive: true });
        window.addEventListener('resize', etat);
      })(cadres[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', suivreTableaux);
  } else {
    suivreTableaux();
  }

  document.addEventListener('click', function (evt) {
    if (!evt.target || !evt.target.closest) { return; }

    var facade = evt.target.closest('.video-embed-play');
    if (facade) {
      charger(facade.parentNode, 0);
      return;
    }

    // Chapitre : la vidéo est celle qui précède la liste des chapitres.
    var chapitre = evt.target.closest('.video-chapitres button');
    if (chapitre) {
      var liste = chapitre.closest('.video-chapitres');
      var conteneur = liste && liste.parentNode
        ? liste.parentNode.querySelector('.video-embed') : null;
      if (conteneur) {
        charger(conteneur, parseInt(chapitre.getAttribute('data-t'), 10) || 0);
        conteneur.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  });
})();
