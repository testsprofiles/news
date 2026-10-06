const PER_PAGE = 9;
let currentPage = 1;
let totalPosts = 0;
let searchTerm = '';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const postsGrid = $('#postsGrid');
const loadingEl = $('#loadingState');
const errorEl = $('#errorState');
const errorText = $('#errorText');
const emptyEl = $('#emptyState');
const prevBtn = $('#prevPage');
const nextBtn = $('#nextPage');
const pageNumbers = $('#pageNumbers');
const searchInput = $('#searchInput');

const renderPostCard = (post) => {
  const catName = (post.category && post.category.name) ? post.category.name : (post.category_name || '—');
  return `
    <article class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden card-hover fade-in">
      <div class="h-48 bg-gradient-to-br from-blue-100 to-blue-50 flex items-center justify-center">
        ${post.image_url ? `<img src="${post.image_url}" alt="${escapeHtml(post.title)}" class="w-full h-full object-cover">` : ''}
        <div class="absolute top-3 right-3 bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded-lg text-xs font-medium text-gray-600 shadow">
          ${escapeHtml(catName)}
        </div>
      </div>
      <div class="p-5">
        <h3 class="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">${escapeHtml(post.title)}</h3>
        <p class="text-sm text-gray-500 mb-4 line-clamp-2">${escapeHtml(post.content || '')}</p>
        <div class="flex items-center justify-between text-xs text-gray-400 border-t border-gray-100 pt-3">
          <span>${formatDate(post.created_at)}</span>
          <a href="post.html?id=${post.id}" class="text-blue-600 font-medium hover:underline">Batafsil →</a>
        </div>
      </div>
    </article>
  `;
};

const escapeHtml = (str) => {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('uz', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch (e) { return dateStr; }
};

const showLoading = () => {
  loadingEl.classList.remove('hidden');
  postsGrid.innerHTML = '';
  prevBtn.disabled = true;
  nextBtn.disabled = true;
};

const hideLoading = () => loadingEl.classList.add('hidden');

const showError = (msg) => {
  errorEl.classList.remove('hidden');
  errorText.textContent = msg;
};

const hideError = () => errorEl.classList.add('hidden');

const showEmpty = (show) => {
  if (show) emptyEl.classList.remove('hidden');
  else emptyEl.classList.add('hidden');
};

const renderPagination = () => {
  const totalPages = Math.ceil(totalPosts / PER_PAGE) || 1;
  prevBtn.disabled = currentPage <= 1;
  nextBtn.disabled = currentPage >= totalPages;

  pageNumbers.innerHTML = '';
  let start = Math.max(1, currentPage - 2);
  let end = Math.min(totalPages, currentPage + 2);

  if (start > 1) {
    pageNumbers.insertAdjacentHTML('beforeend', `<button class="page-btn px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition" data-page="1">1</button>`);
    if (start > 2) {
      pageNumbers.insertAdjacentHTML('beforeend', `<span class="px-2 text-gray-400">...</span>`);
    }
  }

  for (let p = start; p <= end; p++) {
    const btn = document.createElement('button');
    btn.className = `page-btn px-3 py-1.5 text-sm border border-gray-300 rounded-lg transition ${p === currentPage ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-gray-50'}`;
    btn.textContent = p;
    if (p === currentPage) btn.disabled = true;
    btn.dataset.page = p;
    pageNumbers.appendChild(btn);
  }

  if (end < totalPages) {
    if (end < totalPages - 1) {
      pageNumbers.insertAdjacentHTML('beforeend', `<span class="px-2 text-gray-400">...</span>`);
    }
    pageNumbers.insertAdjacentHTML('beforeend', `<button class="page-btn px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition" data-page="${totalPages}">${totalPages}</button>`);
  }
};

const loadPosts = async (page = 1, replace = true) => {
  currentPage = page;
  showLoading();
  hideError();
  showEmpty(false);

  try {
    const params = replace ? { page, limit: PER_PAGE } : {};
    if (searchTerm && searchTerm.length > 0 && searchTerm.length <= 3) {
      params.title = searchTerm;
    }
    const query = new URLSearchParams(params).toString();
    const posts = await api.get(`/api/posts?${query}`);
    totalPosts = Array.isArray(posts) ? posts.length : (posts.total || 0);

    postsGrid.innerHTML = '';
    if (Array.isArray(posts) && posts.length === 0) {
      showEmpty(true);
    } else {
      posts.forEach(post => {
        postsGrid.insertAdjacentHTML('beforeend', renderPostCard(post));
      });
    }
    renderPagination();
  } catch (e) {
    console.error('Posts load error:', e);
    showError(e && e.data ? (e.data.message || e.message) : (e.message || 'Ma\'lumot olinmadi'));
  } finally {
    hideLoading();
  }
};

$(document).addEventListener('elementoftab_clicked', (e) => {
  // noop placeholder for earlier tab logic reuse if needed
});

prevBtn.addEventListener('click', () => loadPosts(currentPage - 1));
nextBtn.addEventListener('click', () => loadPosts(currentPage + 1));

document.addEventListener('click', (e) => {
  const btn = e.target.closest('.page-btn');
  if (btn) {
    const page = parseInt(btn.dataset.page, 10);
    if (!isNaN(page)) loadPosts(page);
  }
});

searchInput.addEventListener('input', (e) => {
  const val = e.target.value.trim();
  if (val.length > 3) {
    searchInput.classList.add('border-red-400');
  } else {
    searchInput.classList.remove('border-red-400');
  }
});

$('#searchBtn').addEventListener('click', () => {
  const val = searchInput.value.trim();
  if (val.length > 3) {
    showError('Qidiruv so\'zi 3 ta harfdan oshmasligi kerak');
    searchInput.focus();
    return;
  }
  searchTerm = val;
  currentPage = 1;
  loadPosts(1, true);
});

loadingEl.classList.remove('hidden');
loadPosts(1, false);
