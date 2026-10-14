/**
 * Smart Campus AI - Notes Summarizer & Interactive Quiz Controller
 * Generates executive summaries, bullet takeaways, and multiple-choice practice quizzes.
 */

const notes = {
  currentQuiz: [],
  quizScore: 0,
  answeredCount: 0,
  savedNotes: [],

  async init() {
    this.setupListeners();
    await this.loadSavedNotes();
  },

  setupListeners() {
    const summarizeBtn = document.getElementById('summarizeNotesBtn');
    if (summarizeBtn) {
      summarizeBtn.addEventListener('click', () => this.handleSummarizeNotes());
    }

    const loadSampleBtn = document.getElementById('loadSampleNotesBtn');
    if (loadSampleBtn) {
      loadSampleBtn.addEventListener('click', () => this.loadSampleNote());
    }

    // File upload reader
    const fileInput = document.getElementById('notesFileInput');
    if (fileInput) {
      fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (evt) => {
          const content = evt.target.result;
          const contentArea = document.getElementById('notesContentInput');
          const titleInput = document.getElementById('notesTitleInput');
          if (contentArea) contentArea.value = content;
          if (titleInput && !titleInput.value) {
            titleInput.value = file.name.replace(/\.[^/.]+$/, "");
          }
          showToast(`File loaded: ${file.name} (${content.length} chars)`, 'success');
        };
        reader.readAsText(file);
      });
    }
  },

  loadSampleNote() {
    const titleInput = document.getElementById('notesTitleInput');
    const courseInput = document.getElementById('notesCourseInput');
    const contentArea = document.getElementById('notesContentInput');

    if (titleInput) titleInput.value = "CS304: Relational Database Normalization (1NF to BCNF)";
    if (courseInput) courseInput.value = "CS304";
    if (contentArea) {
      contentArea.value = `Relational Database Normalization: Comprehensive Principles

1. Purpose of Normalization:
Normalization minimizes redundancy and eliminates update, insertion, and deletion anomalies. It decomposes tables without losing information (lossless-join decomposition) and preserves functional dependencies where possible.

2. Normal Forms Hierarchy:
- First Normal Form (1NF): Requires that all attribute values are atomic (no repeating groups, arrays, or comma-separated lists) and every row has a unique primary key.
- Second Normal Form (2NF): Must be in 1NF, and all non-key attributes must be fully functionally dependent on the entire primary key (eliminates partial dependency on composite keys).
- Third Normal Form (3NF): Must be in 2NF, and no non-key attribute can be transitively dependent on the primary key (X -> Y where neither is a candidate key).
- Boyce-Codd Normal Form (BCNF): A stricter version of 3NF. For every non-trivial functional dependency X -> Y, X MUST be a superkey.

3. Key Tradeoffs:
Higher normal forms prevent update anomalies and save disk storage, but require more JOIN operations during complex queries. In high-throughput read-heavy analytics (OLAP), denormalization is often applied intentionally.`;
    }
    showToast('Loaded sample lecture notes on Database Normalization', 'info');
  },

  async handleSummarizeNotes() {
    const titleInput = document.getElementById('notesTitleInput');
    const courseInput = document.getElementById('notesCourseInput');
    const contentArea = document.getElementById('notesContentInput');
    const btn = document.getElementById('summarizeNotesBtn');

    const title = titleInput ? titleInput.value.trim() : 'Lecture Notes';
    const course_code = courseInput ? courseInput.value.trim() : 'CS301';
    const content = contentArea ? contentArea.value.trim() : '';

    if (!content || content.length < 30) {
      showToast('Please paste or upload at least 30 characters of note text', 'danger');
      return;
    }

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span>⚡ Analyzing Notes & Generating Quiz...</span>`;
    }

    try {
      const result = await api.summarizeNote({
        title,
        course_code,
        content
      });

      this.displayResults(result);
      showToast('Notes summarized and 5-question practice quiz generated!', 'success');
      await this.loadSavedNotes();
    } catch (err) {
      showToast('Failed to summarize notes', 'danger');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<span>🧠 Summarize & Generate Quiz</span>`;
      }
    }
  },

  async loadSavedNotes() {
    try {
      const data = await api.getNotes();
      this.savedNotes = data.notes || [];
      this.renderSavedNotesList();
    } catch (e) {
      console.error('Error loading saved notes:', e);
    }
  },

  async viewSavedNote(id) {
    try {
      const data = await api.getNote(id);
      if (data && data.note) {
        this.displayResults(data.note);
        window.scrollTo({ top: document.getElementById('notesResultSection')?.offsetTop - 80, behavior: 'smooth' });
      }
    } catch (e) {
      showToast('Error loading note', 'danger');
    }
  },

  async deleteNote(id) {
    if (!confirm('Delete this saved note from your library?')) return;
    try {
      await api.deleteNote(id);
      this.savedNotes = this.savedNotes.filter(n => n.id !== id);
      this.renderSavedNotesList();
      showToast('Note deleted', 'info');
    } catch (e) {
      showToast('Failed to delete note', 'danger');
    }
  },

  displayResults(data) {
    const resultSection = document.getElementById('notesResultSection');
    const summaryBox = document.getElementById('noteSummaryContent');
    const takeawaysList = document.getElementById('noteTakeawaysList');
    const quizArea = document.getElementById('noteQuizArea');
    const engineTag = document.getElementById('notesEngineTag');

    if (resultSection) resultSection.style.display = 'block';

    if (summaryBox) {
      summaryBox.textContent = data.summary || 'Summary unavailable.';
    }

    if (engineTag && data.engine) {
      engineTag.textContent = `Generated with ${data.engine}`;
    }

    if (takeawaysList) {
      const takeaways = Array.isArray(data.key_takeaways) ? data.key_takeaways : [];
      takeawaysList.innerHTML = takeaways.map(t => `
        <div class="takeaway-item">
          <span style="color: var(--accent-cyan); font-weight: 700;">✓</span>
          <span>${renderMarkdown(t)}</span>
        </div>
      `).join('');
    }

    // Render Quiz
    this.currentQuiz = Array.isArray(data.quiz) ? data.quiz : [];
    this.quizScore = 0;
    this.answeredCount = 0;
    this.renderQuiz(this.currentQuiz);
  },

  renderQuiz(questions) {
    const quizArea = document.getElementById('noteQuizArea');
    const scoreBanner = document.getElementById('quizScoreBanner');
    if (!quizArea) return;

    if (scoreBanner) {
      scoreBanner.style.display = 'none';
      scoreBanner.innerHTML = '';
    }

    if (!questions || questions.length === 0) {
      quizArea.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">No practice questions generated for this document.</div>`;
      return;
    }

    quizArea.innerHTML = questions.map((q, idx) => `
      <div class="quiz-card" id="quiz_card_${idx}">
        <div class="quiz-question-num">Question ${idx + 1} of ${questions.length}</div>
        <div class="quiz-question-text">${escapeHtml(q.question)}</div>

        <div class="quiz-options-list">
          ${q.options.map((opt, optIdx) => `
            <button class="quiz-option-btn" onclick="notes.selectAnswer(${idx}, ${optIdx})">
              <span style="display: inline-block; width: 24px; font-weight: 700; color: var(--text-muted);">${String.fromCharCode(65 + optIdx)}.</span>
              <span>${escapeHtml(opt)}</span>
            </button>
          `).join('')}
        </div>

        <div class="quiz-explanation-box" id="quiz_exp_${idx}">
          <strong>Explanation:</strong> ${escapeHtml(q.explanation || 'Review the core definition in your notes.')}
        </div>
      </div>
    `).join('');
  },

  selectAnswer(questionIdx, selectedOptIdx) {
    const card = document.getElementById(`quiz_card_${questionIdx}`);
    if (!card) return;

    const q = this.currentQuiz[questionIdx];
    if (!q) return;

    const buttons = card.querySelectorAll('.quiz-option-btn');
    if (buttons[0].disabled) return; // Already answered

    // Disable all options for this question
    buttons.forEach(b => b.disabled = true);

    const isCorrect = selectedOptIdx === q.correct;
    if (isCorrect) {
      this.quizScore++;
      buttons[selectedOptIdx].classList.add('correct');
      showToast('Correct answer! 🎯', 'success');
    } else {
      buttons[selectedOptIdx].classList.add('wrong');
      buttons[q.correct].classList.add('correct'); // Highlight correct answer
    }

    // Show explanation
    const expBox = document.getElementById(`quiz_exp_${questionIdx}`);
    if (expBox) expBox.style.display = 'block';

    this.answeredCount++;
    if (this.answeredCount === this.currentQuiz.length) {
      this.showQuizFinalScore();
    }
  },

  showQuizFinalScore() {
    const scoreBanner = document.getElementById('quizScoreBanner');
    if (!scoreBanner) return;

    const total = this.currentQuiz.length;
    const pct = Math.round((this.quizScore / total) * 100);

    scoreBanner.style.display = 'flex';
    scoreBanner.className = `glass-card`;
    scoreBanner.style.border = pct >= 80 ? '1px solid var(--success)' : '1px solid var(--warning)';
    scoreBanner.style.alignItems = 'center';
    scoreBanner.style.justifyContent = 'space-between';
    scoreBanner.style.padding = '1.25rem';
    scoreBanner.style.marginTop = '1rem';

    scoreBanner.innerHTML = `
      <div>
        <div style="font-size: 1.15rem; font-weight: 700;">Quiz Completed! Score: ${this.quizScore} / ${total} (${pct}%)</div>
        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 2px;">
          ${pct >= 80 ? '🌟 Outstanding mastery of core concepts!' : '💡 Solid attempt! Review the highlighted explanations to solidify retention.'}
        </div>
      </div>
      <button class="btn btn-secondary btn-sm" onclick="notes.renderQuiz(notes.currentQuiz)">
        🔄 Retake Quiz
      </button>
    `;
  },

  renderSavedNotesList() {
    const container = document.getElementById('savedNotesLibraryList');
    if (!container) return;

    if (this.savedNotes.length === 0) {
      container.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted); padding: 0.5rem 0;">No notes saved yet.</div>`;
      return;
    }

    container.innerHTML = this.savedNotes.map(n => `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0.9rem; background: var(--bg-tertiary); border-radius: var(--radius-md); border-left: 3px solid var(--primary); margin-bottom: 0.5rem;">
        <div>
          <div style="font-size: 0.88rem; font-weight: 600;">${escapeHtml(n.title)}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 2px;">${escapeHtml(n.course_code)} • ${escapeHtml(n.created_at?.slice(0, 10))}</div>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-outline btn-sm" onclick="notes.viewSavedNote(${n.id})">Open</button>
          <button class="btn-icon" style="width: 28px; height: 28px;" onclick="notes.deleteNote(${n.id})">🗑️</button>
        </div>
      </div>
    `).join('');
  }
};
