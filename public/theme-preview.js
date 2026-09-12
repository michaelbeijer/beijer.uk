/* A ground to look at, not a setting to keep.
 *
 * Three options - the white the site has, the cream #F0EEE6 that Dario
 * Amodei's essays use, and a dark ground - swapped by setting data-theme on
 * <html>, which the blocks at the end of global.css answer.
 *
 * It only appears when the URL carries ?themes, and the choice is kept in
 * sessionStorage so it follows you from page to page within the one tab and
 * dies with it. A visitor who never types ?themes never loads a byte of this
 * beyond the file itself.
 *
 * Delete this file, its <script> tag in BaseHead.astro and the [data-theme] blocks in global.css
 * together once the question is answered.
 */
(function () {
  var KEY = 'beijer-ground-preview';

  // sessionStorage throws outright in some embedded contexts rather than
  // returning null, so every touch of it is guarded.
  function remembered() {
    try { return sessionStorage.getItem(KEY); } catch (e) { return null; }
  }
  function remember(value) {
    try {
      if (value) sessionStorage.setItem(KEY, value);
      else sessionStorage.removeItem(KEY);
    } catch (e) { /* private mode: the choice lasts this page only */ }
  }

  var asked = /(\?|&)themes(=|&|$)/.test(location.search);
  if (!asked && !remembered()) return;

  var GROUNDS = [
    { id: '', label: 'White', swatch: '#ffffff', note: 'what the site has' },
    { id: 'cream', label: 'Cream', swatch: '#f0eee6', note: '#F0EEE6' },
    { id: 'dark', label: 'Dark', swatch: '#121212', note: '' }
  ];

  function apply(id) {
    if (id) document.documentElement.setAttribute('data-theme', id);
    else document.documentElement.removeAttribute('data-theme');
    remember(id);
    var buttons = panel.querySelectorAll('button[data-ground]');
    for (var i = 0; i < buttons.length; i++) {
      var mine = buttons[i].getAttribute('data-ground') === id;
      buttons[i].setAttribute('aria-pressed', mine ? 'true' : 'false');
    }
  }

  var panel = document.createElement('div');
  panel.className = 'ground-preview';
  panel.setAttribute('role', 'group');
  panel.setAttribute('aria-label', 'Page background, preview only');

  var style = document.createElement('style');
  style.textContent = [
    '.ground-preview{position:fixed;left:1.25rem;bottom:1.25rem;z-index:60;',
    '  display:flex;gap:.35rem;align-items:center;padding:.4rem;',
    '  background:rgb(var(--bg));border:1px solid rgb(var(--border));border-radius:6px;',
    '  box-shadow:0 2px 12px rgba(0,0,0,.12);font-size:.85rem}',
    '.ground-preview button{display:flex;align-items:center;gap:.4rem;',
    '  padding:.3rem .55rem;border:1px solid transparent;border-radius:4px;',
    '  background:none;color:rgb(var(--text));font:inherit;cursor:pointer}',
    '.ground-preview button[aria-pressed="true"]{border-color:rgb(var(--border));',
    '  background:rgb(var(--code-bg));font-weight:600}',
    '.ground-preview i{width:.85rem;height:.85rem;border-radius:50%;',
    '  border:1px solid rgba(128,128,128,.5)}',
    /* On a phone the panel would sit on top of the back-to-top button, so it
       gives up its labels and keeps only the swatches. */
    '@media (max-width:600px){.ground-preview{left:.6rem;bottom:.6rem}',
    '  .ground-preview span{display:none}}'
  ].join('');
  document.head.appendChild(style);

  GROUNDS.forEach(function (g) {
    var b = document.createElement('button');
    b.type = 'button';
    b.setAttribute('data-ground', g.id);
    b.title = g.note ? g.label + ' - ' + g.note : g.label;
    var dot = document.createElement('i');
    dot.style.background = g.swatch;
    var text = document.createElement('span');
    text.textContent = g.label;
    b.appendChild(dot);
    b.appendChild(text);
    b.addEventListener('click', function () { apply(g.id); });
    panel.appendChild(b);
  });

  document.body.appendChild(panel);
  apply(remembered() || '');
})();
