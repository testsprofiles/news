const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const adminBody = $('#adminBody');
const authGuard = $('#authGuard');
const loadingEl = $('#loadingAdmin');
const tabCategories = $('#tabCategories');
const tabPosts = $('#tabPosts');
const categoriesPanel = $('#categoriesPanel');
const postsPanel = $('#postsPanel');
const categoriesTableBody = $('#categoriesTableBody');
const emptyCategories = $('#emptyCategories');
const postsTableBody = $('#postsTableBody');
const emptyPosts = $('#emptyPosts');
const openCategoryForm = $('#openCategoryForm');
const closeCategoryForm = $('#closeCategoryForm');
const cancelCategoryBtn = $('#cancelCategoryBtn');
const categoryForm = $('#categoryForm');
const editCategoryId = $('#editCategoryId');
const categoryName = $('#categoryName');
const categoryFormTitle = $('#categoryFormTitle');
const categoryFormError = $('#categoryFormError');
const saveCategoryBtn = $('#saveCategoryBtn');
const categoryFormModal = $('#categoryFormModal');

const openPostForm = $('#openPostForm');
const closePostForm = $('#closePostForm');
const cancelPostBtn = $('#cancelPostBtn');
const postForm = $('#postForm');
const editPostId = $('#editPostId');
const postTitle = $('#postTitle');
const postCategorySelect = $('#postCategorySelect');
const postImageInput = $('#postImageInput');
const selectedImageName = $('#selectedImageName');
const postContent = $('#postContent');
const postFormTitle = $('#postFormTitle');
const postFormError = $('#postFormError');
const savePostBtn = $('#savePostBtn');
const postFormModal = $('#postFormModal');
const postImagePreview = $('#postImagePreview');

const toast = $('#toast');
const toastMsg = $('#toastMessage');

const showToast = (m, type = 'success') => {
  toastMsg.textContent = m;
  toast.className = `fixed bottom-6 right-6 px-4 py-3 rounded-lg shadow-lg ${type === 'success' ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'} hidden flex items-center gap-3 text-sm max-w-xs w-full sm:w-auto z-50`;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 4000);
};

const escapeHtml = (s) => {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
};

const formatDate = (d) => {
  if (!d) return '—';
  try {
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return d;
    return dt.toLocaleDateString('uz', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch (e) { return d; }
};

const checkAdmin = async () => {
  if (!api.checkAuth()) {
    authGuard.classList.remove('hidden');
    adminBody.classList.add('hidden');
    loadingEl.classList.add('hidden');
    return false;
  }
  // Fetch users/me to see role?
  // This backend has no /auth/me — we rely on token presence + admin test later
  return true;
};

const setupTabs = () => {
  const makeActive = (btn, panel) => {
    tabCategories.classList.remove('tab-active');
    tabPosts.classList.remove('tab-active');
    tabCategories.classList.add('text-gray-500');
    tabPosts.classList.add('text-gray-500');
    btn.classList.add('tab-active');
    btn.classList.remove('text-gray-500');
    categoriesPanel.classList.add('hidden');
    postsPanel.classList.add('hidden');
    panel.classList.remove('hidden');
  };
  tabCategories.addEventListener('click', () => makeActive(tabCategories, categoriesPanel));
  tabPosts.addEventListener('click', () => makeActive(tabPosts, postsPanel));
};

const renderCategories = (cats) => {
  categoriesTableBody.innerHTML = '';
  if (!cats || cats.length === 0) {
    emptyCategories.classList.remove('hidden');
    return;
  }
  emptyCategories.classList.add('hidden');
  cats.forEach(c => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-50 transition';
    tr.innerHTML = `
      <td class="px-4 py-3 whitespace-nowrap">
        <span class="text-sm font-medium text-gray-900">${escapeHtml(c.name || '')}</span>
      </td>
      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">Aktiy</td>
      <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
        <button data-id="${c.id}" data-name="${escapeHtml(c.name)}" class="edit-category-btn text-blue-600 hover:text-blue-800 transition mr-2">
          <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l7.586-7.586a2 2 0 012.828 2.828z"/></svg>
          Tahrirlash
        </button>
        <button data-id="${c.id}" class="delete-category-btn text-red-600 hover:text-red-800 transition">
          <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          O'chirish
        </button>
      </td>
    `;
    categoriesTableBody.appendChild(tr);
  });
};

const renderPosts = (posts) => {
  postsTableBody.innerHTML = '';
  if (!posts || posts.length === 0) {
    emptyPosts.classList.remove('hidden');
    postsTableBody.innerHTML = '';
    return;
  }
  emptyPosts.classList.add('hidden');
  posts.forEach(p => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-50 transition';
    const state = p.state || 'Yaratildi';
    const stateCls = p.state === 'Yaratildi' ? 'text-green-600 bg-green-50 px-2 py-0.5 rounded' : 'text-amber-600 bg-amber-50 px-2 py-0.5 rounded';
    tr.innerHTML = `
      <td class="px-4 py-3 whitespace-nowrap">
        <div class="flex items-center gap-3">
          <div class="w-2 h-2 rounded-full ${p.image_url ? 'bg-blue-500' : 'bg-gray-300'}"></div>
          <span class="text-sm font-medium text-gray-900 max-w-[200px] truncate block">${escapeHtml(p.title || '')}</span>
        </div>
      </td>
      <td class="px-4 py-3 whitespace-nowrap hidden sm:table-cell text-sm text-gray-500">${formatDate(p.created_at)}</td>
      <td class="px-4 py-3 whitespace-nowrap hidden md:table-cell">
        <span class="${stateCls}">${escapeHtml(state)}</span>
      </td>
      <td class="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
        <button data-id="${p.id}" data-title="${escapeHtml(p.title)}" data-content="${escapeHtml(p.content || '')}" data-catid="${p.category_id ?? ''}" class="edit-post-btn text-blue-600 hover:text-blue-800 transition mr-2">
          <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l7.586-7.586a2 2 0 012.828 2.828z"/></svg>
          Tahrirlash
        </button>
        <button data-id="${p.id}" class="delete-post-btn text-red-600 hover:text-red-800 transition">
          <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          O'chirish
        </button>
      </td>
    `;
    postsTableBody.appendChild(tr);
  });
};

const loadCats = async () => {
  try {
    const cats = await api.get('/api/categories');
    renderCategories(Array.isArray(cats) ? cats : []);
  } catch (e) {
    console.error('Load categories error:', e);
    showToast('Kategoriyalar yuklanmadi', 'error');
  }
};

const loadPostsList = async () => {
  try {
    const posts = await api.get('/api/posts');
    renderPosts(Array.isArray(posts) ? posts : []);
  } catch (e) {
    console.error('Load posts error:', e);
    showToast('Yangiliklar yuklanmadi', 'error');
  }
};

const openCategoryModal = (cat = null) => {
  categoryForm.reset();
  categoryFormError.classList.add('hidden');
  saveCategoryBtn.disabled = false;
  if (cat) {
    editCategoryId.value = cat.id;
    categoryName.value = cat.name || '';
    categoryFormTitle.textContent = 'Kategoriya tahrirlash';
  } else {
    editCategoryId.value = '';
    categoryName.value = '';
    categoryFormTitle.textContent = 'Yangi kategoriya';
  }
  categoryFormModal.classList.remove('hidden');
  categoryName.focus();
};

openCategoryForm.addEventListener('click', () => openCategoryModal());
closeCategoryForm.addEventListener('click', () => categoryFormModal.classList.add('hidden'));
cancelCategoryBtn.addEventListener('click', () => categoryFormModal.classList.add('hidden'));
categoryForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = categoryName.value.trim();
  if (!name) {
    categoryFormError.textContent = 'Nomi kiriting';
    categoryFormError.classList.remove('hidden');
    return;
  }
  if (name.length < 2) {
    categoryFormError.textContent = 'Nomi 2 harfdan ko\'p bo\'lishi kerak';
    categoryFormError.classList.remove('hidden');
    return;
  }
  categoryFormError.classList.add('hidden');
  saveCategoryBtn.disabled = true;
  try {
    const payload = { name };
    if (editCategoryId.value) payload.id = Number(editCategoryId.value);
    if (editCategoryId.value) {
      const res = await api.put('/api/categories/' + editCategoryId.value, { name });
      if (res && (res.category || res.message)) {
        showToast('Kategoriya yangilandi');
        categoryFormModal.classList.add('hidden');
        loadCats();
      } else {
        throw new Error(res.message || 'Yangilmadi');
      }
    } else {
      const res = await api.post('/api/categories', payload);
      if (res && (res.category || res.message)) {
        showToast('Kategoriya yaratildi');
        categoryFormModal.classList.add('hidden');
        loadCats();
      } else {
        throw new Error(res.message || 'Yaratilmadi');
      }
    }
  } catch (e) {
    console.error('Category save error:', e);
    categoryFormError.textContent = (e && e.data && e.data.message) ? e.data.message : (e && e.message ? e.message : 'Xatolik yuz berdi');
    categoryFormError.classList.remove('hidden');
  } finally {
    saveCategoryBtn.disabled = false;
  }
});

categoriesTableBody.addEventListener('click', async (e) => {
  const editBtn = e.target.closest('.edit-category-btn');
  if (editBtn) {
    const id = editBtn.dataset.id;
    if (!id) return;
    // The API has no GET /api/categories/<id>; the row already carries the data.
    openCategoryModal({ id, name: editBtn.dataset.name || '' });
  }
  const delBtn = e.target.closest('.delete-category-btn');
  if (delBtn) {
    const id = delBtn.dataset.id;
    if (!id) return;
    if (!confirm('Bu kategoriyani o\'chirishni xohlaysizmi?')) return;
    try {
      const res = await api.delete('/api/categories/' + id);
      if (res && (res.message || true)) {
        showToast('Kategoriya o\'chirildi');
        loadCats();
      }
    } catch (e) {
      console.error('Delete category error:', e);
      showToast('O\'chira olmadı', 'error');
    }
  }
});

const populateCategoriesSelect = async () => {
  try {
    const cats = await api.get('/api/categories');
    const list = Array.isArray(cats) ? cats : [];
    postCategorySelect.innerHTML = '<option value="">Kategoriya tanlang</option>';
    list.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name || '';
      postCategorySelect.appendChild(opt);
    });
  } catch (e) {
    console.error('Populate categories error:', e);
  }
};

const openPostModal = (post = null) => {
  postForm.reset();
  postFormError.classList.add('hidden');
  savePostBtn.disabled = false;
  selectedImageName.textContent = '';
  postImageInput.value = '';
  if (post) {
    editPostId.value = post.id;
    postTitle.value = post.title || '';
    postContent.value = post.content || '';
    // Keep image input cleared for edit unless we track previous
    postFormTitle.textContent = 'Yangilik tahrirlash';
  } else {
    editPostId.value = '';
    postTitle.value = '';
    postContent.value = '';
    postFormTitle.textContent = 'Yangilik yaratish';
  }
  postFormModal.classList.remove('hidden');
  postTitle.focus();
};

openPostForm.addEventListener('click', () => openPostModal());
closePostForm.addEventListener('click', () => postFormModal.classList.add('hidden'));
cancelPostBtn.addEventListener('click', () => postFormModal.classList.add('hidden'));

postImageInput.addEventListener('change', () => {
  const file = postImageInput.files[0];
  if (file) {
    selectedImageName.textContent = file.name.length > 20 ? file.name.slice(0, 20) + '…' : file.name;
  } else {
    selectedImageName.textContent = '';
  }
});

postForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = postTitle.value.trim();
  const content = postContent.value.trim();
  const catId = postCategorySelect.value ? Number(postCategorySelect.value) : null;
  if (!title) {
    postFormError.textContent = 'Sarlavha kiritilishi shart';
    postFormError.classList.remove('hidden');
    return;
  }
  if (!content) {
    postFormError.textContent = 'Matn kiritilishi shart';
    postFormError.classList.remove('hidden');
    return;
  }
  if (!catId) {
    postFormError.textContent = 'Kategoriya tanlang';
    postFormError.classList.remove('hidden');
    return;
  }
  postFormError.classList.add('hidden');
  savePostBtn.disabled = true;
  const isEdit = !!editPostId.value;
  try {
    let newId = null;
    let imageUrl = null;
    if (isEdit) {
      const payload = { title, content, category_id: catId };
      const res = await api.put('/api/posts/' + editPostId.value, payload);
      if (res && res.message) {
        newId = editPostId.value;
        showToast('Yangilik yangilandi');
      } else {
        throw new Error(res.message || 'Yangilmadi');
      }
    } else {
      const payload = { title, content, category_id: catId };
      const res = await api.post('/api/posts', payload);
      if (res && (res.post || res.id || res.message)) {
        newId = res.post ? res.post.id : (res.id || null);
        // If res has full post use that
        const pid = res.post ? res.post.id : (res.id ?? null);
        if (pid) newId = pid;
        showToast('Yangilik qo\'shildi');
      } else {
        throw new Error(res.message || 'Qo\'shilmadi');
      }
    }
    // If image attached and we got id, upload image to the new/existing post
    const file = postImageInput.files[0];
    if (file && newId) {
      const formData = new FormData();
      formData.append('image', file);
      savePostBtn.disabled = true;
      try {
        const uploadRes = await fetch('/api/posts/' + newId + '/image', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + api.getToken() },
          body: formData
        });
        const uploadData = await uploadRes.json().catch(() => ({}));
        if (!uploadRes.ok) {
          console.error('Upload error:', uploadData);
          showToast('Rasm yuklanmadi, lekin yangilik saqlandi', 'error');
        } else {
          console.log('Uploaded:', uploadData);
        }
      } catch (ue) {
        console.error('Upload fetch error:', ue);
      } finally {
        savePostBtn.disabled = false;
      }
    }
    postFormModal.classList.add('hidden');
    loadPostsList();
    populateCategoriesSelect();
  } catch (e) {
    console.error('Post save error:', e);
    postFormError.textContent = (e && e.data && e.data.message) ? e.data.message : (e && e.message ? e.message : 'Xatolik yuz berdi');
    postFormError.classList.remove('hidden');
  } finally {
    savePostBtn.disabled = false;
  }
});

postsTableBody.addEventListener('click', async (e) => {
  const editBtn = e.target.closest('.edit-post-btn');
  if (editBtn) {
    const id = editBtn.dataset.id;
    if (!id) return;
    try {
      const res = await api.get('/api/posts/' + id);
      if (res && (res.id || res.title)) {
        const catId = res.category_id ?? (res.category && res.category.id) ?? '';
        openPostModal({
          id: res.id,
          title: res.title || '',
          content: res.content || '',
          category_id: catId
        });
      }
    } catch (e) {
      showToast('Ma\'lumot olinmadi', 'error');
    }
  }
  const delBtn = e.target.closest('.delete-post-btn');
  if (delBtn) {
    const id = delBtn.dataset.id;
    if (!id) return;
    if (!confirm('Bu yangilikni o\'chirishni xohlaysizmi?')) return;
    try {
      const res = await api.delete('/api/posts/' + id);
      if (res && (res.message || true)) {
        showToast('Yangilik o\'chirildi');
        loadPostsList();
      }
    } catch (e) {
      console.error('Delete post error:', e);
      showToast('O\'chira olmadı', 'error');
    }
  }
});

const init = async () => {
  loadingEl.classList.remove('hidden');
  adminBody.classList.add('hidden');
  authGuard.classList.add('hidden');
  try {
    const ok = await checkAdmin();
    if (!ok) throw new Error('not admin');
    setupTabs();
    await populateCategoriesSelect();
    await loadCats();
    await loadPostsList();
    adminBody.classList.remove('hidden');
  } catch (e) {
    console.error('Admin init error:', e);
    authGuard.classList.remove('hidden');
  } finally {
    loadingEl.classList.add('hidden');
  }
};

document.addEventListener('DOMContentLoaded', init);
