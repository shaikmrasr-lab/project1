/**
 * Smart Campus AI - Announcements Controller
 * Categorized campus notices, events, examination schedules, and timetable relocations.
 */

const announcements = {
  currentCategory: 'All',
  announcementsList: [],
  searchQuery: '',

  async init() {
    this.setupListeners();
    await this.loadAnnouncements();
  },

  setupListeners() {
    const postBtn = document.getElementById('postAnnouncementBtn');
    if (postBtn) postBtn.addEventListener('click', () => openModal('addAnnouncementModal'));

    const submitBtn = document.getElementById('submitNewAnnouncementBtn');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => this.handleCreateAnnouncement());
    }

    // Category Tabs
    document.querySelectorAll('.announcement-filter-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        document.querySelectorAll('.announcement-filter-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentCategory = tab.getAttribute('data-cat') || 'All';
        this.loadAnnouncements();
      });
    });

    // Search Input
    const searchInput = document.getElementById('announcementSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase().trim();
        this.renderAnnouncements();
      });
    }
  },

  async loadAnnouncements() {
    try {
      const data = await api.getAnnouncements(this.currentCategory);
      this.announcementsList = data.announcements || [];
      this.renderAnnouncements();
    } catch (err) {
      console.error('Error loading announcements:', err);
    }
  },

  async handleCreateAnnouncement() {
    const title = document.getElementById('announcementTitleInput')?.value.trim();
    const category = document.getElementById('announcementCatSelect')?.value;
    const author = document.getElementById('announcementAuthorInput')?.value.trim() || 'Student Club';
    const content = document.getElementById('announcementContentInput')?.value.trim();
    const isUrgent = document.getElementById('announcementUrgentCheck')?.checked || false;

    if (!title || !content) {
      showToast('Title and content are required', 'danger');
      return;
    }

    try {
      await api.createAnnouncement({
        title,
        category,
        author,
        content,
        is_urgent: isUrgent
      });

      showToast('Announcement posted successfully!', 'success');
      closeModal('addAnnouncementModal');
      await this.loadAnnouncements();
      dashboard.loadDashboardData();
    } catch (e) {
      showToast('Failed to post announcement', 'danger');
    }
  },

  async markAsRead(id) {
    try {
      await api.markAnnouncementRead(id);
      const item = this.announcementsList.find(a => a.id === id);
      if (item) item.is_read = 1;
      this.renderAnnouncements();
      showToast('Marked as read', 'info');
    } catch (e) {
      console.error(e);
    }
  },

  renderAnnouncements() {
    const container = document.getElementById('announcementsFeedArea');
    if (!container) return;

    let filtered = this.announcementsList.filter(a => {
      if (this.searchQuery) {
        return a.title.toLowerCase().includes(this.searchQuery) ||
               a.content.toLowerCase().includes(this.searchQuery) ||
               a.author.toLowerCase().includes(this.searchQuery);
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="padding: 3rem; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📢</div>
          <div style="font-size: 1.1rem; font-weight: 600;">No announcements found in this category.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(a => {
      const isPinned = a.is_pinned === 1;
      const isUrgent = a.is_urgent === 1;
      const isRead = a.is_read === 1;

      return `
        <div class="glass-card announcement-card ${isPinned ? 'pinned' : ''}" style="${isRead ? 'opacity: 0.85;' : ''}">
          <div class="announcement-top-bar">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="deadline-type-tag">${escapeHtml(a.category)}</span>
              ${isPinned ? '<span style="font-size: 0.75rem; color: var(--warning); font-weight: 700;">⭐ Pinned Notice</span>' : ''}
              ${isUrgent ? '<span class="priority-badge urgent">URGENT</span>' : ''}
            </div>
            <div class="announcement-meta">
              <span>👤 ${escapeHtml(a.author)}</span>
              <span>📅 ${escapeHtml(a.date)}</span>
            </div>
          </div>

          <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary);">
            ${escapeHtml(a.title)}
          </div>

          <div class="announcement-content">
            ${renderMarkdown(a.content)}
          </div>

          <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-subtle);">
            ${!isRead ? `
              <button class="btn btn-outline btn-sm" onclick="announcements.markAsRead(${a.id})">
                ✓ Mark as Read
              </button>
            ` : '<span style="font-size: 0.75rem; color: var(--text-muted); align-self: center;">✓ Read</span>'}
          </div>
        </div>
      `;
    }).join('');
  }
};
