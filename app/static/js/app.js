/**
 * Sistema LIA - Scripts da Aplicacao
 * ===================================
 * Scripts simples para interacoes na pagina
 */

// Funcoes utilitarias
// Captura modelo de IA selecionado e envia ao backend (exemplo de integração)
document.addEventListener('DOMContentLoaded', function () {
    const modelDropdown = document.getElementById('ia-model-dropdown');
    if (modelDropdown) {
        modelDropdown.addEventListener('change', function () {
            const modeloSelecionado = this.value;
            // Exemplo: salvar em localStorage para uso posterior
            localStorage.setItem('modelo_ia_selecionado', modeloSelecionado);
            // Opcional: enviar ao backend via fetch/ajax
            // fetch('/api/set-modelo-ia', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify({ modelo: modeloSelecionado })
            // });
        });
    }
});
const App = {
    /**
     * Mostra overlay de loading
     */
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    },

    /**
     * Oculta overlay de loading
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    /**
     * Confirma acao antes de executar
     */
    confirm(message, callback) {
        if (confirm(message)) {
            callback();
        }
    }
};

// Mostrar loading ao submeter formularios
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            App.showLoading();
        });
    });
});
