/**
 * Smart Campus AI - Frontend API Service
 * Clean async fetch wrapper for all backend REST endpoints.
 */

const API_BASE = '/api';

const api = {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      showToast(err.message || 'Network request failed', 'danger');
      throw err;
    }
  },

  // Dashboard
  getDashboard() {
    return this.request('/dashboard');
  },

  // Timetable
  getTimetable(day = '') {
    return this.request(`/timetable${day ? `?day=${day}` : ''}`);
  },

  // Tasks
  getTasks(filter = '') {
    return this.request(`/tasks${filter ? `?status=${filter}` : ''}`);
  },
  createTask(data) {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  updateTask(id, data) {
    return this.request(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  deleteTask(id) {
    return this.request(`/tasks/${id}`, {
      method: 'DELETE'
    });
  },

  // Deadlines
  getDeadlines() {
    return this.request('/deadlines');
  },
  createDeadline(data) {
    return this.request('/deadlines', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  deleteDeadline(id) {
    return this.request(`/deadlines/${id}`, {
      method: 'DELETE'
    });
  },

  // Announcements
  getAnnouncements(category = 'All') {
    return this.request(`/announcements?category=${encodeURIComponent(category)}`);
  },
  createAnnouncement(data) {
    return this.request('/announcements', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  markAnnouncementRead(id) {
    return this.request(`/announcements/${id}/read`, {
      method: 'POST'
    });
  },

  // Chatbot
  getChatHistory() {
    return this.request('/chat');
  },
  sendChatMessage(message, context_type = 'general', source_doc = null) {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, context_type, source_doc })
    });
  },
  clearChat() {
    return this.request('/chat', {
      method: 'DELETE'
    });
  },

  // Notes & Quizzes
  getNotes() {
    return this.request('/notes');
  },
  getNote(id) {
    return this.request(`/notes/${id}`);
  },
  summarizeNote(data) {
    return this.request('/notes/summarize', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  deleteNote(id) {
    return this.request(`/notes/${id}`, {
      method: 'DELETE'
    });
  },

  // AI Study Planner
  getActiveStudyPlan() {
    return this.request('/study-planner/active');
  },
  generateStudyPlan(data) {
    return this.request('/study-planner/generate', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  toggleSession(slot) {
    return this.request(`/study-planner/session/${slot}`, {
      method: 'PUT'
    });
  },

  // Analytics & Urgency Copilot
  getAnalytics() {
    return this.request('/analytics');
  },
  getCopilot() {
    return this.request('/copilot');
  },

  // Settings
  getSettings() {
    return this.request('/settings');
  },
  updateSettings(data) {
    return this.request('/settings', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
};
