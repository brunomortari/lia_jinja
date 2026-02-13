/**
 * Sistema LIA - Metro Flow JavaScript
 * ====================================
 * Controla interações do fluxo metro: scroll para estações,
 * tooltips dinâmicos, gestão de artefatos (versões, PDF, SEI, deletar)
 */

// ========== ESTADO GLOBAL ==========

const MetroFlow = {
    activeBranch: null,
    stations: new Map(),
    
    init(branch) {
        this.activeBranch = branch;
        this.setupStationClicks();
        this.setupTooltips();
        this.highlightActiveBranch();
    },
    
    // Scroll suave para card do artefato ao clicar na estação
    setupStationClicks() {
        document.querySelectorAll('.metro-station:not(.locked)').forEach(station => {
            station.addEventListener('click', (e) => {
                const artefatoType = station.dataset.type;
                const card = document.querySelector(`[data-artefato-type="${artefatoType}"]`);
                
                if (card) {
                    card.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                    
                    // Flash visual no card
                    card.style.transition = 'all 0.3s';
                    card.style.transform = 'scale(1.02)';
                    card.style.boxShadow = '0 8px 24px rgba(99, 102, 241, 0.3)';
                    
                    setTimeout(() => {
                        card.style.transform = '';
                        card.style.boxShadow = '';
                    }, 600);
                }
            });
        });
    },
    
    // Tooltips dinâmicos com info das versões
    setupTooltips() {
        document.querySelectorAll('.metro-station').forEach(station => {
            const artefatoType = station.dataset.type;
            const versionCount = station.dataset.versions || '0';
            const status = station.classList.contains('completed') ? 'Concluído' :
                          station.classList.contains('active') ? 'Em andamento' :
                          station.classList.contains('locked') ? 'Bloqueado' : 'Disponível';
            
            const tooltip = document.createElement('div');
            tooltip.className = 'station-tooltip';
            tooltip.innerHTML = `
                <div class="tooltip-title">${station.dataset.name || artefatoType}</div>
                <div class="tooltip-status">${status} • ${versionCount} versão(ões)</div>
            `;
            
            station.appendChild(tooltip);
        });
    },
    
    // Destaca visualmente a linha ativa
    highlightActiveBranch() {
        if (!this.activeBranch) return;
        
        // Ativa o trilho SVG correspondente
        const activeTrack = document.querySelector(`.metro-track.track-${this.activeBranch}`);
        if (activeTrack) {
            activeTrack.classList.add('active');
        }
        
        // Tronco compartilhado sempre ativo
        const tronco = document.querySelector('.metro-track.track-tronco');
        if (tronco) {
            tronco.classList.add('active');
        }
    },
    
    // Atualiza estado da estação (quando artefato muda)
    updateStation(artefatoType, newState) {
        const station = document.querySelector(`.metro-station[data-type="${artefatoType}"]`);
        if (!station) return;
        
        station.classList.remove('completed', 'active', 'locked', 'hidden');
        station.classList.add(newState);
        
        // Animação de "desbloqueio" se mudou de locked → active
        if (newState === 'active') {
            station.classList.add('just-unlocked');
            setTimeout(() => station.classList.remove('just-unlocked'), 800);
        }
    }
};

// ========== GESTÃO DE ARTEFATOS (funções migradas do template inline) ==========

async function criarNovaVersao(artefatoType, artefatoId) {
    try {
        const response = await fetch(`/api/projetos/${projetoId}/artefatos/${artefatoType}/${artefatoId}/versao`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            showNotification('Nova versão criada com sucesso!', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Erro ao criar versão', 'error');
        }
    } catch (error) {
        console.error('Erro ao criar versão:', error);
        showNotification('Erro ao criar versão', 'error');
    }
}

async function deletarArtefato(artefatoType, artefatoId) {
    if (!confirm('Tem certeza que deseja deletar este artefato?')) {
        return;
    }

    try {
        const response = await fetch(
            `/api/${artefatoType}/${artefatoId}`,
            { method: 'DELETE' }
        );

        if (response.ok) {
            showNotification('Artefato deletado com sucesso!', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Erro ao deletar', 'error');
        }
    } catch (error) {
        console.error('Erro ao deletar:', error);
        showNotification('Erro ao deletar', 'error');
    }
}

async function baixarPDF(artefatoType, artefatoId) {
    try {
        showNotification('Abrindo PDF...', 'info');
        // Open the print-view HTML in a new tab (browser print-to-PDF)
        window.open(`/api/${artefatoType}/${artefatoId}/pdf`, '_blank');
    } catch (error) {
        console.error('Erro ao abrir PDF:', error);
        showNotification('Erro ao abrir PDF', 'error');
    }
}

async function publicarPortariaSEI(artefatoType, artefatoId, versaoId) {
    if (!confirm('Publicar esta versão no SEI? Esta ação não pode ser desfeita.')) {
        return;
    }

    try {
        showNotification('Publicando no SEI...', 'info');
        
        const response = await fetch(
            `/api/projetos/${projetoId}/artefatos/${artefatoType}/${artefatoId}/versoes/${versaoId}/publicar-sei`,
            { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (response.ok) {
            const data = await response.json();
            showNotification('Publicado no SEI com sucesso!', 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const error = await response.json();
            showNotification(error.detail || 'Erro ao publicar no SEI', 'error');
        }
    } catch (error) {
        console.error('Erro ao publicar:', error);
        showNotification('Erro ao publicar no SEI', 'error');
    }
}

// ========== SISTEMA DE NOTIFICAÇÕES ==========

function showNotification(message, type = 'info') {
    // Remove notificação anterior se existir
    const existing = document.querySelector('.metro-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `metro-notification notification-${type}`;
    notification.textContent = message;
    
    // Estilos inline (pode ser movido para CSS depois)
    Object.assign(notification.style, {
        position: 'fixed',
        top: '24px',
        right: '24px',
        padding: '16px 24px',
        borderRadius: '8px',
        backgroundColor: type === 'success' ? 'var(--color-success)' :
                         type === 'error' ? 'var(--color-danger)' :
                         'var(--color-info)',
        color: 'white',
        fontWeight: '600',
        fontSize: '14px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)',
        zIndex: '9999',
        animation: 'slideInFromRight 0.4s ease-out',
        transition: 'all 0.3s'
    });
    
    document.body.appendChild(notification);
    
    // Auto-remove após 4s
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100px)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// ========== NAVEGAÇÃO POR TECLADO (opcional, UX avançado) ==========

function setupKeyboardNavigation() {
    const stations = Array.from(document.querySelectorAll('.metro-station:not(.locked)'));
    let currentIndex = 0;
    
    document.addEventListener('keydown', (e) => {
        // Apenas se não estiver em input/textarea
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            e.preventDefault();
            currentIndex = (currentIndex + 1) % stations.length;
            stations[currentIndex].click();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            e.preventDefault();
            currentIndex = (currentIndex - 1 + stations.length) % stations.length;
            stations[currentIndex].click();
        }
    });
}

// ========== INICIALIZAÇÃO ==========

document.addEventListener('DOMContentLoaded', () => {
    // Pega branch ativa do atributo data no body ou container
    const container = document.querySelector('.metro-map-container');
    const activeBranch = container?.dataset.activeBranch || null;
    
    MetroFlow.init(activeBranch);
    
    // Navegação por teclado (opcional, comentar se não quiser)
    // setupKeyboardNavigation();
    
    console.log('🚇 Metro Flow inicializado. Linha ativa:', activeBranch || 'nenhuma');
});

// ========== ANIMAÇÕES CSS (keyframes) ==========

// Adiciona keyframes para notificações se não existirem no CSS
if (!document.querySelector('#metro-flow-animations')) {
    const style = document.createElement('style');
    style.id = 'metro-flow-animations';
    style.textContent = `
        @keyframes slideInFromRight {
            from {
                transform: translateX(100px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}

// Exporta para uso global (se necessário)
window.MetroFlow = MetroFlow;
window.criarNovaVersao = criarNovaVersao;
window.deletarArtefato = deletarArtefato;
window.baixarPDF = baixarPDF;
window.publicarPortariaSEI = publicarPortariaSEI;
