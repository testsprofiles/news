const params = new URLSearchParams(window.location.search);
const postId = params.get('id');
if (!postId) window.location.href = 'index.html';

const $ = (s) => document.querySelector(s);
const loadingEl = $('#loadingPost');
const errorEl = $('#errorState');
const errorText = $('#errorText');
const postDetail = $('#postDetail');
const postImage = $('#postImage');
const postCategory = $('#postCategory');
const postDate = $('#postDate span');
const postReadTime = $('#postReadTime span');
const postTitle = $('#postTitle');
const postContent = $('#postContent');
const postAuthorInitial = $('#postAuthorInitial');
const postAuthorName = $('#postAuthorName');
const shareBtn = $('#sharePostBtn');
const backBtn = $('#backToListBtn');
const loginPrompt = $('#loginPrompt');
const commentForm = $('#commentForm');
const commentText = $('#commentText');
const commentCharCount = $('#commentCharCount');
const commentSubmitBtn = $('#commentSubmitBtn');
const commentFormError = $('#commentFormError');
const commentsList = $('#commentsList');
const commentCount = $('#commentCount');
const emptyComments = $('#emptyComments');
const toast = $('#toast');
const toastMsg = $('#toastMessage');

let currentToken = null;
let currentComments = [];

const showToast = (m, type = 'success') => {
  toastMsg.textContent = m;
  toast.className = `fixed bottom-6 right-6 px-4 py-3 rounded-lg shadow-lg ${type === 'success' ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'} hidden flex items-center gap-3 text-sm max-w-xs w-full sm:w-auto`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 4000);
};

const formatDate = (d) => {
  if (!d) return '—';
  try {
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return d;
    return dt.toLocaleDateString('uz', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch (e) { return d; }
};

const estimateReadTime = (text) => {
  if (!text) return '1 daqiqa';
  const w = (text || '').split(/\s+/).length;
  const min = Math.max(1, Math.round(w / 200));
  return min + (min === 1 ? ' daqiqa' : ' daqiqa');
};

const escapeHtml = (s) => {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
};

const renderComment = (c) => `
  <div class="px-6 py-4 fade-in">
    <div class="flex items-start gap-3">
      <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-medium text-gray-600 flex-shrink-0">
        ${escapeHtml((c.username || 'V').charAt(0).toUpperCase())}
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-medium text-gray-900">${escapeHtml(c.username || 'Anonim')}</span>
          <span class="text-xs text-gray-400">${formatDate(c.created_at)}</span>
        </div>
        <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">${escapeHtml(c.text)}</p>
      </div>
    </div>
  </div>
`;

const loadPost = async () => {
  loadingEl.classList.remove('hidden');
  errorEl.classList.add('hidden');
  postDetail.classList.add('hidden');
  loginPrompt.classList.add('hidden');
  commentForm.classList.add('hidden');
  commentsList.innerHTML = '';
  emptyComments.classList.add('hidden');
  commentCount.textContent = '0 ta';
  commentCharCount.textContent = '0 / 1000';

  try {
    const data = await api.get(`/api/posts/${postId}`);
    const d = data || {};

    postImage.src = d.image_url || '';
    postImage.alt = d.title || 'Yangilik';
    postCategory.textContent = d.category_name || (d.category && d.category.name) || '—';

    postDate.textContent = formatDate(d.created_at);
    postTitle.textContent = d.title || '—';
    postContent.textContent = d.content || '—';
    postReadTime.textContent = estimateReadTime(d.content);
    postAuthorName.textContent = d.author || 'Portal';
    postAuthorInitial.textContent = (d.author || 'P').charAt(0).toUpperCase();

    postDetail.classList.remove('hidden');
    postDetail.classList.add('fade-in');

    if (!api.checkAuth()) {
      loginPrompt.classList.remove('hidden');
    } else {
      commentForm.classList.remove('hidden');
    }

    const comments = await api.get('/api/comments');
    currentComments = Array.isArray(comments) ? comments : [];
    renderComments();
  } catch (e) {
    console.error('Load post error:', e);
    errorText.textContent = (e && e.data && e.data.message) ? e.data.message : (e && e.message ? e.message : 'Ma\'lumot olinmadi');
    errorEl.classList.remove('hidden');
  } finally {
    loadingEl.classList.add('hidden');
  }
};

const renderComments = () => {
  commentsList.innerHTML = '';
  if (currentComments.length === 0) {
    emptyComments.classList.remove('hidden');
    commentCount.textContent = '0 ta';
    return;
  }
  emptyComments.classList.add('hidden');
  commentCount.textContent = currentComments.length + ' ta';
  currentComments.forEach(c => {
    commentsList.insertAdjacentHTML('beforeend', renderComment(c));
  });
};

commentText.addEventListener('input', () => {
  const len = commentText.value.length;
  commentCharCount.textContent = len + ' / 1000';
  if (len > 1000) commentText.value = commentText.value.slice(0, 1000);
  commentCharCount.textContent = commentText.value.length + ' / 1000';
  commentFormError.classList.add('hidden');
});

commentForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = commentText.value.trim();
  if (!text || text.length < 5) {
    commentFormError.textContent = 'Kamida 5 ta belgi kiriting';
    commentFormError.classList.remove('hidden');
    return;
  }
  if (text.length > 1000) {
    commentFormError.textContent = 'Maksimal 1000 belgi';
    commentFormError.classList.remove('hidden');
    return;
  }
  if (!api.checkAuth()) {
    commentFormError.textContent = 'Avtorizatsiya kerak';
    commentFormError.classList.remove('hidden');
    return;
  }
  commentSubmitBtn.disabled = true;
  commentFormError.classList.add('hidden');

  try {
    const res = await api.post('/api/comments', { post_id: Number(postId), text });
    if (res && res.id) {
      showToast('Izoh qo\'shildi');
      commentText.value = '';
      commentCharCount.textContent = '0 / 1000';
      currentComments = Array.isArray(res.comments) ? res.comments : currentComments;
      // refetch to be safe
      const fresh = await api.get('/api/comments');
      currentComments = Array.isArray(fresh) ? fresh : currentComments;
      renderComments();
    } else {
      commentFormError.textContent = 'Izoh saqlanmadi';
      commentFormError.classList.remove('hidden');
    }
  } catch (e) {
    console.error('Add comment error:', e);
    commentFormError.textContent = (e && e.data && e.data.message) ? e.data.message : (e && e.message ? e.message : 'Xatolik yuz berdi');
    commentFormError.classList.remove('hidden');
  } finally {
    commentSubmitBtn.disabled = false;
  }
});

shareBtn.addEventListener('click', () => {
  const url = window.location.href;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => showToast('Ko\'pchiya asarisozlandi')).catch(() => {});
  } else {
    prompt('Manzilni nusxalang:', url);
  }
});

backBtn.addEventListener('click', () => window.location.href = 'index.html');

loadingEl.classList.remove('hidden');
loadPost();
