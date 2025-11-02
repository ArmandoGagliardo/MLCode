// Brev Client Frontend JavaScript

// Configuration
let config = {
    apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:5000',
    apiKey: localStorage.getItem('apiKey') || 'dev-key-12345'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
    updateTemperatureValue();

    // Update temperature display
    document.getElementById('temperature').addEventListener('input', updateTemperatureValue);
});

// ==========================================
// Tab Management
// ==========================================

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + 'Tab').classList.add('active');
    event.target.classList.add('active');
}

// ==========================================
// API Communication
// ==========================================

async function makeRequest(endpoint, data) {
    showLoading(true);
    try {
        const response = await fetch(`${config.apiUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${config.apiKey}`
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        return result;

    } catch (error) {
        console.error('Request error:', error);
        throw error;
    } finally {
        showLoading(false);
    }
}

async function checkConnection() {
    try {
        const response = await fetch(`${config.apiUrl}/health`);
        const data = await response.json();

        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');

        if (data.status === 'healthy') {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
        }
    } catch (error) {
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        statusDot.className = 'status-dot disconnected';
        statusText.textContent = 'Connection Error';
    }
}

// ==========================================
// Code Generation
// ==========================================

async function generateCode() {
    const prompt = document.getElementById('prompt').value.trim();

    if (!prompt) {
        showError('generateError', 'Inserisci un prompt');
        return;
    }

    const data = {
        prompt: prompt,
        language: document.getElementById('language').value,
        max_length: parseInt(document.getElementById('maxLength').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        top_p: 0.9
    };

    try {
        const result = await makeRequest('/api/generate', data);

        // Display result
        document.getElementById('generatedCode').textContent = result.data.code || result.data.generated_text || 'No code generated';
        document.getElementById('generateResult').style.display = 'block';
        document.getElementById('generateError').style.display = 'none';

    } catch (error) {
        showError('generateError', `Errore: ${error.message}`);
        document.getElementById('generateResult').style.display = 'none';
    }
}

// ==========================================
// Security Analysis
// ==========================================

async function analyzeCode() {
    const code = document.getElementById('codeToAnalyze').value.trim();

    if (!code) {
        showError('securityError', 'Inserisci del codice da analizzare');
        return;
    }

    const data = {
        code: code,
        language: document.getElementById('analysisLanguage').value,
        scan_type: document.getElementById('scanType').value
    };

    try {
        const result = await makeRequest('/api/security', data);

        // Display vulnerabilities
        const vulnerabilities = result.data.vulnerabilities || [];
        const container = document.getElementById('vulnerabilities');
        container.innerHTML = '';

        if (vulnerabilities.length === 0) {
            container.innerHTML = '<p style="color: var(--success-color);">✓ Nessuna vulnerabilità trovata!</p>';
        } else {
            vulnerabilities.forEach(vuln => {
                const item = createVulnerabilityElement(vuln);
                container.appendChild(item);
            });
        }

        document.getElementById('securityResult').style.display = 'block';
        document.getElementById('securityError').style.display = 'none';

    } catch (error) {
        showError('securityError', `Errore: ${error.message}`);
        document.getElementById('securityResult').style.display = 'none';
    }
}

function createVulnerabilityElement(vuln) {
    const div = document.createElement('div');
    div.className = `vulnerability-item ${vuln.severity}`;

    div.innerHTML = `
        <div class="vulnerability-header">
            <span class="vulnerability-type">${vuln.type || 'Unknown'}</span>
            <span class="severity-badge ${vuln.severity}">${vuln.severity}</span>
        </div>
        <div style="color: #ccc; margin-bottom: 10px;">${vuln.description || 'No description'}</div>
        <div style="font-size: 0.9rem; color: #999;">
            <strong>File:</strong> ${vuln.file || 'N/A'}<br>
            <strong>Line:</strong> ${vuln.line || 'N/A'}<br>
            <strong>Fix:</strong> ${vuln.fix || 'No fix available'}
        </div>
    `;

    return div;
}

// ==========================================
// Batch Generation
// ==========================================

async function batchGenerate() {
    const promptsText = document.getElementById('batchPrompts').value.trim();

    if (!promptsText) {
        showError('batchError', 'Inserisci almeno un prompt');
        return;
    }

    const prompts = promptsText.split('\n').filter(p => p.trim());

    const data = {
        prompts: prompts,
        language: document.getElementById('batchLanguage').value
    };

    try {
        const result = await makeRequest('/api/batch', data);

        // Display results
        const container = document.getElementById('batchCodes');
        container.innerHTML = '';

        const results = result.data.results || [];

        results.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'code-block';
            div.style.marginBottom = '20px';

            div.innerHTML = `
                <button class="copy-btn" onclick="copyCode('batchCode${index}')">📋 Copy</button>
                <h4 style="color: var(--primary-color); margin-bottom: 10px;">Prompt ${index + 1}: ${prompts[index]}</h4>
                <pre><code id="batchCode${index}">${item.code || item.generated_text || 'No code generated'}</code></pre>
            `;

            container.appendChild(div);
        });

        document.getElementById('batchResult').style.display = 'block';
        document.getElementById('batchError').style.display = 'none';

    } catch (error) {
        showError('batchError', `Errore: ${error.message}`);
        document.getElementById('batchResult').style.display = 'none';
    }
}

// ==========================================
// Utility Functions
// ==========================================

function updateTemperatureValue() {
    const value = document.getElementById('temperature').value;
    document.getElementById('tempValue').textContent = value;
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.style.display = 'block';

    setTimeout(() => {
        errorElement.style.display = 'none';
    }, 5000);
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function copyCode(elementId) {
    const code = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(code).then(() => {
        // Show feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = 'var(--success-color)';

        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    });
}

// ==========================================
// Settings
// ==========================================

function showSettings() {
    const modal = document.getElementById('settingsModal');
    modal.classList.add('active');

    // Load current settings
    document.getElementById('apiUrl').value = config.apiUrl;
    document.getElementById('apiKey').value = config.apiKey;
}

function closeSettings() {
    const modal = document.getElementById('settingsModal');
    modal.classList.remove('active');
}

function saveSettings() {
    config.apiUrl = document.getElementById('apiUrl').value.trim();
    config.apiKey = document.getElementById('apiKey').value.trim();

    // Save to localStorage
    localStorage.setItem('apiUrl', config.apiUrl);
    localStorage.setItem('apiKey', config.apiKey);

    closeSettings();
    checkConnection();

    alert('Settings saved!');
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('settingsModal');
    if (event.target == modal) {
        closeSettings();
    }
}
