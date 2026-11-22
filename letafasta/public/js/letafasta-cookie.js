/* LetaFasta cookie consent banner — Tanzania PDPA 2022 compliant */
(function() {
  try {
    if (localStorage.getItem('lf_cookie_consent')) return;
  } catch(e) { return; }

  var banner = document.createElement('div');
  banner.id = 'lf-cookie-banner';
  banner.innerHTML =
    '<p>Tunatumia <strong>vidakuzi (cookies)</strong> ili kuboresha uzoefu wako.' +
    ' Soma <a href="/letafasta/privacy">Sera yetu ya Faragha</a> na' +
    ' <a href="/letafasta/cookies">Sera ya Vidakuzi</a>.</p>' +
    '<div class="lf-cookie-actions">' +
    '<button id="lf-cookie-accept">Kukubali Vyote</button>' +
    '<button id="lf-cookie-essential">Muhimu Tu</button>' +
    '</div>';

  document.body.appendChild(banner);

  document.getElementById('lf-cookie-accept').onclick = function() {
    try { localStorage.setItem('lf_cookie_consent', 'all'); } catch(e) {}
    banner.remove();
  };
  document.getElementById('lf-cookie-essential').onclick = function() {
    try { localStorage.setItem('lf_cookie_consent', 'essential'); } catch(e) {}
    banner.remove();
  };
})();
