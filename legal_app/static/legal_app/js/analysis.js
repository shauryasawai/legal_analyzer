// Analysis page: filter + ELI5
(function () {

  // ── Filter ────────────────────────────────────────────────────
  const filterBtns = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.clause-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.filter;

      cards.forEach(card => {
        if (filter === 'all' || card.dataset.risk === filter) {
          card.style.display = '';
          card.style.animation = 'fadeIn .25s ease';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // ── ELI5 buttons ─────────────────────────────────────────────
  document.querySelectorAll('.btn-eli5').forEach(btn => {
    btn.addEventListener('click', async () => {
      const clauseId = btn.dataset.clauseId;
      const container = document.getElementById(`eli5-${clauseId}`);
      const loading   = container.querySelector('.eli5-loading');
      const textEl    = container.querySelector('.eli5-text');

      // If already shown, toggle
      if (!textEl.classList.contains('hidden') && textEl.textContent) {
        container.classList.toggle('hidden');
        return;
      }

      btn.classList.add('loading');
      btn.textContent = '⏳ Explaining…';
      container.classList.remove('hidden');
      loading.classList.remove('hidden');
      textEl.classList.add('hidden');

      try {
        const resp = await fetch(`/api/eli5/${clauseId}/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': LexAI.getCsrfToken() },
        });
        const data = await resp.json();

        loading.classList.add('hidden');

        if (data.eli5) {
          textEl.classList.remove('hidden');
          typewriterEffect(textEl, data.eli5);
        } else {
          textEl.classList.remove('hidden');
          textEl.textContent = data.error || 'Could not generate explanation.';
        }
      } catch (err) {
        loading.classList.add('hidden');
        textEl.classList.remove('hidden');
        textEl.textContent = 'Network error. Please try again.';
      } finally {
        btn.classList.remove('loading');
        btn.innerHTML = '🧒 Explain Like I\'m 10';
      }
    });
  });

  // ── Typewriter effect ─────────────────────────────────────────
  function typewriterEffect(el, text, speed = 12) {
    el.textContent = '';
    let i = 0;
    const timer = setInterval(() => {
      el.textContent += text[i++];
      if (i >= text.length) clearInterval(timer);
    }, speed);
  }

  // ── Smooth scroll for sidebar nav ─────────────────────────────
  document.querySelectorAll('.clause-nav-item').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

})();
