document.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get('slug');
  const titleEl = document.getElementById('pageTitle');
  const contentEl = document.getElementById('pageContent');

  if (!slug) {
    titleEl.textContent = 'Sahifa topilmadi';
    contentEl.textContent = 'Sahifa havolasi noto\'g\'ri.';
    return;
  }

  try {
    const res = await api.get('/api/pages');
    const pages = Array.isArray(res) ? res : [];
    const page = pages.find(p => p.slug === slug);
    if (!page) {
      titleEl.textContent = 'Sahifa topilmadi';
      contentEl.textContent = 'Bunday sahifa mavjud emas.';
      return;
    }
    titleEl.textContent = page.title || 'Sahifa';
    contentEl.textContent = page.content || 'Ma\'lumot yo\'q.';
  } catch (e) {
    console.error('Page load error:', e);
    titleEl.textContent = 'Xato';
    contentEl.textContent = 'Sahifa yuklanmadi.';
  }
});
