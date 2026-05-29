/* =====================================================
   Skill Setu — resume.js
   AI Resume Analyser: upload, analyse, render results
   ===================================================== */

async function analyseResume() {
    const resumeText = document.getElementById('resumeText');
    const targetRole = document.getElementById('targetRole');
    const jobDesc    = document.getElementById('jobDescription');
    const btn        = document.getElementById('resumeBtn');
    const resultEl   = document.getElementById('resumeResult');

    if (!resumeText || !resultEl) return;

    const text = resumeText.value.trim();
    if (!text || text.length < 50) {
        shakeEl(resumeText);
        resumeText.focus();
        return;
    }

    setButtonLoading(btn, true);
    resultEl.innerHTML = buildResumeLoadingHTML();

    const loadingBar  = document.getElementById('dashLoadingBar');
    const loadingText = document.getElementById('dashLoadingText');
    const messages = [
        'Reading your resume...',
        'Checking ATS compatibility...',
        'Identifying keyword gaps...',
        'Evaluating experience & impact...',
        'Generating suggestions...',
        'Almost ready...'
    ];

    let msgIdx = 0, width = 0;
    const barInterval = setInterval(() => {
        width = Math.min(width + 5, 88);
        if (loadingBar) loadingBar.style.width = width + '%';
    }, 300);
    const msgInterval = setInterval(() => {
        msgIdx = (msgIdx + 1) % messages.length;
        if (loadingText) loadingText.textContent = messages[msgIdx];
    }, 1100);

    try {
        const res = await fetch('/analyse-resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                resume_text:      text,
                target_role:      targetRole ? targetRole.value : '',
                job_description:  jobDesc ? jobDesc.value.trim() : ''
            })
        });

        const data = await res.json();

        clearInterval(barInterval);
        clearInterval(msgInterval);
        if (loadingBar) loadingBar.style.width = '100%';

        await sleep(300);
        renderResumeResults(data, resultEl);

    } catch (err) {
        clearInterval(barInterval);
        clearInterval(msgInterval);
        resultEl.innerHTML = buildErrorHTML('Could not connect to the server. Make sure ANTHROPIC_API_KEY is set.');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ---- RENDER RESULTS ----

function renderResumeResults(data, container) {
    if (data.error) {
        container.innerHTML = buildErrorHTML(data.error);
        return;
    }

    let html = '';
    html += buildAtsScoreCard(data);
    html += buildStrengthsCard(data.strengths);
    html += buildImprovementsCard(data.improvements);
    html += buildKeywordsCard(data.keywords);
    html += buildSuggestionsCard(data.suggestions);

    container.innerHTML = html;

    requestAnimationFrame(() => {
        renderAtsDonut(data.ats_score);
        animateResumeBars(data.section_scores);
    });
}

// ---- CARD BUILDERS ----

function buildAtsScoreCard(data) {
    const score = data.ats_score || 0;
    const label = score >= 75 ? 'Strong Match' : score >= 50 ? 'Needs Work' : 'Major Gaps';
    const roleLabel = data.target_role ? `for ${escHtml(data.target_role)}` : 'Overall';

    const sections = data.section_scores || {};
    const sectionBars = Object.entries(sections).map(([name, val]) => `
        <div class="rs-bar-row">
            <span class="rs-bar-label">${escHtml(name)}</span>
            <div class="rs-bar-track">
                <div class="rs-bar-fill" data-val="${val}" style="width:0%"></div>
            </div>
            <span class="rs-bar-num">${val}%</span>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0s">
        <div class="out-section-header">
            <div class="out-icon">🎯</div>
            <h3>ATS Score ${roleLabel}</h3>
        </div>
        <div class="score-layout">
            <div class="score-chart-wrap">
                <canvas id="atsChart" width="160" height="160"></canvas>
            </div>
            <div class="score-details">
                <div class="score-number">${score}%</div>
                <div class="score-label">${label}</div>
                <div class="rs-summary-pill rs-pill-${score >= 75 ? 'green' : score >= 50 ? 'yellow' : 'red'}">
                    ${score >= 75 ? '✓ ATS-friendly' : score >= 50 ? '⚡ Improvable' : '✗ Needs revision'}
                </div>
            </div>
        </div>
        ${sectionBars ? `<div class="rs-bars">${sectionBars}</div>` : ''}
    </div>`;
}

function buildStrengthsCard(strengths) {
    if (!strengths || !strengths.length) return '';
    const items = strengths.map(s => `
        <div class="insight-item rs-strength-item">
            <div class="insight-bullet rs-strength-bullet">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                    <path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <span>${escHtml(s)}</span>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0.05s">
        <div class="out-section-header">
            <div class="out-icon">💪</div>
            <h3>Strengths</h3>
        </div>
        ${items}
    </div>`;
}

function buildImprovementsCard(improvements) {
    if (!improvements || !improvements.length) return '';
    const items = improvements.map(i => `
        <div class="insight-item rs-improve-item">
            <div class="insight-bullet rs-improve-bullet">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none">
                    <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <span>${escHtml(i)}</span>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0.1s">
        <div class="out-section-header">
            <div class="out-icon">⚠️</div>
            <h3>Areas to Improve</h3>
        </div>
        ${items}
    </div>`;
}

function buildKeywordsCard(keywords) {
    if (!keywords) return '';

    const presentPills = (keywords.present || []).map(k =>
        `<span class="rs-kw-pill rs-kw-present">${escHtml(k)}</span>`
    ).join('');

    const missingPills = (keywords.missing || []).map(k =>
        `<span class="rs-kw-pill rs-kw-missing">${escHtml(k)}</span>`
    ).join('');

    return `
    <div class="out-section" style="animation-delay:0.15s">
        <div class="out-section-header">
            <div class="out-icon">🔍</div>
            <h3>Keyword Analysis</h3>
        </div>
        ${presentPills ? `
        <div class="rs-kw-group">
            <div class="rs-kw-group-label rs-kw-label-green">✓ Found in resume</div>
            <div class="rs-kw-cloud">${presentPills}</div>
        </div>` : ''}
        ${missingPills ? `
        <div class="rs-kw-group" style="margin-top:14px">
            <div class="rs-kw-group-label rs-kw-label-red">✗ Missing — add these</div>
            <div class="rs-kw-cloud">${missingPills}</div>
        </div>` : ''}
    </div>`;
}

function buildSuggestionsCard(suggestions) {
    if (!suggestions || !suggestions.length) return '';

    const items = suggestions.map((s, i) => `
        <div class="rs-suggestion-item">
            <div class="rs-suggestion-num">${i + 1}</div>
            <span>${escHtml(s)}</span>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0.2s">
        <div class="out-section-header">
            <div class="out-icon">💡</div>
            <h3>Actionable Suggestions</h3>
        </div>
        <div class="rs-suggestions">${items}</div>
    </div>`;
}

// ---- LOADING ----

function buildResumeLoadingHTML() {
    return `
    <div class="loading-card">
        <div class="spin-ring" style="width:32px;height:32px;border-width:3px;"></div>
        <p id="dashLoadingText">Reading your resume...</p>
        <div class="loading-bar-wrap" style="max-width:320px;">
            <div class="loading-bar-fill" id="dashLoadingBar"></div>
        </div>
    </div>`;
}

// ---- CHARTS ----

function renderAtsDonut(score) {
    const canvas = document.getElementById('atsChart');
    if (!canvas || !window.Chart) return;
    if (canvas._chartInstance) canvas._chartInstance.destroy();

    const ctx = canvas.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 160, 0);

    if (score >= 75) {
        grad.addColorStop(0, '#10b981');
        grad.addColorStop(1, '#059669');
    } else if (score >= 50) {
        grad.addColorStop(0, '#f59e0b');
        grad.addColorStop(1, '#d97706');
    } else {
        grad.addColorStop(0, '#ef4444');
        grad.addColorStop(1, '#dc2626');
    }

    canvas._chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['ATS Score', 'Gap'],
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [grad, 'rgba(0,0,0,0.05)'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: false,
            cutout: '76%',
            animation: { animateRotate: true, duration: 1200, easing: 'easeInOutQuart' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(6,11,20,0.9)',
                    titleFont: { family: 'Plus Jakarta Sans', size: 13 },
                    bodyFont: { family: 'Inter', size: 12 },
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1
                }
            }
        }
    });
}

function animateResumeBars(sections) {
    if (!sections) return;
    document.querySelectorAll('.rs-bar-fill').forEach(bar => {
        const val = parseInt(bar.dataset.val || '0', 10);
        requestAnimationFrame(() => {
            bar.style.transition = 'width 1s cubic-bezier(0.4,0,0.2,1)';
            bar.style.width = val + '%';
        });
    });
}

/* =====================================================
   PDF upload + tab switching
   ===================================================== */

let currentMode = 'paste'; // 'paste' | 'upload'

function switchTab(mode) {
    currentMode = mode;
    document.getElementById('pasteMode').style.display  = mode === 'paste'  ? '' : 'none';
    document.getElementById('uploadMode').style.display = mode === 'upload' ? '' : 'none';
    document.getElementById('tabPaste').classList.toggle('active',  mode === 'paste');
    document.getElementById('tabUpload').classList.toggle('active', mode === 'upload');
}

function handlePdfSelect(input) {
    const file = input.files[0];
    if (!file) return;
    const inner = document.getElementById('pdfDropInner');
    inner.innerHTML = `
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M9 12l2 2 4-4" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="pdf-drop-text" style="color:var(--text-1)">${escHtml(file.name)}</p>
        <p class="pdf-drop-hint">${(file.size / 1024).toFixed(1)} KB — click to change</p>
    `;
    document.getElementById('pdfDropZone').style.borderColor = '#059669';
}

// Drag and drop support
document.addEventListener('DOMContentLoaded', () => {
    const zone = document.getElementById('pdfDropZone');
    if (!zone) return;

    zone.addEventListener('dragover', e => {
        e.preventDefault();
        zone.classList.add('pdf-drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('pdf-drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('pdf-drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            const input = document.getElementById('resumePdf');
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            handlePdfSelect(input);
        }
    });
});

// Override analyseResume to handle both modes
const _origAnalyseResume = window.analyseResume;
window.analyseResume = async function() {
    if (currentMode === 'upload') {
        await analyseResumePdf();
    } else {
        await _origAnalyseResume();
    }
};

async function analyseResumePdf() {
    const pdfInput   = document.getElementById('resumePdf');
    const targetRole = document.getElementById('targetRole');
    const jobDesc    = document.getElementById('jobDescription');
    const btn        = document.getElementById('resumeBtn');
    const resultEl   = document.getElementById('resumeResult');

    if (!pdfInput.files.length) {
        const zone = document.getElementById('pdfDropZone');
        if (zone) { zone.style.borderColor = '#ef4444'; setTimeout(() => zone.style.borderColor = '', 1200); }
        return;
    }

    setButtonLoading(btn, true);
    resultEl.innerHTML = buildResumeLoadingHTML();

    const loadingBar  = document.getElementById('dashLoadingBar');
    const loadingText = document.getElementById('dashLoadingText');
    const messages    = ['Reading PDF...', 'Extracting text...', 'Checking ATS compatibility...', 'Analysing keywords...', 'Almost ready...'];
    let msgIdx = 0, width = 0;
    const barInterval = setInterval(() => { width = Math.min(width + 4, 85); if (loadingBar) loadingBar.style.width = width + '%'; }, 300);
    const msgInterval = setInterval(() => { msgIdx = (msgIdx + 1) % messages.length; if (loadingText) loadingText.textContent = messages[msgIdx]; }, 1100);

    try {
        const formData = new FormData();
        formData.append('resume_pdf',     pdfInput.files[0]);
        formData.append('target_role',    targetRole ? targetRole.value : '');
        formData.append('job_description', jobDesc   ? jobDesc.value.trim() : '');

        const res  = await fetch('/analyse-resume', { method: 'POST', body: formData });
        const data = await res.json();

        clearInterval(barInterval); clearInterval(msgInterval);
        if (loadingBar) loadingBar.style.width = '100%';
        await sleep(300);
        renderResumeResults(data, resultEl);

    } catch (err) {
        clearInterval(barInterval); clearInterval(msgInterval);
        resultEl.innerHTML = buildErrorHTML('Could not process the PDF. Make sure pdfplumber is installed.');
    } finally {
        setButtonLoading(btn, false);
    }
}
