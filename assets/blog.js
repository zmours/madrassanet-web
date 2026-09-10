/* ============================================================================
 * MadrassaNET — lecteur vidéo des articles du blog
 * ----------------------------------------------------------------------------
 * Chargé uniquement par les articles qui portent une vidéo.
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
