/**
 * Sistema LIA - Componente: Sidebar
 * ==================================
 */

(function() {
    'use strict';

    window.LIA = window.LIA || {};
    window.LIA.sidebar = {
        elements: {
            sidebar: null,
            toggle: null,
            app: null
        },

        init() {
            this.elements.sidebar = document.getElementById('sidebar');
            this.elements.toggle = document.getElementById('sidebar-toggle');
            this.elements.app = document.getElementById('app');

            if (!this.elements.sidebar || !this.elements.toggle) {
                return;
            }

            this.bindEvents();
            this.restoreState();
            this.initAccordions();
        },

        bindEvents() {
            this.elements.toggle.addEventListener('click', () => this.toggle());
        },

        toggle() {
            this.elements.sidebar.classList.toggle('collapsed');
            if (this.elements.app) {
                this.elements.app.classList.toggle('sidebar-collapsed');
            }
            this.saveState();
        },

        saveState() {
            const isCollapsed = this.elements.sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebar_collapsed', isCollapsed);
        },

        restoreState() {
            if (localStorage.getItem('sidebar_collapsed') === 'true') {
                this.elements.sidebar.classList.add('collapsed');
                if (this.elements.app) {
                    this.elements.app.classList.add('sidebar-collapsed');
                }
            }
        },

        initAccordions() {
            const triggers = document.querySelectorAll('.nav-accordion-trigger');

            triggers.forEach(trigger => {
                const targetId = trigger.getAttribute('data-target');
                const content = document.getElementById(targetId);

                if (!content) return;

                // Evento de clique
                trigger.addEventListener('click', () => {
                    content.classList.toggle('open');
                    trigger.classList.toggle('open');
                    localStorage.setItem('accordion_' + targetId, content.classList.contains('open'));
                });

                // Restaurar estado
                const savedState = localStorage.getItem('accordion_' + targetId);
                if (savedState === 'true' || content.classList.contains('open')) {
                    content.classList.add('open');
                    trigger.classList.add('open');
                }
            });
        },

        collapse() {
            this.elements.sidebar.classList.add('collapsed');
            if (this.elements.app) {
                this.elements.app.classList.add('sidebar-collapsed');
            }
            this.saveState();
        },

        expand() {
            this.elements.sidebar.classList.remove('collapsed');
            if (this.elements.app) {
                this.elements.app.classList.remove('sidebar-collapsed');
            }
            this.saveState();
        }
    };

    // Auto-inicializar quando DOM estiver pronto
    document.addEventListener('DOMContentLoaded', () => {
        window.LIA.sidebar.init();
    });
})();
