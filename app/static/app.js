/**
 * InterviewIQ — AI Interview Simulator Client Script
 * 
 * Strict Zero Persistence:
 * - NO localStorage
 * - NO sessionStorage
 * - NO cookies
 * All state is maintained in runtime memory only.
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

    // Interview Tracking
    currentCategoryTag: document.getElementById('currentCategoryTag'),
    currentDifficultyTag: document.getElementById('currentDifficultyTag'),
    questionNumberIndicator: document.getElementById('questionNumberIndicator'),
    totalQuestionsIndicator: document.getElementById('totalQuestionsIndicator'),
    interviewProgressBar: document.getElementById('interviewProgressBar'),

    // Question & Answer
    questionStatementText: document.getElementById('questionStatementText'),
    answerFormCard: document.getElementById('answerFormCard'),
    answerTextarea: document.getElementById('answerTextarea'),
    charCounter: document.getElementById('charCounter'),
    answerLengthHint: document.getElementById('answerLengthHint'),
    submitAnswerBtn: document.getElementById('submitAnswerBtn'),

    // Evaluation States
    evalLoadingCard: document.getElementById('evalLoadingCard'),
    evalResultCard: document.getElementById('evalResultCard'),
    evalScoreValue: document.getElementById('evalScoreValue'),
    evalFeedbackText: document.getElementById('evalFeedbackText'),
    rmCorrectness: document.getElementById('rmCorrectness'),
    rmRelevance: document.getElementById('rmRelevance'),
    rmCompleteness: document.getElementById('rmCompleteness'),
    rmClarity: document.getElementById('rmClarity'),
    evalStrengthsList: document.getElementById('evalStrengthsList'),
    evalWeaknessesList: document.getElementById('evalWeaknessesList'),
    missingConceptsContainer: document.getElementById('missingConceptsContainer'),
    evalMissingTags: document.getElementById('evalMissingTags'),
    evalImprovementTipText: document.getElementById('evalImprovementTipText'),
    toggleIdealBtn: document.getElementById('toggleIdealBtn'),
    idealAnswerContent: document.getElementById('idealAnswerContent'),
    idealChevron: document.getElementById('idealChevron'),
    evalIdealAnswerText: document.getElementById('evalIdealAnswerText'),
    nextQuestionBtn: document.getElementById('nextQuestionBtn'),
    nextBtnText: document.getElementById('nextBtnText'),

    // Results Elements
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

  // Helper: Sanitize Text for safe rendering
  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // View Switching
  function switchView(activeViewName) {
    elements.setupView.style.display = activeViewName === 'setup' ? 'block' : 'none';
    elements.interviewView.style.display = activeViewName === 'interview' ? 'block' : 'none';
    elements.resultsView.style.display = activeViewName === 'results' ? 'block' : 'none';

    // Trigger animation classes
    [elements.setupView, elements.interviewView, elements.resultsView].forEach(v => {
      v.classList.remove('active');
    });

    if (activeViewName === 'setup') {
      setTimeout(() => elements.setupView.classList.add('active'), 10);
    } else if (activeViewName === 'interview') {
      setTimeout(() => elements.interviewView.classList.add('active'), 10);
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

  // Setup Form Card Selection Listeners
  function initSetupFormListeners() {
    // Categories
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

    // Difficulty
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

    // Question Count
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

    // Start button
    elements.startInterviewBtn.addEventListener('click', handleStartInterview);
  }

  // Start Interview Handler
  async function handleStartInterview() {
    elements.startInterviewBtn.disabled = true;
    elements.startInterviewBtn.querySelector('.btn-text').textContent = 'Generating Questions with AI...';

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

      // Render first question
      renderInterviewScreen();
      switchView('interview');
    } catch (err) {
      showError('Interview Generation Failed', err.message || 'Could not connect to the interview service.');
    } finally {
      elements.startInterviewBtn.disabled = false;
      elements.startInterviewBtn.querySelector('.btn-text').textContent = 'Generate Questions & Begin';
    }
  }

  // Render Interview Screen for Current Question
  function renderInterviewScreen() {
    elements.currentCategoryTag.textContent = appState.category;
    elements.currentDifficultyTag.textContent = appState.difficulty;

    const qNum = appState.currentQuestionIndex + 1;
    elements.questionNumberIndicator.textContent = qNum;
    elements.totalQuestionsIndicator.textContent = appState.totalQuestions;

    const progressPercent = Math.round((appState.currentQuestionIndex / appState.totalQuestions) * 100);
    elements.interviewProgressBar.style.width = `${Math.max(5, progressPercent)}%`;

    elements.questionStatementText.textContent = appState.currentQuestion ? appState.currentQuestion.question : '';

    // Reset answer textarea & state
    elements.answerTextarea.value = '';
    elements.charCounter.textContent = '0 / 5,000 characters';
    elements.submitAnswerBtn.disabled = true;
    elements.answerLengthHint.textContent = 'Minimum 2 characters required';
    elements.answerLengthHint.style.color = 'var(--text-dim)';

    // Show answer input card, hide loading and result cards
    elements.answerFormCard.style.display = 'block';
    elements.evalLoadingCard.style.display = 'none';
    elements.evalResultCard.style.display = 'none';
    elements.idealAnswerContent.style.display = 'none';
    elements.idealChevron.textContent = '▼';

    elements.answerTextarea.focus();
  }

  // Live Answer Character Counter & Validation
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
      elements.answerLengthHint.textContent = 'Ready to submit for AI evaluation';
      elements.answerLengthHint.style.color = 'var(--accent-emerald)';
    }
  });

  // Submit Answer Handler
  elements.submitAnswerBtn.addEventListener('click', async () => {
    const answer = elements.answerTextarea.value.trim();
    if (answer.length < 2) return;

    elements.submitAnswerBtn.disabled = true;
    elements.answerFormCard.style.display = 'none';
    elements.evalLoadingCard.style.display = 'flex';

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
      displayEvaluationResult(evalData);
    } catch (err) {
      elements.evalLoadingCard.style.display = 'none';
      elements.answerFormCard.style.display = 'block';
      elements.submitAnswerBtn.disabled = false;
      showError('Evaluation Failed', err.message || 'Could not complete AI evaluation.');
    }
  });

  // Display Evaluation Results for the Current Question
  function displayEvaluationResult(evaluation) {
    elements.evalLoadingCard.style.display = 'none';
    elements.evalResultCard.style.display = 'block';

    // Scores
    elements.evalScoreValue.textContent = evaluation.score;
    elements.evalFeedbackText.textContent = evaluation.feedback;
    elements.rmCorrectness.textContent = `${evaluation.correctness_score}/4`;
    elements.rmRelevance.textContent = `${evaluation.relevance_score}/2`;
    elements.rmCompleteness.textContent = `${evaluation.completeness_score}/2`;
    elements.rmClarity.textContent = `${evaluation.clarity_score}/2`;

    // Strengths
    elements.evalStrengthsList.innerHTML = '';
    if (evaluation.strengths && evaluation.strengths.length > 0) {
      evaluation.strengths.forEach(s => {
        const li = document.createElement('li');
        li.textContent = s;
        elements.evalStrengthsList.appendChild(li);
      });
    } else {
      elements.evalStrengthsList.innerHTML = '<li>Baseline response provided.</li>';
    }

    // Weaknesses
    elements.evalWeaknessesList.innerHTML = '';
    if (evaluation.weaknesses && evaluation.weaknesses.length > 0) {
      evaluation.weaknesses.forEach(w => {
        const li = document.createElement('li');
        li.textContent = w;
        elements.evalWeaknessesList.appendChild(li);
      });
    } else {
      elements.evalWeaknessesList.innerHTML = '<li>No significant deficiencies noted.</li>';
    }

    // Missing Concepts
    elements.evalMissingTags.innerHTML = '';
    if (evaluation.missing_concepts && evaluation.missing_concepts.length > 0) {
      evaluation.missing_concepts.forEach(c => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = c;
        elements.evalMissingTags.appendChild(tag);
      });
      elements.missingConceptsContainer.style.display = 'block';
    } else {
      elements.missingConceptsContainer.style.display = 'none';
    }

    // Tip & Ideal Answer
    elements.evalImprovementTipText.textContent = evaluation.improvement_tip;
    elements.evalIdealAnswerText.textContent = evaluation.ideal_answer;

    // Check if this was the last question
    appState.isInterviewCompleted = evaluation.is_interview_completed;
    if (evaluation.is_interview_completed) {
      elements.nextBtnText.textContent = 'View Final Performance Report';
    } else {
      elements.nextBtnText.textContent = 'Proceed to Next Question';
    }

    // Update progress bar to current completion
    const newProgress = Math.round(((appState.currentQuestionIndex + 1) / appState.totalQuestions) * 100);
    elements.interviewProgressBar.style.width = `${newProgress}%`;
  }

  // Toggle Ideal Answer Box
  elements.toggleIdealBtn.addEventListener('click', () => {
    const isHidden = elements.idealAnswerContent.style.display === 'none';
    elements.idealAnswerContent.style.display = isHidden ? 'block' : 'none';
    elements.idealChevron.textContent = isHidden ? '▲' : '▼';
  });

  // Next Question / Finish Button
  elements.nextQuestionBtn.addEventListener('click', async () => {
    if (appState.isInterviewCompleted) {
      await fetchFinalResults();
    } else {
      // Advance to next question
      appState.currentQuestionIndex += 1;
      await fetchNextQuestion();
    }
  });

  // Fetch Next Question
  async function fetchNextQuestion() {
    try {
      const response = await fetch(`/api/interviews/${appState.interviewId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch next question (${response.status})`);
      }
      const data = await response.json();
      appState.currentQuestionIndex = data.current_question_index;
      appState.currentQuestion = data.current_question;
      renderInterviewScreen();
    } catch (err) {
      showError('Navigation Error', err.message || 'Could not load next question.');
    }
  }

  // Fetch Final Results and Show Report
  async function fetchFinalResults() {
    elements.nextQuestionBtn.disabled = true;
    elements.nextBtnText.textContent = 'Generating Performance Report...';

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
    } finally {
      elements.nextQuestionBtn.disabled = false;
      elements.nextBtnText.textContent = 'View Final Performance Report';
    }
  }

  // Render Performance Report
  function renderResultsScreen(report) {
    // Score & Gauge
    const pct = report.percentage_score;
    elements.reportPercentage.textContent = `${pct}%`;
    elements.reportScoreRatio.textContent = `${report.total_score}/${report.max_possible_score}`;
    elements.reportAvgScore.textContent = report.average_score.toFixed(1);

    // Animate SVG Gauge
    // Circumference = 2 * PI * r = 2 * 3.14159 * 50 = ~314.159
    const circumference = 314.159;
    const offset = circumference - (pct / 100) * circumference;
    setTimeout(() => {
      elements.gaugeMeter.style.strokeDashoffset = `${offset}`;
    }, 100);

    // Grade Badge
    elements.reportGradeBadge.textContent = report.grade;
    elements.reportGradeTitle.textContent = `${report.grade} Overall Performance`;
    elements.reportGradeDesc.textContent = report.grade_description;

    // Apply Grade Color Modifier
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
      elements.strongestQTitle.textContent = `Q${report.strongest_answer.question_number}: ${report.strongest_answer.question}`;
      elements.strongestQScore.textContent = `Score: ${report.strongest_answer.score}/10 (Correctness: ${report.strongest_answer.correctness_score}/4)`;
      elements.strongestQFeedback.textContent = report.strongest_answer.feedback;
    }

    if (report.weakest_answer) {
      elements.weakestQTitle.textContent = `Q${report.weakest_answer.question_number}: ${report.weakest_answer.question}`;
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

    // 3 Prioritized Recommendations
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

  // Render Question Review Accordion
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
            <div class="acc-sub-title">Rubric Component Breakdown</div>
            <div style="font-size: 0.85rem; color: #cbd5e1; font-family: var(--font-mono); margin-bottom: 8px;">
              Correctness: ${q.correctness_score}/4 &bull; Relevance: ${q.relevance_score}/2 &bull; Completeness: ${q.completeness_score}/2 &bull; Clarity: ${q.clarity_score}/2
            </div>
            <p style="font-size: 0.88rem; color: var(--text-muted);">${escapeHtml(q.feedback)}</p>
          </div>

          <div class="acc-sub-section">
            <div class="acc-sub-title">Actionable Recommendation</div>
            <p style="font-size: 0.88rem; color: var(--accent-cyan);">${escapeHtml(q.improvement_tip)}</p>
          </div>

          <div class="acc-sub-section" style="margin-bottom: 0;">
            <div class="acc-sub-title">Reference Model Answer</div>
            <p style="font-size: 0.86rem; color: #94a3b8; line-height: 1.5; font-style: italic;">${escapeHtml(q.ideal_answer)}</p>
          </div>
        </div>
      `;

      // Accordion toggle listener
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
    // Clear all in-memory interview variables
    appState.interviewId = null;
    appState.currentQuestionIndex = 0;
    appState.currentQuestion = null;
    appState.isInterviewCompleted = false;
    appState.finalReport = null;

    // Reset gauge
    elements.gaugeMeter.style.strokeDashoffset = '314';

    // Switch view
    switchView('setup');
  });

  // Modal dismiss
  elements.errorModalCloseBtn.addEventListener('click', hideError);
  elements.errorModal.addEventListener('click', (e) => {
    if (e.target === elements.errorModal) hideError();
  });

  // Initialize
  initSetupFormListeners();

})();
