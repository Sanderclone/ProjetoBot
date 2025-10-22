document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. SELEÇÃO DE ELEMENTOS ---
    
    // Seção de Análise
    const insightsContainer = document.getElementById("insights-container");
    const loadingIndicator = document.getElementById("loading");
    const formPergunta = document.getElementById("form-pergunta");
    const inputPergunta = document.getElementById("input-pergunta");
    
    // 🚨 NOVO: Seção de Gerenciamento
    const formAddPlanilha = document.getElementById("form-add-planilha");
    const inputNomePlanilha = document.getElementById("input-nome-planilha");
    const listaPlanilhasContainer = document.getElementById("lista-planilhas-container");
    const gerenciamentoStatus = document.getElementById("gerenciamento-status");
    const planilhasLoading = document.getElementById("planilhas-loading");

    // --- 2. CONFIGURAÇÃO DA API ---
    // 🚨 NOVO: Definimos a URL base pois temos múltiplos endpoints
    const API_BASE_URL = "https://bot-vendas-api.onrender.com"; // 🚨 Verifique se este é o nome do seu backend

    /**
     * Mostra uma mensagem de status (sucesso ou erro) na área de gerenciamento.
     */
    function mostrarStatusGerenciamento(mensagem, tipo = 'sucesso') {
        gerenciamentoStatus.textContent = mensagem;
        gerenciamentoStatus.className = (tipo === 'sucesso') ? 'status-success' : 'status-error';
        
        // Limpa a mensagem após 5 segundos
        setTimeout(() => {
            gerenciamentoStatus.textContent = '';
            gerenciamentoStatus.className = '';
        }, 5000);
    }

    // ==========================================================
    // --- LÓGICA DE ANÁLISE DE INSIGHTS (Função Principal) ---
    // ==========================================================

    formPergunta.addEventListener("submit", (event) => {
        event.preventDefault(); 
        const pergunta = inputPergunta.value;
        if (pergunta) {
            fetchInsights(pergunta);
        }
    });

    async function fetchInsights(pergunta) {
        loadingIndicator.classList.remove("hidden");
        insightsContainer.innerHTML = ""; 

        try {
            const response = await fetch(`${API_BASE_URL}/api/gerar-insights`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pergunta: pergunta }) 
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.erro || `Erro na API: ${response.statusText}`);
            }

            if (data.insights && data.insights.length > 0) {
                renderInsights(data.insights);
            } else {
                insightsContainer.innerHTML = "<p>Nenhum insight encontrado.</p>";
            }

        } catch (error) {
            console.error("Falha ao buscar insights:", error);
            // Cria um cartão de erro formatado
            insightsContainer.innerHTML = `
                <div class="insight-card">
                    <h3>Erro na Análise</h3>
                    <p class="error-message">${error.message}</p>
                </div>
            `;
        } finally {
            loadingIndicator.classList.add("hidden");
        }
    }

    function renderInsights(insights) {
        insightsContainer.innerHTML = "";
        insights.forEach(insight => {
            const card = document.createElement("div");
            card.className = "insight-card";
            card.innerHTML = `
                <h3>${insight.titulo || 'Insight'}</h3>
                <p>${insight.dados || 'Sem detalhes'}</p>
            `;
            insightsContainer.appendChild(card);
        });
    }

    // ==========================================================
    // --- 🚨 NOVAS FUNÇÕES DE GERENCIAMENTO DE PLANILHAS ---
    // ==========================================================

    /**
     * Busca a lista de planilhas da API e as exibe na tela.
     */
    async function carregarListaPlanilhas() {
        planilhasLoading.classList.remove("hidden");
        listaPlanilhasContainer.innerHTML = "";
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/planilhas`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.erro || "Falha ao carregar planilhas.");
            }

            if (data.planilhas && data.planilhas.length > 0) {
                data.planilhas.forEach(nome => {
                    const item = document.createElement("div");
                    item.className = "planilha-item";
                    item.innerHTML = `
                        <span>${nome}</span>
                        <button class="btn-remover-planilha" data-nome="${nome}">Remover</button>
                    `;
                    listaPlanilhasContainer.appendChild(item);
                });
                
                // Adiciona os "ouvintes" aos botões de remover
                document.querySelectorAll('.btn-remover-planilha').forEach(button => {
                    button.addEventListener('click', () => {
                        const nomeParaRemover = button.getAttribute('data-nome');
                        if (confirm(`Tem certeza que deseja remover a planilha "${nomeParaRemover}"? O bot irá recarregar todos os dados.`)) {
                            removerPlanilha(nomeParaRemover);
                        }
                    });
                });
                
            } else {
                listaPlanilhasContainer.innerHTML = "<p>Nenhuma planilha configurada.</p>";
            }

        } catch (error) {
            mostrarStatusGerenciamento(error.message, 'erro');
        } finally {
            planilhasLoading.classList.add("hidden");
        }
    }

    /**
     * Adiciona uma nova planilha.
     */
    formAddPlanilha.addEventListener('submit', async (event) => {
        event.preventDefault();
        const nomePlanilha = inputNomePlanilha.value;
        if (!nomePlanilha) return;

        // Desabilita o botão para evitar cliques duplos
        const btnAdd = document.getElementById('btn-add-planilha');
        btnAdd.disabled = true;
        btnAdd.textContent = 'Adicionando...';

        try {
            const response = await fetch(`${API_BASE_URL}/api/planilhas/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome: nomePlanilha }) 
            });
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.erro || "Falha ao adicionar planilha.");
            }

            mostrarStatusGerenciamento(data.sucesso, 'sucesso');
            inputNomePlanilha.value = ''; // Limpa o campo
            carregarListaPlanilhas(); // Recarrega a lista

        } catch (error) {
            mostrarStatusGerenciamento(error.message, 'erro');
        } finally {
            btnAdd.disabled = false;
            btnAdd.textContent = 'Adicionar';
        }
    });

    /**
     * Remove uma planilha existente.
     */
    async function removerPlanilha(nome) {
        planilhasLoading.classList.remove("hidden"); // Reusa o loading

        try {
            const response = await fetch(`${API_BASE_URL}/api/planilhas/remove`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome: nome }) 
            });
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.erro || "Falha ao remover planilha.");
            }

            mostrarStatusGerenciamento(data.sucesso, 'sucesso');
            carregarListaPlanilhas(); // Recarrega a lista

        } catch (error) {
            mostrarStatusGerenciamento(error.message, 'erro');
        } finally {
            planilhasLoading.classList.add("hidden");
        }
    }

    // --- CARREGAMENTO INICIAL ---
    // Carrega a lista de planilhas assim que a página é aberta
    carregarListaPlanilhas();
});
