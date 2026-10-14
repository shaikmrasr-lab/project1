/**
 * Smart Campus AI - Central Store & Utility Functions
 */

const store = {
  activeView: 'dashboard',
  user: null,
  activeDoc: null,
  unreadCount: 2,
  theme: 'dark',
  settings: {}
};

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'danger' ? '✕' : 'ℹ';
  toast.innerHTML = `
    <span style="font-weight: 700; font-size: 1.1rem;">${icon}</span>
    <span style="flex: 1;">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal open/close helpers
function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Escape HTML utility
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Safe lightweight Markdown renderer for AI responses
function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 5px; border-radius: 4px; font-family: monospace;">$1</code>');

  // Blockquotes
  html = html.replace(/^&gt;\s?(.*)$/gm, '<blockquote style="border-left: 3px solid var(--primary); padding-left: 0.75rem; margin: 0.5rem 0; color: var(--text-secondary);">$1</blockquote>');

  // Bullet items
  html = html.replace(/^•\s?(.*)$/gm, '<li style="margin-left: 1.25rem; list-style-type: disc;">$1</li>');
  html = html.replace(/^-\s?(.*)$/gm, '<li style="margin-left: 1.25rem; list-style-type: disc;">$1</li>');

  // Convert line breaks
  html = html.replace(/\n\n/g, '<p style="margin: 0.5rem 0;"></p>');
  html = html.replace(/\n/g, '<br>');

  return html;
}

// Human relative date/time formatter
function formatDueDateTime(isoString) {
  if (!isoString) return '';
  try {
    const dt = new Date(isoString);
    const now = new Date();
    const diffHours = (dt - now) / (1000 * 60 * 60);

    const timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = dt.toLocaleDateString([], { month: 'short', day: 'numeric' });

    if (diffHours < 0) return `Overdue (${dateStr} ${timeStr})`;
    if (diffHours <= 24) return `Today at ${timeStr}`;
    if (diffHours <= 48) return `Tomorrow at ${timeStr}`;
    return `${dateStr} at ${timeStr}`;
  } catch (e) {
    return isoString.replace('T', ' ');
  }
}
