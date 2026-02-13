/**
 * Sistema LIA - Configuracoes: Skills (Habilidades)
 * ==================================================
 * Gerenciamento de skills: CRUD + Wizard Chat com IA
 */

let allSkills = [];
let wizardHistory = [];
let wizardSending = false;
let pendingSkillData = null;

// ========== LOAD & RENDER ==========

let availableModels = [];

async function loadModels() {
    try {
        const resp = await fetch('/api/ia/models');
        if (!resp.ok) throw new Error('Erro ao carregar modelos');
        const data = await resp.json();
        availableModels = data.models || [];
    } catch (e) {
        console.error('Erro ao carregar modelos:', e);
    }
}

async function loadSkills() {
    try {
        await loadModels(); // Carregar modelos antes
        const resp = await fetch('/api/skills?incluir_sistema=true');
        if (!resp.ok) throw new Error('Erro ao carregar skills');
        allSkills = await resp.json();
        renderSkills();
    } catch (e) {
        console.error('Erro ao carregar skills:', e);
    }
}

function renderSkills() {
    const systemSkills = allSkills.filter(s => s.escopo === 'system');
    const userSkills = allSkills.filter(s => s.escopo === 'user');

    const systemList = document.getElementById('systemSkillsList');
    const userList = document.getElementById('userSkillsList');
    const noSkills = document.getElementById('noUserSkills');

    if (systemList) {
        systemList.innerHTML = systemSkills.map(s => renderSkillCard(s, false)).join('');
    }

    if (userList) {
        userList.innerHTML = userSkills.map(s => renderSkillCard(s, true)).join('');
    }

    if (noSkills) {
        noSkills.style.display = userSkills.length === 0 ? 'block' : 'none';
    }
}

function renderSkillCard(skill, editable) {
    const badgeClass = skill.escopo === 'system' ? 'system' : 'user';
    const badgeText = skill.escopo === 'system' ? 'Sistema' : 'Minha';

    const actions = editable
        ? `<div class="skill-card-actions">
            <button onclick="event.stopPropagation(); abrirEditarSkill(${skill.id})" title="Editar">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="btn-delete" onclick="event.stopPropagation(); excluirSkill(${skill.id}, '${skill.nome.replace(/'/g, "\\'")}')" title="Excluir">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
           </div>`
        : '';

    return `
    <div class="skill-card" id="skill-card-${skill.id}" onclick="toggleSkillCard(${skill.id})">
        <div class="skill-card-header">
            <div class="skill-card-info">
                <div class="skill-card-nome">${skill.nome}</div>
                <div class="skill-card-desc">${skill.descricao || 'Sem descricao'}</div>
            </div>
            ${skill.tools && skill.tools.length ? '<span class="skill-badge tools" title="Usa ferramentas">🛠️</span>' : ''}
            ${skill.textos_base && skill.textos_base.length ? '<span class="skill-badge docs" title="Usa base de conhecimento">📚</span>' : ''}
            <span class="skill-badge ${badgeClass}">${badgeText}</span>
            ${actions}
        </div>
        <div class="skill-card-body">
            <label>Instrucoes</label>
            <div class="instrucoes-text">${skill.instrucoes}</div>
        </div>
    </div>`;
}

function toggleSkillCard(skillId) {
    const card = document.getElementById(`skill-card-${skillId}`);
    if (card) card.classList.toggle('expanded');
}

// ========== CRUD ==========

async function excluirSkill(skillId, nome) {
    if (!confirm(`Excluir a skill "${nome}"?`)) return;

    try {
        const resp = await fetch(`/api/skills/${skillId}`, { method: 'DELETE' });
        if (!resp.ok) throw new Error('Erro ao excluir');
        await loadSkills();
    } catch (e) {
        alert('Erro ao excluir skill: ' + e.message);
    }
}

function abrirEditarSkill(skillId) {
    const skill = allSkills.find(s => s.id === skillId);
    if (!skill) return;

    // Alternar views
    document.getElementById('skills-list-view').style.display = 'none';
    const createView = document.getElementById('skills-create-view');
    createView.style.display = 'block';

    createView.innerHTML = `
    <div class="skills-section-header">
        <h3>Editar Habilidade: ${skill.nome}</h3>
        <button class="btn btn-secondary" onclick="fecharWizard()">Voltar para Lista</button>
    </div>

    <div class="edit-skill-container" style="max-width: 800px; margin: 0 auto; background: var(--bg-secondary); padding: 30px; border-radius: 12px; margin-top: 20px;">
        <div class="form-group">
            <label>Nome</label>
            <input type="text" id="editNome" value="${skill.nome}" maxlength="200" style="padding: 10px; width: 100%; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary);">
        </div>
        <div class="form-group" style="margin-top: 15px;">
            <label>Descricao</label>
            <input type="text" id="editDescricao" value="${skill.descricao || ''}" maxlength="1000" style="padding: 10px; width: 100%; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary);">
        </div>
        <div class="form-group" style="margin-top: 15px;">
            <label>Instrucoes (Prompt)</label>
            <textarea id="editInstrucoes" rows="8" maxlength="5000" style="padding: 10px; width: 100%; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-family: monospace;">${skill.instrucoes}</textarea>
        </div>
        <div class="form-group" style="margin-top: 15px;">
            <label>Tools (JSON)</label>
            <input type="text" id="editTools" value="${skill.tools ? JSON.stringify(skill.tools) : ''}" placeholder='Ex: ["google_search"]' style="padding: 10px; width: 100%; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-family: monospace;">
        </div>
        <div class="form-group" style="margin-top: 15px;">
            <label style="display:flex; justify-content:space-between; align-items:center;">
                Base de Conhecimento (JSON)
                <button class="btn btn-sm btn-light" onclick="document.getElementById('editFileUpload').click()">📎 Adicionar Arquivo</button>
            </label>
            <input type="file" id="editFileUpload" style="display: none;" onchange="uploadArquivoParaEdit(this)">
            <textarea id="editTextosBase" rows="6" placeholder='Ex: [{"titulo": "Lei...", "conteudo": "..."}]' style="padding: 10px; width: 100%; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-family: monospace;">${skill.textos_base ? JSON.stringify(skill.textos_base, null, 2) : ''}</textarea>
        </div>
        <div class="form-actions" style="margin-top: 30px; display: flex; justify-content: flex-end; gap: 10px;">
            <button class="btn btn-secondary" onclick="fecharWizard()">Cancelar</button>
            <button class="btn btn-primary" onclick="salvarEdicao(${skill.id})">Salvar Alterações</button>
        </div>
    </div>`;
}

async function uploadArquivoParaEdit(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    // Feedback visual
    const btn = input.previousElementSibling.querySelector('button');
    const originalText = btn.textContent;
    btn.textContent = '⏳ Processando...';
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const resp = await fetch('/api/ia-upload/', {
            method: 'POST',
            body: formData
        });

        if (!resp.ok) throw new Error('Falha no upload');
        const data = await resp.json();

        if (data.extracted_text) {
            const area = document.getElementById('editTextosBase');
            let current = [];
            try {
                if (area.value.trim()) current = JSON.parse(area.value);
            } catch (e) { }

            if (!Array.isArray(current)) current = [];

            current.push({
                titulo: data.filename,
                conteudo: data.extracted_text
            });

            area.value = JSON.stringify(current, null, 2);
            alert(`Arquivo "${data.filename}" processado e adicionado!`);
        } else {
            alert('Arquivo enviado, mas nenhum texto pôde ser extraído.');
        }

    } catch (e) {
        alert('Erro no upload: ' + e.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
        input.value = '';
    }
}

async function salvarEdicao(skillId) {
    let tools = null;
    try {
        const toolsStr = document.getElementById('editTools').value.trim();
        if (toolsStr) {
            tools = JSON.parse(toolsStr);
            if (!Array.isArray(tools)) throw new Error('Tools deve ser uma lista JSON');
        }
    } catch (e) {
        alert('Erro no formato JSON das tools: ' + e.message);
        return;
    }

    let textosBase = null;
    try {
        const textosStr = document.getElementById('editTextosBase').value.trim();
        if (textosStr) {
            textosBase = JSON.parse(textosStr);
            if (!Array.isArray(textosBase)) throw new Error('Base de conhecimento deve ser uma lista JSON');
        }
    } catch (e) {
        alert('Erro no formato JSON da Base de Conhecimento: ' + e.message);
        return;
    }

    const data = {
        nome: document.getElementById('editNome').value,
        descricao: document.getElementById('editDescricao').value || null,
        instrucoes: document.getElementById('editInstrucoes').value,
        tools: tools,
        textos_base: textosBase
    };

    try {
        const resp = await fetch(`/api/skills/${skillId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Erro ao salvar');
        }
        fecharWizard();
        await loadSkills();
    } catch (e) {
        alert('Erro: ' + e.message);
    }
}

// ========== WIZARD CHAT ==========

function abrirCriarSkill() {
    // Alternar views
    document.getElementById('skills-list-view').style.display = 'none';
    const createView = document.getElementById('skills-create-view');
    createView.style.display = 'block';

    const modelOptions = availableModels.map(m =>
        `<option value="${m.id}">${m.name} (${m.context_window})</option>`
    ).join('');

    createView.innerHTML = `
    <div class="skills-section-header">
        <h3>Criar Habilidade com IA</h3>
        <div style="display: flex; gap: 10px; align-items: center;">
             <select id="wizardModelSelect" style="padding: 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary);">
                ${modelOptions}
             </select>
            <button class="btn btn-secondary" onclick="fecharWizard()">Voltar para Lista</button>
        </div>
    </div>
    
    <div class="wizard-container" style="display: flex; gap: 20px; height: calc(100vh - 250px);">
        <!-- Chat Column -->
        <div class="wizard-chat-column" style="flex: 1; display: flex; flex-direction: column; background: var(--bg-secondary); border-radius: 12px; padding: 20px;">
            <div class="wizard-chat-messages" id="wizardMessages" style="flex: 1; overflow-y: auto; margin-bottom: 20px;"></div>
            
            <!-- File Upload Preview -->
            <div id="wizardFilePreview" style="display: none; padding: 10px; background: var(--bg-hover); border-radius: 8px; margin-bottom: 10px; font-size: 0.9em; display: flex; align-items: center; justify-content: space-between;">
                <span id="wizardFileName"></span>
                <button onclick="clearWizardFile()" style="background: none; border: none; cursor: pointer; color: var(--text-secondary);">❌</button>
            </div>

            <div class="wizard-input-area" style="display: flex; gap: 10px; align-items: center;">
                <button class="btn-icon" onclick="document.getElementById('wizardFileUpload').click()" title="Anexar arquivo" style="padding: 10px; background: var(--bg-hover); border: none; border-radius: 8px; cursor: pointer;">
                    📎
                </button>
                <input type="file" id="wizardFileUpload" style="display: none;" onchange="handleWizardFileUpload(this)">
                
                <input type="text" id="wizardInput" style="flex: 1; padding: 12px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary);" 
                       placeholder="Descreva o que voce quer..."
                       onkeydown="if(event.key==='Enter' && !event.shiftKey) enviarMensagemWizard()">
                <button id="wizardSendBtn" class="btn btn-primary" onclick="enviarMensagemWizard()">Enviar</button>
            </div>
        </div>

        <!-- Preview Column -->
        <div class="wizard-preview-column" id="wizardPreviewArea" style="flex: 1; overflow-y: auto; padding: 10px;">
            <div style="text-align: center; color: var(--text-secondary); margin-top: 50px;">
                <div style="font-size: 3rem; margin-bottom: 20px;">🤖</div>
                <p>O rascunho da sua habilidade aparecerá aqui conforme você conversa com a IA.</p>
            </div>
        </div>
    </div>`;

    wizardHistory = [];
    pendingSkillData = null;
    currentWizardFile = null;

    // Mensagem inicial
    const msgs = document.getElementById('wizardMessages');
    const inicial = "Ola! Vou te ajudar a criar uma nova **habilidade** para a IA.\n\n" +
        "**Me conta: o que voce gostaria que a IA fizesse diferente ao gerar seus documentos?**";
    addWizardMessage('assistant', inicial);

    setTimeout(() => document.getElementById('wizardInput')?.focus(), 200);
}

// Wizard File Handling
let currentWizardFile = null;

async function handleWizardFileUpload(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    // Preview
    const preview = document.getElementById('wizardFilePreview');
    const nameSpan = document.getElementById('wizardFileName');

    preview.style.display = 'flex';
    nameSpan.textContent = `⏳ Processando: ${file.name}...`;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const resp = await fetch('/api/ia-upload/', {
            method: 'POST',
            body: formData
        });

        if (!resp.ok) throw new Error('Falha no upload');
        const data = await resp.json();

        if (data.extracted_text) {
            currentWizardFile = {
                filename: data.filename,
                extracted_text: data.extracted_text
            };
            nameSpan.textContent = `📎 ${data.filename} (Texto extraído)`;
        } else {
            nameSpan.textContent = `⚠️ ${data.filename} (Sem texto extraído)`;
        }

    } catch (e) {
        alert('Erro no upload: ' + e.message);
        clearWizardFile();
    } finally {
        input.value = '';
    }
}

function clearWizardFile() {
    currentWizardFile = null;
    document.getElementById('wizardFilePreview').style.display = 'none';
    document.getElementById('wizardFileName').textContent = '';
}

function fecharWizard() {
    document.getElementById('skills-create-view').style.display = 'none';
    document.getElementById('skills-list-view').style.display = 'block';
}

function addWizardMessage(role, text) {
    const msgs = document.getElementById('wizardMessages');
    if (!msgs) return;

    // Limpar marcadores internos do texto visivel
    let displayText = text.replace(/\[SKILL_READY\]/g, '').trim();
    // Remover JSON no final se presente
    displayText = displayText.replace(/\{[\s\S]*\}$/m, '').trim();

    const div = document.createElement('div');
    div.className = `wizard-msg ${role}`;
    div.innerHTML = formatMarkdown(displayText);
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

async function enviarMensagemWizard() {
    if (wizardSending) return;

    const input = document.getElementById('wizardInput');
    let content = input.value.trim();

    // Se tem arquivo e sem texto, o arquivo conta como mensagem
    if (!content && !currentWizardFile) return;

    input.value = '';

    // Visualmente mostrar o arquivo na mensagem do usuario
    let displayContent = content;
    if (currentWizardFile) {
        displayContent += `<br><br><em>[Arquivo Anexado: ${currentWizardFile.filename}]</em>`;
        // Adicionar contexto do arquivo na mensagem tecnica
        content += `\n\n--- CONTEXTO DO ARQUIVO ANEXO (${currentWizardFile.filename}) ---\n${currentWizardFile.extracted_text}\n--- FIM DO ARQUIVO ---`;
    }

    addWizardMessage('user', displayContent);
    wizardHistory.push({ role: 'user', content }); // Histórico leva o texto completo com anexo

    // Limpar anexo apos envio
    clearWizardFile();

    const sendBtn = document.getElementById('wizardSendBtn');
    sendBtn.disabled = true;
    wizardSending = true;

    // Adicionar placeholder de resposta
    const msgs = document.getElementById('wizardMessages');
    const aiMsg = document.createElement('div');
    aiMsg.className = 'wizard-msg assistant';
    aiMsg.textContent = '...';
    msgs.appendChild(aiMsg);
    msgs.scrollTop = msgs.scrollHeight;

    const modelId = document.getElementById('wizardModelSelect').value;

    try {
        const resp = await fetch('/api/skills/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content,
                history: wizardHistory,
                model: modelId
            }),
        });

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'chunk') {
                        fullResponse += data.content;
                        // Atualizar mensagem sem marcadores
                        let display = fullResponse.replace(/\[SKILL_READY\]/g, '').replace(/\{[\s\S]*$/m, '');
                        aiMsg.innerHTML = formatMarkdown(display.trim());
                        msgs.scrollTop = msgs.scrollHeight;
                    }

                    if (data.type === 'skill_ready' && data.skill) {
                        pendingSkillData = data.skill;
                        mostrarPreview(data.skill);
                    }
                } catch (e) { /* ignore parse errors */ }
            }
        }

        wizardHistory.push({ role: 'assistant', content: fullResponse });

    } catch (e) {
        aiMsg.textContent = 'Erro ao se comunicar com a IA. Tente novamente.';
        console.error('Erro wizard:', e);
    } finally {
        sendBtn.disabled = false;
        wizardSending = false;
    }
}

function mostrarPreview(skill) {
    const area = document.getElementById('wizardPreviewArea');
    if (!area) return;

    area.innerHTML = `
    <div class="skill-preview">
        <h4>${skill.nome}</h4>
        <div style="margin-bottom: 12px; font-size: 0.9em; color: var(--text-secondary);">
            Revise os dados gerados pela IA e adicione documentos se necessário.
        </div>
        
        <div class="edit-skill-form" style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; margin-bottom: 12px;">
            <div class="form-group">
                <label>Nome</label>
                <input type="text" id="previewNome" value="${skill.nome}" maxlength="200">
            </div>
            <div class="form-group">
                <label>Descricao</label>
                <input type="text" id="previewDescricao" value="${skill.descricao || ''}" maxlength="1000">
            </div>
            <div class="form-group">
                <label>Instrucoes</label>
                <textarea id="previewInstrucoes" rows="6" maxlength="5000">${skill.instrucoes}</textarea>
            </div>
            <div class="form-group">
                <label>Tools (JSON Array - Opcional)</label>
                <input type="text" id="previewTools" value="${skill.tools ? JSON.stringify(skill.tools) : ''}" placeholder='Ex: ["google_search"]'>
            </div>
            <div class="form-group">
                <label style="display:flex; justify-content:space-between; align-items:center;">
                    Base de Conhecimento (JSON)
                    <button class="btn btn-sm btn-light" onclick="document.getElementById('previewFileUpload').click()">📎 Adicionar Arquivo</button>
                </label>
                <input type="file" id="previewFileUpload" style="display: none;" onchange="uploadArquivoParaPreview(this)">
                <textarea id="previewTextosBase" rows="4" placeholder='Cole aqui o JSON dos documentos: [{"titulo": "...", "conteudo": "..."}]'>${skill.textos_base ? JSON.stringify(skill.textos_base, null, 2) : ''}</textarea>
            </div>
        </div>

        <div class="skill-preview-actions">
            <button class="btn btn-primary" onclick="salvarSkillDoWizard()">Salvar Habilidade</button>
            <button class="btn btn-secondary" onclick="document.getElementById('wizardPreviewArea').innerHTML=''">Gostaria de mudar algo na conversa...</button>
        </div>
    </div>`;
}

async function uploadArquivoParaPreview(input) {
    // Reutiliza logica do Edit
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    // Feedback
    const btn = input.previousElementSibling.querySelector('button');
    const originalText = btn.textContent;
    btn.textContent = '⏳ ...';
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const resp = await fetch('/api/ia-upload/', {
            method: 'POST',
            body: formData
        });

        if (!resp.ok) throw new Error('Falha no upload');
        const data = await resp.json();

        if (data.extracted_text) {
            const area = document.getElementById('previewTextosBase');
            let current = [];
            try {
                if (area.value.trim()) current = JSON.parse(area.value);
            } catch (e) { }

            if (!Array.isArray(current)) current = [];

            current.push({
                titulo: data.filename,
                conteudo: data.extracted_text
            });

            area.value = JSON.stringify(current, null, 2);
            // alerta discreto
            // alert(`Arquivo "${data.filename}" adicionado!`);
        }

    } catch (e) {
        alert('Erro no upload: ' + e.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
        input.value = '';
    }
}

async function salvarSkillDoWizard() {
    if (!pendingSkillData) return;

    let tools = null;
    try {
        const toolsStr = document.getElementById('previewTools').value.trim();
        if (toolsStr) {
            tools = JSON.parse(toolsStr);
            if (!Array.isArray(tools)) throw new Error('Tools deve ser uma lista JSON');
        }
    } catch (e) {
        alert('Erro no formato JSON das tools: ' + e.message);
        return;
    }

    let textosBase = null;
    try {
        const textosStr = document.getElementById('previewTextosBase').value.trim();
        if (textosStr) {
            textosBase = JSON.parse(textosStr);
            if (!Array.isArray(textosBase)) throw new Error('Base de conhecimento deve ser uma lista JSON');
        }
    } catch (e) {
        alert('Erro no formato JSON da Base de Conhecimento: ' + e.message);
        return;
    }

    const data = {
        nome: document.getElementById('previewNome').value,
        descricao: document.getElementById('previewDescricao').value || null,
        instrucoes: document.getElementById('previewInstrucoes').value,
        tools: tools,
        textos_base: textosBase
    };

    try {
        const resp = await fetch('/api/skills', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Erro ao salvar');
        }

        fecharWizard();
        await loadSkills();
    } catch (e) {
        alert('Erro ao salvar skill: ' + e.message);
    }
}

// ========== INIT ==========

document.addEventListener('DOMContentLoaded', () => {
    // Carregar skills quando a aba for ativada
    const habilidadesBtn = document.querySelector('.config-tab-btn[data-tab="habilidades"]');
    if (habilidadesBtn) {
        habilidadesBtn.addEventListener('click', () => {
            if (allSkills.length === 0) loadSkills();
        });
    }
});
