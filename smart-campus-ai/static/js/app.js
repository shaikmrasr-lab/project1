/**
 * Smart Campus AI - Main SPA Controller & View Router
 * Handles navigation, theme toggling, settings modal, and lifecycle bootstrap.
 */

const app = {
  views: ['dashboard', 'chat', 'tasks', 'deadlines', 'planner', 'notes', 'announcements', 'tracker'],

  async init() {
    this.setupNavigation();
    this.setupTheme();
    this.setupSettingsModal();
    this.setupGlobalSearch();

    // Initialize individual modules
    await dashboard.init();
    await chat.init();
    await tasks.init();
    await deadlines.init();
    await planner.init();
    await notes.init();
    await announcements.init();
    await tracker.init();

    // Check for hash route in URL
    const hash = window.location.hash.replace('#', '');
    if (this.views.includes(hash)) {
      this.switchView(hash);
    } else {
      this.switchView('dashboard');
    }

    console.log('Smart Campus AI initialized successfully.');
  },

  setupNavigation() {
    // Sidebar nav links
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetView = link.getAttribute('data-view');
        if (targetView && this.views.includes(targetView)) {
          this.switchView(targetView);
          this.closeMobileSidebar();
        }
      });
    });

    // Mobile sidebar toggle
    const toggleBtn = document.getElementById('menuToggleBtn');
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        backdrop?.classList.toggle('active');
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', () => {
        this.closeMobileSidebar();
      });
    }

    // Modal background clicks & Escape key
    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('active');
        }
      });
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
      }
    });

    // Hash change event
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '');
      if (this.views.includes(hash)) {
        this.switchView(hash);
      }
    });
  },

  closeMobileSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    sidebar?.classList.remove('open');
    backdrop?.classList.remove('active');
  },

  switchView(viewName) {
    if (!this.views.includes(viewName)) return;
    store.activeView = viewName;
    window.location.hash = viewName;

    // Update nav links
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
      if (link.getAttribute('data-view') === viewName) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Update panels
    document.querySelectorAll('.view-panel').forEach(panel => {
      if (panel.id === `view_${viewName}`) {
        panel.classList.add('active');
      } else {
        panel.classList.remove('active');
      }
    });

    // Update page header title
    const headerTitle = document.getElementById('headerPageTitle');
    if (headerTitle) {
      const titles = {
        dashboard: 'Student Dashboard',
        chat: 'CampusBot AI Assistant',
        tasks: 'Smart Task Manager',
        deadlines: 'Deadline & Exam Reminders',
        planner: 'AI Study Planner',
        notes: 'Notes Summarizer & Practice Quizzes',
        announcements: 'Campus Notice Board',
        tracker: 'Progress & Analytics Tracker'
      };
      headerTitle.textContent = titles[viewName] || 'Smart Campus AI';
    }

    // Refresh active view data if needed
    if (viewName === 'dashboard') dashboard.loadDashboardData();
    if (viewName === 'tasks') tasks.loadTasks();
    if (viewName === 'deadlines') deadlines.loadDeadlines();
    if (viewName === 'tracker') tracker.loadAnalytics();
  },

  setupTheme() {
    const themeBtn = document.getElementById('themeToggleBtn');
    const currentTheme = localStorage.getItem('smart_campus_theme') || 'dark';

    document.documentElement.setAttribute('data-theme', currentTheme);
    this.updateThemeIcon(currentTheme);

    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const active = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = active === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('smart_campus_theme', next);
        this.updateThemeIcon(next);
        api.updateSettings({ theme: next });
        showToast(`Theme changed to ${next} mode`, 'info');
      });
    }
  },

  updateThemeIcon(theme) {
    const icon = document.getElementById('themeToggleIcon');
    if (icon) {
      icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
  },

  setupSettingsModal() {
    const openSettingsBtn = document.getElementById('openSettingsBtn');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const aiPill = document.getElementById('aiEngineHeaderPill');

    const openHandler = async () => {
      try {
        const settings = await api.getSettings();
        const keyInput = document.getElementById('geminiApiKeyInput');
        const modelSelect = document.getElementById('geminiModelSelect');
        const statusText = document.getElementById('activeEngineStatusText');

        if (keyInput) keyInput.value = settings.has_gemini_key ? settings.masked_key : '';
        if (modelSelect && settings.gemini_model) modelSelect.value = settings.gemini_model;
        if (statusText) statusText.textContent = `Current Engine: ${settings.engine_label}`;

        openModal('settingsModal');
      } catch (e) {
        openModal('settingsModal');
      }
    };

    if (openSettingsBtn) openSettingsBtn.addEventListener('click', openHandler);
    if (aiPill) aiPill.addEventListener('click', openHandler);

    if (saveSettingsBtn) {
      saveSettingsBtn.addEventListener('click', async () => {
        const keyInput = document.getElementById('geminiApiKeyInput')?.value.trim();
        const modelSelect = document.getElementById('geminiModelSelect')?.value;

        const payload = {};
        if (keyInput && !keyInput.includes('...')) {
          payload.gemini_api_key = keyInput;
        } else if (keyInput === '') {
          payload.gemini_api_key = ''; // Cleared
        }
        if (modelSelect) payload.gemini_model = modelSelect;

        try {
          await api.updateSettings(payload);
          showToast('Settings saved successfully', 'success');
          closeModal('settingsModal');
          dashboard.loadDashboardData();
        } catch (e) {
          showToast('Failed to save settings', 'danger');
        }
      });
    }
  },

  setupGlobalSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const val = searchInput.value.trim().toLowerCase();
          if (!val) return;

          // Route to tasks and search
          this.switchView('tasks');
          const taskSearch = document.getElementById('taskSearchInput');
          if (taskSearch) {
            taskSearch.value = val;
            tasks.searchQuery = val;
            tasks.renderTasks();
          }
          showToast(`Searching tasks for "${val}"`, 'info');
        }
      });
    }
  }
};

// Bootstrap when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
