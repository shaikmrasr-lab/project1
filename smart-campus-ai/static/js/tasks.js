/**
 * Smart Campus AI - Task Manager Controller
 * Full CRUD, filters, priority tagging, and study session launch.
 */

const tasks = {
  currentFilter: 'all',
  searchQuery: '',
  taskList: [],

  async init() {
    this.setupListeners();
    await this.loadTasks();
  },

  setupListeners() {
    // Add Task Button
    const addBtn = document.getElementById('addNewTaskBtn');
    if (addBtn) addBtn.addEventListener('click', () => openModal('addTaskModal'));

    // Submit Task Modal
    const submitBtn = document.getElementById('submitNewTaskBtn');
    if (submitBtn) {
      submitBtn.addEventListener('click', () => this.handleCreateTask());
    }

    // Filter Pills
    document.querySelectorAll('.task-filter-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        document.querySelectorAll('.task-filter-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        this.currentFilter = pill.getAttribute('data-filter') || 'all';
        this.renderTasks();
      });
    });

    // Task Search
    const searchInput = document.getElementById('taskSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase().trim();
        this.renderTasks();
      });
    }
  },

  async loadTasks() {
    try {
      const data = await api.getTasks();
      this.taskList = data.tasks || [];
      this.renderTasks();
    } catch (err) {
      console.error('Error loading tasks:', err);
    }
  },

  async handleCreateTask() {
    const titleInput = document.getElementById('taskTitleInput');
    const courseInput = document.getElementById('taskCourseInput');
    const dueInput = document.getElementById('taskDueInput');
    const prioInput = document.getElementById('taskPriorityInput');
    const estInput = document.getElementById('taskEstMinutesInput');
    const descInput = document.getElementById('taskDescInput');

    const title = titleInput ? titleInput.value.trim() : '';
    if (!title) {
      showToast('Please enter a task title', 'danger');
      return;
    }

    const payload = {
      title,
      course_code: courseInput ? courseInput.value.trim() : 'GEN101',
      due_date: dueInput && dueInput.value ? dueInput.value : new Date().toISOString().slice(0, 16),
      priority: prioInput ? prioInput.value : 'Medium',
      estimated_minutes: estInput ? parseInt(estInput.value) || 60 : 60,
      description: descInput ? descInput.value.trim() : ''
    };

    try {
      await api.createTask(payload);
      showToast('Task added successfully', 'success');
      closeModal('addTaskModal');

      // Clear inputs
      if (titleInput) titleInput.value = '';
      if (descInput) descInput.value = '';

      await this.loadTasks();
      dashboard.loadDashboardData();
    } catch (err) {
      showToast('Failed to create task', 'danger');
    }
  },

  async toggleTaskStatus(task) {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    try {
      await api.updateTask(task.id, { status: newStatus });
      task.status = newStatus;
      this.renderTasks();
      showToast(`Task marked as ${newStatus}`, 'success');
      dashboard.loadDashboardData();
    } catch (err) {
      showToast('Failed to update task status', 'danger');
    }
  },

  async deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.deleteTask(taskId);
      this.taskList = this.taskList.filter(t => t.id !== taskId);
      this.renderTasks();
      showToast('Task deleted', 'info');
      dashboard.loadDashboardData();
    } catch (err) {
      showToast('Failed to delete task', 'danger');
    }
  },

  renderTasks() {
    const container = document.getElementById('tasksCardsList');
    if (!container) return;

    let filtered = this.taskList.filter(t => {
      // Status filter
      if (this.currentFilter === 'pending' && t.status === 'completed') return false;
      if (this.currentFilter === 'completed' && t.status !== 'completed') return false;
      if (this.currentFilter === 'urgent' && t.priority !== 'Urgent' && t.priority !== 'High') return false;

      // Search query
      if (this.searchQuery) {
        const match = t.title.toLowerCase().includes(this.searchQuery) ||
                      (t.description && t.description.toLowerCase().includes(this.searchQuery)) ||
                      t.course_code.toLowerCase().includes(this.searchQuery);
        if (!match) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: var(--text-muted); background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
          <div style="font-weight: 600;">No tasks found matching this criteria.</div>
          <div style="font-size: 0.82rem; margin-top: 4px;">Click "+ Add Task" to create your next academic milestone!</div>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered.map(t => {
      const isCompleted = t.status === 'completed';
      const prioClass = (t.priority || 'Medium').toLowerCase();

      return `
        <div class="task-card ${isCompleted ? 'completed' : ''}" data-id="${t.id}">
          <div class="task-checkbox ${isCompleted ? 'checked' : ''}" onclick="tasks.toggleTaskStatus(tasks.taskList.find(x => x.id === ${t.id}))">
            ${isCompleted ? '✓' : ''}
          </div>

          <div class="task-details">
            <div class="task-title-row">
              <span class="task-course-tag">${escapeHtml(t.course_code)}</span>
              <span class="task-title-text">${escapeHtml(t.title)}</span>
              <span class="priority-badge ${prioClass}">${escapeHtml(t.priority)}</span>
            </div>
            ${t.description ? `<div class="task-desc-text">${escapeHtml(t.description)}</div>` : ''}
            <div class="task-meta-row">
              <span>📅 ${formatDueDateTime(t.due_date)}</span>
              <span>⏱️ Est: ${t.estimated_minutes || 60} mins</span>
              ${isCompleted && t.completed_at ? `<span>✅ Finished on ${t.completed_at.slice(0, 10)}</span>` : ''}
            </div>
          </div>

          <div class="task-actions">
            <button class="btn btn-outline btn-sm" title="Convert to Study Plan" onclick="tasks.scheduleAsSession(${t.id})">
              🎯 Study
            </button>
            <button class="btn-icon" style="width: 32px; height: 32px;" title="Delete Task" onclick="tasks.deleteTask(${t.id})">
              🗑️
            </button>
          </div>
        </div>
      `;
    }).join('');
  },

  scheduleAsSession(taskId) {
    const task = this.taskList.find(t => t.id === taskId);
    if (!task) return;
    showToast(`Routing ${task.course_code} to AI Study Planner...`, 'info');
    app.switchView('planner');
    
    // Auto populate planner subjects
    const subInput = document.getElementById('plannerSubjectsInput');
    if (subInput) {
      subInput.value = `${task.course_code} (${task.title})`;
    }
  }
};
