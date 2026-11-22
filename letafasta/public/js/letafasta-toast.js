/* LetaFasta toast notifications — replace browser alert() */
function lf_toast(message, type) {
  var colors = {success: '#16A34A', error: '#DC2626', warning: '#D97706', info: '#2563EB'};
  var t = document.createElement('div');
  t.style.cssText = [
    'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);',
    'background:' + (colors[type || 'success']) + ';color:white;',
    'padding:12px 24px;border-radius:999px;',
    'font-size:14px;font-weight:600;font-family:var(--lf-font,system-ui),sans-serif;',
    'box-shadow:0 4px 12px rgba(0,0,0,0.2);',
    'z-index:9998;white-space:nowrap;',
  ].join('');
  t.textContent = message;
  document.body.appendChild(t);
  setTimeout(function() { t.remove(); }, 3000);
}

window.lf_toast = lf_toast;
