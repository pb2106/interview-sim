/**
 * InterviewIQ — 1-on-1 Conversational AI Interview Simulator
 * 
 * Guarantees:
 * - Zero Browser Persistence (No localStorage, sessionStorage, or cookies)
 * - Zero Emojis
 * - Minimal, human-like feedback after each question
 * - Direct statement of the right answer if candidate answer is wrong/incomplete
 * - Comprehensive end-of-interview report downloadable in PDF format
 */

(() => {
  'use strict';

  // In-Memory Application State (Wiped on page reload)
  const appState = {
    interviewId: null,
    category: 'Software Development',
    difficulty: 'Intermediate',
    questionCount: 5,
    currentQuestionIndex: 0,
    totalQuestions: 5,
    currentQuestion: null,
    isInterviewCompleted: false,
    finalReport: null,
  };

  // DOM Elements
  const elements = {
    // Views
    setupView: document.getElementById('setupView'),
    interviewView: document.getElementById('interviewView'),
    resultsView: document.getElementById('resultsView'),

    // Setup Form
    setupForm: document.getElementById('setupForm'),
    categoryGroup: document.getElementById('categoryGroup'),
    difficultyGroup: document.getElementById('difficultyGroup'),
    countGroup: document.getElementById('countGroup'),
    startInterviewBtn: document.getElementById('startInterviewBtn'),

    // Chat Header
    currentCategoryTag: document.getElementById('currentCategoryTag'),
    currentDifficultyTag: document.getElementById('currentDifficultyTag'),
    questionNumberIndicator: document.getElementById('questionNumberIndicator'),
    totalQuestionsIndicator: document.getElementById('totalQuestionsIndicator'),
    interviewProgressBar: document.getElementById('interviewProgressBar'),

    // Chat Stream & Input
    chatStream: document.getElementById('chatStream'),
    evalTypingIndicator: document.getElementById('evalTypingIndicator'),
    chatInputBar: document.getElementById('chatInputBar'),
    answerTextarea: document.getElementById('answerTextarea'),
    charCounter: document.getElementById('charCounter'),
    answerLengthHint: document.getElementById('answerLengthHint'),
    submitAnswerBtn: document.getElementById('submitAnswerBtn'),

    // Results Elements
    downloadPdfBtn: document.getElementById('downloadPdfBtn'),
    gaugeMeter: document.getElementById('gaugeMeter'),
    reportPercentage: document.getElementById('reportPercentage'),
    reportScoreRatio: document.getElementById('reportScoreRatio'),
    reportGradeBadge: document.getElementById('reportGradeBadge'),
    reportGradeTitle: document.getElementById('reportGradeTitle'),
    reportGradeDesc: document.getElementById('reportGradeDesc'),
    reportAvgScore: document.getElementById('reportAvgScore'),
    reportCategory: document.getElementById('reportCategory'),
    reportDifficulty: document.getElementById('reportDifficulty'),
    reportTotalQ: document.getElementById('reportTotalQ'),
    criteriaBreakdownGrid: document.getElementById('criteriaBreakdownGrid'),
    strongestQTitle: document.getElementById('strongestQTitle'),
    strongestQScore: document.getElementById('strongestQScore'),
    strongestQFeedback: document.getElementById('strongestQFeedback'),
    weakestQTitle: document.getElementById('weakestQTitle'),
    weakestQScore: document.getElementById('weakestQScore'),
    weakestQFeedback: document.getElementById('weakestQFeedback'),
    reportFrequentlyMissingTags: document.getElementById('reportFrequentlyMissingTags'),
    reportRecommendationsList: document.getElementById('reportRecommendationsList'),
    questionsAccordion: document.getElementById('questionsAccordion'),
    reportGradingNote: document.getElementById('reportGradingNote'),
    reportDisclaimerNote: document.getElementById('reportDisclaimerNote'),
    retakeInterviewBtn: document.getElementById('retakeInterviewBtn'),

    // Error Modal
    errorModal: document.getElementById('errorModal'),
    errorModalTitle: document.getElementById('errorModalTitle'),
    errorModalMsg: document.getElementById('errorModalMsg'),
    errorModalCloseBtn: document.getElementById('errorModalCloseBtn'),
  };

  // Helper: Sanitize Text
  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Scroll Chat to Bottom
  function scrollChatToBottom() {
    setTimeout(() => {
      elements.chatStream.scrollTop = elements.chatStream.scrollHeight;
    }, 50);
  }

  // View Switching
  function switchView(activeViewName) {
    elements.setupView.style.display = activeViewName === 'setup' ? 'block' : 'none';
    elements.interviewView.style.display = activeViewName === 'interview' ? 'flex' : 'none';
    elements.resultsView.style.display = activeViewName === 'results' ? 'block' : 'none';

    [elements.setupView, elements.interviewView, elements.resultsView].forEach(v => {
      v.classList.remove('active');
    });

    if (activeViewName === 'setup') {
      setTimeout(() => elements.setupView.classList.add('active'), 10);
    } else if (activeViewName === 'interview') {
      setTimeout(() => elements.interviewView.classList.add('active'), 10);
      scrollChatToBottom();
    } else if (activeViewName === 'results') {
      setTimeout(() => elements.resultsView.classList.add('active'), 10);
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Show Error Modal
  function showError(title, message) {
    elements.errorModalTitle.textContent = title || 'Error';
    elements.errorModalMsg.textContent = message || 'An unexpected error occurred.';
    elements.errorModal.style.display = 'flex';
  }

  function hideError() {
    elements.errorModal.style.display = 'none';
  }

  // Setup Form Listeners
  function initSetupFormListeners() {
    const categoryCards = elements.categoryGroup.querySelectorAll('.option-card');
    categoryCards.forEach(card => {
      card.addEventListener('click', () => {
        categoryCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          appState.category = radio.value;
        }
      });
    });

    const diffCards = elements.difficultyGroup.querySelectorAll('.pill-card');
    diffCards.forEach(card => {
      card.addEventListener('click', () => {
        diffCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          appState.difficulty = radio.value;
        }
      });
    });

    const countCards = elements.countGroup.querySelectorAll('.pill-card');
    countCards.forEach(card => {
      card.addEventListener('click', () => {
        countCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          appState.questionCount = parseInt(radio.value, 10);
        }
      });
    });

    elements.startInterviewBtn.addEventListener('click', handleStartInterview);
  }

  // Append Interviewer Chat Message
  function appendInterviewerMessage(htmlContent, customClass = '') {
    const row = document.createElement('div');
    row.className = `chat-row chat-row-interviewer ${customClass}`;
    row.innerHTML = `
      <div class="avatar interviewer-avatar" aria-hidden="true">AI</div>
      <div class="chat-bubble bubble-interviewer">
        ${htmlContent}
      </div>
    `;
    elements.chatStream.appendChild(row);
    scrollChatToBottom();
  }

  // Append Candidate Chat Message
  function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'chat-row chat-row-user';
    row.innerHTML = `
      <div class="avatar avatar-user" aria-hidden="true">You</div>
      <div class="chat-bubble bubble-user">
        ${escapeHtml(text)}
      </div>
    `;
    elements.chatStream.appendChild(row);
    scrollChatToBottom();
  }

  // Append Question Bubble to Chat Stream
  function appendQuestionBubble(questionObj, qNum, total) {
    const qHtml = `
      <div class="q-label-tag">Question ${qNum} of ${total}</div>
      <div class="bubble-question-text">${escapeHtml(questionObj.question)}</div>
    `;
    appendInterviewerMessage(qHtml, 'bubble-question');
  }

  // Start Interview Handler
  async function handleStartInterview() {
    elements.startInterviewBtn.disabled = true;
    elements.startInterviewBtn.querySelector('.btn-text').textContent = 'Connecting with Interviewer...';

    try {
      const response = await fetch('/api/interviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: appState.category,
          difficulty: appState.difficulty,
          question_count: appState.questionCount,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server responded with status ${response.status}`);
      }

      const data = await response.json();
      appState.interviewId = data.interview_id;
      appState.totalQuestions = data.total_questions;
      appState.currentQuestionIndex = data.current_question_index;
      appState.currentQuestion = data.current_question;
      appState.isInterviewCompleted = false;

      // Initialize Chat Stream
      elements.chatStream.innerHTML = '';

      // Update header meta
      elements.currentCategoryTag.textContent = appState.category;
      elements.currentDifficultyTag.textContent = appState.difficulty;
      elements.questionNumberIndicator.textContent = '1';
      elements.totalQuestionsIndicator.textContent = appState.totalQuestions;
      elements.interviewProgressBar.style.width = '10%';

      // 1-on-1 Welcome message
      const welcomeMsg = `Hello! I am Alex, and I will be conducting your 1-on-1 interview today on <strong>${escapeHtml(appState.category)}</strong> at the <strong>${escapeHtml(appState.difficulty)}</strong> level. We will work through ${appState.totalQuestions} questions together. Whenever you are ready, here is your first question.`;
      appendInterviewerMessage(welcomeMsg);

      // First question prompt
      appendQuestionBubble(appState.currentQuestion, 1, appState.totalQuestions);

      // Reset input bar
      elements.chatInputBar.style.display = 'block';
      elements.answerTextarea.value = '';
      elements.charCounter.textContent = '0 / 5,000 characters';
      elements.submitAnswerBtn.disabled = true;

      switchView('interview');
      setTimeout(() => elements.answerTextarea.focus(), 300);
    } catch (err) {
      showError('Interview Initialization Failed', err.message || 'Could not connect to the interview service.');
    } finally {
      elements.startInterviewBtn.disabled = false;
      elements.startInterviewBtn.querySelector('.btn-text').textContent = 'Start 1-on-1 Interview';
    }
  }

  // Answer Textarea Live Validation
  elements.answerTextarea.addEventListener('input', () => {
    const val = elements.answerTextarea.value;
    const len = val.length;
    elements.charCounter.textContent = `${len.toLocaleString()} / 5,000 characters`;

    const trimmed = val.trim();
    if (trimmed.length < 2) {
      elements.submitAnswerBtn.disabled = true;
      elements.answerLengthHint.textContent = 'Minimum 2 characters required';
      elements.answerLengthHint.style.color = 'var(--text-dim)';
    } else {
      elements.submitAnswerBtn.disabled = false;
      elements.answerLengthHint.textContent = 'Ready to send';
      elements.answerLengthHint.style.color = 'var(--accent-emerald)';
    }
  });

  // Submit Answer
  elements.submitAnswerBtn.addEventListener('click', handleSendAnswer);
  elements.answerTextarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (!elements.submitAnswerBtn.disabled) {
        handleSendAnswer();
      }
    }
  });

  async function handleSendAnswer() {
    const answer = elements.answerTextarea.value.trim();
    if (answer.length < 2) return;

    // Append candidate message bubble to stream
    appendUserMessage(answer);

    // Clear and lock input bar
    elements.answerTextarea.value = '';
    elements.charCounter.textContent = '0 / 5,000 characters';
    elements.submitAnswerBtn.disabled = true;
    elements.chatInputBar.style.display = 'none';

    // Show typing / reviewing indicator
    elements.evalTypingIndicator.style.display = 'flex';
    scrollChatToBottom();

    try {
      const response = await fetch(`/api/interviews/${appState.interviewId}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Evaluation failed with status ${response.status}`);
      }

      const evalData = await response.json();
      elements.evalTypingIndicator.style.display = 'none';

      // Render minimal, human-like chatbot response bubble
      displayMinimalFeedback(evalData);
    } catch (err) {
      elements.evalTypingIndicator.style.display = 'none';
      elements.chatInputBar.style.display = 'block';
      elements.submitAnswerBtn.disabled = false;
      showError('Evaluation Error', err.message || 'Could not complete answer evaluation.');
    }
  }

  // Display Minimal Human-like Chatbot Feedback
  function displayMinimalFeedback(evalData) {
    appState.isInterviewCompleted = evalData.is_interview_completed;

    let scoreClass = 'score-badge-mid';
    if (evalData.score >= 8) scoreClass = 'score-badge-high';
    else if (evalData.score <= 4) scoreClass = 'score-badge-low';

    // Build minimal feedback bubble
    let feedbackHtml = `
      <div class="score-tag-row">
        <span class="score-badge-pill ${scoreClass}">Score: ${evalData.score}/10</span>
      </div>
      <p class="feedback-text-p">${escapeHtml(evalData.feedback)}</p>
    `;

    // If answer wasn't full marks (e.g. score < 10) or correctness < 4, state the right answer directly without explaining why
    if (evalData.score < 10 && evalData.ideal_answer) {
      feedbackHtml += `
        <div class="right-answer-box">
          <strong>Right Answer:</strong> ${escapeHtml(evalData.ideal_answer)}
        </div>
      `;
    }

    appendInterviewerMessage(feedbackHtml, 'bubble-feedback');

    // Update progress tracker
    const completedCount = appState.currentQuestionIndex + 1;
    const progressPercent = Math.round((completedCount / appState.totalQuestions) * 100);
    elements.interviewProgressBar.style.width = `${progressPercent}%`;

    // Append Action Button (Next Question or Final Report)
    const actionRow = document.createElement('div');
    actionRow.className = 'chat-action-row';

    if (evalData.is_interview_completed) {
      actionRow.innerHTML = `
        <button type="button" class="btn btn-primary btn-chat-next" id="viewReportBtn">
          View Complete Performance Report &amp; PDF
        </button>
      `;
      elements.chatStream.appendChild(actionRow);
      scrollChatToBottom();

      document.getElementById('viewReportBtn').addEventListener('click', fetchFinalResults);
    } else {
      const nextQNum = completedCount + 1;
      actionRow.innerHTML = `
        <button type="button" class="btn btn-primary btn-chat-next" id="continueNextQBtn">
          Continue to Question ${nextQNum}
        </button>
      `;
      elements.chatStream.appendChild(actionRow);
      scrollChatToBottom();

      document.getElementById('continueNextQBtn').addEventListener('click', async (e) => {
        // Disable continue button to prevent re-clicks
        e.target.disabled = true;
        appState.currentQuestionIndex += 1;
        await advanceToNextQuestion();
      });
    }
  }

  // Advance to Next Question
  async function advanceToNextQuestion() {
    try {
      const response = await fetch(`/api/interviews/${appState.interviewId}`);
      if (!response.ok) {
        throw new Error(`Failed to load next question (${response.status})`);
      }
      const data = await response.json();
      appState.currentQuestionIndex = data.current_question_index;
      appState.currentQuestion = data.current_question;

      // Update header indicator
      const qNum = appState.currentQuestionIndex + 1;
      elements.questionNumberIndicator.textContent = qNum;

      // Interviewer presents the question
      appendQuestionBubble(appState.currentQuestion, qNum, appState.totalQuestions);

      // Re-enable input bar
      elements.chatInputBar.style.display = 'block';
      elements.answerTextarea.value = '';
      elements.charCounter.textContent = '0 / 5,000 characters';
      elements.submitAnswerBtn.disabled = true;
      elements.answerLengthHint.textContent = 'Minimum 2 characters required';
      elements.answerLengthHint.style.color = 'var(--text-dim)';
      elements.answerTextarea.focus();
      scrollChatToBottom();
    } catch (err) {
      showError('Navigation Error', err.message || 'Could not load next question.');
    }
  }

  // Fetch Final Results and Show Report
  async function fetchFinalResults() {
    try {
      const response = await fetch(`/api/interviews/${appState.interviewId}/results`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Could not retrieve performance report.');
      }

      const reportData = await response.json();
      appState.finalReport = reportData;
      renderResultsScreen(reportData);
      switchView('results');
    } catch (err) {
      showError('Report Generation Error', err.message);
    }
  }

  // Render Performance Report
  function renderResultsScreen(report) {
    // Configure PDF Download link
    elements.downloadPdfBtn.href = `/api/interviews/${report.interview_id}/pdf`;
    elements.downloadPdfBtn.download = `InterviewIQ_Report_${report.interview_id.substring(0, 8)}.pdf`;

    // Overall Score & Gauge
    const pct = report.percentage_score;
    elements.reportPercentage.textContent = `${pct}%`;
    elements.reportScoreRatio.textContent = `${report.total_score}/${report.max_possible_score}`;
    elements.reportAvgScore.textContent = report.average_score.toFixed(1);

    const circumference = 314.159;
    const offset = circumference - (pct / 100) * circumference;
    setTimeout(() => {
      elements.gaugeMeter.style.strokeDashoffset = `${offset}`;
    }, 100);

    // Grade Badge
    elements.reportGradeBadge.textContent = report.grade;
    elements.reportGradeTitle.textContent = `${report.grade} Overall Performance`;
    elements.reportGradeDesc.textContent = report.grade_description;

    const gradeClassMap = {
      'Excellent': 'grade-excellent',
      'Good': 'grade-good',
      'Satisfactory': 'grade-satisfactory',
      'Needs Improvement': 'grade-needs-improvement',
      'Poor': 'grade-poor',
    };
    elements.reportGradeBadge.className = `grade-pill-badge ${gradeClassMap[report.grade] || 'grade-good'}`;

    // Meta Details
    elements.reportCategory.textContent = report.category;
    elements.reportDifficulty.textContent = report.difficulty;
    elements.reportTotalQ.textContent = report.total_questions;

    // Criteria Breakdown Grid
    elements.criteriaBreakdownGrid.innerHTML = '';
    report.criteria_breakdown.forEach(crit => {
      const card = document.createElement('div');
      card.className = 'criterion-card';
      card.innerHTML = `
        <div class="crit-header">
          <span class="crit-name">${escapeHtml(crit.criterion)}</span>
          <span class="crit-pts">${crit.earned_points} / ${crit.max_points} pts (${crit.percentage}%)</span>
        </div>
        <div class="crit-track">
          <div class="crit-fill" style="width: ${crit.percentage}%"></div>
        </div>
        <p class="crit-desc">${escapeHtml(crit.description)}</p>
      `;
      elements.criteriaBreakdownGrid.appendChild(card);
    });

    // Highlights: Strongest & Weakest
    if (report.strongest_answer) {
      elements.strongestQTitle.textContent = `Question ${report.strongest_answer.question_number}: ${report.strongest_answer.question}`;
      elements.strongestQScore.textContent = `Score: ${report.strongest_answer.score}/10 (Correctness: ${report.strongest_answer.correctness_score}/4)`;
      elements.strongestQFeedback.textContent = report.strongest_answer.feedback;
    }

    if (report.weakest_answer) {
      elements.weakestQTitle.textContent = `Question ${report.weakest_answer.question_number}: ${report.weakest_answer.question}`;
      elements.weakestQScore.textContent = `Score: ${report.weakest_answer.score}/10 (Correctness: ${report.weakest_answer.correctness_score}/4)`;
      elements.weakestQFeedback.textContent = report.weakest_answer.feedback;
    }

    // Frequently Missing Concepts
    elements.reportFrequentlyMissingTags.innerHTML = '';
    if (report.frequently_missing_concepts && report.frequently_missing_concepts.length > 0) {
      report.frequently_missing_concepts.forEach(item => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = item;
        elements.reportFrequentlyMissingTags.appendChild(span);
      });
    } else {
      elements.reportFrequentlyMissingTags.innerHTML = '<span class="tag" style="background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); color: #6ee7b7;">None — Strong conceptual coverage</span>';
    }

    // Prioritized Recommendations
    elements.reportRecommendationsList.innerHTML = '';
    report.prioritized_recommendations.forEach(rec => {
      const li = document.createElement('li');
      li.textContent = rec;
      elements.reportRecommendationsList.appendChild(li);
    });

    // Accordion for all questions
    renderQuestionsAccordion(report.question_results);

    // Disclaimers
    elements.reportGradingNote.textContent = report.grading_band_note;
    elements.reportDisclaimerNote.textContent = report.evaluation_disclaimer;
  }

  // Render Detailed Question Accordion
  function renderQuestionsAccordion(questionResults) {
    elements.questionsAccordion.innerHTML = '';
    questionResults.forEach((q, idx) => {
      const item = document.createElement('div');
      item.className = 'accordion-item';

      const isFirst = idx === 0;

      item.innerHTML = `
        <div class="accordion-summary" role="button" tabindex="0" aria-expanded="${isFirst}">
          <div class="acc-title-left">
            <span class="acc-q-num">Q${q.question_number}</span>
            <span class="acc-q-text">${escapeHtml(q.question.length > 70 ? q.question.substring(0, 70) + '...' : q.question)}</span>
          </div>
          <div class="acc-title-right">
            <span class="acc-score">${q.score}/10 pts</span>
            <span class="chevron">${isFirst ? '▲' : '▼'}</span>
          </div>
        </div>
        <div class="accordion-detail" style="display: ${isFirst ? 'block' : 'none'};">
          <div class="acc-sub-section">
            <div class="acc-sub-title">Full Question</div>
            <p style="font-size: 0.92rem; color: #ffffff; margin-bottom: 10px;">${escapeHtml(q.question)}</p>
          </div>

          <div class="acc-sub-section">
            <div class="acc-sub-title">Your Submitted Answer</div>
            <div class="acc-answer-quote">${escapeHtml(q.user_answer)}</div>
          </div>

          <div class="acc-sub-section">
            <div class="acc-sub-title">Component Breakdown</div>
            <div style="font-size: 0.84rem; color: #cbd5e1; font-family: var(--font-mono); margin-bottom: 8px;">
              Correctness: ${q.correctness_score}/4 &bull; Relevance: ${q.relevance_score}/2 &bull; Completeness: ${q.completeness_score}/2 &bull; Clarity: ${q.clarity_score}/2
            </div>
            <p style="font-size: 0.88rem; color: var(--text-muted);">${escapeHtml(q.feedback)}</p>
          </div>

          <div class="acc-sub-section">
            <div class="acc-sub-title">Actionable Recommendation</div>
            <p style="font-size: 0.88rem; color: var(--accent-cyan);">${escapeHtml(q.improvement_tip)}</p>
          </div>

          <div class="acc-sub-section" style="margin-bottom: 0;">
            <div class="acc-sub-title">Reference Answer</div>
            <p style="font-size: 0.86rem; color: #94a3b8; line-height: 1.5; font-style: italic;">${escapeHtml(q.ideal_answer)}</p>
          </div>
        </div>
      `;

      const summary = item.querySelector('.accordion-summary');
      const detail = item.querySelector('.accordion-detail');
      const chevron = item.querySelector('.chevron');

      summary.addEventListener('click', () => {
        const isOpen = detail.style.display !== 'none';
        detail.style.display = isOpen ? 'none' : 'block';
        chevron.textContent = isOpen ? '▼' : '▲';
        summary.setAttribute('aria-expanded', !isOpen);
      });

      elements.questionsAccordion.appendChild(item);
    });
  }

  // Retake Interview: Reset State & Return to Setup
  elements.retakeInterviewBtn.addEventListener('click', () => {
    appState.interviewId = null;
    appState.currentQuestionIndex = 0;
    appState.currentQuestion = null;
    appState.isInterviewCompleted = false;
    appState.finalReport = null;

    elements.gaugeMeter.style.strokeDashoffset = '314';
    elements.chatStream.innerHTML = '';

    switchView('setup');
  });

  // Modal dismiss
  elements.errorModalCloseBtn.addEventListener('click', hideError);
  elements.errorModal.addEventListener('click', (e) => {
    if (e.target === elements.errorModal) hideError();
  });

  // Initialize Setup Form
  initSetupFormListeners();

})();
