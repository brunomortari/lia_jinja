/**
 * Sistema LIA - Artifact Chat Core
 * =================================
 * JavaScript reutilizável para páginas de geração de artefatos com IA
 * Usado por: DFD, ETP, TR, Edital, PGR, etc.
 * 
 * USAGE:
 * 1. Include this script in your artifact page
 * 2. Define ARTIFACT_CONFIG before including this script
 * 3. Define ARTIFACT_FIELDS with the fields for your artifact
 * 4. Optionally override functions as needed
 */

console.log('[Artifact Chat] Core script loaded');

// ========== CORE STATE ==========
let chatHistory = [];
let currentPhase = 'preparation';
window.artifactData = {};
let readyToGenerate = false;
let hasMessages = false;
let chatAttachments = []; // Global attachments (Main Chat)
let isGenerating = false;
let currentRegenerateField = null;
let deepResearchActive = false; // Deep Research State

// Knowledge Base
let projectFiles = [];

// Skills (Global/Main Chat)
let availableSkills = [];
let activeSessionSkills = new Set(); // IDs of active skills for Main Chat

// Models
let availableModels = [];
let selectedModel = 'arcee-ai/trinity-mini:free'; // Default: Trinity
let modelsLoaded = false;

// ========== SKILLS MANAGEMENT ==========
async function loadSkills() {
    try {
        const response = await fetch('/api/skills?incluir_sistema=true');
        if (response.ok) {
            availableSkills = await response.json();
            console.log('[Artifact Chat] Skills carregadas:', availableSkills.length);
        }
    } catch (error) {
        console.error('[Artifact Chat] Erro ao carregar skills:', error);
    }
}


// ========== REGENERATION CONTEXT MANAGER ==========
/**
 * Manages isolated state for each inline chat instance.
 * Ensures that field regeneration uses its own Model, Attachments, and Skills
 * without affecting the global page state.
 */
const RegenContextManager = {
    contexts: {}, // Map<fieldKey, { model, attachments: [], skills: Set<id> }>

    init(fieldKey) {
        if (!this.contexts[fieldKey]) {
            // Default to global values initially, but validly independent thereafter
            this.contexts[fieldKey] = {
                model: localStorage.getItem('selectedAIModel') || 'arcee-ai/trinity-mini:free',
                modelName: localStorage.getItem('selectedAIModelName') || 'Trinity Mini',
                attachments: [], // Start empty for specific field
                skills: new Set() // Start empty or copy global if desired (empty is safer for "specific")
            };
        }
        return this.contexts[fieldKey];
    },

    get(fieldKey) {
        return this.contexts[fieldKey] || this.init(fieldKey);
    },

    reset(fieldKey) {
        delete this.contexts[fieldKey];
    },

    // Updates
    setModel(fieldKey, modelId, modelName) {
        const ctx = this.get(fieldKey);
        ctx.model = modelId;
        ctx.modelName = modelName;
        this.updateUI(fieldKey);
    },

    addAttachment(fieldKey, fileData) {
        const ctx = this.get(fieldKey);
        ctx.attachments.push(fileData);
        this.updateUI(fieldKey);
    },

    removeAttachment(fieldKey, index) {
        const ctx = this.get(fieldKey);
        ctx.attachments.splice(index, 1);
        this.updateUI(fieldKey);
    },

    toggleSkill(fieldKey, skillId) {
        const ctx = this.get(fieldKey);
        if (ctx.skills.has(skillId)) {
            ctx.skills.delete(skillId);
        } else {
            ctx.skills.add(skillId);
        }
        this.updateUI(fieldKey);
    },

    updateUI(fieldKey) {
        const ctx = this.get(fieldKey);
        const container = document.getElementById(`inline-context-${fieldKey}`);
        if (!container) return;

        // Update Model Pill
        const modelPill = container.querySelector('.pill-model .pill-text');
        if (modelPill) modelPill.textContent = ctx.modelName;

        // Update Attachments Pill
        const attachPill = container.querySelector('.pill-attach');
        if (attachPill) {
            const count = ctx.attachments.length;
            attachPill.querySelector('.pill-text').textContent = `${count} arquivo(s)`;
            if (count > 0) attachPill.classList.add('active');
            else attachPill.classList.remove('active');
        }

        // Update Skills Pill
        const skillsPill = container.querySelector('.pill-skills');
        if (skillsPill) {
            const count = ctx.skills.size;
            skillsPill.querySelector('.pill-text').textContent = `${count} skill(s)`;
            if (count > 0) skillsPill.classList.add('active');
            else skillsPill.classList.remove('active');
        }
    }
};

// ========== DOM ELEMENTS ==========
let artifactChatLayout;
let chatWelcome;
let chatMessages;
let chatInput;
let btnSend;
let generateAuthBar;
let artifactFieldsContainer;
let workspaceActions;
let modelSelectorBtn;
let modelDropdown;
let selectedModelName;
let btnAttach;
let fileInput;
let knowledgeBaseList;
let knowledgeBaseCount;
// Attachments State
// chatAttachments declared at top

// ========== INITIALIZATION ==========
function initArtifactChat(config, fields) {
    console.log('[Artifact Chat] Initializing with config:', config);

    // Store config globally
    window.ARTIFACT_CONFIG = config;
    window.ARTIFACT_FIELDS = fields;

    // Get DOM elements
    artifactChatLayout = document.getElementById('artifactChatLayout');
    chatWelcome = document.getElementById('chatWelcome');
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    btnSend = document.getElementById('btnSend');
    generateAuthBar = document.getElementById('generateAuthBar');
    artifactFieldsContainer = document.getElementById('artifactFieldsContainer');
    workspaceActions = document.getElementById('workspaceActions');
    modelSelectorBtn = document.getElementById('modelSelectorBtn');
    modelDropdown = document.getElementById('modelDropdown');
    selectedModelName = document.getElementById('selectedModelName');

    // Attachments DOM
    btnAttach = document.getElementById('btnAttach');
    fileInput = document.getElementById('fileInput');
    knowledgeBaseList = document.getElementById('knowledgeBaseList');
    knowledgeBaseCount = document.getElementById('knowledgeBaseCount');

    // Set initial phase from config
    if (config.faseInicial) {
        currentPhase = config.faseInicial;
    }

    // Load existing data if in edit mode
    if (config.editarDados) {
        window.artifactData = config.editarDados;
    }

    // Setup event listeners
    setupEventListeners();

    // Load AI models
    loadAIModels();

    // Load skills
    loadProjectSkills();

    // Initialize based on mode
    if (config.faseInicial === 'editing' && config.editarId) {
        initEditMode();
    } else {
        initChat();
    }

    // Initialize Deep Research UI (Only for ETP/TR)
    if (['etp', 'tr'].includes(config.artifactType)) {
        initDeepResearchUI();
    }
}

function setupEventListeners() {
    // Input handlers - textarea expansível
    if (chatInput) {
        chatInput.addEventListener('input', autoResizeTextarea);
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (btnSend) {
        btnSend.addEventListener('click', sendMessage);
    }
    
    const btnForceGenerate = document.getElementById('btnForceGenerate');
    if (btnForceGenerate) {
        btnForceGenerate.addEventListener('click', forceGenerateArtefact);
    }

    // Model selector listeners
    if (modelSelectorBtn) {
        modelSelectorBtn.addEventListener('click', toggleModelDropdown);
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (modelDropdown && !modelDropdown.contains(e.target) && !modelSelectorBtn.contains(e.target)) {
            modelDropdown.classList.remove('show');
        }
    });

    // File Upload Handlers
    if (btnAttach && fileInput) {
        console.log('[Artifact Chat] Attach button and file input found, binding events');
        btnAttach.addEventListener('click', (e) => {
            e.stopPropagation();
            console.log('[Artifact Chat] Attach button clicked, opening file picker');
            fileInput.click();
        });
        fileInput.addEventListener('change', handleFileUpload);
    } else {
        console.warn('[Artifact Chat] Attach button or file input NOT found!', { btnAttach, fileInput });
    }
}

// ========== ATTACHMENT HANDLERS ==========
async function handleFileUpload(event) {
    console.log('[Artifact Chat] File input change event fired');
    const files = event.target.files;
    if (!files || files.length === 0) {
        console.warn('[Artifact Chat] No files selected');
        return;
    }

    console.log(`[Artifact Chat] ${files.length} file(s) selected:`, Array.from(files).map(f => `${f.name} (${f.type}, ${f.size}b)`));

    // Reset input so same file can be selected again
    const fileArray = Array.from(files);
    event.target.value = '';

    for (const file of fileArray) {
        // Create FormData
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Show loading state
            addMessage('assistant', `📂 Carregando arquivo: **${file.name}**...`, true);

            console.log(`[Artifact Chat] Uploading ${file.name} to /api/ia-upload/...`);
            const response = await fetch('/api/ia-upload/', {
                method: 'POST',
                body: formData
            });

            console.log(`[Artifact Chat] Upload response status: ${response.status}`);
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[Artifact Chat] Upload failed:', errorText);
                throw new Error(`Falha no upload (${response.status})`);
            }

            const data = await response.json();
            console.log('[Artifact Chat] Upload success:', { filename: data.filename, hasText: !!data.extracted_text, textLength: data.extracted_text?.length });

            // Add to state
            chatAttachments.push({
                type: file.type,
                filename: data.filename,
                url: data.url,
                extracted_text: data.extracted_text
            });

            // Update UI
            renderKnowledgeBase();

            // Remove loading msg and notify success
            const streamingMsg = document.getElementById('streaming-message');
            if (streamingMsg) streamingMsg.remove();

            addMessage('assistant', `✅ Arquivo anexado: **${data.filename}**`);

        } catch (error) {
            console.error('[Artifact Chat] Upload error:', error);
            const streamingMsg = document.getElementById('streaming-message');
            if (streamingMsg) streamingMsg.remove();
            addMessage('assistant', `❌ Erro ao anexar **${file.name}**: ${error.message}`);
        }
    }
}

function renderKnowledgeBase() {
    if (!knowledgeBaseList || !knowledgeBaseCount) return;

    knowledgeBaseCount.textContent = chatAttachments.length;

    if (chatAttachments.length === 0) {
        knowledgeBaseList.innerHTML = '<div class="empty-state-small">Nenhum arquivo anexado</div>';
        return;
    }

    knowledgeBaseList.innerHTML = chatAttachments.map((att, index) => {
        let icon = '📄';
        if (att.type.startsWith('image/')) icon = '🖼️';
        if (att.type === 'application/pdf') icon = '📕';

        return `
        <div class="kb-item">
            <div class="kb-icon">${icon}</div>
            <div class="kb-info">
                <div class="kb-name" title="${att.filename}">${att.filename}</div>
                <div class="kb-meta">${att.type.startsWith('image/') ? 'Imagem' : 'Documento'}</div>
            </div>
            <button class="kb-remove" onclick="removeAttachment(${index})" title="Remover">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
        `;
    }).join('');
}

window.removeAttachment = function (index) {
    chatAttachments.splice(index, 1);
    renderKnowledgeBase();
    addMessage('assistant', '🗑️ Arquivo removido da base de conhecimento.');
}

// ========== EDIT MODE INITIALIZATION ==========
async function initEditMode() {
    const config = window.ARTIFACT_CONFIG;
    const fields = window.ARTIFACT_FIELDS;

    console.log('[Artifact Chat] Iniciando modo edição para', config.artifactType, config.editarId);
    console.log('[Artifact Chat] Dados de edição:', config.editarDados);

    // Load skills
    loadSkills();
    console.log('[Artifact Chat] Artifact Data global:', window.artifactData);

    // Change to editing phase
    currentPhase = 'editing';
    artifactChatLayout.classList.remove('phase-preparation', 'phase-generation');
    artifactChatLayout.classList.add('phase-editing');

    // Hide welcome and show messages
    if (chatWelcome) chatWelcome.style.display = 'none';
    hasMessages = true;

    // Render fields with existing data
    renderFieldsForEdit();

    // Show workspace actions
    if (workspaceActions) workspaceActions.classList.add('show');

    // Update workspace header
    const title = document.getElementById('workspaceTitle');
    const badge = document.getElementById('workspaceBadge');
    const progress = document.getElementById('workspaceProgress');
    const spinner = document.getElementById('workspaceSpinner');

    if (spinner) spinner.classList.add('done');
    if (title) title.textContent = `Editando ${config.artifactLabel} v${config.editarVersao}`;
    if (badge) {
        badge.textContent = config.editarStatus === 'aprovado' ? 'Aprovado' : 'Rascunho';
        badge.style.background = config.editarStatus === 'aprovado'
            ? 'rgba(16, 185, 129, 0.15)'
            : 'rgba(59, 130, 246, 0.15)';
        badge.style.color = config.editarStatus === 'aprovado'
            ? 'var(--chat-success)'
            : 'var(--chat-info)';
    }
    if (progress) progress.textContent = 'Edite os campos ou use o chat para regenerar';

    // Initial message in chat
    addMessage('assistant', `📝 **Modo Edição - ${config.artifactLabel} v${config.editarVersao}**\n\nVocê pode:\n- Editar os campos ✏️ diretamente no formulário\n- Me pedir para **regenerar** campos específicos usando IA\n- Campos automáticos 🔒 não podem ser alterados\n\n*Como posso ajudar?*`);
}

// Render fields for edit mode
function renderFieldsForEdit() {
    const fields = window.ARTIFACT_FIELDS;

    artifactFieldsContainer.innerHTML = fields.map((field, index) => {
        const isEditable = field.type === 'ia' || field.type === 'user';
        const cardClass = isEditable ? 'editable' : 'locked';
        const value = window.artifactData[field.key] || '';
        console.log(`[Render] Field ${field.key}: value='${value}'`);

        return `
        <div class="field-card visible done ${cardClass}" id="field-${field.key}" style="transition-delay: ${index * 60}ms">
            <div class="field-header">
                <div class="field-title">
                    <span class="field-icon">${field.icon}</span>
                    ${field.label}
                </div>
                <span class="field-status done" id="status-${field.key}">
                    ${isEditable ? 'Editável' : 'Automático'}
                </span>
            </div>
            <div class="field-body">
                <textarea
                    class="field-textarea"
                    id="input-${field.key}"
                    rows="${field.rows}"
                    ${isEditable ? '' : 'readonly disabled'}
                    placeholder="${isEditable ? 'Digite ou peça para a IA regenerar...' : 'Campo automático'}"
                >${value}</textarea>
                ${field.type === 'ia' ? `
                <button class="btn-regenerate-field" onclick="showRegenerateModal('${field.key}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                    Regenerar com IA
                </button>
                ` : ''}
            </div>
        </div>
    `}).join('');
}

async function initChat() {
    const config = window.ARTIFACT_CONFIG;

    try {
        // Load skills in background
        loadSkills();

        const response = await fetch(`${config.apiBase}/chat/init/${config.projetoId}`, {
            credentials: 'include'
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        showWelcomeMessage(data.welcome_message);
    } catch (error) {
        console.error('Erro ao iniciar chat:', error);
        const fallbackMessage = config.fallbackMessage ||
            `Olá! Sou a **LIA**, sua assistente para elaboração do ${config.artifactLabel} conforme a Lei 14.133/2021.\n\nVou te ajudar a elaborar um documento completo e bem fundamentado. Para começar:\n\n**Me conta: qual problema ou necessidade motivou essa contratação?**`;
        showWelcomeMessage(fallbackMessage);
    }
}

// ========== DEEP RESEARCH ==========
function initDeepResearchUI() {
    // Locate the left toolbar container
    const toolbarLeft = document.getElementById('chatToolbarLeft');
    if (!toolbarLeft) return;

    // Create Toggle Button (Text + Icon)
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'btn-deep-research';
    toggleBtn.id = 'btnDeepResearch';
    toggleBtn.type = 'button';
    toggleBtn.title = 'Pesquisa Profunda (Deep Research)';
    toggleBtn.innerHTML = `
        <span class="icon">🔍</span>
        <span class="label">Deep Research</span>
        <span class="toggle-switch"></span>
    `;
    toggleBtn.onclick = toggleDeepResearch;

    // Add to toolbar
    toolbarLeft.appendChild(toggleBtn);
}

function toggleDeepResearch() {
    deepResearchActive = !deepResearchActive;
    const btn = document.getElementById('btnDeepResearch');

    if (btn) {
        btn.classList.toggle('active', deepResearchActive);
        // Visual indicator change
        if (deepResearchActive) {
            btn.style.color = 'var(--primary-color)';
            btn.style.borderColor = 'var(--primary-color)';
            btn.style.background = 'rgba(var(--primary-rgb), 0.1)';
        } else {
            btn.style.color = '';
            btn.style.borderColor = '';
            btn.style.background = '';
        }
    }

    addMessage('system', deepResearchActive
        ? '🔍 **Deep Research ativado.** A geração será enriquecida com dados da web.'
        : '🔍 **Deep Research desativado.**'
        , false);
}

function startDeepResearchFlow() {
    // 1. Show Modal to ask for context/confirmation
    const modal = document.createElement('div');
    modal.className = 'modal-overlay show';
    modal.id = 'deepResearchModal';
    modal.innerHTML = `
        <div class="modal-card research-modal">
            <div class="modal-header">
                <h3>🔍 Deep Research</h3>
                <button class="btn-close" onclick="closeDeepResearchModal()">×</button>
            </div>
            <div class="modal-body" id="researchModalBody">
                <p>O Deep Research realizará uma busca aprofundada na web para enriquecer seu documento.</p>
                <div class="form-group">
                    <label>Qual o objetivo desta pesquisa? (Contexto)</label>
                    <textarea id="researchContextInput" rows="3" placeholder="Ex: Buscar legislações específicas sobre cadeiras ergonômicas e preços de referência para 2024."></textarea>
                </div>
            </div>
            <div class="modal-footer" id="researchModalFooter">
                <button class="btn-secondary" onclick="closeDeepResearchModal()">Cancelar</button>
                <button class="btn-primary" onclick="executeDeepResearch()">Iniciar Pesquisa 🚀</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeDeepResearchModal() {
    const modal = document.getElementById('deepResearchModal');
    if (modal) modal.remove();
}

async function executeDeepResearch() {
    const contextInput = document.getElementById('researchContextInput');
    const userContext = contextInput ? contextInput.value.trim() : '';

    if (!userContext) {
        alert('Por favor, forneça um contexto para a pesquisa.');
        return;
    }

    // Switch to progress view
    const modalBody = document.getElementById('researchModalBody');
    const modalFooter = document.getElementById('researchModalFooter');

    if (modalFooter) modalFooter.style.display = 'none';

    modalBody.innerHTML = `
        <div class="research-progress-container">
            <div class="research-status">Iniciando agentes de pesquisa...</div>
            <div class="progress-steps" id="researchSteps">
                <!-- Steps will connect here -->
            </div>
        </div>
    `;

    // Stream Research
    try {
        const config = window.ARTIFACT_CONFIG;
        const response = await fetch('/api/ia-native/deep-research/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: config.artifactLabel, // e.g. "ETP"
                context: userContext
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let researchResult = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line.trim() || !line.startsWith('data: ')) continue;
                try {
                    const event = JSON.parse(line.slice(6));
                    renderResearchEvent(event);
                    if (event.step === 'complete') {
                        researchResult = event.data.context;
                    }
                } catch (e) {
                    console.error('SSE Error:', e);
                }
            }
        }

        // Research Complete -> Proceed to Generation
        setTimeout(() => {
            closeDeepResearchModal();
            // Call original authorizeGeneration with injected context
            authorizeGeneration(researchResult);
        }, 1500);

    } catch (error) {
        modalBody.innerHTML = `<div class="error-text">❌ Erro na pesquisa: ${error.message}</div>`;
        if (modalFooter) modalFooter.style.display = 'flex';
    }
}

function renderResearchEvent(event) {
    const container = document.getElementById('researchSteps');
    if (!container) return;

    const stepDiv = document.createElement('div');
    stepDiv.className = `research-step ${event.step}`;

    let content = '';
    const icon = {
        'start': '🏁', 'plan': '🗺️', 'queries': '❓',
        'search': '🔍', 'read': '📖', 'synthesize': '🧠', 'complete': '✅'
    }[event.step] || 'ℹ️';

    content = `<span class="step-icon">${icon}</span> <span class="step-msg">${event.message}</span>`;

    if (event.step === 'queries' && event.data.queries) {
        content += `<ul class="queries-list">${event.data.queries.map(q => `<li>${q}</li>`).join('')}</ul>`;
    }

    stepDiv.innerHTML = content;
    container.appendChild(stepDiv);
    container.scrollTop = container.scrollHeight;

    // Update main status text
    const statusDiv = document.querySelector('.research-status');
    if (statusDiv) statusDiv.textContent = event.message;
}

// ========== WELCOME MESSAGE (CENTERED) ==========
function showWelcomeMessage(content) {
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'chat-welcome-inline';
    welcomeDiv.id = 'welcomeInline';

    welcomeDiv.innerHTML = `
        <div class="welcome-icon">🤖</div>
        <div class="welcome-content">
            ${formatMessage(content)}
        </div>
    `;

    chatMessages.appendChild(welcomeDiv);

    // Store in history but don't mark as hasMessages yet
    chatHistory.push({ role: 'assistant', content });
}


// ========== CHAT FUNCTIONS ==========
function addMessage(role, content, isStreaming = false) {
    // Remove welcome message when first real message appears
    if (!hasMessages) {
        const welcomeInline = document.getElementById('welcomeInline');
        if (welcomeInline) welcomeInline.remove();
        if (chatWelcome) chatWelcome.style.display = 'none';
        hasMessages = true;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const messageId = isStreaming ? 'streaming-message' : `msg-${Date.now()}`;

    messageDiv.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">
            <div class="message-bubble" id="${messageId}">
                ${formatMessage(content)}${isStreaming ? '<span class="streaming-cursor"></span>' : ''}
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    if (!isStreaming && content) {
        chatHistory.push({ role, content });
        // Update force generate button visibility after adding message
        updateForceGenerateButton();
    }

    return messageDiv;
}

function formatMessage(content) {
    if (!content) return '';
    return content
        // Remove technical markers
        .replace(/\[GERAR_\w+\]/g, '')
        // Remove possible JSONs
        .replace(/\{"action":\s*"generate"[^}]*\}/g, '')
        // Markdown formatting
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .trim();
}

function updateStreamingMessage(content) {
    const bubble = document.getElementById('streaming-message');
    if (bubble) {
        bubble.innerHTML = formatMessage(content) + '<span class="streaming-cursor"></span>';
        scrollToBottom();
    }
}

function finalizeStreamingMessage(content) {
    const bubble = document.getElementById('streaming-message');
    if (bubble) {
        bubble.innerHTML = formatMessage(content);
        bubble.id = `msg-${Date.now()}`;
        chatHistory.push({ role: 'assistant', content });
    }
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

async function sendMessage() {
    const content = chatInput.value.trim();
    if (!content) return;

    // Block sending during generation
    if (isGenerating) {
        console.log('[Artifact Chat] Mensagem bloqueada durante geração');
        return;
    }

    addMessage('user', content);
    chatInput.value = '';
    autoResizeTextarea();

    btnSend.disabled = true;
    showTypingIndicator();

    const config = window.ARTIFACT_CONFIG;

    try {
        // Collect context fields if they exist
        const contextData = {};
        if (document.getElementById('inputGestor')) {
            contextData.gestor = document.getElementById('inputGestor').value;
        }
        if (document.getElementById('inputFiscal')) {
            contextData.fiscal = document.getElementById('inputFiscal').value;
        }
        if (document.getElementById('inputDataLimite')) {
            contextData.data_limite = document.getElementById('inputDataLimite').value;
        }

        const response = await fetch(`${config.apiBase}/chat/${config.projetoId}`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                history: chatHistory.slice(-10),
                model: selectedModel,
                attachments: chatAttachments, // Send current attachments
                ...contextData
            })
        });

        removeTypingIndicator();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let reasoningBuffer = '';
        let contentBuffer = '';
        let streamingStarted = false;
        let lineBuffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            lineBuffer += decoder.decode(value, { stream: true });
            const lines = lineBuffer.split('\n');
            lineBuffer = lines.pop(); // Keep partial line

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

                try {
                    const data = JSON.parse(trimmedLine.slice(6));

                    if (data.type === 'reasoning') {
                        if (!streamingStarted) {
                            addMessage('assistant', '', true);
                            streamingStarted = true;
                        }
                        // OpenRouter Items Paradigm: data.content is cumulative
                        reasoningBuffer = data.content;

                        let combinedResponse = '';
                        if (reasoningBuffer) {
                            combinedResponse += `
<details class="reasoning-accordion" ${reasoningBuffer.length < 500 ? 'open' : ''}>
    <summary class="reasoning-summary">Processo de Raciocínio</summary>
    <div class="reasoning-content">${reasoningBuffer}</div>
</details>`;
                        }
                        combinedResponse += contentBuffer;

                        fullResponse = combinedResponse;
                        updateStreamingMessage(combinedResponse);
                    }

                    if (data.type === 'chunk') {
                        if (!streamingStarted) {
                            addMessage('assistant', '', true);
                            streamingStarted = true;
                        }
                        // OpenRouter Items Paradigm: data.content is cumulative
                        contentBuffer = data.content;

                        let combinedResponse = '';
                        if (reasoningBuffer) {
                            combinedResponse += `
<details class="reasoning-accordion" ${reasoningBuffer.length < 500 ? 'open' : ''}>
    <summary class="reasoning-summary">Processo de Raciocínio</summary>
    <div class="reasoning-content">${reasoningBuffer}</div>
</details>`;
                        }
                        combinedResponse += contentBuffer;

                        fullResponse = combinedResponse;
                        updateStreamingMessage(combinedResponse);
                    }

                    if (data.type === 'action' && data.action === 'generate') {
                        finalizeStreamingMessage(fullResponse);
                        showGenerateAuthorization();
                    }

                    if (data.type === 'done') {
                        finalizeStreamingMessage(fullResponse);
                        updateForceGenerateButton(); // Update button visibility
                        // Detect generation marker
                        const generateMarker = config.generateMarker || '[GERAR_DFD]';
                        if (fullResponse.includes(generateMarker) ||
                            fullResponse.toLowerCase().includes('vou iniciar a geração') ||
                            fullResponse.toLowerCase().includes('iniciando a geração')) {
                            showGenerateAuthorization();
                        }
                    }
                } catch (e) {
                    console.error('SSE parse error:', e);
                }
            }
        }

        // Fallback: finalize if stream ended without 'done' event
        if (streamingStarted && fullResponse) {
            finalizeStreamingMessage(fullResponse);
            updateForceGenerateButton(); // Update button visibility
            // Check for generation marker after finalization
            const generateMarker = config.generateMarker || '[GERAR_DFD]';
            if (fullResponse.includes(generateMarker) ||
                fullResponse.toLowerCase().includes('vou iniciar a geração') ||
                fullResponse.toLowerCase().includes('iniciando a geração')) {
                showGenerateAuthorization();
            }
        }
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        removeTypingIndicator();
        addMessage('assistant', 'Desculpe, ocorreu um erro na comunicação. Por favor, tente novamente.');
    }

    btnSend.disabled = false;
    chatInput.focus();
}

function showGenerateAuthorization() {
    readyToGenerate = true;
    if (generateAuthBar) {
        generateAuthBar.classList.add('show');
    }
}

// ========== FORCE GENERATE ==========
function updateForceGenerateButton() {
    const btnForceGenerate = document.getElementById('btnForceGenerate');
    if (!btnForceGenerate) return;
    
    // Show button if:
    // 1. Has at least 1 message in history
    // 2. Not currently generating
    // 3. Not already in generation phase
    const shouldShow = chatHistory.length > 0 && !isGenerating && currentPhase === 'preparation';
    
    btnForceGenerate.style.display = shouldShow ? 'flex' : 'none';
    btnForceGenerate.disabled = isGenerating;
}

async function forceGenerateArtefact() {
    const config = window.ARTIFACT_CONFIG;
    
    // Validations
    if (isGenerating) {
        console.log('[Force Gen] Já está gerando');
        return;
    }
    
    if (chatHistory.length === 0) {
        alert('Converse primeiro para coletar informações antes de gerar o artefato.');
        return;
    }
    
    if (currentPhase !== 'preparation') {
        console.log('[Force Gen] Não está na fase de preparação');
        return;
    }
    
    // Confirm
    const confirmed = confirm(
        `Deseja gerar o ${config.artifactLabel} com as informações coletadas até agora?\n\n` +
        `Nota: A geração pode resultar em campos incompletos se não houver dados suficientes na conversa.`
    );
    
    if (!confirmed) return;
    
    console.log('[Force Gen] Iniciando geração forçada');
    
    // Add system message
    addMessage('assistant', `✨ Gerando ${config.artifactLabel} com base na conversa atual...`);
    
    // Call authorizeGeneration directly
    await authorizeGeneration();
}

// ========== GENERATION FUNCTIONS ==========
async function authorizeGeneration(researchContext = null) {
    // Intercept for Deep Research
    if (deepResearchActive && !researchContext) {
        console.log('[Generation] Intercepted by Deep Research');
        startDeepResearchFlow();
        return;
    }
    const config = window.ARTIFACT_CONFIG;
    const fields = window.ARTIFACT_FIELDS;

    console.log(`[${config.artifactType} Gen] === INICIANDO GERAÇÃO ===`);

    // Disable chat during generation
    isGenerating = true;
    disableChat();

    // Get optional field values
    const gestor = document.getElementById('inputGestor')?.value?.trim() || '';
    const fiscal = document.getElementById('inputFiscal')?.value?.trim() || '';
    const dataLimite = document.getElementById('inputDataLimite')?.value || '';

    console.log(`[${config.artifactType} Gen] Dados coletados:`, { gestor, fiscal, dataLimite });

    // Change to generation phase
    currentPhase = 'generation';
    artifactChatLayout.classList.remove('phase-preparation');
    artifactChatLayout.classList.add('phase-generation');

    if (generateAuthBar) generateAuthBar.classList.remove('show');

    // Render fields
    renderArtifactFields();

    // Fill user fields if values exist
    setTimeout(() => {
        if (gestor) {
            const inputGestor = document.getElementById('input-responsavel_gestor');
            if (inputGestor) inputGestor.value = gestor;
        }
        if (fiscal) {
            const inputFiscal = document.getElementById('input-responsavel_fiscal');
            if (inputFiscal) inputFiscal.value = fiscal;
        }
        if (dataLimite) {
            const inputData = document.getElementById('input-data_pretendida');
            if (inputData) inputData.value = dataLimite;
        }
    }, 200);

    // Add status message in chat
    addMessage('assistant', `⚡ **Iniciando geração do ${config.artifactLabel}...** Aguarde enquanto preencho os campos.`);

    const requestBody = {
        history: chatHistory,
        gestor: gestor || null,
        fiscal: fiscal || null,
        data_limite: dataLimite || null,
        model: selectedModel,
        attachments: chatAttachments,
        skills: Array.from(activeSessionSkills),
        deep_research_context: researchContext || null
    };

    try {
        const response = await fetch(`${config.apiBase}/chat/${config.projetoId}/gerar`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let processedFields = new Set();
        let lineBuffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            lineBuffer += decoder.decode(value, { stream: true });
            const lines = lineBuffer.split('\n');
            lineBuffer = lines.pop(); // Keep partial line

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

                const rawData = trimmedLine.slice(6);

                try {
                    const data = JSON.parse(rawData);

                    if (data.type === 'reasoning') {
                        // Ignorar raciocinio durante a geracao de artefatos para nao quebrar o JSON
                        console.debug('[Generation] Ignorando reasoning chunk (cumulative):', data.content.substring(0, 20) + '...');
                    }

                    if (data.type === 'chunk') {
                        // OpenRouter Items Paradigm: data.content is cumulative
                        fullResponse = data.content;
                        const newFields = updateFieldsFromStream(fullResponse, processedFields);
                        newFields.forEach(f => processedFields.add(f));
                        updateProgress(processedFields.size);
                    }

                    if (data.type === 'field') {
                        const fieldKey = data.field;
                        const fieldValue = data.value;
                        updateFieldValue(fieldKey, fieldValue);
                    }

                    if (data.type === 'complete') {
                        if (data.success && data.data) {
                            window.artifactData = data.data;
                            populateAllFields(data.data);
                        }
                        finishGeneration();
                    }

                    if (data.type === 'error') {
                        console.error(`[${config.artifactType} Gen] Erro do servidor:`, data.error);
                        addMessage('assistant', '❌ **Erro do servidor:** ' + data.error);
                    }
                } catch (e) {
                    console.error('SSE parse error:', e);
                }
            }
        }

        // Check if we received data
        if (processedFields.size === 0 && fullResponse.length > 0) {
            try {
                let cleaned = fullResponse.trim();
                if (cleaned.startsWith('```json')) cleaned = cleaned.slice(7);
                if (cleaned.startsWith('```')) cleaned = cleaned.slice(3);
                if (cleaned.endsWith('```')) cleaned = cleaned.slice(0, -3);

                const parsed = JSON.parse(cleaned.trim());
                window.artifactData = parsed;
                populateAllFields(parsed);
                finishGeneration();
            } catch (parseErr) {
                console.error('Falha no parse manual:', parseErr);
                // Try additional fixes for common JSON issues
                try {
                    // Fix: unescape already-escaped newlines that were double-escaped
                    let fixed = fullResponse.replace(/\\\\n/g, '\\n');
                    const parsed = JSON.parse(fixed.trim());
                    window.artifactData = parsed;
                    populateAllFields(parsed);
                    finishGeneration();
                } catch (secondErr) {
                    console.error('Falha no parse com fix:', secondErr);
                }
            }
        }

    } catch (error) {
        console.error(`[${config.artifactType} Gen] === ERRO NA GERAÇÃO ===`, error);
        addMessage('assistant', '❌ **Erro na geração:** ' + error.message + '. Tente novamente ou entre em contato com o suporte.');
    }
}

function renderArtifactFields() {
    const fields = window.ARTIFACT_FIELDS;

    // Check if there's a custom render function defined
    if (window.customWorkspaceRender && typeof window.customWorkspaceRender === 'function') {
        artifactFieldsContainer.innerHTML = window.customWorkspaceRender(window.artifactData, fields);
        return;
    }

    artifactFieldsContainer.innerHTML = fields.map((field, index) => {
        // Skip special field types that need custom rendering
        if (field.type === 'riscos' || field.type === 'custom' || field.type === 'hidden') {
            return '';
        }

        const isAuto = field.type === 'auto';
        const isIA = field.type === 'ia';
        const autoValue = field.value || '';
        const statusText = isAuto ? 'Automático' : 'Aguardando';
        const statusClass = isAuto ? 'done' : 'pending';
        const cardClass = isAuto ? 'visible done locked' : '';

        return `
        <div class="field-card ${cardClass}" id="field-${field.key}" style="transition-delay: ${index * 60}ms">
            <div class="field-header">
                <div class="field-title">
                    <span class="field-icon">${field.icon}</span>
                    ${field.label}
                </div>
                <span class="field-status ${statusClass}" id="status-${field.key}">${statusText}</span>
            </div>
            <div class="field-body">
                <textarea
                    class="field-textarea"
                    id="input-${field.key}"
                    rows="${field.rows}"
                    placeholder="${isAuto ? 'Campo automático' : 'Aguardando geração pela IA...'}"
                    ${isAuto ? 'readonly disabled' : ''}
                >${autoValue}</textarea>
                ${isIA ? `
                <button class="btn-regenerate-field" onclick="showRegenerateModal('${field.key}', '${field.label}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                    Regenerar com IA
                </button>
                ` : ''}
            </div>
        </div>
    `}).join('');

    // Trigger visibility animation for non-automatic fields
    setTimeout(() => {
        fields.forEach((field, index) => {
            if (field.type !== 'auto') {
                setTimeout(() => {
                    const card = document.getElementById(`field-${field.key}`);
                    if (card) card.classList.add('visible');
                }, index * 60);
            }
        });
    }, 100);
}

function updateFieldValue(fieldKey, value) {
    const input = document.getElementById(`input-${fieldKey}`);
    const status = document.getElementById(`status-${fieldKey}`);
    const card = document.getElementById(`field-${fieldKey}`);

    // Skip if value is array/object and we have a custom renderer
    if (typeof value === 'object' && value !== null) {
        // For arrays/objects, store in artifactData for custom renderer
        window.artifactData[fieldKey] = value;
        // Re-render if we have custom workspace renderer
        if (window.customWorkspaceRender && typeof window.customWorkspaceRender === 'function') {
            const fields = window.ARTIFACT_FIELDS;
            artifactFieldsContainer.innerHTML = window.customWorkspaceRender(window.artifactData, fields);
        }
        return;
    }

    if (input) {
        input.value = value;
    }
    if (status) {
        status.textContent = '✓ Gerado';
        status.className = 'field-status done';
    }
    if (card) {
        card.classList.remove('generating');
        card.classList.add('done');
    }
}

function updateFieldsFromStream(jsonString, processedFields) {
    const fields = window.ARTIFACT_FIELDS;
    const newlyCompleted = [];

    fields.forEach(field => {
        if (processedFields.has(field.key)) return;

        // Skip special field types that need custom rendering
        if (field.type === 'riscos' || field.type === 'custom' || field.type === 'hidden') return;

        const patterns = [
            new RegExp(`"${field.key}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)"`),
            new RegExp(`"${field.key}"\\s*:\\s*"([^"]*)`),
        ];

        for (const regex of patterns) {
            const match = jsonString.match(regex);
            if (match) {
                const input = document.getElementById(`input-${field.key}`);
                const status = document.getElementById(`status-${field.key}`);
                const card = document.getElementById(`field-${field.key}`);

                if (input && status && card) {
                    const value = match[1]
                        .replace(/\\n/g, '\n')
                        .replace(/\\"/g, '"')
                        .replace(/\\t/g, '\t');

                    input.value = value;
                    status.textContent = 'Gerando...';
                    status.className = 'field-status generating';
                    card.classList.add('generating');
                    card.classList.remove('done');

                    if (match[0].endsWith('"')) {
                        status.textContent = '✓ Gerado';
                        status.className = 'field-status done';
                        card.classList.remove('generating');
                        card.classList.add('done');
                        newlyCompleted.push(field.key);
                    }
                }
                break;
            }
        }
    });

    return newlyCompleted;
}

function populateAllFields(data) {
    const fields = window.ARTIFACT_FIELDS;

    // Store data globally for custom renderers
    window.artifactData = data;

    // If custom render function exists, re-render the entire workspace
    if (window.customWorkspaceRender && typeof window.customWorkspaceRender === 'function') {
        artifactFieldsContainer.innerHTML = window.customWorkspaceRender(window.artifactData, fields);

        // Add visible/done classes to all field cards
        setTimeout(() => {
            const cards = artifactFieldsContainer.querySelectorAll('.workspace-field-card, .field-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('visible', 'done');
                }, index * 60);
            });
        }, 100);
        return;
    }

    // Standard field population for non-custom artifacts
    fields.forEach(field => {
        // Skip special types
        if (field.type === 'riscos' || field.type === 'custom' || field.type === 'hidden') {
            return;
        }

        const input = document.getElementById(`input-${field.key}`);
        const status = document.getElementById(`status-${field.key}`);
        const card = document.getElementById(`field-${field.key}`);

        if (input && status && card) {
            const value = data[field.key];
            if (value !== null && value !== undefined) {
                // Handle arrays and objects
                if (typeof value === 'object') {
                    input.value = JSON.stringify(value, null, 2);
                } else {
                    input.value = String(value);
                }
            }
            status.textContent = '✓ Gerado';
            status.className = 'field-status done';
            card.classList.remove('generating');
            card.classList.add('done');
        }
    });
}

function updateProgress(completedCount) {
    const fields = window.ARTIFACT_FIELDS;
    const progress = document.getElementById('workspaceProgress');
    if (progress) {
        progress.textContent = `${completedCount} de ${fields.length} campos`;
    }
}

function finishGeneration() {
    const config = window.ARTIFACT_CONFIG;
    const fields = window.ARTIFACT_FIELDS;

    const spinner = document.getElementById('workspaceSpinner');
    const title = document.getElementById('workspaceTitle');
    const badge = document.getElementById('workspaceBadge');
    const progress = document.getElementById('workspaceProgress');

    if (spinner) spinner.classList.add('done');
    if (title) title.textContent = `${config.artifactLabel} Gerado`;
    if (badge) {
        badge.textContent = 'Pronto';
        badge.style.background = 'rgba(16, 185, 129, 0.15)';
        badge.style.color = 'var(--chat-success)';
    }
    if (progress) progress.textContent = 'Todos os campos preenchidos';

    if (workspaceActions) workspaceActions.classList.add('show');

    // Transition to editing phase
    currentPhase = 'editing';
    artifactChatLayout.classList.remove('phase-generation');
    artifactChatLayout.classList.add('phase-editing');

    // Mark fields as editable/locked
    fields.forEach(field => {
        const card = document.getElementById(`field-${field.key}`);
        if (card) {
            if (field.type === 'ia' || field.type === 'user') {
                card.classList.add('editable');
            } else {
                card.classList.add('locked');
            }
        }
    });

    // Completion message in chat
    isGenerating = false;
    enableChat();
    addMessage('assistant', `✅ **${config.artifactLabel} gerado com sucesso!** Revise os campos à direita e faça ajustes se necessário. Você pode editar diretamente ou me pedir para regenerar campos específicos. Quando estiver satisfeito, clique em **Aprovar ${config.artifactLabel}**.`);
}

// ========== CHAT ENABLE/DISABLE ==========
function disableChat() {
    if (chatInput) {
        chatInput.disabled = true;
        chatInput.placeholder = 'Aguarde a geração...';
    }
    if (btnSend) btnSend.disabled = true;
}

function enableChat() {
    if (chatInput) {
        chatInput.disabled = false;
        chatInput.placeholder = 'Digite sua mensagem...';
    }
    if (btnSend) btnSend.disabled = false;
}

// ========== REGENERATE INLINE CHAT ==========
function showRegenerateModal(fieldKey, fieldLabel) {
    // If already has a chat open, close it
    if (currentRegenerateField && currentRegenerateField !== fieldKey) {
        closeInlineChat(currentRegenerateField);
    }

    currentRegenerateField = fieldKey;
    const card = document.getElementById(`field-${fieldKey}`);
    if (!card) return;

    // Check if inline chat already exists
    let inlineChat = card.querySelector('.inline-chat');
    if (inlineChat) {
        // Toggle - close if already open
        closeInlineChat(fieldKey);
        return;
    }

    // Fix undefined label
    if (!fieldLabel) {
        const fieldConfig = window.ARTIFACT_FIELDS.find(f => f.key === fieldKey);
        if (fieldConfig) fieldLabel = fieldConfig.label;
    }

    // Create inline chat (Premium Regenerator Workspace)
    inlineChat = document.createElement('div');
    inlineChat.className = 'inline-chat premium';

    // Initialize local context
    const ctx = RegenContextManager.init(fieldKey);

    inlineChat.innerHTML = `
        <div class="inline-chat-header">
            <div class="inline-chat-header-title">
                <span class="inline-chat-icon">✨</span>
                <span>Refinar <b>${fieldLabel || fieldKey}</b></span>
            </div>
            <button class="inline-chat-close" onclick="closeInlineChat('${fieldKey}')" title="Fechar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
        
        <div class="inline-chat-body">
            <!-- Inline Attachments List (Visual Feedback) -->
            <div class="inline-attachments-list" id="inline-attachments-${fieldKey}"></div>

            <div class="inline-chat-input-wrapper">
                <textarea 
                    class="inline-chat-textarea" 
                    id="inline-input-${fieldKey}"
                    placeholder="Como deseja melhorar este campo? (Pressione Enter para enviar, Shift+Enter para nova linha)"
                    rows="1"
                    onkeydown="handleRegenKeydown(event, '${fieldKey}')"
                    oninput="handleInlineInput(this, '${fieldKey}')"
                ></textarea>
                
                <div class="inline-chat-toolbar">
                    <div class="inline-toolbar-left">
                        <!-- Model Pill -->
                        <div class="toolbar-btn" onclick="toggleInlineModelDropdown(event, '${fieldKey}')" title="Modelo: ${ctx.modelName}">
                            <span class="toolbar-icon">🤖</span>
                            <!-- Local Dropdown Container -->
                            <div class="inline-dropdown" id="inline-model-dropdown-${fieldKey}"></div>
                        </div>

                        <!-- Attachments Pill -->
                        <div class="toolbar-btn ${ctx.attachments.length > 0 ? 'active' : ''}" onclick="triggerInlineAttach(event, '${fieldKey}')" title="Anexar arquivos">
                            <span class="toolbar-icon">📎</span>
                            <span class="toolbar-badge" id="attach-badge-${fieldKey}" style="display: ${ctx.attachments.length > 0 ? 'flex' : 'none'}">${ctx.attachments.length}</span>
                            <!-- Local Input -->
                            <input type="file" id="inline-file-input-${fieldKey}" style="display: none;" multiple onchange="handleInlineFileUpload(this, '${fieldKey}')">
                        </div>

                        <!-- Skills Pill -->
                        <div class="toolbar-btn ${ctx.skills.size > 0 ? 'active' : ''}" onclick="toggleInlineSkillsDropdown(event, '${fieldKey}')" title="Habilidades">
                            <span class="toolbar-icon">⚡</span>
                             <span class="toolbar-badge" id="skills-badge-${fieldKey}" style="display: ${ctx.skills.size > 0 ? 'flex' : 'none'}">${ctx.skills.size}</span>
                            <!-- Local Dropdown Container -->
                            <div class="inline-dropdown skills-dropdown" id="inline-skills-dropdown-${fieldKey}"></div>
                        </div>
                    </div>
                     <div class="inline-toolbar-right">
                        <button class="inline-chat-submit" onclick="sendInlineChat('${fieldKey}')" title="Regenerar">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <div id="inline-autocomplete-${fieldKey}" class="skills-autocomplete" style="display: none;"></div>
            </div>
        </div>
        
        <div class="inline-chat-footer-hint">
            <span class="hint">💡 Dica: Use <b>\\</b> para invocar uma habilidade.</span>
        </div>
        <div id="inline-status-${fieldKey}" class="inline-chat-status"></div>
    `;

    card.appendChild(inlineChat);

    // Focus on input
    setTimeout(() => {
        const textarea = document.getElementById(`inline-input-${fieldKey}`);
        if (textarea) {
            textarea.focus();
            autoResizeInlineTextarea(textarea);
        }
    }, 100);
}

function autoResizeInlineTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function handleRegenKeydown(event, fieldKey) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendInlineChat(fieldKey);
    }
}

function triggerInlineAttach(event, fieldKey) {
    event.stopPropagation();
    const input = document.getElementById(`inline-file-input-${fieldKey}`);
    if (input) input.click();
}

async function handleInlineFileUpload(input, fieldKey) {
    if (!input.files || input.files.length === 0) return;

    // Show uploading status locally? 
    // For now, simpler implementation: read file name and mock extraction or real extraction
    // Ideally, Reuse `uploadFile` logic but store in local context

    // ... logic for upload ...
    // Using simple mock for "Context" mainly involves passing the file info

    // Real implementation: Upload to extract text for RAG
    const formData = new FormData();
    formData.append('file', input.files[0]);

    try {
        const response = await fetch('/api/ia-upload/', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.extracted_text) {
            const fileData = {
                id: Date.now(),
                name: data.filename,
                content: data.extracted_text,
                type: 'file'
            };
            RegenContextManager.addAttachment(fieldKey, fileData);
        }
    } catch (e) {
        console.error("Local upload failed", e);
        // Fallback: just add name
        RegenContextManager.addAttachment(fieldKey, { name: input.files[0].name, content: "Conteudo pendente" });
    }

    input.value = ''; // Reset
}


// ========== LOCAL HELPERS (Models & Skills) ==========

// ========== LOCAL HELPERS (Models & Skills) ==========

function toggleInlineModelDropdown(event, fieldKey) {
    event.stopPropagation();
    const dropdown = document.getElementById(`inline-model-dropdown-${fieldKey}`);
    if (!dropdown) return;

    // Close others
    document.querySelectorAll('.inline-dropdown').forEach(el => {
        if (el !== dropdown) el.style.display = 'none';
        if (el.classList.contains('skills-autocomplete')) el.style.display = 'none';
    });

    if (dropdown.style.display === 'block') {
        dropdown.style.display = 'none';
        return;
    }

    // Render using rich UI
    dropdown.innerHTML = availableModels.map(m => `
        <div class="inline-option model-option-item ${m.id === (RegenContextManager.get(fieldKey).model) ? 'selected' : ''}" 
             onclick="selectInlineModel('${fieldKey}', '${m.id}', '${m.name}')">
            <div class="model-icon">${m.tier === 'free' ? '🌱' : '⚡'}</div>
            <div class="model-details">
                <div class="model-name">${m.name}</div>
                <div class="model-tier">${m.tier}</div>
            </div>
            ${m.id === (RegenContextManager.get(fieldKey).model) ? '<span class="check">✓</span>' : ''}
        </div>
    `).join('');

    dropdown.style.display = 'block';

    const closeFn = (e) => {
        if (!dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
            document.removeEventListener('click', closeFn);
        }
    };
    setTimeout(() => document.addEventListener('click', closeFn), 10);
}

function selectInlineModel(fieldKey, modelId, modelName) {
    RegenContextManager.setModel(fieldKey, modelId, modelName);
}

function toggleInlineSkillsDropdown(event, fieldKey) {
    event.stopPropagation();
    const dropdown = document.getElementById(`inline-skills-dropdown-${fieldKey}`);
    if (!dropdown) return;

    // Close others
    document.querySelectorAll('.inline-dropdown').forEach(el => {
        if (el !== dropdown) el.style.display = 'none';
    });

    if (dropdown.style.display === 'block') {
        dropdown.style.display = 'none';
        return;
    }

    const ctx = RegenContextManager.get(fieldKey);

    if (availableSkills.length === 0) {
        dropdown.innerHTML = '<div class="inline-option disabled">Carregando skills...</div>';
    } else {
        dropdown.innerHTML = availableSkills.map(s => {
            const isActive = ctx.skills.has(s.id);
            return `
            <div class="inline-option skill-option-item ${isActive ? 'selected' : ''}" onclick="toggleInlineSkill(event, '${fieldKey}', ${s.id})">
                <div class="skill-icon-wrapper">
                    ${isActive ? '⚡' : '⚪'}
                </div>
                <div class="skill-details">
                    <div class="skill-name">${s.nome}</div>
                    <div class="skill-desc">${s.descricao || ''}</div>
                </div>
                ${isActive ? '<span class="check">✓</span>' : ''}
            </div>`;
        }).join('');
    }

    dropdown.style.display = 'block';

    const closeFn = (e) => {
        if (!dropdown.contains(e.target) && !e.target.closest('.inline-option')) {
            dropdown.style.display = 'none';
            document.removeEventListener('click', closeFn);
        }
    };
    setTimeout(() => document.addEventListener('click', closeFn), 10);
}

function toggleInlineSkill(event, fieldKey, skillId) {
    event.stopPropagation();
    RegenContextManager.toggleSkill(fieldKey, skillId);

    // Re-render to update state without closing
    const dropdown = document.getElementById(`inline-skills-dropdown-${fieldKey}`);
    if (dropdown && dropdown.style.display === 'block') {
        // Re-render content functionality
        const ctx = RegenContextManager.get(fieldKey);
        dropdown.innerHTML = availableSkills.map(s => {
            const isActive = ctx.skills.has(s.id);
            return `
            <div class="inline-option skill-option-item ${isActive ? 'selected' : ''}" onclick="toggleInlineSkill(event, '${fieldKey}', ${s.id})">
                 <div class="skill-icon-wrapper">
                    ${isActive ? '⚡' : '⚪'}
                </div>
                <div class="skill-details">
                    <div class="skill-name">${s.nome}</div>
                    <div class="skill-desc">${s.descricao || ''}</div>
                </div>
                ${isActive ? '<span class="check">✓</span>' : ''}
            </div>`;
        }).join('');
    }
}



// ========== INLINE AUTOCOMPLETE ==========
function handleInlineInput(textarea, fieldKey) {
    autoResizeInlineTextarea(textarea);

    const value = textarea.value;
    const cursorPos = textarea.selectionStart;

    // Check for trigger character "\"
    // We look for "\" at the beginning or preceded by space
    const lastTrigger = value.lastIndexOf('\\', cursorPos - 1);

    const autocompleteContainer = document.getElementById(`inline-autocomplete-${fieldKey}`);
    if (!autocompleteContainer) return;

    if (lastTrigger !== -1) {
        // Check if there's a space before (or it's start of string)
        const isStart = lastTrigger === 0;
        const hasSpaceBefore = !isStart && /\s/.test(value[lastTrigger - 1]);

        if (isStart || hasSpaceBefore) {
            const query = value.substring(lastTrigger + 1, cursorPos).toLowerCase();
            // Don't show if query contains spaces (user typing something else)
            if (!query.includes(' ')) {
                showSkillsAutocomplete(fieldKey, query, lastTrigger);
                return;
            }
        }
    }

    // Hide if no match
    autocompleteContainer.style.display = 'none';
}

function showSkillsAutocomplete(fieldKey, query, triggerIndex) {
    const container = document.getElementById(`inline-autocomplete-${fieldKey}`);
    if (!availableSkills.length || !container) return;

    const matches = availableSkills.filter(s =>
        s.nome.toLowerCase().includes(query) ||
        (s.descricao && s.descricao.toLowerCase().includes(query))
    );

    if (matches.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.innerHTML = matches.map(s => `
        <div class="autocomplete-item" onclick="selectSkillAutocomplete('${fieldKey}', ${s.id}, '${s.nome}', ${triggerIndex})">
            <span class="skill-icon">⚡</span>
            <div class="skill-info">
                <div class="skill-name">${s.nome}</div>
                <div class="skill-desc">${s.descricao || ''}</div>
            </div>
        </div>
    `).join('');

    container.style.display = 'block';
}

function selectSkillAutocomplete(fieldKey, skillId, skillName, triggerIndex) {
    const textarea = document.getElementById(`inline-input-${fieldKey}`);
    const container = document.getElementById(`inline-autocomplete-${fieldKey}`);

    if (textarea) {
        const text = textarea.value;
        const queryEnd = textarea.selectionStart;

        // Remove the Trigger + Query
        // We replace from triggerIndex to queryEnd with nothing, but we add the skill to context

        const before = text.substring(0, triggerIndex);
        const after = text.substring(queryEnd);

        textarea.value = before + after;

        // Toggle the skill on
        RegenContextManager.toggleSkill(fieldKey, skillId);

        // Update badge
        const badge = document.getElementById(`skills-badge-${fieldKey}`);
        const ctx = RegenContextManager.get(fieldKey);
        if (badge) {
            badge.style.display = 'flex';
            badge.textContent = ctx.skills.size;
        }

        textarea.focus();
        // Set cursor position back
        textarea.selectionStart = textarea.selectionEnd = triggerIndex;
    }

    if (container) container.style.display = 'none';
}

function closeInlineChat(fieldKey) {
    const card = document.getElementById(`field-${fieldKey}`);
    if (!card) return;

    const inlineChat = card.querySelector('.inline-chat');
    if (inlineChat) {
        inlineChat.remove();
    }

    if (currentRegenerateField === fieldKey) {
        currentRegenerateField = null;
    }
}

async function sendInlineChat(fieldKey) {
    const input = document.getElementById(`inline-input-${fieldKey}`);
    const card = document.getElementById(`field-${fieldKey}`);
    if (!input || !card) return;

    const instructions = input.value.trim();
    if (!instructions) return;

    const inlineChat = card.querySelector('.inline-chat');

    // Disable input and show loading
    input.disabled = true;
    const submitBtn = inlineChat.querySelector('.inline-chat-submit');
    if (submitBtn) submitBtn.disabled = true;

    // Show loading in status
    const statusDiv = document.getElementById(`inline-status-${fieldKey}`);
    if (statusDiv) {
        statusDiv.innerHTML = `
            <div class="inline-chat-loading">
                <div class="spinner-small"></div>
                <span>Regenerando com IA...</span>
            </div>
        `;
        statusDiv.classList.add('show');
    }

    // Capture model specific to this regeneration if needed
    const ctx = RegenContextManager.get(fieldKey);
    const modelId = ctx.model;
    const activeSkills = Array.from(ctx.skills);

    // Attachments need to be handled. schema accepts list of dicts.
    // We'll pass them in new param or extend regenerateField signature

    try {
        await regenerateField(fieldKey, instructions, modelId, activeSkills, ctx.attachments);
        // Success: the card itself will update via regenerateField -> updateFieldValue
        closeInlineChat(fieldKey);
    } catch (error) {
        // Error handling
        if (statusDiv) {
            statusDiv.innerHTML = `<span class="error-text">❌ Erro: ${error.message}</span>`;
        }
        input.disabled = false;
        if (submitBtn) submitBtn.disabled = false;
    }
}

// ========== FIELD REGENERATION ==========
async function regenerateField(fieldKey, customInstructions = '', modelOverride = null, skillsOverride = [], attachmentsOverride = []) {
    const config = window.ARTIFACT_CONFIG;
    const fields = window.ARTIFACT_FIELDS;

    const fieldConfig = fields.find(f => f.key === fieldKey);
    const fieldLabel = fieldConfig ? fieldConfig.label : fieldKey;
    const currentValue = document.getElementById(`input-${fieldKey}`)?.value || '';

    addMessage('assistant', `🔄 Regenerando **${fieldLabel}**...${customInstructions ? ` (${customInstructions})` : ''}`);

    const card = document.getElementById(`field-${fieldKey}`);
    const status = document.getElementById(`status-${fieldKey}`);

    if (card) card.classList.add('generating');
    if (status) {
        status.textContent = 'Gerando...';
        status.className = 'field-status generating';
    }

    try {
        // Resolve active skills (local override or current session)
        const activeSkills = skillsOverride.length > 0 ? skillsOverride : Array.from(activeSessionSkills);

        const response = await fetch(`${config.apiBase}/chat/${config.projetoId}/regenerar-campo`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                campo: fieldKey,
                history: chatHistory,
                prompt_adicional: customInstructions || `Melhore o texto mantendo a essência.`,
                valor_atual: currentValue,
                model: modelOverride || localStorage.getItem('selectedAIModel'),
                active_skills: activeSkills,
                attachments: attachmentsOverride
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        // Server returns SSE stream — read it
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let contentBuffer = '';
        let lineBuffer = '';
        let success = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            lineBuffer += decoder.decode(value, { stream: true });
            const lines = lineBuffer.split('\n');
            lineBuffer = lines.pop();

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;

                try {
                    const data = JSON.parse(trimmedLine.slice(6));

                    if (data.type === 'chunk') {
                        contentBuffer = data.content;
                        // Live-update the field as it streams
                        const input = document.getElementById(`input-${fieldKey}`);
                        if (input) input.value = contentBuffer;
                    }

                    if (data.type === 'done') {
                        contentBuffer = data.content || contentBuffer;
                        success = true;
                    }

                    if (data.type === 'error') {
                        throw new Error(data.error || 'Falha na regeneração');
                    }
                } catch (e) {
                    if (e.message && !e.message.includes('Unexpected')) throw e;
                    console.error('SSE parse error (regen):', e);
                }
            }
        }

        if (success || contentBuffer) {
            updateFieldValue(fieldKey, contentBuffer);
            addMessage('assistant', `✅ **${fieldLabel}** regenerado com sucesso!`);
        } else {
            throw new Error('Nenhum conteúdo recebido da IA');
        }
    } catch (error) {
        console.error('Regeneration error:', error);
        addMessage('assistant', `❌ Erro ao regenerar: ${error.message}`);
        if (status) {
            status.textContent = 'Erro';
            status.className = 'field-status';
        }
        if (card) card.classList.remove('generating');
    }
}

function collectCurrentFields() {
    const fields = window.ARTIFACT_FIELDS;
    const fieldValues = {};
    fields.forEach(field => {
        const input = document.getElementById(`input-${field.key}`);
        if (input) {
            fieldValues[field.key] = input.value;
        }
    });
    return fieldValues;
}

function voltarProjeto() {
    const config = window.ARTIFACT_CONFIG;
    window.location.href = `/projetos/${config.projetoId}`;
}

// ========== SAVE FUNCTIONS ==========
async function saveArtifact(status) {
    const config = window.ARTIFACT_CONFIG;
    const fields = window.ARTIFACT_FIELDS;

    const finalData = {};
    fields.forEach(field => {
        const input = document.getElementById(`input-${field.key}`);
        if (input) {
            finalData[field.key] = input.value;
        }
    });

    // Check if it's edit or creation mode
    const isEditMode = config.editarId !== null && config.editarId !== undefined;

    try {
        let response;

        if (isEditMode && config.updateEndpoint) {
            // EDIT MODE: Update existing artifact via PUT
            const updatePayload = config.buildUpdatePayload ?
                config.buildUpdatePayload(finalData, status) :
                { ...finalData, status };

            response = await fetch(config.updateEndpoint.replace('{id}', config.editarId), {
                method: 'PUT',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatePayload)
            });
        } else if (config.saveEndpoint) {
            // CREATE MODE: Save new artifact via POST
            const payload = config.buildSavePayload ?
                config.buildSavePayload(finalData, status) :
                {
                    projeto_id: config.projetoId,
                    tipo_artefato: config.artifactType,
                    data: finalData,
                    status: status
                };

            response = await fetch(config.saveEndpoint, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }

        if (response && response.ok) {
            const actionText = status === 'aprovado' ? 'aprovado' : 'salvo';
            const modeText = isEditMode ? 'atualizado' : actionText;
            addMessage('assistant', `🎉 **${config.artifactLabel} ${modeText} com sucesso!** Redirecionando...`);
            setTimeout(() => {
                window.location.href = `/projetos/${config.projetoId}`;
            }, 1500);
        } else {
            const errorData = await response?.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Erro ao salvar');
        }
    } catch (error) {
        console.error('Erro ao salvar:', error);
        addMessage('assistant', '❌ **Erro ao salvar:** ' + error.message);
    }
}

// ========== UTILITIES ==========
function autoResizeTextarea() {
    if (chatInput) {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
    }
}

// ========== MODEL SELECTOR FUNCTIONS ==========
async function loadAIModels() {
    console.log('[Model Selector] Loading AI models...');

    try {
        const response = await fetch('/api/ia/models', {
            credentials: 'include'
        });

        if (!response.ok) throw new Error('Failed to load models');

        const data = await response.json();
        availableModels = data.models;
        modelsLoaded = true;

        console.log('[Model Selector] Loaded models:', availableModels.length);

        // Load saved model from localStorage or use default
        const savedModel = localStorage.getItem('selectedAIModel');
        selectedModel = savedModel || data.default;

        // Render models in dropdown
        renderModelOptions();

        // Update button label
        updateSelectedModelDisplay();

    } catch (error) {
        console.error('[Model Selector] Error loading models:', error);
        // Fallback to default
        selectedModel = 'arcee-ai/trinity-mini:free';
        if (selectedModelName) {
            selectedModelName.textContent = 'Trinity Mini';
        }
    }
}

function renderModelOptions() {
    const container = document.getElementById('modelDropdownBody');
    if (!container) return;

    container.innerHTML = availableModels.map(model => `
        <div class="model-option ${model.id === selectedModel ? 'selected' : ''}" 
             data-model-id="${model.id}"
             data-model-name="${model.name}"
             onclick="selectModel('${model.id}', '${model.name}')"
        >
            <div class="model-option-header">
                <span class="model-option-icon">${model.icon}</span>
                <span class="model-option-name">${model.name}</span>
                <span class="model-option-tier ${model.tier}">${model.tier}</span>
                <svg class="model-option-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <div class="model-option-description">${model.description}</div>
        </div>
    `).join('');
}

function toggleModelDropdown(e) {
    e.stopPropagation();
    if (modelDropdown) {
        modelDropdown.classList.toggle('show');
    }
}

function selectModel(modelId, modelName) {
    console.log('[Model Selector] Model selected:', modelName, '(' + modelId + ')');

    selectedModel = modelId;

    // Save to localStorage
    localStorage.setItem('selectedAIModel', modelId);
    localStorage.setItem('selectedAIModelName', modelName);

    // Update display
    updateSelectedModelDisplay();

    // Update selected class on options
    document.querySelectorAll('.model-option').forEach(option => {
        option.classList.toggle('selected', option.dataset.modelId === modelId);
    });

    // Close dropdown
    if (modelDropdown) {
        modelDropdown.classList.remove('show');
    }
}

function updateSelectedModelDisplay() {
    if (!selectedModelName) return;

    const model = availableModels.find(m => m.id === selectedModel);
    if (model) {
        selectedModelName.textContent = model.name;
        // Set data attribute for tooltip
        if (modelSelectorBtn) {
            modelSelectorBtn.setAttribute('data-model-name', model.name);
        }
    } else {
        selectedModelName.textContent = 'Trinity Mini';
        if (modelSelectorBtn) {
            modelSelectorBtn.setAttribute('data-model-name', 'Trinity Mini');
        }
    }
}

function toggleContextCard(cardId) {
    const card = document.getElementById(cardId);
    if (card) {
        card.classList.toggle('collapsed');
    }
}

// Export functions globally
window.initArtifactChat = initArtifactChat;
window.addMessage = addMessage;
window.sendMessage = sendMessage;
window.authorizeGeneration = authorizeGeneration;
window.saveArtifact = saveArtifact;
window.regenerateField = regenerateField;
window.showRegenerateModal = showRegenerateModal;
window.closeInlineChat = closeInlineChat;
window.sendInlineChat = sendInlineChat;
window.toggleContextCard = toggleContextCard;
window.toggleDeepResearch = toggleDeepResearch;
window.closeDeepResearchModal = closeDeepResearchModal;
window.executeDeepResearch = executeDeepResearch;
window.toggleSkillsDropdown = toggleSkillsDropdown;

// ========== SKILLS MANAGEMENT ==========
// activeSessionSkills declared at top

function toggleSkillsDropdown(e) {
    e.stopPropagation();
    const dropdown = document.getElementById('skillsDropdown');
    const btn = document.getElementById('btnSkills');

    if (dropdown) {
        const isShowing = dropdown.classList.contains('show');

        // Helper to close other dropdowns if needed
        document.querySelectorAll('.model-dropdown, .skills-dropdown').forEach(d => d.classList.remove('show'));

        if (!isShowing) {
            dropdown.classList.add('show');
            if (btn) btn.classList.add('active');
        } else {
            if (btn) btn.classList.remove('active');
        }
    }
}

// Close dropdowns on click outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.model-selector-wrapper') && !e.target.closest('.skills-selector-wrapper')) {
        document.querySelectorAll('.model-dropdown, .skills-dropdown').forEach(d => d.classList.remove('show'));
        document.querySelectorAll('#btnSkills, #modelSelectorBtn').forEach(b => b.classList.remove('active'));
    }
});

async function loadProjectSkills() {
    const config = window.ARTIFACT_CONFIG;
    if (!config) return;

    try {
        const resp = await fetch(`/api/skills?incluir_sistema=true`);
        if (!resp.ok) throw new Error('Falha ao carregar skills');

        let skills = await resp.json();
        renderSkillsContext(skills);
    } catch (e) {
        console.error('[Artifact Chat] Erro ao carregar skills:', e);
        const container = document.getElementById('skillsListContainer');
        if (container) container.innerHTML = '<span style="font-size: 12px; color: var(--text-secondary);">Erro ao carregar skills.</span>';
    }
}

function renderSkillsContext(skills) {
    const container = document.getElementById('skillsListContainer');
    const badge = document.getElementById('activeSkillsCount');
    if (!container) return;

    if (skills.length === 0) {
        container.innerHTML = '<span style="font-size: 12px; color: var(--text-secondary);">Nenhuma skill disponível.</span>';
        if (badge) badge.style.display = 'none';
        return;
    }

    // Sort: System first, then by name
    skills.sort((a, b) => {
        if (a.escopo === b.escopo) return a.nome.localeCompare(b.nome);
        return a.escopo === 'system' ? -1 : 1;
    });

    container.innerHTML = skills.map(skill => {
        const isActive = activeSessionSkills.has(skill.id);
        return `
         <div class="skill-item ${isActive ? 'active' : ''}" 
              onclick="toggleSkillSelection(${skill.id})" 
              style="display: flex; align-items: start; gap: 8px; font-size: 13px; padding: 6px 8px; border-radius: var(--radius-sm); cursor: pointer; transition: var(--transition-fast);">
             <div class="skill-checkbox" style="width: 16px; height: 16px; border: 2px solid ${isActive ? 'var(--chat-accent)' : 'var(--chat-border)'}; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin-top: 2px;">
                 ${isActive ? '<div style="width: 8px; height: 8px; background: var(--chat-accent); border-radius: 1px;"></div>' : ''}
             </div>
             <div style="line-height: 1.3; flex: 1;">
                 <div style="font-weight: 500; display: flex; align-items: center; gap: 4px; color: ${isActive ? 'var(--chat-accent-light)' : 'inherit'}">
                    ${skill.icone || '⚡'} ${skill.nome}
                 </div>
                 <div style="font-size: 11px; color: var(--text-secondary); margin-top: 1px;">
                    ${skill.descricao || ''}
                 </div>
             </div>
         </div>
         `;
    }).join('');

    updateActiveSkillsBadge();
}

function toggleSkillSelection(skillId) {
    if (activeSessionSkills.has(skillId)) {
        activeSessionSkills.delete(skillId);
    } else {
        activeSessionSkills.add(skillId);
    }

    // Re-render skills list
    loadProjectSkills();
    updateActiveSkillsBadge();
}

function updateActiveSkillsBadge() {
    const badge = document.getElementById('activeSkillsCount');
    if (badge) {
        const count = activeSessionSkills.size;
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
}
