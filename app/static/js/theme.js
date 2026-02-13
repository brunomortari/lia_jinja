/**
 * Sistema LIA - Controle de Tema
 * ===============================
 * Gerencia múltiplos temas:
 * - light: Tema claro
 * - dark: Tema escuro azulado
 * - dark-gray: Tema cinza escuro (ChatGPT/Gemini)
 * - nativa: Tema verde oliva (Floresta)
 */

const Theme = {
    THEME_KEY: 'lia_theme',

    // Lista de temas disponíveis
    THEMES: [
        { id: 'light', name: 'Claro', icon: '☀️', description: 'Tema claro padrão' },
        { id: 'dark', name: 'Escuro', icon: '🌙', description: 'Tema escuro azulado' },
        { id: 'dark-gray', name: 'Cinza', icon: '🌑', description: 'Estilo ChatGPT/Gemini' },
        { id: 'nativa', name: 'Nativa', icon: '🌲', description: 'Verde floresta' }
    ],

    /**
     * Inicializa o tema
     */
    init() {
        // Carregar tema salvo ou usar padrão (light)
        const savedTheme = localStorage.getItem(this.THEME_KEY) || 'light';
        this.set(savedTheme);

        // Configurar botão de alternância
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                // Se clicar com shift, abre seletor
                if (e.shiftKey) {
                    this.showSelector();
                } else {
                    this.cycle();
                }
            });

            // Long press para abrir seletor em mobile
            let pressTimer;
            toggleBtn.addEventListener('touchstart', () => {
                pressTimer = setTimeout(() => this.showSelector(), 500);
            });
            toggleBtn.addEventListener('touchend', () => clearTimeout(pressTimer));
        }

        // Criar seletor de temas se não existir
        this.createSelector();
    },

    /**
     * Obtém o tema atual
     */
    get() {
        return document.body.getAttribute('data-theme') || 'light';
    },

    /**
     * Obtém informações do tema atual
     */
    getInfo(themeId = null) {
        const id = themeId || this.get();
        return this.THEMES.find(t => t.id === id) || this.THEMES[0];
    },

    /**
     * Define o tema
     */
    set(theme) {
        // Validar tema
        const validTheme = this.THEMES.find(t => t.id === theme);
        if (!validTheme) {
            theme = 'light';
        }

        // Adicionar classe de transição apenas se for troca de tema (não no carregamento inicial)
        const isThemeChange = document.body.hasAttribute('data-theme') && document.body.getAttribute('data-theme') !== theme;
        if (isThemeChange) {
            document.body.classList.add('theme-transitioning');
            // Remover classe após transição
            setTimeout(() => {
                document.body.classList.remove('theme-transitioning');
            }, 200);
        }

        document.body.setAttribute('data-theme', theme);
        localStorage.setItem(this.THEME_KEY, theme);

        // Atualizar ícone
        const icon = document.getElementById('theme-icon');
        if (icon) {
            const themeInfo = this.getInfo(theme);
            icon.textContent = themeInfo.icon;
            icon.title = themeInfo.name;
        }

        // Atualizar seletor se existir
        this.updateSelector(theme);

        // Disparar evento customizado
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    },

    /**
     * Alterna para o próximo tema na lista
     */
    cycle() {
        const current = this.get();
        const currentIndex = this.THEMES.findIndex(t => t.id === current);
        const nextIndex = (currentIndex + 1) % this.THEMES.length;
        this.set(this.THEMES[nextIndex].id);
    },

    /**
     * Alterna apenas entre claro e escuro
     */
    toggle() {
        const current = this.get();
        const next = current === 'light' ? 'dark' : 'light';
        this.set(next);
    },

    /**
     * Verifica se é um tema escuro
     */
    isDark() {
        const theme = this.get();
        return theme !== 'light';
    },

    /**
     * Cria o seletor de temas
     */
    createSelector() {
        // Verificar se já existe
        if (document.getElementById('theme-selector')) return;

        const selector = document.createElement('div');
        selector.id = 'theme-selector';
        selector.className = 'theme-selector';
        selector.innerHTML = `
            <div class="theme-selector-backdrop"></div>
            <div class="theme-selector-content">
                <div class="theme-selector-header">
                    <h4>Escolha o Tema</h4>
                    <button class="theme-selector-close">&times;</button>
                </div>
                <div class="theme-selector-grid">
                    ${this.THEMES.map(theme => `
                        <button class="theme-option" data-theme="${theme.id}">
                            <span class="theme-option-icon">${theme.icon}</span>
                            <span class="theme-option-name">${theme.name}</span>
                            <span class="theme-option-desc">${theme.description}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        document.body.appendChild(selector);

        // Event listeners
        selector.querySelector('.theme-selector-backdrop').addEventListener('click', () => this.hideSelector());
        selector.querySelector('.theme-selector-close').addEventListener('click', () => this.hideSelector());

        selector.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', () => {
                this.set(btn.dataset.theme);
                this.hideSelector();
            });
        });

        // Estilos inline do seletor
        const style = document.createElement('style');
        style.textContent = `
            .theme-selector {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 9999;
                align-items: center;
                justify-content: center;
            }
            .theme-selector.show {
                display: flex;
            }
            .theme-selector-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
            }
            .theme-selector-content {
                position: relative;
                background: var(--bg-secondary, #ffffff);
                border-radius: 16px;
                padding: 24px;
                min-width: 320px;
                max-width: 90vw;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                border: 1px solid var(--border, #e2e8f0);
            }
            .theme-selector-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .theme-selector-header h4 {
                margin: 0;
                font-size: 1.1rem;
                color: var(--text-primary, #0f172a);
            }
            .theme-selector-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                color: var(--text-muted, #94a3b8);
                cursor: pointer;
                padding: 0;
                line-height: 1;
            }
            .theme-selector-close:hover {
                color: var(--text-primary, #0f172a);
            }
            .theme-selector-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }
            .theme-option {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                padding: 20px 16px;
                background: var(--bg-tertiary, #f1f5f9);
                border: 2px solid transparent;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .theme-option:hover {
                background: var(--bg-hover, #e2e8f0);
                border-color: var(--accent, #334155);
            }
            .theme-option.active {
                border-color: var(--accent, #334155);
                background: var(--accent-soft, rgba(51, 65, 85, 0.1));
            }
            .theme-option-icon {
                font-size: 2rem;
            }
            .theme-option-name {
                font-size: 0.9rem;
                font-weight: 600;
                color: var(--text-primary, #0f172a);
            }
            .theme-option-desc {
                font-size: 0.7rem;
                color: var(--text-muted, #94a3b8);
                text-align: center;
            }
            @media (max-width: 400px) {
                .theme-selector-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    },

    /**
     * Mostra o seletor de temas
     */
    showSelector() {
        const selector = document.getElementById('theme-selector');
        if (selector) {
            selector.classList.add('show');
            this.updateSelector(this.get());
        }
    },

    /**
     * Esconde o seletor de temas
     */
    hideSelector() {
        const selector = document.getElementById('theme-selector');
        if (selector) {
            selector.classList.remove('show');
        }
    },

    /**
     * Atualiza o seletor para mostrar tema ativo
     */
    updateSelector(activeTheme) {
        const selector = document.getElementById('theme-selector');
        if (!selector) return;

        selector.querySelectorAll('.theme-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === activeTheme);
        });
    }
};

// Inicializar tema ao carregar página
document.addEventListener('DOMContentLoaded', () => {
    Theme.init();
});

// Exportar para uso global
window.Theme = Theme;
