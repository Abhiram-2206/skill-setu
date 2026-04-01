/* =====================================================
   SkillPilot AI — script.js
   Handles: scroll reveal, navbar, dashboard generation
   ===================================================== */

// ---- NAVBAR SCROLL EFFECT ----
(function () {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;

    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 20);
    }, { passive: true });
})();

// ---- SCROLL REVEAL ----
(function () {
    const els = document.querySelectorAll('.reveal');
    if (!els.length) return;

    const obs = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('visible');
                obs.unobserve(e.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    els.forEach(el => obs.observe(el));
})();

// ---- DASHBOARD GENERATE ----
async function generatePath() {
    const skillsInput = document.getElementById('skills');
    const roleInput   = document.getElementById('role');
    const btn         = document.getElementById('generateBtn');
    const resultEl    = document.getElementById('result');

    if (!skillsInput || !roleInput || !resultEl) return;

    const skills = skillsInput.value
        .split(',')
        .map(s => s.trim())
        .filter(s => s.length > 0);

    const role = roleInput.value;

    if (skills.length === 0) {
        shakeEl(skillsInput);
        return;
    }

    // Loading state
    setButtonLoading(btn, true);
    resultEl.innerHTML = buildLoadingHTML();

    const loadingBar  = document.getElementById('dashLoadingBar');
    const loadingText = document.getElementById('dashLoadingText');
    const messages = [
        'Analyzing your skills...',
        'Mapping role requirements...',
        'Generating your roadmap...',
        'Building timeline...',
        'Almost there...'
    ];
    let msgIdx = 0;
    let width  = 0;

    const barInterval = setInterval(() => {
        width = Math.min(width + 7, 88);
        if (loadingBar) loadingBar.style.width = width + '%';
    }, 200);

    const msgInterval = setInterval(() => {
        msgIdx = (msgIdx + 1) % messages.length;
        if (loadingText) loadingText.textContent = messages[msgIdx];
    }, 900);

    try {
        const res  = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skills, role })
        });
        const data = await res.json();

        clearInterval(barInterval);
        clearInterval(msgInterval);
        if (loadingBar) loadingBar.style.width = '100%';

        await sleep(300);

        renderResults(data, resultEl);
    } catch (err) {
        clearInterval(barInterval);
        clearInterval(msgInterval);
        resultEl.innerHTML = buildErrorHTML(err.message);
    } finally {
        setButtonLoading(btn, false);
    }
}

function renderResults(data, container) {
    let html = '';

    // 1. Score
    html += buildScoreCard(data);

    // 2. AI Insights
    if (data.feedback && data.feedback.length) {
        html += buildInsightsCard(data.feedback);
    }

    // 3. Roadmap
    if (data.learning_path && data.learning_path.length) {
        html += buildRoadmapCard(data.learning_path);
    }

    // 4. Timeline
    if (data.timeline && data.timeline.length) {
        html += buildTimelineCard(data.timeline);
    }

    // 5. Courses
    if (data.courses && Object.keys(data.courses).length) {
        html += buildCoursesSection(data.courses);
    }

    container.innerHTML = html;

    // Animate chart after DOM render
    requestAnimationFrame(() => {
        renderDoughnut(data.score);
        animateConfBar(data.confidence);
    });
}

// ---- CARD BUILDERS ----

function buildScoreCard(data) {
    return `
    <div class="out-section" style="animation-delay:0s">
        <div class="out-section-header">
            <div class="out-icon">📊</div>
            <h3>Skill Score</h3>
        </div>
        <div class="score-layout">
            <div class="score-chart-wrap">
                <canvas id="skillChart" width="160" height="160"></canvas>
            </div>
            <div class="score-details">
                <div class="score-number">${data.score}%</div>
                <div class="score-label">Match with ${escHtml(document.getElementById('role')?.value || 'role')}</div>
                <div class="confidence-row">
                    <span>Confidence</span>
                    <div class="conf-bar">
                        <div class="conf-fill" id="confFill" style="width:0%"></div>
                    </div>
                    <span id="confNum">${data.confidence}%</span>
                </div>
            </div>
        </div>
    </div>`;
}

function buildInsightsCard(feedback) {
    const items = feedback.map(f => `
        <div class="insight-item">
            <div class="insight-bullet">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="5" fill="currentColor"/>
                </svg>
            </div>
            <span>${escHtml(f)}</span>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0.05s">
        <div class="out-section-header">
            <div class="out-icon">🧠</div>
            <h3>AI Insights</h3>
        </div>
        ${items}
    </div>`;
}

function buildRoadmapCard(path) {
    const items = path.map(item => `
        <div class="roadmap-item">
            <div class="roadmap-step">${item.step}</div>
            <span class="roadmap-skill">${escHtml(item.skill)}</span>
            <span class="priority-badge priority-${item.priority.toLowerCase()}">${item.priority}</span>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0.1s">
        <div class="out-section-header">
            <div class="out-icon">📌</div>
            <h3>Learning Roadmap</h3>
        </div>
        <div class="roadmap-list">${items}</div>
    </div>`;
}

function buildTimelineCard(timeline) {
    const rows = timeline.map(t => `
        <div class="timeline-row">
            <div class="timeline-dot">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                    <path d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="timeline-content">
                <div class="timeline-month">${escHtml(t.month)}</div>
                <div class="timeline-skills">${t.skills.map(s => escHtml(s)).join(', ')}</div>
            </div>
        </div>
    `).join('');

    return `
    <div class="out-section" style="animation-delay:0.15s">
        <div class="out-section-header">
            <div class="out-icon">🗓️</div>
            <h3>Monthly Timeline</h3>
        </div>
        <div class="timeline">${rows}</div>
    </div>`;
}

function buildCoursesSection(courses) {
    let html = `
    <div class="out-section" style="animation-delay:0.2s">
        <div class="out-section-header">
            <div class="out-icon">📚</div>
            <h3>Course Recommendations</h3>
        </div>`;

    for (const skill in courses) {
        html += `<div style="margin-bottom:20px">
            <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:700;
                color:var(--text-1);margin-bottom:12px;padding-bottom:8px;
                border-bottom:1px solid var(--border);">
                ${escHtml(skill)}
            </div>`;

        const c = courses[skill];

        if (c.free && c.free.length) {
            html += `<div class="courses-header">🟢 Free</div>`;
            c.free.forEach(x => {
                html += `<a href="${escHtml(x.link)}" target="_blank" rel="noopener" class="course-link">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    ${escHtml(x.title)}
                    <span class="course-free-tag">FREE</span>
                </a>`;
            });
        }

        if (c.paid && c.paid.length) {
            html += `<div class="courses-header">💰 Paid</div>`;
            c.paid.forEach(x => {
                html += `<a href="${escHtml(x.link)}" target="_blank" rel="noopener" class="course-link">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    ${escHtml(x.title)}
                </a>`;
            });
        }

        html += `</div>`;
    }

    html += `</div>`;
    return html;
}

function buildLoadingHTML() {
    return `
    <div class="loading-card">
        <div class="spin-ring" style="width:32px;height:32px;border-width:3px;"></div>
        <p id="dashLoadingText">Analyzing your skills...</p>
        <div class="loading-bar-wrap" style="max-width:320px;">
            <div class="loading-bar-fill" id="dashLoadingBar"></div>
        </div>
    </div>`;
}

function buildErrorHTML(msg) {
    return `
    <div class="out-section" style="border-color:rgba(239,68,68,0.3);">
        <div class="out-section-header">
            <div class="out-icon">⚠️</div>
            <h3>Something went wrong</h3>
        </div>
        <p style="color:var(--text-2);font-size:14px;">${escHtml(msg || 'Could not connect to the server.')}</p>
    </div>`;
}

// ---- CHART ----
function renderDoughnut(score) {
    const canvas = document.getElementById('skillChart');
    if (!canvas || !window.Chart) return;

    // Destroy existing chart if any
    if (canvas._chartInstance) canvas._chartInstance.destroy();

    const ctx = canvas.getContext('2d');
    const grad = ctx.createLinearGradient(0, 0, 160, 0);
    grad.addColorStop(0, '#3b82f6');
    grad.addColorStop(1, '#a78bfa');

    canvas._chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Matched', 'Gap'],
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [grad, 'rgba(255,255,255,0.06)'],
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
                    titleFont: { family: 'Syne', size: 13 },
                    bodyFont: { family: 'DM Sans', size: 12 },
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1
                }
            }
        }
    });
}

function animateConfBar(confidence) {
    const fill = document.getElementById('confFill');
    if (!fill) return;
    requestAnimationFrame(() => {
        fill.style.width = confidence + '%';
    });
}

// ---- UTILS ----
function setButtonLoading(btn, isLoading) {
    if (!btn) return;
    const textEl    = btn.querySelector('.btn-text');
    const loadingEl = btn.querySelector('.btn-loading');
    if (!textEl || !loadingEl) return;

    btn.disabled = isLoading;
    textEl.style.display    = isLoading ? 'none' : 'flex';
    loadingEl.style.display = isLoading ? 'flex' : 'none';
}

function shakeEl(el) {
    el.style.animation = 'shake 0.4s ease';
    el.addEventListener('animationend', () => {
        el.style.animation = '';
        el.focus();
    }, { once: true });
}

function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

// Inject shake keyframe once
(function () {
    if (document.getElementById('sp-keyframes')) return;
    const s = document.createElement('style');
    s.id = 'sp-keyframes';
    s.textContent = `
        @keyframes shake {
            0%,100%{transform:translateX(0)}
            20%{transform:translateX(-6px)}
            40%{transform:translateX(6px)}
            60%{transform:translateX(-4px)}
            80%{transform:translateX(4px)}
        }
    `;
    document.head.appendChild(s);
})();
