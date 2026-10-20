/* Source browsing only: no session, world mutation or action endpoint. */
'use strict';
(() => {
  const cards = [...document.querySelectorAll('[data-reference]')];
  const search = document.getElementById('reference-search');
  const category = document.getElementById('reference-category');
  const count = document.getElementById('reference-count');
  const status = document.getElementById('preview-status');
  const entries = cards.map(card => ({card, text: card.textContent.toLocaleLowerCase()}));
  let active = null;
  function closePreview() {
    if (!active) return;
    active.slot.replaceChildren();
    active.button.setAttribute('aria-expanded', 'false');
    active.button.textContent = 'Preview image';
    active = null;
  }
  function filter() {
    const query = search.value.trim().toLocaleLowerCase();
    let shown = 0;
    for (const entry of entries) {
      const visible = (!category.value || entry.card.dataset.category === category.value) &&
        (!query || entry.text.includes(query));
      entry.card.hidden = !visible;
      if (visible) shown++;
      if (!visible && active && active.card === entry.card) closePreview();
    }
    count.textContent = `${shown} of ${cards.length} unique references shown.`;
  }
  for (const card of cards) {
    const button = card.querySelector('[data-preview]');
    const link = card.querySelector('[data-original]');
    const slot = card.querySelector('.reference-preview');
    button.hidden = false;
    button.addEventListener('click', () => {
      const wasActive = active && active.button === button;
      closePreview();
      if (wasActive) { status.textContent = 'Preview closed.'; return; }
      const img = document.createElement('img');
      img.alt = card.querySelector('[data-observation]').textContent;
      img.width = Number(card.dataset.width); img.height = Number(card.dataset.height);
      img.decoding = 'async';
      const loading = document.createElement('p');
      loading.className = 'subtle'; loading.textContent = 'Loading original image…';
      img.addEventListener('load', () => {
        if (!active || active.img !== img) return;
        loading.textContent = 'Original image. Open the full-size link to inspect small text.';
        status.textContent = `${card.querySelector('h2').textContent} preview ready.`;
      });
      img.addEventListener('error', () => {
        if (!active || active.img !== img) return;
        loading.textContent = 'Preview could not load. Use the full-size link or reopen this preview.';
        status.textContent = 'Image preview could not load.';
      });
      active = {card, button, slot, img};
      slot.replaceChildren(loading, img);
      img.src = link.getAttribute('href');
      button.setAttribute('aria-expanded', 'true'); button.textContent = 'Close preview';
      status.textContent = `Loading ${card.querySelector('h2').textContent}.`;
    });
  }
  document.getElementById('reference-controls').hidden = false;
  search.addEventListener('input', filter); category.addEventListener('change', filter);
  filter();
})();
