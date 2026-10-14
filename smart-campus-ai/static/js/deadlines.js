/**
 * Smart Campus AI - Deadline Reminders Controller
 * Visual countdown timers, examination weightage, and critical alerts.
 */

const deadlines = {
  deadlineList: [],
  timerInterval: null,

  async init() {
    this.setupListeners();
    await this.loadDeadlines();
    this.startLiveCountdown();
  },

  setupListeners() {
    const addBtn = document.getElementById('addNewDeadlineBtn');
    if (addBtn) addBtn.addEventListener('click', () => openModal('addDeadlineModal'));

    const submitBtn = document.getElementById('submitNewDeadlineBtn');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => this.handleCreateDeadline());
    }
  },

  async loadDeadlines() {
    try {
      const data = await api.getDeadlines();
      this.deadlineList = data.deadlines || [];
      this.renderDeadlines();
    } catch (err) {
      console.error('Error loading deadlines:', err);
    }
  },

  async handleCreateDeadline() {
    const title = document.getElementById('deadlineTitleInput')?.value.trim();
    const course = document.getElementById('deadlineCourseInput')?.value.trim();
    const type = document.getElementById('deadlineTypeSelect')?.value;
    const date = document.getElementById('deadlineDateInput')?.value;
    const weight = parseInt(document.getElementById('deadlineWeightInput')?.value || 15);
    const location = document.getElementById('deadlineLocationInput')?.value.trim();
    const desc = document.getElementById('deadlineDescInput')?.value.trim();

    if (!title || !date) {
      showToast('Title and deadline date are required', 'danger');
      return;
    }

    try {
      await api.createDeadline({
        title,
        course_code: course || 'GEN101',
        type: type || 'Assignment',
        deadline_date: date,
        weight_pct: weight,
        location: location || '',
        description: desc || ''
      });

      showToast('Deadline registered successfully', 'success');
      closeModal('addDeadlineModal');
      await this.loadDeadlines();
      dashboard.loadDashboardData();
    } catch (e) {
      showToast('Failed to create deadline', 'danger');
    }
  },

  async deleteDeadline(id) {
    if (!confirm('Remove this examination/assignment deadline?')) return;
    try {
      await api.deleteDeadline(id);
      this.deadlineList = this.deadlineList.filter(d => d.id !== id);
      this.renderDeadlines();
      showToast('Deadline removed', 'info');
      dashboard.loadDashboardData();
    } catch (err) {
      showToast('Failed to delete deadline', 'danger');
    }
  },

  startLiveCountdown() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    this.timerInterval = setInterval(() => {
      this.updateCountdownElements();
    }, 1000);
  },

  computeTimeLeft(isoString) {
    try {
      const target = new Date(isoString).getTime();
      const now = new Date().getTime();
      const diff = target - now;

      if (diff <= 0) return { expired: true, text: 'Due Now / Overdue' };

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const secs = Math.floor((diff % (1000 * 60)) / 1000);

      if (days > 0) {
        return { expired: false, text: `${days}d ${hours}h ${mins}m ${secs}s` };
      }
      return { expired: false, text: `${hours}h ${mins}m ${secs}s` };
    } catch (e) {
      return { expired: false, text: 'Upcoming' };
    }
  },

  updateCountdownElements() {
    document.querySelectorAll('.live-timer-text').forEach(el => {
      const iso = el.getAttribute('data-date');
      if (iso) {
        const res = this.computeTimeLeft(iso);
        el.textContent = res.text;
        if (res.expired) {
          el.style.color = 'var(--danger)';
        }
      }
    });
  },

  renderDeadlines() {
    const container = document.getElementById('deadlinesCardsGrid');
    if (!container) return;

    if (this.deadlineList.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 3rem; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
          <div style="font-size: 1.1rem; font-weight: 600;">No impending exams or deadlines!</div>
          <div style="font-size: 0.85rem; margin-top: 4px;">Enjoy your free academic cycle or add upcoming milestones.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = this.deadlineList.map(d => {
      const urgency = d.urgency_level || 'normal';
      const weight = d.weight_pct || 10;
      const timeLeft = this.computeTimeLeft(d.deadline_date);

      return `
        <div class="glass-card deadline-card ${urgency}">
          <div class="deadline-top-row">
            <span class="deadline-type-tag">${escapeHtml(d.type)} • ${escapeHtml(d.course_code)}</span>
            <div class="deadline-countdown-clock">
              <span>⏳</span>
              <span class="live-timer-text" data-date="${d.deadline_date}">${timeLeft.text}</span>
            </div>
          </div>

          <div>
            <div class="deadline-title">${escapeHtml(d.title)}</div>
            ${d.description ? `<div class="deadline-course-name" style="margin-top: 4px;">${escapeHtml(d.description)}</div>` : ''}
          </div>

          ${d.location ? `
            <div class="deadline-location-info">
              <span>📍 Venue/Portal:</span>
              <strong>${escapeHtml(d.location)}</strong>
            </div>
          ` : ''}

          <div class="weight-progress-wrap">
            <div class="weight-label">
              <span>Grade Weightage</span>
              <span>${weight}% of Semester Grade</span>
            </div>
            <div class="risk-progress-track">
              <div class="risk-progress-fill" style="width: ${Math.min(100, weight * 2.5)}%; background: ${urgency === 'critical' ? 'var(--danger)' : 'var(--primary)'};"></div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
            <button class="btn btn-primary btn-sm" onclick="deadlines.planForDeadline(${d.id})">
              🧠 Plan Study Sprint
            </button>
            <button class="btn-icon" style="width: 32px; height: 32px;" title="Delete" onclick="deadlines.deleteDeadline(${d.id})">
              🗑️
            </button>
          </div>
        </div>
      `;
    }).join('');
  },

  planForDeadline(id) {
    const d = this.deadlineList.find(x => x.id === id);
    if (!d) return;
    showToast(`Setting study planner target for ${d.title}`, 'info');
    app.switchView('planner');

    const subInput = document.getElementById('plannerSubjectsInput');
    const targetDateInput = document.getElementById('plannerTargetDateInput');
    if (subInput) subInput.value = `${d.course_code} (${d.title})`;
    if (targetDateInput) targetDateInput.value = d.deadline_date.slice(0, 10);
  }
};
