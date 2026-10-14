/**
 * Smart Campus AI - AI Study Planner Controller
 * Generates personalized daily study schedules with Pomodoro time-blocking.
 */

const planner = {
  activePlan: null,

  async init() {
    this.setupListeners();
    await this.loadActivePlan();
  },

  setupListeners() {
    const genBtn = document.getElementById('generatePlanBtn');
    if (genBtn) genBtn.addEventListener('click', () => this.handleGeneratePlan());

    // Subject suggestion pills
    document.querySelectorAll('.planner-preset-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const input = document.getElementById('plannerSubjectsInput');
        if (input) {
          const val = pill.textContent.trim();
          if (input.value && !input.value.includes(val)) {
            input.value += `, ${val}`;
          } else if (!input.value) {
            input.value = val;
          }
        }
      });
    });

    // Hours slider display
    const hoursSlider = document.getElementById('plannerHoursSlider');
    const hoursVal = document.getElementById('plannerHoursValue');
    if (hoursSlider && hoursVal) {
      hoursSlider.addEventListener('input', (e) => {
        hoursVal.textContent = `${e.target.value} hrs`;
      });
    }
  },

  async loadActivePlan() {
    try {
      const data = await api.getActiveStudyPlan();
      if (data && data.active_plan && data.active_plan.details) {
        this.activePlan = data.active_plan.details;
        this.renderSchedule(this.activePlan);
      }
    } catch (err) {
      console.error('Error loading active study plan:', err);
    }
  },

  async handleGeneratePlan() {
    const subjectsInput = document.getElementById('plannerSubjectsInput');
    const hoursSlider = document.getElementById('plannerHoursSlider');
    const targetDateInput = document.getElementById('plannerTargetDateInput');
    const techniqueSelect = document.getElementById('plannerTechniqueSelect');
    const btn = document.getElementById('generatePlanBtn');

    const subjectsRaw = subjectsInput ? subjectsInput.value.trim() : '';
    const available_hours = hoursSlider ? parseFloat(hoursSlider.value) : 4.0;
    const target_date = targetDateInput && targetDateInput.value ? targetDateInput.value : new Date().toISOString().slice(0, 10);
    const technique = techniqueSelect ? techniqueSelect.value : 'Pomodoro (25/5)';

    const subjects = subjectsRaw.split(',').map(s => s.trim()).filter(Boolean);
    if (subjects.length === 0) {
      showToast('Please specify at least one subject or course', 'danger');
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span>⏳ Optimizing Schedule...</span>`;
    }

    try {
      const plan = await api.generateStudyPlan({
        subjects,
        available_hours,
        target_date,
        technique
      });

      this.activePlan = plan;
      this.renderSchedule(plan);
      showToast(`Personalized schedule generated with ${plan.sessions?.length || 0} study blocks!`, 'success');
      dashboard.loadDashboardData();
    } catch (err) {
      showToast('Failed to generate study plan', 'danger');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>✨ Generate AI Schedule</span>`;
      }
    }
  },

  async toggleSession(slot) {
    try {
      const res = await api.toggleSession(slot);
      if (this.activePlan && res.sessions) {
        this.activePlan.sessions = res.sessions;
        this.renderSchedule(this.activePlan);
      }
      showToast('Session status updated', 'success');
    } catch (e) {
      showToast('Error updating session', 'danger');
    }
  },

  renderSchedule(plan) {
    const titleEl = document.getElementById('activePlanTitle');
    const metaEl = document.getElementById('activePlanMeta');
    const container = document.getElementById('scheduleTimelineList');
    const engineTag = document.getElementById('plannerEngineTag');

    if (!container) return;

    if (!plan || !plan.sessions || plan.sessions.length === 0) {
      container.innerHTML = `
        <div style="padding: 3rem; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📅</div>
          <div style="font-size: 1.1rem; font-weight: 600;">No Active Study Plan</div>
          <div style="font-size: 0.85rem; margin-top: 4px;">Select your subjects and daily hours on the left to generate an optimized schedule!</div>
        </div>
      `;
      return;
    }

    if (titleEl) titleEl.textContent = plan.title || 'Personalized Academic Schedule';
    if (metaEl) {
      const completed = plan.sessions.filter(s => s.status === 'completed').length;
      metaEl.textContent = `Target: ${plan.target_date} • ${plan.available_hours} Hours Allocated • ${completed}/${plan.sessions.length} Sessions Done`;
    }
    if (engineTag && plan.engine) {
      engineTag.textContent = `Generated by ${plan.engine}`;
      engineTag.style.display = 'inline-block';
    }

    container.innerHTML = plan.sessions.map(s => {
      const isCompleted = s.status === 'completed';
      const slotNum = s.slot || 1;

      return `
        <div class="schedule-block ${isCompleted ? 'completed' : ''}">
          <div class="task-checkbox ${isCompleted ? 'checked' : ''}" onclick="planner.toggleSession(${slotNum})" title="Mark Session Done">
            ${isCompleted ? '✓' : ''}
          </div>

          <div class="schedule-time-badge">${escapeHtml(s.time)}</div>

          <div class="schedule-content">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span class="task-course-tag">${escapeHtml(s.subject)}</span>
              <span class="schedule-topic">${escapeHtml(s.topic)}</span>
            </div>
            <div class="schedule-task">${escapeHtml(s.task)}</div>
            <div class="schedule-technique-pill">${escapeHtml(s.technique_type || plan.technique)}</div>
          </div>
        </div>
      `;
    }).join('');
  }
};
