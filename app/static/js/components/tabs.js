/**
 * Sistema LIA - Componente: Tabs
 * ===============================
 */

(function() {
    'use strict';

    window.LIA = window.LIA || {};
    window.LIA.tabs = {
        init(container, options = {}) {
            const tabContainer = typeof container === 'string'
                ? document.querySelector(container)
                : container;

            if (!tabContainer) return null;

            const config = {
                tabSelector: '.tab',
                contentSelector: '.tab-content',
                activeClass: 'active',
                storageKey: options.storageKey || null,
                onChange: options.onChange || null,
                ...options
            };

            const tabs = tabContainer.querySelectorAll(config.tabSelector);
            const contents = document.querySelectorAll(config.contentSelector);

            function activate(targetTab) {
                const targetId = targetTab.dataset.tab;

                // Desativar todas as tabs
                tabs.forEach(tab => tab.classList.remove(config.activeClass));
                contents.forEach(content => content.classList.remove(config.activeClass));

                // Ativar tab selecionada
                targetTab.classList.add(config.activeClass);

                // Ativar conteúdo correspondente
                const targetContent = document.getElementById(targetId) ||
                                      document.querySelector(`[data-tab-content="${targetId}"]`);
                if (targetContent) {
                    targetContent.classList.add(config.activeClass);
                }

                // Salvar estado
                if (config.storageKey) {
                    localStorage.setItem(config.storageKey, targetId);
                }

                // Callback
                if (config.onChange) {
                    config.onChange(targetId, targetTab);
                }
            }

            // Bind eventos
            tabs.forEach(tab => {
                tab.addEventListener('click', () => activate(tab));
            });

            // Restaurar estado salvo
            if (config.storageKey) {
                const savedTab = localStorage.getItem(config.storageKey);
                if (savedTab) {
                    const tabToActivate = Array.from(tabs).find(t => t.dataset.tab === savedTab);
                    if (tabToActivate) {
                        activate(tabToActivate);
                    }
                }
            }

            return {
                activate: (tabId) => {
                    const tab = Array.from(tabs).find(t => t.dataset.tab === tabId);
                    if (tab) activate(tab);
                },
                getActive: () => {
                    const activeTab = Array.from(tabs).find(t => t.classList.contains(config.activeClass));
                    return activeTab ? activeTab.dataset.tab : null;
                }
            };
        }
    };
})();
