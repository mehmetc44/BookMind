/**
 * BookMind — Frontend JavaScript
 * PDF yükleme, kitap listesi, tree view rendering, chat
 */

// ============ State ============
let currentBookId = null;
let books = [];
let isChatLoading = false;

// ============ DOM Elements ============
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const bookList = document.getElementById('bookList');
const bookCount = document.getElementById('bookCount');
const emptyState = document.getElementById('emptyState');
const bookDetail = document.getElementById('bookDetail');
const loadingOverlay = document.getElementById('loadingOverlay');
const toastContainer = document.getElementById('toastContainer');
const uploadBtn = document.getElementById('uploadBtn');
const deleteBookBtn = document.getElementById('deleteBookBtn');
const expandAllBtn = document.getElementById('expandAllBtn');
const collapseAllBtn = document.getElementById('collapseAllBtn');

// Chat DOM
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');
const chatClearBtn = document.getElementById('chatClearBtn');
const chatSubtitle = document.getElementById('chatSubtitle');

// ============ Init ============
document.addEventListener('DOMContentLoaded', () => {
  setupUpload();
  setupActions();
  setupChat();
  loadBooks();
});

// ============ Upload Setup ============
function setupUpload() {
  uploadArea.addEventListener('click', () => fileInput.click());
  uploadBtn.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
      fileInput.value = '';
    }
  });

  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
  });

  uploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
  });

  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      handleUpload(file);
    } else {
      showToast('Sadece PDF dosyaları yüklenebilir.', 'error');
    }
  });

  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => e.preventDefault());
}

// ============ Actions Setup ============
function setupActions() {
  deleteBookBtn.addEventListener('click', () => {
    if (currentBookId) deleteBook(currentBookId);
  });

  expandAllBtn.addEventListener('click', () => toggleAllNodes(true));
  collapseAllBtn.addEventListener('click', () => toggleAllNodes(false));
}

// ============ Chat Setup ============
function setupChat() {
  // Send on button click
  chatSendBtn.addEventListener('click', sendChatMessage);

  // Send on Enter, new line on Shift+Enter
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // Auto-resize textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });

  // Clear chat
  chatClearBtn.addEventListener('click', () => {
    chatHistory = [];
    chatMessages.innerHTML = `
      <div class="chat-welcome">
        <div class="welcome-icon">✦</div>
        <p class="welcome-text">Bir kitap seçin ve kitap hakkında sorular sorun. Bölümler, konular ve içerik hakkında size yardımcı olabilirim.</p>
      </div>`;
  });
}

async function sendChatMessage() {
  const message = chatInput.value.trim();
  if (!message || isChatLoading) return;

  // UI temizle
  chatInput.value = '';
  chatInput.style.height = 'auto';

  // Welcome mesajını kaldır
  const welcome = chatMessages.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  // Kullanıcı mesajını ekle
  appendMessage('user', message);

  // Typing indicator göster
  const typingEl = showTyping();
  isChatLoading = true;
  chatSendBtn.disabled = true;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        book_id: currentBookId || null,
        message,
        history: [], // Hafıza yok — her mesaj bağımsız
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Model yanıt vermedi.');
    }

    typingEl.remove();
    const reply = data.reply;
    appendMessage('assistant', reply);

  } catch (error) {
    typingEl.remove();
    appendMessage('assistant', `⚠️ Hata: ${error.message}`);
  } finally {
    isChatLoading = false;
    chatSendBtn.disabled = false;
    chatInput.focus();
  }
}

function appendMessage(role, content) {
  const now = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });

  const msgEl = document.createElement('div');
  msgEl.className = `chat-msg ${role}`;
  msgEl.innerHTML = `
    <div class="msg-bubble">${formatMessage(content)}</div>
    <span class="msg-time">${now}</span>
  `;

  chatMessages.appendChild(msgEl);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'typing-indicator';
  el.innerHTML = `
    <div class="typing-bubble">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return el;
}

function formatMessage(text) {
  // Basit markdown: **bold**, *italic*, satır sonları
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

// ============ API Calls ============
async function handleUpload(file) {
  showLoading(true);

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Yükleme başarısız.');
    }

    showToast(`"${data.title}" başarıyla haritalandı!`, 'success');
    await loadBooks();
    selectBook(data.book_id);
  } catch (error) {
    showToast(error.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function loadBooks() {
  try {
    const response = await fetch('/api/books');
    books = await response.json();
    renderBookList();
  } catch (error) {
    console.error('Kitap listesi yüklenemedi:', error);
  }
}

async function selectBook(bookId) {
  currentBookId = bookId;

  document.querySelectorAll('.book-item').forEach((el) => {
    el.classList.toggle('active', el.dataset.bookId === bookId);
  });

  // Chat subtitle güncelle
  const book = books.find((b) => b.id === bookId);
  if (book && chatSubtitle) {
    chatSubtitle.textContent = book.title;
  }

  try {
    const response = await fetch(`/api/books/${bookId}/map`);
    if (!response.ok) throw new Error('Harita yüklenemedi.');

    const data = await response.json();
    renderBookDetail(data);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deleteBook(bookId) {
  try {
    const response = await fetch(`/api/books/${bookId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Silme başarısız.');

    showToast('Kitap silindi.', 'success');
    currentBookId = null;
    if (chatSubtitle) chatSubtitle.textContent = 'Bir kitap seçin';
    await loadBooks();
    showEmptyState();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// ============ Renderers ============
function renderBookList() {
  bookCount.textContent = books.length;

  if (books.length === 0) {
    bookList.innerHTML = '';
    showEmptyState();
    return;
  }

  bookList.innerHTML = books
    .map(
      (book) => `
    <div class="book-item ${book.id === currentBookId ? 'active' : ''}"
         data-book-id="${book.id}"
         onclick="selectBook('${book.id}')">
      <div class="book-item-icon">${getBookInitials(book.title)}</div>
      <div class="book-item-info">
        <div class="book-item-title" title="${escapeHtml(book.title)}">${escapeHtml(book.title)}</div>
        <div class="book-item-meta">${book.chapter_count} bölüm · ${book.total_pages} sayfa</div>
      </div>
    </div>
  `
    )
    .join('');
}

function renderBookDetail(data) {
  const bookMap = data.book_map;

  document.getElementById('detailTitle').textContent = bookMap.book_title;
  document.getElementById('detailAuthor').querySelector('span').textContent = bookMap.author;
  document.getElementById('detailPages').querySelector('span').textContent = `${bookMap.total_pages} sayfa`;

  const treeContainer = document.getElementById('chapterTree');
  treeContainer.innerHTML = renderTree(bookMap.chapters);

  emptyState.style.display = 'none';
  bookDetail.style.display = 'block';
  bookDetail.style.animation = 'none';
  bookDetail.offsetHeight;
  bookDetail.style.animation = 'slideIn 0.4s ease-out';
}

function renderTree(chapters, depth = 0) {
  if (!chapters || chapters.length === 0) return '';

  return chapters
    .map((chapter) => {
      const hasChildren = chapter.children && chapter.children.length > 0;
      const nodeId = `node-${chapter.id}`;

      return `
      <div class="tree-node" id="${nodeId}">
        <div class="tree-node-header" onclick="toggleNode('${nodeId}')">
          <div class="tree-toggle ${hasChildren ? '' : 'no-children'}" id="toggle-${nodeId}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="tree-node-content">
            <div style="display:flex;align-items:baseline;flex-wrap:wrap;">
              <span class="tree-node-title">${escapeHtml(chapter.title)}</span>
              <span class="tree-node-pages">s. ${chapter.page_start}–${chapter.page_end}</span>
            </div>
            ${chapter.summary ? `<div class="tree-node-summary">${escapeHtml(chapter.summary)}</div>` : ''}
            <div class="tree-node-tags">
              ${(chapter.topics || []).map((t) => `<span class="tag tag-topic">${escapeHtml(t)}</span>`).join('')}
              ${(chapter.keywords || []).map((k) => `<span class="tag tag-keyword">${escapeHtml(k)}</span>`).join('')}
            </div>
          </div>
        </div>
        ${
          hasChildren
            ? `<div class="tree-node-children expanded" id="children-${nodeId}">
              ${renderTree(chapter.children, depth + 1)}
            </div>`
            : ''
        }
      </div>
    `;
    })
    .join('');
}

// ============ Tree Controls ============
function toggleNode(nodeId) {
  const toggle = document.getElementById(`toggle-${nodeId}`);
  const children = document.getElementById(`children-${nodeId}`);

  if (!children || toggle.classList.contains('no-children')) return;

  const isExpanded = children.classList.contains('expanded');

  if (isExpanded) {
    children.classList.remove('expanded');
    children.classList.add('collapsed');
    toggle.classList.remove('expanded');
  } else {
    children.classList.remove('collapsed');
    children.classList.add('expanded');
    toggle.classList.add('expanded');
  }
}

function toggleAllNodes(expand) {
  document.querySelectorAll('.tree-node-children').forEach((el) => {
    el.classList.toggle('collapsed', !expand);
    el.classList.toggle('expanded', expand);
  });
  document.querySelectorAll('.tree-toggle:not(.no-children)').forEach((el) => {
    el.classList.toggle('expanded', expand);
  });
}

// ============ UI Helpers ============
function showEmptyState() {
  emptyState.style.display = 'flex';
  bookDetail.style.display = 'none';
}

function showLoading(show) {
  loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = 'toast';
  const icon = type === 'success' ? '✓' : '✕';
  toast.innerHTML = `
    <div class="toast-icon ${type}">${icon}</div>
    <div class="toast-message">${escapeHtml(message)}</div>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function getBookInitials(title) {
  if (!title) return '?';
  const words = title.split(/\s+/).filter(Boolean);
  if (words.length === 0) return '?';
  if (words.length === 1) return words[0].charAt(0).toUpperCase();
  return (words[0].charAt(0) + words[1].charAt(0)).toUpperCase();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
