/**
 * Smart Campus AI - CampusBot Chatbot Controller
 * Handles conversation, prompt suggestions, document Q&A, and markdown rendering.
 */

const chat = {
  mode: 'general', // 'general' or 'doc'
  attachedDocText: null,
  attachedDocTitle: null,

  async init() {
    this.setupListeners();
    await this.loadHistory();
  },

  setupListeners() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');
    const clearBtn = document.getElementById('chatClearBtn');
    const modeGeneral = document.getElementById('chatModeGeneral');
    const modeDoc = document.getElementById('chatModeDoc');
    const attachDocBtn = document.getElementById('chatAttachDocBtn');
    const removeDocBtn = document.getElementById('chatRemoveDocBtn');

    if (sendBtn) sendBtn.addEventListener('click', () => this.sendMessage());
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        if (confirm('Clear all conversation history?')) {
          await api.clearChat();
          const area = document.getElementById('chatMessagesArea');
          if (area) area.innerHTML = '';
          this.appendWelcomeMessage();
          showToast('Chat history cleared', 'info');
        }
      });
    }

    if (modeGeneral) {
      modeGeneral.addEventListener('click', () => this.setMode('general'));
    }
    if (modeDoc) {
      modeDoc.addEventListener('click', () => this.setMode('doc'));
    }

    if (attachDocBtn) {
      attachDocBtn.addEventListener('click', () => openModal('chatDocModal'));
    }
    if (removeDocBtn) {
      removeDocBtn.addEventListener('click', () => this.detachDocument());
    }

    // Modal submit for attaching document
    const attachSubmitBtn = document.getElementById('submitAttachDocBtn');
    if (attachSubmitBtn) {
      attachSubmitBtn.addEventListener('click', () => {
        const title = document.getElementById('chatDocTitleInput')?.value.trim() || 'Attached Document';
        const content = document.getElementById('chatDocContentInput')?.value.trim();
        if (!content || content.length < 20) {
          showToast('Please enter document content to query', 'danger');
          return;
        }
        this.attachDocument(title, content);
        closeModal('chatDocModal');
      });
    }

    // Prompt suggestion chips
    document.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.getAttribute('data-prompt') || chip.textContent;
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
          chatInput.value = text;
          this.sendMessage();
        }
      });
    });
  },

  setMode(mode) {
    this.mode = mode;
    const modeGeneral = document.getElementById('chatModeGeneral');
    const modeDoc = document.getElementById('chatModeDoc');

    if (mode === 'general') {
      modeGeneral?.classList.add('active');
      modeDoc?.classList.remove('active');
    } else {
      modeDoc?.classList.add('active');
      modeGeneral?.classList.remove('active');
      if (!this.attachedDocText) {
        openModal('chatDocModal');
      }
    }
  },

  attachDocument(title, content) {
    this.attachedDocText = content;
    this.attachedDocTitle = title;
    this.setMode('doc');

    const banner = document.getElementById('chatDocBanner');
    const titleEl = document.getElementById('chatDocBannerTitle');
    if (banner && titleEl) {
      titleEl.textContent = `Active Study Document: ${title} (${content.length} chars)`;
      banner.style.display = 'flex';
    }
    showToast(`Document attached: ${title}`, 'success');
  },

  detachDocument() {
    this.attachedDocText = null;
    this.attachedDocTitle = null;
    const banner = document.getElementById('chatDocBanner');
    if (banner) banner.style.display = 'none';
    this.setMode('general');
    showToast('Document detached', 'info');
  },

  async loadHistory() {
    try {
      const data = await api.getChatHistory();
      const area = document.getElementById('chatMessagesArea');
      if (!area) return;

      area.innerHTML = '';
      if (!data.messages || data.messages.length === 0) {
        this.appendWelcomeMessage();
        return;
      }

      data.messages.forEach(msg => {
        this.renderMessage(msg.role, msg.message, 'Campus AI');
      });
      this.scrollToBottom();
    } catch (e) {
      console.error('Error loading chat history:', e);
    }
  },

  appendWelcomeMessage() {
    this.renderMessage('assistant', 
      "Hello! 👋 I am your **Smart Campus AI Assistant**.\n\n" +
      "Ask me anything about:\n" +
      "• 📅 Today's class timings and lecture halls\n" +
      "• 📋 Upcoming assignments and exam countdowns\n" +
      "• 🏛️ Library regulations, hostel passes, and attendance rules\n" +
      "• 📖 Or attach your lecture notes for instant contextual Q&A!",
      "Campus AI"
    );
  },

  async sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input ? input.value.trim() : '';
    if (!text) return;

    input.value = '';

    // Render User Message
    this.renderMessage('user', text, 'You');
    this.scrollToBottom();

    // Render Typing Placeholder
    const typingId = this.renderTypingIndicator();
    this.scrollToBottom();

    try {
      const res = await api.sendChatMessage(text, this.mode, this.attachedDocText);
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();

      this.renderMessage('assistant', res.message, res.engine);
      this.scrollToBottom();
    } catch (err) {
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();
      this.renderMessage('assistant', "⚠️ Sorry, I encountered an issue processing your request. Please try again.", "Error");
      this.scrollToBottom();
    }
  },

  renderMessage(role, text, engineName = null) {
    const area = document.getElementById('chatMessagesArea');
    if (!area) return;

    const div = document.createElement('div');
    div.className = `chat-message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';
    const parsedHtml = renderMarkdown(text);

    div.innerHTML = `
      <div class="chat-avatar">${avatar}</div>
      <div class="chat-bubble">
        <div>${parsedHtml}</div>
        ${role === 'assistant' && engineName ? `<div class="chat-engine-tag">⚡ ${escapeHtml(engineName)}</div>` : ''}
      </div>
    `;

    area.appendChild(div);
  },

  renderTypingIndicator() {
    const area = document.getElementById('chatMessagesArea');
    const id = `typing_${Date.now()}`;
    const div = document.createElement('div');
    div.id = id;
    div.className = 'chat-message assistant';
    div.innerHTML = `
      <div class="chat-avatar">🤖</div>
      <div class="chat-bubble" style="display: flex; align-items: center; gap: 4px; padding: 0.75rem 1rem;">
        <span style="font-size: 0.8rem; color: var(--text-muted);">Thinking</span>
        <span class="typing-dot" style="animation: pulse 1s infinite;">.</span>
        <span class="typing-dot" style="animation: pulse 1s infinite 0.2s;">.</span>
        <span class="typing-dot" style="animation: pulse 1s infinite 0.4s;">.</span>
      </div>
    `;
    area.appendChild(div);
    return id;
  },

  scrollToBottom() {
    const area = document.getElementById('chatMessagesArea');
    if (area) {
      area.scrollTop = area.scrollHeight;
    }
  }
};
