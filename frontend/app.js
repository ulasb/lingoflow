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
        loadScenarios();
    } catch (e) {
        console.error(e);
        alert("Failed to save settings");
    }
}

async function loadModels(selectedModel) {
    const select = document.getElementById('modelSelect');
    try {
        const res = await fetch('/api/models');
        if (!res.ok) throw new Error('Failed to fetch models');
        const data = await res.json();
        if (data.models && data.models.length > 0) {
            select.innerHTML = '';
            data.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.name;
                opt.innerText = m.parameter_size ? `${m.name} (${m.parameter_size})` : m.name;
                select.appendChild(opt);
            });
            const names = data.models.map(m => m.name);
            if (names.includes(selectedModel)) {
                select.value = selectedModel;
            } else if (selectedModel) {
                // Current saved model not in list — add it so selection isn't lost
                const opt = document.createElement('option');
                opt.value = selectedModel;
                opt.innerText = `${selectedModel} (saved)`;
                select.appendChild(opt);
                select.value = selectedModel;
            }
        }
    } catch (e) {
        console.warn("Failed loading models from API:", e);
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
            setTimeout(() => {
                alert("Goal reached! You did great! Back to dashboard.");
                document.getElementById('chat').classList.add('hidden');
                document.getElementById('dashboard').classList.remove('hidden');
                loadSettings();
                loadScenarios();
            }, 1000);
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
            container.innerHTML = '<div style="color: var(--text-secondary);">No completed conversations yet.</div>';
            return;
        }

        data.history.forEach(item => {
            const date = new Date(item.timestamp).toLocaleString();
            const btn = document.createElement('button');
            btn.className = 'secondary';
            btn.style.textAlign = 'left';
            btn.style.width = '100%';
            btn.innerHTML = `<strong>${DOMPurify.sanitize(item.scenario_id.replace(/_/g, ' '))}</strong> - ${date}`;
            btn.onclick = () => viewHistoryItem(item.id);
            container.appendChild(btn);
        });
    } catch (e) {
        loading.classList.add('hidden');
        container.innerHTML = '<div class="error-banner">Failed to load history</div>';
    }
}

function closeHistory() {
    document.getElementById('historyModal').classList.add('hidden');
}

async function viewHistoryItem(historyId) {
    document.getElementById('historyModal').classList.add('hidden');
    document.getElementById('historyDetailModal').classList.remove('hidden');
    const container = document.getElementById('history-detail-messages');
    container.innerHTML = 'Loading transcript...';

    try {
        const res = await fetch(`/api/history/${historyId}`);
        const data = await res.json();

        container.innerHTML = '';

        if (!data.conversation || data.conversation.length === 0) {
            container.innerHTML = 'Empty transcript.';
            return;
        }

        data.conversation.forEach(turn => {
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

    } catch (e) {
        container.innerHTML = '<div class="error-banner">Failed to load transcript</div>';
    }
}

function closeHistoryDetail() {
    document.getElementById('historyDetailModal').classList.add('hidden');
    document.getElementById('historyModal').classList.remove('hidden');
}
