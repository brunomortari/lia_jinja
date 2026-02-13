/**
 * Sistema LIA - Pesquisa de Preços CATMAT/CATSERV
 * JavaScript Nativo (sem jQuery, sem DataTables, sem Bootstrap)
 * =============================================================
 */

// ==================== ESTADO GLOBAL ====================
const estado = {
    dadosAtuais: null,
    itensSelecionados: new Set(),
    incluirOutliers: false,
    paginaAtual: 1,
    itensPorPagina: 25,
    filtros: {},
    ordenacao: { coluna: 'data', direcao: 'desc' },
    charts: {}
};

// ==================== UTILIDADES ====================
const utils = {
    formatarMoeda: (valor) => {
        if (valor === null || valor === undefined) return '-';
        return 'R$ ' + parseFloat(valor).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 4
        });
    },

    formatarData: (data) => {
        if (!data) return '-';
        return new Date(data).toLocaleDateString('pt-BR');
    },

    truncarTexto: (texto, tamanho = 40) => {
        if (!texto) return '-';
        return texto.length > tamanho ? texto.substring(0, tamanho) + '...' : texto;
    }
};

// ==================== API ====================
const api = {
    async pesquisarPrecos(codigo, tipo, uf) {
        let url = `/api/v1/precos/${codigo}?tipo=${tipo}&pesquisar_familia_pdm=false`;
        if (uf) url += `&estado=${uf}`;

        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro ao consultar API');
        }
        return response.json();
    }
};

// ==================== UI - LOADING E MENSAGENS ====================
const ui = {
    mostrarLoading: () => {
        document.getElementById('loading').classList.remove('d-none');
        document.getElementById('resultados').classList.add('d-none');
        document.getElementById('mensagemErro').classList.add('d-none');
    },

    esconderLoading: () => {
        document.getElementById('loading').classList.add('d-none');
    },

    mostrarErro: (mensagem) => {
        document.getElementById('textoErro').textContent = mensagem;
        document.getElementById('mensagemErro').classList.remove('d-none');
        ui.esconderLoading();
    },

    mostrarResultados: () => {
        document.getElementById('resultados').classList.remove('d-none');
        document.getElementById('mensagemErro').classList.add('d-none');
        ui.esconderLoading();
    }
};

// ==================== RENDERIZAÇÃO ====================
const render = {
    // Detectar tema da página
    getTheme: () => {
        return document.documentElement.getAttribute('data-theme') || 'light';
    },

    getChartColors: () => {
        const isDark = render.getTheme() === 'dark';
        return {
            primary: isDark ? '#4dabf7' : '#1351B4',
            success: isDark ? '#51cf66' : '#168821',
            warning: isDark ? '#ffd43b' : '#FFCD07',
            danger: isDark ? '#ff6b6b' : '#E52207',
            text: isDark ? '#a0a0a0' : '#666666',
            grid: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
            bg: isDark ? '#16213e' : '#ffffff'
        };
    },

    infoItem: (dados) => {
        document.getElementById('itemCodigo').textContent = dados.codigo_catmat;
        document.getElementById('descricaoItem').textContent = dados.descricao_item || 'Descrição não disponível';
        document.getElementById('itemClasse').textContent = dados.itens[0]?.nome_classe || '';
        document.getElementById('badgeTipo').textContent = dados.tipo_catalogo === 'material' ? 'CATMAT' : 'CATSERV';
        document.getElementById('badgeTotalRegistros').textContent = `${dados.total_registros} registros`;
    },

    outliers: (stats) => {
        const elQtd = document.getElementById('qtdOutliers');
        if (elQtd) elQtd.textContent = stats.quantidade_outliers || 0;

        const elInf = document.getElementById('limiteInferior');
        if (elInf) elInf.textContent = utils.formatarMoeda(stats.limite_inferior);

        const elSup = document.getElementById('limiteSuperior');
        if (elSup) elSup.textContent = utils.formatarMoeda(stats.limite_superior);
    },

    estatisticas: (stats) => {
        document.getElementById('precoMinimo').textContent = utils.formatarMoeda(stats.preco_minimo);
        document.getElementById('precoQ1').textContent = utils.formatarMoeda(stats.q1);
        document.getElementById('precoMediana').textContent = utils.formatarMoeda(stats.preco_mediana);
        document.getElementById('precoMedio').textContent = utils.formatarMoeda(stats.preco_medio);
        document.getElementById('precoQ3').textContent = utils.formatarMoeda(stats.q3);
        document.getElementById('precoMaximo').textContent = utils.formatarMoeda(stats.preco_maximo);
        document.getElementById('desvioPadrao').textContent = utils.formatarMoeda(stats.desvio_padrao);

        const cv = stats.coeficiente_variacao || 0;
        document.getElementById('coeficienteVariacao').textContent = cv.toFixed(2) + '%';

        const badgeCV = document.getElementById('badgeCV');
        badgeCV.textContent = cv < 15 ? 'Baixo' : cv < 30 ? 'Médio' : 'Alto';
        badgeCV.className = 'badge ' + (cv < 15 ? 'badge-cv-baixo' : cv < 30 ? 'badge-cv-medio' : 'badge-cv-alto');
    },

    tabela: () => {
        const dados = estado.incluirOutliers ? estado.dadosAtuais.itens : estado.dadosAtuais.itens.filter(i => !i.isOutlier);

        // Aplicar filtros
        let dadosFiltrados = dados.filter(item => {
            if (estado.filtros.fornecedor && !item.nomeFornecedor?.toLowerCase().includes(estado.filtros.fornecedor.toLowerCase())) return false;
            if (estado.filtros.uf && item.estado !== estado.filtros.uf) return false;
            if (estado.filtros.precoMin && item.precoUnitario < parseFloat(estado.filtros.precoMin)) return false;
            if (estado.filtros.precoMax && item.precoUnitario > parseFloat(estado.filtros.precoMax)) return false;
            if (estado.filtros.dataInicio && new Date(item.dataResultado) < new Date(estado.filtros.dataInicio)) return false;
            if (estado.filtros.dataFim && new Date(item.dataResultado) > new Date(estado.filtros.dataFim)) return false;
            return true;
        });

        const mapeamento = {
            uasg: 'nomeUasg',
            uf: 'estado',
            data: 'dataResultado',
            fornecedor: 'nomeFornecedor',
            preco: 'precoUnitario',
            quantidade: 'quantidade',
            unidade: 'siglaUnidadeFornecimento'
        };

        // Ordenar
        dadosFiltrados.sort((a, b) => {
            const col = estado.ordenacao.coluna;
            let aVal = a[mapeamento[col]] ?? a[col];
            let bVal = b[mapeamento[col]] ?? b[col];

            // Tratamento especial para datas (comparar como Date)
            if (col === 'data') {
                aVal = a.dataResultado ? new Date(a.dataResultado).getTime() : 0;
                bVal = b.dataResultado ? new Date(b.dataResultado).getTime() : 0;
                return estado.ordenacao.direcao === 'asc' ? aVal - bVal : bVal - aVal;
            }

            // Tratamento para preço e quantidade (numérico)
            if (col === 'preco' || col === 'quantidade') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
                return estado.ordenacao.direcao === 'asc' ? aVal - bVal : bVal - aVal;
            }

            // Strings
            if (typeof aVal === 'string' && typeof bVal === 'string') {
                return estado.ordenacao.direcao === 'asc' ?
                    aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }

            return estado.ordenacao.direcao === 'asc' ? (aVal || 0) - (bVal || 0) : (bVal || 0) - (aVal || 0);
        });

        // Paginação
        const inicio = (estado.paginaAtual - 1) * estado.itensPorPagina;
        const fim = inicio + estado.itensPorPagina;
        const dadosPagina = dadosFiltrados.slice(inicio, fim);

        // Renderizar tbody
        const tbody = document.getElementById('tbody');
        tbody.innerHTML = '';

        dadosPagina.forEach((item, idx) => {
            const id = item.idCompra + '-' + idx;
            const isSelected = estado.itensSelecionados.has(id);
            const tr = document.createElement('tr');
            tr.className = (item.isOutlier ? 'outlier-row' : '') + (isSelected ? ' selected-row' : '');
            tr.dataset.id = id;

            tr.innerHTML = `
                <td><input type="checkbox" class="table-checkbox" data-id="${id}" ${isSelected ? 'checked' : ''}></td>
                <td class="table-text-truncate" title="${item.nomeUasg || ''}">${utils.truncarTexto(item.nomeUasg, 30)}</td>
                <td>${item.estado || '-'}</td>
                <td>${utils.formatarData(item.dataResultado)}</td>
                <td class="table-text-truncate" title="${item.nomeFornecedor || ''}">${utils.truncarTexto(item.nomeFornecedor, 35)}</td>
                <td class="table-price">${utils.formatarMoeda(item.precoUnitario)}</td>
                <td>${item.quantidade || '-'}</td>
                <td>${item.siglaUnidadeFornecimento || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="verDetalhes('${id}')" title="Ver Detalhes"><i class="fas fa-eye"></i></button>
                    <button class="btn btn-sm btn-outline-success ms-1" onclick="abrirPNCP('${item.idCompra}', '${item.codigoItemCatalogo}')" title="PNCP"><i class="fas fa-external-link-alt"></i></button>
                </td>
            `;

            // Adicionar item ao estado para acesso posterior
            tr.dataset.itemData = JSON.stringify(item);
            tbody.appendChild(tr);
        });

        // Atualizar ícones de ordenação
        document.querySelectorAll('#tabelaPrecos th[data-sort]').forEach(th => {
            const icon = th.querySelector('i');
            if (icon) {
                if (th.dataset.sort === estado.ordenacao.coluna) {
                    icon.className = estado.ordenacao.direcao === 'asc' ?
                        'fas fa-sort-up text-primary small' : 'fas fa-sort-down text-primary small';
                } else {
                    icon.className = 'fas fa-sort text-muted small';
                }
            }
        });

        // Atualizar info de paginação
        const totalPaginas = Math.ceil(dadosFiltrados.length / estado.itensPorPagina);
        document.getElementById('paginationInfo').textContent =
            `Mostrando ${inicio + 1}-${Math.min(fim, dadosFiltrados.length)} de ${dadosFiltrados.length} registros`;

        document.getElementById('btnPrevPage').disabled = estado.paginaAtual === 1;
        document.getElementById('btnNextPage').disabled = estado.paginaAtual >= totalPaginas;

        atualizarContadorSelecionados();
    },

    grafico: () => {
        const stats = estado.incluirOutliers ? estado.dadosAtuais.estatisticas : estado.dadosAtuais.estatisticas_sem_outliers;
        const itens = estado.incluirOutliers ? estado.dadosAtuais.itens : estado.dadosAtuais.itens.filter(i => !i.isOutlier);
        const colors = render.getChartColors();

        // Destruir gráficos antigos
        Object.values(estado.charts).forEach(chart => chart && chart.destroy());

        // Histograma - Melhorado
        const precos = itens.map(i => i.precoUnitario).filter(Boolean);
        const bins = criarHistograma(precos, 12); // Menos bins para labels mais legíveis

        estado.charts.histograma = new Chart(document.getElementById('chartHistograma'), {
            type: 'bar',
            data: {
                labels: bins.labels,
                datasets: [{
                    label: 'Frequência',
                    data: bins.values,
                    backgroundColor: colors.primary,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (ctx) => `Faixa: ${ctx[0].label}`,
                            label: (ctx) => `${ctx.raw} itens`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: colors.text,
                            maxRotation: 45,
                            minRotation: 45,
                            font: { size: 10 }
                        }
                    },
                    y: {
                        grid: { color: colors.grid },
                        ticks: { color: colors.text },
                        beginAtZero: true
                    }
                }
            }
        });

        // Box Plot - Simulado
        const boxData = {
            min: stats.preco_minimo,
            q1: stats.q1,
            median: stats.preco_mediana,
            q3: stats.q3,
            max: stats.preco_maximo
        };

        const boxplotWhiskersPlugin = {
            id: 'boxplotWhiskers',
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                const yAxis = chart.scales.y;
                const xAxis = chart.scales.x;
                if (!xAxis || !yAxis) return;

                const y = yAxis.getPixelForValue(0);
                const minX = xAxis.getPixelForValue(boxData.min);
                const q1X = xAxis.getPixelForValue(boxData.q1);
                const medianX = xAxis.getPixelForValue(boxData.median);
                const q3X = xAxis.getPixelForValue(boxData.q3);
                const maxX = xAxis.getPixelForValue(boxData.max);
                const barHeight = 30;

                ctx.strokeStyle = '#888888';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(minX, y);
                ctx.lineTo(q1X, y);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(q3X, y);
                ctx.lineTo(maxX, y);
                ctx.stroke();

                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(minX, y - 12);
                ctx.lineTo(minX, y + 12);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(maxX, y - 12);
                ctx.lineTo(maxX, y + 12);
                ctx.stroke();

                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(medianX, y - barHeight / 2 - 5);
                ctx.lineTo(medianX, y + barHeight / 2 + 5);
                ctx.stroke();
            }
        };

        estado.charts.boxplot = new Chart(document.getElementById('chartBoxPlot'), {
            type: 'bar',
            data: {
                labels: ['Distribuição'],
                datasets: [
                    { label: 'Espaçador', data: [boxData.q1 - boxData.min], backgroundColor: 'transparent', borderWidth: 0, barPercentage: 0.5 },
                    { label: 'Q1 a Mediana', data: [boxData.median - boxData.q1], backgroundColor: colors.primary, borderRadius: 0, barPercentage: 0.5 },
                    { label: 'Mediana a Q3', data: [boxData.q3 - boxData.median], backgroundColor: colors.success, borderRadius: 0, barPercentage: 0.5 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        stacked: true,
                        grid: { color: colors.grid },
                        ticks: { color: colors.text, callback: (v) => 'R$ ' + v.toFixed(0) },
                        min: boxData.min * 0.9,
                        max: boxData.max * 1.1
                    },
                    y: { stacked: true, display: false }
                }
            },
            plugins: [boxplotWhiskersPlugin]
        });

        // Timeline
        const dadosTempo = agruparPorMes(itens);
        estado.charts.timeline = new Chart(document.getElementById('chartTimeline'), {
            type: 'line',
            data: {
                labels: dadosTempo.labels,
                datasets: [{
                    label: 'Preço Médio',
                    data: dadosTempo.values,
                    borderColor: colors.primary,
                    backgroundColor: colors.primary + '20',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: colors.primary
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: colors.text } },
                    y: { grid: { color: colors.grid }, ticks: { color: colors.text, callback: (v) => 'R$ ' + v.toFixed(0) } }
                }
            }
        });

        // Estados
        const dadosEstados = agruparPorEstado(itens);
        const estadosCores = dadosEstados.values.map((_, i, arr) => {
            const ratio = i / (arr.length - 1 || 1);
            if (ratio < 0.5) return `rgb(${Math.round(255 * (ratio * 2))}, 180, 80)`;
            return `rgb(255, ${Math.round(180 * (1 - (ratio - 0.5) * 2))}, 80)`;
        });

        estado.charts.estados = new Chart(document.getElementById('chartEstados'), {
            type: 'bar',
            data: {
                labels: dadosEstados.labels,
                datasets: [{
                    label: 'Preço Médio',
                    data: dadosEstados.values,
                    backgroundColor: estadosCores,
                    borderRadius: 4,
                    barPercentage: 0.85,
                    categoryPercentage: 0.9
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: colors.text } },
                    y: { grid: { color: colors.grid }, ticks: { color: colors.text, callback: (v) => 'R$ ' + v.toFixed(0) } }
                }
            }
        });
    }
};

function criarHistograma(valores, numBins) {
    if (valores.length === 0) return { labels: [], values: [] };
    const min = Math.min(...valores);
    const max = Math.max(...valores);
    const binSize = (max - min) / numBins || 1;
    const bins = Array(numBins).fill(0);
    const labels = [];
    const formatValue = (v) => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : (v >= 100 ? v.toFixed(0) : v.toFixed(2));

    valores.forEach(v => {
        const binIndex = Math.min(Math.floor((v - min) / binSize), numBins - 1);
        bins[binIndex]++;
    });

    for (let i = 0; i < numBins; i++) {
        labels.push(formatValue(min + i * binSize));
    }
    return { labels, values: bins };
}

function agruparPorMes(itens) {
    const grupos = {};
    itens.forEach(item => {
        if (!item.dataResultado) return;
        const mes = item.dataResultado.substring(0, 7);
        if (!grupos[mes]) grupos[mes] = [];
        grupos[mes].push(item.precoUnitario);
    });
    const labels = Object.keys(grupos).sort();
    const values = labels.map(mes => grupos[mes].reduce((a, b) => a + b, 0) / grupos[mes].length);
    return { labels, values };
}

function agruparPorEstado(itens) {
    const grupos = {};
    itens.forEach(item => {
        const uf = item.estado || 'N/A';
        if (!grupos[uf]) grupos[uf] = [];
        grupos[uf].push(item.precoUnitario);
    });
    const estadosComMedia = Object.keys(grupos).map(uf => ({
        uf,
        media: grupos[uf].reduce((a, b) => a + b, 0) / grupos[uf].length
    })).sort((a, b) => a.media - b.media);
    return { labels: estadosComMedia.map(e => e.uf), values: estadosComMedia.map(e => e.media) };
}

// ==================== EVENT HANDLERS ====================
function atualizarContadorSelecionados() {
    const qtd = estado.itensSelecionados.size;
    document.getElementById('contadorSelecionados').textContent = qtd;

    // Habilitar/Desabilitar botões que dependem da seleção
    // (Pode adicionar lógica específica aqui se necessário, mas geralmente o CSS ou clique já cobre)
}

function atualizarVisualizacao() {
    render.estatisticas(estado.incluirOutliers ? estado.dadosAtuais.estatisticas : estado.dadosAtuais.estatisticas_sem_outliers);
    render.tabela();
    render.grafico();
}

async function realizarPesquisa(e) {
    e.preventDefault();
    if (typeof App !== 'undefined' && App.hideLoading) App.hideLoading();

    const codigo = document.getElementById('codigoCatmat').value;
    const tipo = document.getElementById('tipoCatalogo').value;
    const uf = document.getElementById('estado').value;

    if (!codigo) {
        alert('Digite um código CATMAT/CATSERV');
        return;
    }

    if (estado.itensSelecionados.size > 0 && !confirm('Realizar nova pesquisa? Seleção atual será perdida.')) {
        return;
    }

    ui.mostrarLoading();
    estado.itensSelecionados.clear();

    try {
        const dados = await api.pesquisarPrecos(codigo, tipo, uf);
        estado.dadosAtuais = dados;

        render.infoItem(dados);
        render.outliers(dados.estatisticas);

        const ufs = [...new Set(dados.itens.map(i => i.estado).filter(Boolean))].sort();
        const selectUF = document.getElementById('filtroUF');
        selectUF.innerHTML = '<option value="">Todos</option>' + ufs.map(uf => `<option value="${uf}">${uf}</option>`).join('');

        atualizarVisualizacao();
        ui.mostrarResultados();
    } catch (error) {
        ui.mostrarErro(error.message);
    }
}

function limparFormulario() {
    document.getElementById('searchForm').reset();
    document.getElementById('resultados').classList.add('d-none');
    document.getElementById('mensagemErro').classList.add('d-none');
    estado.dadosAtuais = null;
    estado.itensSelecionados.clear();
}

function aplicarFiltros() {
    const getVal = (id) => document.getElementById(id)?.value || '';
    estado.filtros = {
        fornecedor: getVal('filtroFornecedor'),
        uf: getVal('filtroUF'),
        precoMin: getVal('filtroPrecoMin'),
        precoMax: getVal('filtroPrecoMax'),
        dataInicio: getVal('filtroDataInicio'),
        dataFim: getVal('filtroDataFim')
    };
    estado.paginaAtual = 1;
    render.tabela();
}

function limparFiltros() {
    document.querySelectorAll('.filters-inline input, .filters-inline select').forEach(el => el.value = '');
    estado.filtros = {};
    render.tabela();
}

function abrirModal(modalId) {
    const el = document.getElementById(modalId);
    if (el && typeof bootstrap !== 'undefined') new bootstrap.Modal(el).show();
}

function fecharModal(modalId) { }

async function verDetalhes(id) {
    const tr = document.querySelector(`tr[data-id="${id}"]`);
    const item = JSON.parse(tr.dataset.itemData);

    abrirModal('modalDetalhes');
    const modalContent = document.getElementById('conteudoDetalhes');
    const modalLoading = document.getElementById('modalLoading');
    const linkPncp = document.getElementById('linkPncp');

    modalContent.innerHTML = '';
    modalContent.classList.add('d-none');
    modalLoading.classList.remove('d-none');
    linkPncp.classList.add('d-none');

    try {
        let url = `/api/v1/contratacao/${encodeURIComponent(item.idCompra)}`;
        if (item.codigoItemCatalogo) url += `?codigo_item_catalogo=${item.codigoItemCatalogo}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error('Erro ao carregar detalhes');
        const data = await response.json();
        const c = data.contratacao || {};
        const i = data.itens?.[0] || {};

        modalContent.innerHTML = `
            <div class="row g-3">
                <div class="col-12"><h6 class="fw-bold border-bottom pb-2">Dados da Compra</h6></div>
                <div class="col-md-6"><strong>Órgão:</strong> ${c.orgaoEntidadeNome || item.nomeUasg || '-'}</div>
                <div class="col-md-6"><strong>UASG:</strong> ${c.uasg || item.codigoUasg || '-'}</div>
                <div class="col-md-6"><strong>Modalidade:</strong> ${c.modalidadeNome || item.modalidadeNome || '-'}</div>
                <div class="col-md-6"><strong>Objeto:</strong> ${c.objetoCompra || '-'}</div>
                
                <div class="col-12 mt-3"><h6 class="fw-bold border-bottom pb-2">Dados do Item</h6></div>
                <div class="col-md-6"><strong>Descrição:</strong> ${i.descricaoItem || item.descricaoItem || '-'}</div>
                <div class="col-md-6"><strong>Quantidade:</strong> ${i.quantidade || item.quantidade || '-'}</div>
                <div class="col-md-6"><strong>Valor Unitário:</strong> ${utils.formatarMoeda(i.valorUnitarioHomologado || item.precoUnitario)}</div>
                <div class="col-md-6"><strong>Valor Total:</strong> ${utils.formatarMoeda(i.valorTotalHomologado || (item.precoUnitario * item.quantidade))}</div>
                
                <div class="col-12 mt-3"><h6 class="fw-bold border-bottom pb-2">Fornecedor</h6></div>
                <div class="col-md-8"><strong>Razão Social:</strong> ${item.nomeFornecedor || '-'}</div>
                <div class="col-md-4"><strong>CNPJ:</strong> ${item.niFornecedor || '-'}</div>
            </div>
        `;
        modalContent.classList.remove('d-none');
        modalLoading.classList.add('d-none');

        if (item.linkPncp) {
            linkPncp.href = item.linkPncp;
            linkPncp.classList.remove('d-none');
        }
    } catch (error) {
        modalContent.innerHTML = `<div class="alert alert-warning">Detalhes não disponíveis no momento.</div>`;
        modalContent.classList.remove('d-none');
        modalLoading.classList.add('d-none');
    }
}

function abrirPNCP(idCompra, codigoItem) {
    const win = window.open('', '_blank');
    win.document.write('<html><head><title>Carregando PNCP...</title></head><body style="text-align:center;padding:50px;"><h3>Aguarde...</h3></body></html>');

    let url = `/api/v1/contratacao/${encodeURIComponent(idCompra)}`;
    if (codigoItem) url += `?codigo_item_catalogo=${codigoItem}`;

    fetch(url).then(r => r.ok ? r.json() : Promise.reject('Erro API'))
        .then(data => {
            let link = data.urlPncp || data.url_pncp || data.contratacao?.linkPncp || data.contratacao?.link_pncp || data.contratacao?.uriPncp;
            if (link && link.startsWith('/')) link = 'https://pncp.gov.br' + link;
            if (link) win.location.href = link;
            else { win.document.body.innerHTML = '<h3>Link não encontrado</h3><button onclick="window.close()">Fechar</button>'; }
        })
        .catch(() => { win.document.body.innerHTML = '<h3>Erro ao buscar PNCP</h3><button onclick="window.close()">Fechar</button>'; });
}

function abrirModalRelatorio() {
    if (estado.itensSelecionados.size === 0) {
        alert('Selecione pelo menos um item para gerar o relatório.');
        return;
    }

    document.getElementById('relCodigo').value = estado.dadosAtuais.codigo_catmat;
    document.getElementById('relTipoCatalogo').value = estado.dadosAtuais.tipo_catalogo === 'material' ? 'CATMAT' : 'CATSERV';
    document.getElementById('relDescricao').value = estado.dadosAtuais.descricao_item || '';

    const itensSelecionados = Array.from(estado.itensSelecionados).map(id => JSON.parse(document.querySelector(`tr[data-id="${id}"]`).dataset.itemData));
    const precos = itensSelecionados.map(i => i.precoUnitario).sort((a, b) => a - b);
    const media = precos.reduce((a, b) => a + b, 0) / precos.length;
    const desvio = Math.sqrt(precos.reduce((s, p) => s + Math.pow(p - media, 2), 0) / precos.length);
    const cv = media > 0 ? (desvio / media) * 100 : 0;

    const stats = {
        minimo: precos[0],
        maximo: precos[precos.length - 1],
        media: media,
        mediana: precos[Math.floor(precos.length / 2)],
        q1: precos[Math.floor(precos.length * 0.25)],
        q3: precos[Math.floor(precos.length * 0.75)],
        desvio: desvio,
        cv: cv
    };

    document.getElementById('relMinimo').value = utils.formatarMoeda(stats.minimo);
    document.getElementById('relQ1').value = utils.formatarMoeda(stats.q1);
    document.getElementById('relMediana').value = utils.formatarMoeda(stats.mediana);
    document.getElementById('relMedia').value = utils.formatarMoeda(stats.media);
    document.getElementById('relQ3').value = utils.formatarMoeda(stats.q3);
    document.getElementById('relMaximo').value = utils.formatarMoeda(stats.maximo);
    document.getElementById('relDesvio').value = utils.formatarMoeda(stats.desvio);
    document.getElementById('relCV').value = stats.cv.toFixed(2) + '%';
    document.getElementById('relQtdItens').textContent = itensSelecionados.length;

    const tbody = document.getElementById('corpoRelatorio');
    tbody.innerHTML = itensSelecionados.map(item => `
        <tr>
            <td>${utils.truncarTexto(item.nomeFornecedor, 30)}</td>
            <td>${item.niFornecedor || '-'}</td>
            <td>${utils.formatarMoeda(item.precoUnitario)}</td>
            <td>${item.quantidade}</td>
            <td>${item.siglaUnidadeFornecimento || '-'}</td>
            <td><input type="text" class="form-control" placeholder="Obs..."></td>
        </tr>
    `).join('');

    abrirModal('modalRelatorio');
}

function obterCotacaoCompleta() {
    const itensSelecionados = Array.from(estado.itensSelecionados).map(id => JSON.parse(document.querySelector(`tr[data-id="${id}"]`).dataset.itemData));
    const precos = itensSelecionados.map(i => i.precoUnitario);
    const media = precos.reduce((a, b) => a + b, 0) / precos.length;

    return {
        item: {
            codigo: estado.dadosAtuais.codigo_catmat,
            tipo: document.getElementById('relTipoCatalogo').value,
            descricao: document.getElementById('relDescricao').value,
            unidade: document.getElementById('relUnidadeMedida').value
        },
        document_header: {
            objeto: document.getElementById('relObjeto').value,
            justificativa: document.getElementById('relJustificativa').value,
            responsavel: document.getElementById('relResponsavel').value,
            setor: document.getElementById('relSetor').value,
            observacoes: document.getElementById('relObservacoes').value
        },
        estatisticas: {
            minimo: Math.min(...precos),
            media: media,
            mediana: precos.sort((a, b) => a - b)[Math.floor(precos.length / 2)],
            maximo: Math.max(...precos),
            quantidade_itens: itensSelecionados.length
        },
        itens: itensSelecionados.map(item => ({
            fornecedor: item.nomeFornecedor,
            cnpj: item.niFornecedor,
            preco_unitario: item.precoUnitario,
            quantidade: item.quantidade,
            unidade: item.siglaUnidadeFornecimento
        }))
    };
}

function exportarJSON() {
    if (!estado.dadosAtuais) return;
    const blob = new Blob([JSON.stringify(estado.dadosAtuais, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `precos_${estado.dadosAtuais.codigo_catmat}.json`;
    a.click();
}

function exportarCSV() { /* Simple export logic same as before but without outliers check if desired, keeping simple */
    if (!estado.dadosAtuais) return;
    const itens = estado.incluirOutliers ? estado.dadosAtuais.itens : estado.dadosAtuais.itens.filter(i => !i.isOutlier);
    const headers = ['UASG', 'UF', 'Data', 'Fornecedor', 'Preço Unit.', 'Qtd', 'Unidade'];
    let csv = headers.join(';') + '\n';
    itens.forEach(item => {
        csv += [item.nomeUasg, item.estado, utils.formatarData(item.dataResultado), `"${(item.nomeFornecedor || '').replace(/"/g, '""')}"`, item.precoUnitario, item.quantidade, item.siglaUnidadeFornecimento].join(';') + '\n';
    });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }));
    a.download = `precos.csv`;
    a.click();
}

function exportarCotacaoJSON() {
    const cotacao = obterCotacaoCompleta();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(cotacao, null, 2)], { type: 'application/json' }));
    a.download = `cotacao.json`;
    a.click();
}

function imprimirRelatorio() {
    const cotacao = obterCotacaoCompleta();
    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>Relatório</title></head><body><h1>Relatório</h1><p>${cotacao.item.descricao}</p><script>window.print()</script></body></html>`);
    win.document.close();
}

async function salvarPesquisa() {
    const btn = document.getElementById('btnSalvarPesquisa');
    const oldText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';

    try {
        const projetoId = document.getElementById('projetoId').value;
        const cotacao = obterCotacaoCompleta();
        const response = await fetch('/api/pesquisa_precos/salvar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                projeto_id: parseInt(projetoId),
                artefato_data: {
                    ...cotacao,
                    valor_total: cotacao.estatisticas.media
                }
            })
        });
        if (!response.ok) throw new Error('Erro ao salvar');
        const res = await response.json();
        const elModal = document.getElementById('modalRelatorio');
        if (typeof bootstrap !== 'undefined') bootstrap.Modal.getInstance(elModal)?.hide();
        window.location.href = `/projetos/${projetoId}`;
    } catch (e) {
        alert('Erro: ' + e.message);
        btn.disabled = false;
        btn.innerHTML = oldText;
    }
}

// ==================== LEVANTAMENTO DE SOLUÇÕES (IA) ====================
const fila = {
    adicionar: (itens) => {
        const filaAtual = JSON.parse(localStorage.getItem('filaPesquisa') || '[]');
        // Adicionar apenas itens novos
        const novos = itens.filter(i => !filaAtual.some(f => f.codigo === i.codigo));
        const atualizada = [...filaAtual, ...novos];
        localStorage.setItem('filaPesquisa', JSON.stringify(atualizada));
        fila.renderizar();
    },

    remover: (codigo) => {
        const filaAtual = JSON.parse(localStorage.getItem('filaPesquisa') || '[]');
        const atualizada = filaAtual.filter(i => parseInt(i.codigo) !== parseInt(codigo));
        localStorage.setItem('filaPesquisa', JSON.stringify(atualizada));
        fila.renderizar();
    },

    proximo: () => {
        const filaAtual = JSON.parse(localStorage.getItem('filaPesquisa') || '[]');
        if (filaAtual.length === 0) {
            alert('Fila vazia!');
            return;
        }
        const item = filaAtual[0];

        // Preencher form e pesquisar
        document.getElementById('codigoCatmat').value = item.codigo;
        document.getElementById('tipoCatalogo').value = 'material';

        // Trigger search
        document.getElementById('searchForm').dispatchEvent(new Event('submit'));
    },

    limpar: () => {
        if (confirm('Limpar toda a fila?')) {
            localStorage.removeItem('filaPesquisa');
            fila.renderizar();
        }
    },

    renderizar: () => {
        const container = document.getElementById('queueContainer');
        const lista = document.getElementById('queueList');
        const count = document.getElementById('queueCount');
        const btnNext = document.getElementById('btnNextQueue');
        const btnClear = document.getElementById('btnClearQueue');

        if (!container) return;

        const filaAtual = JSON.parse(localStorage.getItem('filaPesquisa') || '[]');
        count.textContent = filaAtual.length;

        if (filaAtual.length > 0) {
            container.classList.remove('d-none');
            // Mostrar resumo dos próximos 5 itens
            lista.innerHTML = filaAtual.slice(0, 5).map(i =>
                `<span class="badge bg-light text-dark border me-1 mb-1">
                    ${i.codigo} - ${utils.truncarTexto(i.descricao, 20)}
                    <i class="fas fa-times ms-1 text-danger cursor-pointer" onclick="fila.remover('${i.codigo}')" style="cursor:pointer"></i>
                </span>`
            ).join('') + (filaAtual.length > 5 ? ` <span class="text-muted small">+${filaAtual.length - 5} mais</span>` : '');
        } else {
            container.classList.add('d-none');
            lista.innerHTML = '';
        }
    }
};

const levantamento = {
    abrirModal: () => {
        abrirModal('modalLevantamento');
    },

    gerar: async () => {
        const prompt = document.getElementById('iaPrompt').value;
        const dfdRadio = document.querySelector('input[name="dfdSelection"]:checked');
        const selectedDfdId = dfdRadio ? dfdRadio.value : null;
        const projetoId = document.getElementById('projetoId').value;

        // Coletar itens PAC selecionados
        const pacItens = [];
        document.querySelectorAll('.ia-contexto-pac:checked').forEach(cb => {
            const label = document.querySelector(`label[for="${cb.id}"]`).textContent;
            pacItens.push({
                id: cb.value,
                descricao: label.trim()
            });
        });

        if (!prompt) {
            alert('Por favor, descreva sua necessidade.');
            return;
        }

        // Validation removed to allow "No DFD" (Generic Search)
        // if (!selectedDfdId) { ... }

        document.getElementById('iaLoading').classList.remove('d-none');
        document.getElementById('iaResultadosContainer').classList.remove('d-none'); // Show container
        document.getElementById('iaResultadosContent').classList.add('d-none'); // Hide results content
        document.getElementById('btnGerarSolucoes').disabled = true;

        try {
            const response = await fetch('/api/ia/levantamento-solucoes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: prompt,
                    projeto_id: parseInt(projetoId),
                    contexto: {
                        dfd_id: parseInt(selectedDfdId),
                        itens_pac: pacItens
                    }
                })
            });

            if (!response.ok) throw new Error('Erro na geração');

            const data = await response.json();

            // Renderizar resultados
            document.getElementById('iaAnalise').textContent = data.analise_ia || 'Análise concluída.';

            const tbody = document.getElementById('iaTabelaResultado');
            tbody.innerHTML = '';

            if (data.sugestoes && data.sugestoes.length > 0) {
                data.sugestoes.forEach(item => {
                    const tr = document.createElement('tr');
                    // Encode item data for retrieval
                    const itemData = JSON.stringify(item).replace(/"/g, '&quot;');

                    tr.innerHTML = `
                        <td class="text-center">
                            <input type="checkbox" class="form-check-input ia-check" value="${item.codigo}" data-item="${itemData}">
                        </td>
                        <td><span class="badge bg-light text-dark border">${item.codigo}</span></td>
                        <td>
                            <p class="mb-0 fw-medium text-dark small text-truncate-2" title="${item.descricao}">${item.descricao}</p>
                            ${item.sustentavel ? '<span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 rounded-pill px-2" style="font-size: 0.65rem;"><i class="fas fa-leaf me-1"></i>Sustentável</span>' : ''}
                        </td>
                        <td>
                            <div class="d-flex flex-column gap-1">
                                <span class="badge bg-secondary bg-opacity-10 text-secondary text-start fw-normal px-2 py-1" style="font-size: 0.7rem;">
                                    <i class="fas fa-layer-group me-1 opacity-50"></i>${item.grupo || '-'}
                                </span>
                                <span class="badge bg-secondary bg-opacity-10 text-secondary text-start fw-normal px-2 py-1" style="font-size: 0.7rem;">
                                    <i class="fas fa-tags me-1 opacity-50"></i>${item.classe || '-'}
                                </span>
                                <span class="badge bg-info bg-opacity-10 text-info text-start fw-normal px-2 py-1" style="font-size: 0.7rem;">
                                    <i class="fas fa-cube me-1 opacity-50"></i>${item.pdm || '-'}
                                </span>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                document.getElementById('iaResultadosContent').classList.remove('d-none');
                document.getElementById('btnAdicionarFila').disabled = false;
            } else {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center py-5 text-muted">Nenhuma sugestão encontrada para sua descrição.</td></tr>';
                document.getElementById('iaResultadosContent').classList.remove('d-none');
            }

        } catch (error) {
            console.error(error);
            alert('Erro ao gerar sugestões. Verifique o console.');
        } finally {
            document.getElementById('iaLoading').classList.add('d-none');
            document.getElementById('btnGerarSolucoes').disabled = false;
        }
    },

    adicionarFila: () => {
        const selecionados = [];
        document.querySelectorAll('.ia-check:checked').forEach(cb => {
            const item = JSON.parse(cb.dataset.item);
            selecionados.push(item);
        });

        if (selecionados.length === 0) {
            alert('Selecione ao menos um item.');
            return;
        }

        fila.adicionar(selecionados);

        // Fechar modal
        const el = document.getElementById('modalLevantamento');
        if (typeof bootstrap !== 'undefined') bootstrap.Modal.getInstance(el)?.hide();

        // Optional toast or alert
        // alert(`${selecionados.length} itens adicionados à fila de pesquisa.`);
    }
};

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    if (typeof App !== 'undefined' && App.hideLoading) App.hideLoading();

    // Listeners
    const add = (id, evt, fn) => document.getElementById(id)?.addEventListener(evt, fn);
    add('searchForm', 'submit', realizarPesquisa);
    add('btnLimpar', 'click', limparFormulario);
    add('toggleOutliers', 'change', (e) => { estado.incluirOutliers = e.target.checked; if (estado.dadosAtuais) atualizarVisualizacao(); });
    add('btnAplicarFiltros', 'click', aplicarFiltros);
    add('btnLimparFiltros', 'click', limparFiltros);

    // Selection listeners
    add('checkTodos', 'change', (e) => {
        document.querySelectorAll('#tbody .table-checkbox').forEach(cb => {
            cb.checked = e.target.checked;
            e.target.checked ? estado.itensSelecionados.add(cb.dataset.id) : estado.itensSelecionados.delete(cb.dataset.id);
            cb.closest('tr').classList.toggle('selected-row', e.target.checked);
        });
        atualizarContadorSelecionados();
    });

    document.addEventListener('change', (e) => {
        if (e.target.classList.contains('table-checkbox') && e.target.id !== 'checkTodos') {
            e.target.checked ? estado.itensSelecionados.add(e.target.dataset.id) : estado.itensSelecionados.delete(e.target.dataset.id);
            e.target.closest('tr').classList.toggle('selected-row', e.target.checked);
            atualizarContadorSelecionados();
        }
    });

    // Sort & Pagination
    document.querySelectorAll('#tabelaPrecos th[data-sort]').forEach(th => th.addEventListener('click', () => {
        estado.ordenacao.direcao = (estado.ordenacao.coluna === th.dataset.sort && estado.ordenacao.direcao === 'asc') ? 'desc' : 'asc';
        estado.ordenacao.coluna = th.dataset.sort;
        render.tabela();
    }));
    add('pageSize', 'change', (e) => { estado.itensPorPagina = parseInt(e.target.value); estado.paginaAtual = 1; render.tabela(); });
    add('btnPrevPage', 'click', () => { if (estado.paginaAtual > 1) { estado.paginaAtual--; render.tabela(); } });
    add('btnNextPage', 'click', () => { estado.paginaAtual++; render.tabela(); });

    // Actions
    add('btnGerarRelatorio', 'click', abrirModalRelatorio); // "Relatório Consolidado" from main view calls this logic now? No, we need a button in the main view.
    add('btnLimparSelecao', 'click', () => {
        estado.itensSelecionados.clear();
        document.querySelectorAll('.table-checkbox').forEach(cb => cb.checked = false);
        document.querySelectorAll('.selected-row').forEach(tr => tr.classList.remove('selected-row'));
        document.getElementById('checkTodos').checked = false;
        atualizarContadorSelecionados();
    });

    add('btnExportJson', 'click', exportarJSON);
    add('btnExportCsv', 'click', exportarCSV);
    add('btnExportarCotacaoJson', 'click', exportarCotacaoJSON);

    // Modal buttons
    add('btnImprimirRelatorio', 'click', imprimirRelatorio);
    add('btnSalvarPesquisa', 'click', salvarPesquisa);
    add('btnBaixarJsonModal', 'click', exportarCotacaoJSON);

    // Levantamento IA & Fila
    add('btnLevantamento', 'click', levantamento.abrirModal);
    add('btnGerarSolucoes', 'click', levantamento.gerar);
    add('btnAdicionarFila', 'click', levantamento.adicionarFila);
    add('btnNextQueue', 'click', fila.proximo);
    add('btnClearQueue', 'click', fila.limpar);

    // Check all in IA modal
    add('checkTodosIA', 'change', (e) => {
        document.querySelectorAll('.ia-check').forEach(cb => cb.checked = e.target.checked);
    });

    // Renderizar fila ao carregar
    fila.renderizar();
    window.fila = fila; // Expose globally for inline onclicks

    // Globals
    window.render = render;
    window.verDetalhes = verDetalhes;
    window.abrirPNCP = abrirPNCP;
    window.aplicarFiltros = aplicarFiltros;
    window.limparFiltros = limparFiltros;

    console.log('Sistema de Pesquisa de Precos (Direct Flow) v4.0');
});