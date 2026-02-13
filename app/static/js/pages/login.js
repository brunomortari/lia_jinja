/**
 * Sistema LIA - Página: Login
 * ============================
 */

(function() {
    'use strict';

    // Toggle visibility de senha
    function togglePassword() {
        const passwordInput = document.getElementById('password');
        const eyeIcon = document.getElementById('eyeIcon');

        if (!passwordInput || !eyeIcon) return;

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            // Muda ícone para "olho com linha"
            eyeIcon.innerHTML = `
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
                <line x1="1" y1="1" x2="23" y2="23" stroke-width="2" />
            `;
        } else {
            passwordInput.type = 'password';
            // Volta ícone normal
            eyeIcon.innerHTML = `
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
            `;
        }
    }

    // Expor função globalmente
    window.togglePassword = togglePassword;

    // Inicialização quando DOM estiver pronto
    document.addEventListener('DOMContentLoaded', function() {
        const loginForm = document.getElementById('liaLoginForm');

        if (loginForm) {
            loginForm.addEventListener('submit', function(e) {
                const btn = this.querySelector('.submit-btn');
                if (!btn) return;

                const originalText = btn.innerHTML;

                // Estado de loading
                btn.innerHTML = '<span>Autenticando...</span>';
                btn.style.opacity = '0.8';
                btn.style.cursor = 'wait';
                btn.disabled = true;

                // Permite envio padrão do formulário
                // O backend irá processar a requisição
            });
        }

        // Feedback visual nos inputs
        const inputs = document.querySelectorAll('.input-field');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
        });
    });
})();
