let currentScenarioId = null;

window.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    await loadScenarios();
});

function applyTheme(theme) {
    if (theme === 'system') {
        const darkMq = window.matchMedia('(prefers-color-scheme: dark)');
        document.body.setAttribute('data-theme', darkMq.matches ? 'dark' : 'light');
    } else {
        document.body.setAttribute('data-theme', theme);
    }
}

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();

        document.getElementById('themeSelect').value = data.theme || 'system';
        document.getElementById('practiceLangSelect').value = data.practice_language || 'Japanese';
        document.getElementById('uiLangSelect').value = data.ui_language || 'English';
        document.getElementById('score-display').innerText = `Score: ${data.score || 0}`;

        const modelToSelect = data.model || 'gemma3:4b';

        applyTheme(data.theme || 'system');

        // loadModels will populate the select and set the correct value
        await loadModels(modelToSelect);
    } catch (e) {
        console.warn("Failed loading settings, using defaults.");
        applyTheme('system');
    }
}

async function saveSettings() {
    const theme = document.getElementById('themeSelect').value;
    const model = document.getElementById('modelSelect').value;
    const practice_language = document.getElementById('practiceLangSelect').value;
    const ui_language = document.getElementById('uiLangSelect').value;

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme, model, practice_language, ui_language })
        });
        applyTheme(theme);
        closeSettings();
        generateScenarios();
    } catch (e) {
        console.error(e);
        alert("Failed to save settings");
    }
}

async function loadModels(selectedModel) {
    const select = document.getElementById('modelSelect');
    // Always reset the dropdown so it never shows stale hardcoded HTML values
    select.innerHTML = '';

    try {
        const res = await fetch('/api/models');
        if (!res.ok) throw new Error('Failed to fetch models');
        const data = await res.json();
        const models = data.models || [];

        // Populate whatever the API returned
        models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.name;
            opt.innerText = m.parameter_size ? `${m.name} (${m.parameter_size})` : m.name;
            select.appendChild(opt);
        });

        // Always ensure the currently saved model is present and selected,
        // even if Ollama returned an empty list or the model isn't in it.
        const names = models.map(m => m.name);
        if (selectedModel && !names.includes(selectedModel)) {
            const opt = document.createElement('option');
            opt.value = selectedModel;
            opt.innerText = `${selectedModel} (saved)`;
            select.appendChild(opt);
        }
        if (selectedModel) {
            select.value = selectedModel;
        }
    } catch (e) {
        console.warn("Failed loading models from API:", e);
        // On failure, still show the saved model so the UI is consistent
        if (selectedModel) {
            const opt = document.createElement('option');
            opt.value = selectedModel;
            opt.innerText = `${selectedModel} (saved)`;
            select.appendChild(opt);
            select.value = selectedModel;
        }
    }
}

async function loadScenarios() {
    const container = document.getElementById('scenarios-container');
    const loadingObj = document.getElementById('scenarios-loading');
    const errorBanner = document.getElementById('error-banner-dashboard');
    const regenBtn = document.getElementById('regenerateBtn');

    container.innerHTML = '';
    errorBanner.classList.add('hidden');
    loadingObj.classList.remove('hidden');
    regenBtn.disabled = true;

    try {
        const res = await fetch('/api/scenarios');
        const data = await res.json();

        loadingObj.classList.add('hidden');
        regenBtn.disabled = false;

        if (!data.scenarios || data.scenarios.length === 0) {
            // Automatically generate scenarios if there are none, removing the burden from the server startup!
            generateScenarios();
            return;
        }

        data.scenarios.forEach(scen => {
            const card = document.createElement('div');
            card.className = 'scenario-card';
            card.onclick = () => startChat(scen);

            const img = document.createElement('img');
            img.src = `/api/clipart/${scen.clipart}`;

            const textDiv = document.createElement('div');
            const h3 = document.createElement('h3');
            h3.innerText = scen.setting;
            const p = document.createElement('p');
            p.innerText = scen.goal;

            textDiv.appendChild(h3);
            textDiv.appendChild(p);
            card.appendChild(img);
            card.appendChild(textDiv);
            container.appendChild(card);
        });
    } catch (e) {
        loadingObj.classList.add('hidden');
        regenBtn.disabled = false;
        errorBanner.innerText = 'Failed to load scenarios. Make sure backend is running.';
        errorBanner.classList.remove('hidden');
    }
}

async function generateScenarios() {
    const loadingObj = document.getElementById('scenarios-loading');
    const regenBtn = document.getElementById('regenerateBtn');
    const container = document.getElementById('scenarios-container');
    const errorBanner = document.getElementById('error-banner-dashboard');

    container.innerHTML = '';
    errorBanner.classList.add('hidden');
    loadingObj.classList.remove('hidden');
    regenBtn.disabled = true;

    try {
        await fetch('/api/scenarios/generate', { method: 'POST' });
        await loadScenarios();
    } catch (e) {
        loadingObj.classList.add('hidden');
        regenBtn.disabled = false;
        errorBanner.innerText = 'Error generating scenarios: model took too long or failed.';
        errorBanner.classList.remove('hidden');
    }
}

function startChat(scenario) {
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('chat').classList.remove('hidden');

    document.getElementById('scenario-clipart').src = `/api/clipart/${scenario.clipart}`;
    document.getElementById('scenario-setting').innerText = scenario.setting;
    document.getElementById('scenario-goal').innerText = scenario.goal;
    document.getElementById('scenario-description').innerText = scenario.description || '';

    currentScenarioId = scenario.id;
    document.getElementById('messages').innerHTML = '';

    // Reset summary panel state for new chat
    document.getElementById('chat-summary-panel').classList.add('hidden');
    document.getElementById('chat-summary-content').innerHTML = '';
    document.getElementById('backToDashboardBtn').classList.add('hidden');
    document.getElementById('chat-input-area').classList.remove('hidden');
    document.getElementById('userInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('hintBtn').disabled = false;
}

async function returnToDashboard() {
    document.getElementById('chat').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    currentScenarioId = null;
    await loadSettings();
    await loadScenarios();
}

async function abandonChat() {
    if (!confirm("Are you sure you want to abandon this chat?")) return;
    try {
        await fetch(`/api/chat/abandon`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario_id: currentScenarioId })
        });
    } catch (e) { }

    document.getElementById('chat').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    currentScenarioId = null;
}

function handleEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    appendMessage('User', msg);
    document.getElementById('typing-indicator').classList.remove('hidden');

    try {
        const res = await fetch('/api/chat/turn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario_id: currentScenarioId,
                message: msg
            })
        });
        const data = await res.json();

        document.getElementById('typing-indicator').classList.add('hidden');

        if (data.bot_message) {
            appendMessage('Bot', data.bot_message);
        }

        if (data.status === 'REACHED') {
            // Lock input
            document.getElementById('userInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('hintBtn').disabled = true;
            document.getElementById('chat-input-area').classList.add('hidden');

            // Show the summary panel with a loading state
            const panel = document.getElementById('chat-summary-panel');
            const loading = document.getElementById('chat-summary-loading');
            const content = document.getElementById('chat-summary-content');
            panel.classList.remove('hidden');
            loading.classList.remove('hidden');
            content.innerHTML = '';
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            if (data.summary) {
                loading.classList.add('hidden');
                content.innerHTML = DOMPurify.sanitize(marked.parse(data.summary));
            } else {
                loading.classList.add('hidden');
                const em = document.createElement('em');
                em.className = 'summary-error';
                em.textContent = 'Summary could not be generated.';
                content.appendChild(em);
            }

            document.getElementById('backToDashboardBtn').classList.remove('hidden');
        }
    } catch (e) {
        document.getElementById('typing-indicator').classList.add('hidden');
        alert("Failed to get response");
    }
}

function appendMessage(speaker, content) {
    const container = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${speaker.toLowerCase()}`;

    const label = document.createElement('span');
    label.className = 'role-label';
    label.innerText = speaker;

    const text = document.createElement('div');
    text.className = 'content';
    if (typeof DOMPurify !== 'undefined' && typeof marked !== 'undefined') {
        text.innerHTML = DOMPurify.sanitize(marked.parse(content));
    } else {
        text.innerHTML = content;
    }

    div.appendChild(label);
    div.appendChild(text);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function getHint() {
    document.getElementById('typing-indicator').classList.remove('hidden');
    try {
        const res = await fetch('/api/chat/hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario_id: currentScenarioId })
        });
        const data = await res.json();
        document.getElementById('typing-indicator').classList.add('hidden');
        document.getElementById('hint-content').innerHTML = DOMPurify.sanitize(marked.parse(data.hint));
        document.getElementById('hintModal').classList.remove('hidden');
    } catch (e) {
        document.getElementById('typing-indicator').classList.add('hidden');
        alert("Hint failed to load");
    }
}

function closeHint() { document.getElementById('hintModal').classList.add('hidden'); }

async function openSettings() {
    const settings = await fetch('/api/settings').then(r => r.json()).catch(() => ({}));
    const currentModel = settings.model || document.getElementById('modelSelect').value || 'gemma3:4b';
    document.getElementById('settingsModal').classList.remove('hidden');
    await loadModels(currentModel);
}

function closeSettings() { document.getElementById('settingsModal').classList.add('hidden'); }

// --- HISTORY LOGIC ---

const LANGUAGE_FLAGS = {
    'Japanese': '🇯🇵',
    'Spanish': '🇪🇸',
    'Turkish': '🇹🇷',
    'Chinese': '🇨🇳',
    'French': '🇫🇷',
    'German': '🇩🇪',
    'Italian': '🇮🇹',
    'Portuguese': '🇧🇷',
    'Korean': '🇰🇷',
    'Arabic': '🇸🇦',
    'Russian': '🇷🇺',
    'Dutch': '🇳🇱',
    'Polish': '🇵🇱',
    'Hindi': '🇮🇳',
};

function langBadge(language) {
    if (!language) return '';
    const flag = LANGUAGE_FLAGS[language] || '🌐';
    return `<span class="history-badge lang-badge">${flag} ${language}</span>`;
}

function modelBadge(model) {
    if (!model) return '';
    // Shorten the model name for display (strip tag if long)
    const display = model.length > 22 ? model.slice(0, 20) + '…' : model;
    return `<span class="history-badge model-badge">${display}</span>`;
}

async function openHistory() {
    document.getElementById('historyModal').classList.remove('hidden');
    const container = document.getElementById('history-container');
    const loading = document.getElementById('history-loading');

    container.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const res = await fetch('/api/history');
        const data = await res.json();

        loading.classList.add('hidden');

        if (!data.history || data.history.length === 0) {
            const div = document.createElement('div');
            div.className = 'summary-error';
            div.textContent = 'No completed conversations yet.';
            container.appendChild(div);
            return;
        }

        data.history.forEach(item => {
            const date = new Date(item.timestamp).toLocaleString();
            const row = document.createElement('div');
            row.className = 'history-row';

            const btn = document.createElement('button');
            btn.className = 'secondary history-row-btn';

            const titleSpan = document.createElement('span');
            titleSpan.className = 'history-row-title';
            titleSpan.textContent = item.scenario_id.replace(/_/g, ' ');

            const metaSpan = document.createElement('span');
            metaSpan.className = 'history-row-meta';
            metaSpan.innerHTML = langBadge(item.practice_language) + modelBadge(item.model);

            const dateSpan = document.createElement('span');
            dateSpan.className = 'history-row-date';
            dateSpan.textContent = date;

            metaSpan.appendChild(dateSpan);
            btn.appendChild(titleSpan);
            btn.appendChild(metaSpan);

            btn.onclick = () => viewHistoryItem(item.id, item.practice_language, item.model);

            const delBtn = document.createElement('button');
            delBtn.className = 'danger-btn';
            delBtn.title = 'Delete this conversation';
            delBtn.innerHTML = '🗑';
            delBtn.onclick = async (e) => {
                e.stopPropagation();
                if (!confirm('Delete this conversation?')) return;
                await fetch(`/api/history/${item.id}`, { method: 'DELETE' });
                row.remove();
                if (document.getElementById('history-container').children.length === 0) {
                    const emptyDiv = document.createElement('div');
                    emptyDiv.className = 'summary-error';
                    emptyDiv.textContent = 'No completed conversations yet.';
                    document.getElementById('history-container').appendChild(emptyDiv);
                }
            };

            row.appendChild(btn);
            row.appendChild(delBtn);
            container.appendChild(row);
        });
    } catch (e) {
        loading.classList.add('hidden');
        const err = document.createElement('div');
        err.className = 'error-banner';
        err.textContent = 'Failed to load history';
        container.appendChild(err);
    }
}

function closeHistory() {
    document.getElementById('historyModal').classList.add('hidden');
}

async function clearAllHistory() {
    if (!confirm('Delete ALL conversation history? This cannot be undone.')) return;
    await fetch('/api/history', { method: 'DELETE' });
    openHistory();
}

async function viewHistoryItem(historyId, practiceLanguage, model) {
    document.getElementById('historyModal').classList.add('hidden');
    document.getElementById('historyDetailModal').classList.remove('hidden');
    const container = document.getElementById('history-detail-messages');
    const summaryLoading = document.getElementById('history-summary-loading');
    const summaryContent = document.getElementById('history-summary-content');

    // Inject language + model badges into the transcript column heading
    const transcriptHeading = document.querySelector('.history-col-transcript .history-col-heading');
    if (transcriptHeading) {
        transcriptHeading.innerHTML = `Transcript ${langBadge(practiceLanguage)} ${modelBadge(model)}`;
    }

    const em = document.createElement('em');
    em.className = 'summary-error';
    em.textContent = 'Loading transcript...';
    container.innerHTML = '';
    container.appendChild(em);

    summaryContent.innerHTML = '';
    summaryLoading.classList.remove('hidden');

    // Fetch transcript and summary in parallel
    try {
        const [transcriptRes, summaryRes] = await Promise.all([
            fetch(`/api/history/${historyId}`),
            fetch(`/api/history/${historyId}/summary`)
        ]);
        const transcriptData = await transcriptRes.json();
        const summaryData = await summaryRes.json();

        // Render transcript
        container.innerHTML = '';
        if (!transcriptData.conversation || transcriptData.conversation.length === 0) {
            container.textContent = 'Empty transcript.';
        } else {
            transcriptData.conversation.forEach(turn => {
                const div = document.createElement('div');
                div.className = `message ${turn.speaker.toLowerCase()}`;

                const label = document.createElement('span');
                label.className = 'role-label';
                label.innerText = turn.speaker;

                const text = document.createElement('div');
                text.className = 'content';
                text.innerHTML = DOMPurify.sanitize(marked.parse(turn.content));

                div.appendChild(label);
                div.appendChild(text);
                container.appendChild(div);
            });
        }

        // Render summary
        summaryLoading.classList.add('hidden');
        if (summaryData.summary) {
            summaryContent.innerHTML = DOMPurify.sanitize(marked.parse(summaryData.summary));
        } else {
            const em = document.createElement('em');
            em.className = 'summary-error';
            em.textContent = 'No breakdown available for this session.';
            summaryContent.appendChild(em);
        }

    } catch (e) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-banner';
        errorDiv.textContent = 'Failed to load transcript';
        container.innerHTML = '';
        container.appendChild(errorDiv);

        summaryLoading.classList.add('hidden');
        const em = document.createElement('em');
        em.className = 'summary-error';
        em.textContent = 'Could not load breakdown.';
        summaryContent.appendChild(em);
    }
}

function closeHistoryDetail() {
    document.getElementById('historyDetailModal').classList.add('hidden');
    document.getElementById('historyModal').classList.remove('hidden');
}
