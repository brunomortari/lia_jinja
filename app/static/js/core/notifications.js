/**
 * Sistema LIA - Core: Sistema de Notificações
 * ============================================
 */

(function() {
    'use strict';

    // Criar container de notificações se não existir
    function getContainer() {
        let container = document.getElementById('lia-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'lia-notifications';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    // Criar notificação
    function createNotification(message, type, duration) {
        const container = getContainer();

        const colors = {
            success: { bg: '#D1FAE5', text: '#065F46', border: '#10b981' },
            error: { bg: '#FEE2E2', text: '#991B1B', border: '#ef4444' },
            warning: { bg: '#FEF3C7', text: '#92400E', border: '#f59e0b' },
            info: { bg: '#DBEAFE', text: '#1E40AF', border: '#3b82f6' }
        };

        const color = colors[type] || colors.info;

        const notification = document.createElement('div');
        notification.style.cssText = `
            padding: 16px 20px;
            background: ${color.bg};
            color: ${color.text};
            border-left: 4px solid ${color.border};
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            animation: slideIn 0.3s ease;
            font-size: 14px;
            font-weight: 500;
        `;

        notification.innerHTML = `
            <span>${message}</span>
            <button style="
                background: none;
                border: none;
                color: ${color.text};
                cursor: pointer;
                font-size: 18px;
                padding: 0;
                opacity: 0.6;
            ">&times;</button>
        `;

        // Botão de fechar
        notification.querySelector('button').addEventListener('click', () => {
            removeNotification(notification);
        });

        container.appendChild(notification);

        // Auto-remover após duração
        if (duration > 0) {
            setTimeout(() => {
                removeNotification(notification);
            }, duration);
        }

        return notification;
    }

    // Remover notificação com animação
    function removeNotification(notification) {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    // Adicionar estilos de animação
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // API pública
    window.LIA = window.LIA || {};
    window.LIA.notify = {
        show: function(message, type = 'info', duration = 5000) {
            return createNotification(message, type, duration);
        },
        success: function(message, duration) {
            return this.show(message, 'success', duration);
        },
        error: function(message, duration) {
            return this.show(message, 'error', duration);
        },
        warning: function(message, duration) {
            return this.show(message, 'warning', duration);
        },
        info: function(message, duration) {
            return this.show(message, 'info', duration);
        }
    };

    // Alias global para compatibilidade
    window.mostrarNotificacao = function(message, type, duration) {
        return window.LIA.notify.show(message, type, duration);
    };
})();
