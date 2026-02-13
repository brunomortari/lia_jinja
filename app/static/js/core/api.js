/**
 * Sistema LIA - Core: API Wrapper
 * ================================
 */

(function() {
    'use strict';

    window.LIA = window.LIA || {};

    window.LIA.api = {
        baseUrl: '',

        // Configurações padrão
        defaultOptions: {
            headers: {
                'Content-Type': 'application/json'
            }
        },

        // Método genérico de fetch
        async fetch(url, options = {}) {
            const mergedOptions = {
                ...this.defaultOptions,
                ...options,
                headers: {
                    ...this.defaultOptions.headers,
                    ...options.headers
                }
            };

            try {
                const response = await fetch(this.baseUrl + url, mergedOptions);

                // Se não for OK, lançar erro
                if (!response.ok) {
                    let errorMessage = `Erro ${response.status}`;

                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorData.message || errorMessage;
                    } catch (e) {
                        // Não conseguiu parsear JSON
                    }

                    throw new Error(errorMessage);
                }

                // Tentar retornar JSON, senão retornar texto
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                }
                return await response.text();

            } catch (error) {
                // Mostrar notificação de erro se disponível
                if (window.LIA.notify) {
                    window.LIA.notify.error(error.message);
                }
                throw error;
            }
        },

        // GET
        async get(url, options = {}) {
            return this.fetch(url, { ...options, method: 'GET' });
        },

        // POST
        async post(url, data, options = {}) {
            return this.fetch(url, {
                ...options,
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        // PUT
        async put(url, data, options = {}) {
            return this.fetch(url, {
                ...options,
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        // DELETE
        async delete(url, options = {}) {
            return this.fetch(url, { ...options, method: 'DELETE' });
        },

        // POST com FormData (para uploads)
        async postForm(url, formData, options = {}) {
            const formOptions = { ...options };
            delete formOptions.headers; // Deixar o browser definir o Content-Type

            return this.fetch(url, {
                ...formOptions,
                method: 'POST',
                body: formData
            });
        }
    };
})();
