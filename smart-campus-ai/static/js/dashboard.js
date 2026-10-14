/**
 * Smart Campus AI - Dashboard Controller
 * Populates student overview, live class timeline, urgent deadlines, and AI Co-pilot.
 */

const dashboard = {
  async init() {
    await this.loadDashboardData();
  },

  async loadDashboardData() {
    try {
      const data = await api.getDashboard();
      store.user = data.user;
      store.stats = data.stats;

      this.renderWelcome(data.user, data.stats, data.urgent_deadlines);
      this.renderStats(data.stats, data.user);
      this.renderCopilot(data.copilot);
      this.renderTodayClasses(data.today_classes, data.today_day);
      this.renderUrgentDeadlines(data.urgent_deadlines);
      this.renderNoticesTicker(data.notices);
      this.renderSidebarUser(data.user);

      // Update AI Engine Status Pill in Header
      const pill = document.getElementById('aiEngineHeaderPill');
      if (pill) {
        pill.innerHTML = `
          <span class="ai-status-dot"></span>
          <span>${escapeHtml(data.stats.ai_engine_active)}</span>
        `;
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  },

  renderWelcome(user, stats, deadlines) {
    const welcomeTitle = document.getElementById('welcomeUserTitle');
    const welcomeDesc = document.getElementById('welcomeUserDesc');

    if (welcomeTitle && user) {
      welcomeTitle.textContent = `Welcome back, ${user.name}! 👋`;
    }

    if (welcomeDesc) {
      const count = deadlines ? deadlines.length : 0;
      welcomeDesc.textContent = `You have ${count} critical academic deadlines approaching. Your current attendance stands strong at ${stats.attendance}%, with a ${stats.streak_days}-day active study streak.`;
    }
  },

  renderSidebarUser(user) {
    if (!user) return;
    const nameEl = document.getElementById('sidebarUserName');
    const roleEl = document.getElementById('sidebarUserRole');
    const avatarEl = document.getElementById('sidebarUserAvatar');

    if (nameEl) nameEl.textContent = user.name;
    if (roleEl) roleEl.textContent = `${user.major.split(' ')[0]} • ${user.semester.split(' ')[0]}`;
    if (avatarEl) avatarEl.textContent = user.name.split(' ').map(n => n[0]).join('');
  },

  renderStats(stats, user) {
    const gpaEl = document.getElementById('statGpa');
    const attEl = document.getElementById('statAttendance');
    const tasksEl = document.getElementById('statTasks');
    const streakEl = document.getElementById('statStreak');

    if (gpaEl) gpaEl.textContent = stats.gpa.toFixed(2);
    if (attEl) attEl.textContent = `${stats.attendance}%`;
    if (tasksEl) tasksEl.textContent = `${stats.completed_tasks} / ${stats.total_tasks}`;
    if (streakEl) streakEl.textContent = `${stats.streak_days} Days 🔥`;
  },

  renderCopilot(copilot) {
    if (!copilot) return;

    const riskIndexVal = document.getElementById('copilotRiskValue');
    const riskLabel = document.getElementById('copilotRiskLabel');
    const riskFill = document.getElementById('copilotRiskFill');
    const actionTitle = document.getElementById('copilotActionTitle');
    const actionReason = document.getElementById('copilotActionReason');
    const actionFirstStep = document.getElementById('copilotActionStep');

    if (riskIndexVal) riskIndexVal.textContent = `${copilot.risk_index}%`;
    if (riskLabel) {
      riskLabel.textContent = copilot.risk_label;
      riskLabel.style.color = copilot.risk_color;
    }
    if (riskFill) {
      riskFill.style.width = `${copilot.risk_index}%`;
      riskFill.style.backgroundColor = copilot.risk_color;
    }

    if (copilot.recommended_action) {
      const act = copilot.recommended_action;
      if (actionTitle) actionTitle.textContent = `${act.course}: ${act.title}`;
      if (actionReason) actionReason.textContent = act.reason;
      if (actionFirstStep) actionFirstStep.textContent = `🎯 Recommended First Step: ${act.first_step}`;
    }
  },

  renderTodayClasses(classes, dayName) {
    const container = document.getElementById('todayClassesList');
    const dayLabel = document.getElementById('todayDayLabel');
    if (dayLabel) dayLabel.textContent = `(${dayName || 'Today'})`;

    if (!container) return;

    if (!classes || classes.length === 0) {
      container.innerHTML = `
        <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
          🎉 No scheduled lectures for today! Enjoy your self-directed study and project sprint time.
        </div>
      `;
      return;
    }

    container.innerHTML = classes.map(c => `
      <div class="timeline-item">
        <div class="timeline-time">${escapeHtml(c.start_time)} - ${escapeHtml(c.end_time)}</div>
        <div class="timeline-details">
          <div class="timeline-course">
            <span class="task-course-tag">${escapeHtml(c.course_code)}</span>
            <span>${escapeHtml(c.topic || 'Lecture Session')}</span>
          </div>
          <div class="timeline-meta">
            <span>📍 ${escapeHtml(c.room)}</span>
            <span>👨‍🏫 ${escapeHtml(c.professor)}</span>
          </div>
        </div>
      </div>
    `).join('');
  },

  renderUrgentDeadlines(deadlines) {
    const container = document.getElementById('urgentDeadlinesList');
    if (!container) return;

    if (!deadlines || deadlines.length === 0) {
      container.innerHTML = `
        <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
          ✨ All clear! No urgent assignments due in the immediate 48-hour window.
        </div>
      `;
      return;
    }

    container.innerHTML = deadlines.map(d => {
      const isCritical = d.weight_pct >= 20 || d.title.toLowerCase().includes('exam');
      return `
        <div class="deadline-mini-item" style="border-left-color: ${isCritical ? 'var(--danger)' : 'var(--warning)'};">
          <div>
            <div class="deadline-mini-title">${escapeHtml(d.title)}</div>
            <div class="deadline-mini-course">${escapeHtml(d.course_code)} • Weight: ${d.weight_pct}%</div>
          </div>
          <span class="deadline-countdown-badge" style="color: ${isCritical ? 'var(--danger)' : 'var(--warning)'}; background: ${isCritical ? 'var(--danger-light)' : 'var(--warning-light)'};">
            ${formatDueDateTime(d.deadline_date)}
          </span>
        </div>
      `;
    }).join('');
  },

  renderNoticesTicker(notices) {
    const container = document.getElementById('noticesTickerList');
    if (!container) return;

    if (!notices || notices.length === 0) {
      container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">No announcements today.</div>`;
      return;
    }

    container.innerHTML = notices.map(n => `
      <div style="display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.65rem 0; border-bottom: 1px solid var(--border-subtle);">
        <span style="font-size: 1.1rem;">📢</span>
        <div style="flex: 1; min-width: 0;">
          <div style="font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;">
            <span>${escapeHtml(n.title)}</span>
            ${n.is_urgent ? '<span class="priority-badge urgent" style="font-size: 0.65rem;">Urgent</span>' : ''}
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 2px;">
            ${escapeHtml(n.author)} • ${escapeHtml(n.date)}
          </div>
        </div>
      </div>
    `).join('');
  }
};
