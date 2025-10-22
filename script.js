document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. SELEÇÃO DE ELEMENTOS ---
    
    // Seção de Chat
    const chatHistoryContainer = document.getElementById("chat-history");
    const formPergunta = document.getElementById("form-pergunta");
    const inputPergunta = document.getElementById("input-pergunta");
    const btnAnalisar = document.getElementById("btn-analisar");
    const btnLimparChat = document.getElementById("btn-limpar-chat");
    
    // Seção da Sidebar
    const formAddPlanilha = document.getElementById("form-add-planilha");
    const inputNomePlanilha = document.getElementById("input-nome-planilha");
    const btnAddPlanilha = document.getElementById("btn-add-planilha");
    const listaPlanilhasContainer = document.getElementById("lista-planilhas-container");
    const gerenciamentoStatus = document.getElementById("gerenciamento-status");
    const planilhasLoading = document.getElementById("planilhas-loading");

    // --- 2. CONFIGURAÇÃO DA API ---
    const API_BASE_URL = "https://bot-vendas-api.onrender.com"; // 🚨 Verifique se este é o nome do seu backend

    // --- 3. LÓGICA DO CHAT ---

    /**
     * Adiciona uma nova mensagem ao histórico do chat.
     * @param {string} mensagem - O conteúdo da mensagem (texto ou HTML).
     * @param {'user' | 'bot' | 'error' | 'loading'} tipo - O tipo de mensagem.
     * @returns {HTMLElement} O elemento da mensagem criado.
     */
    function adicionarMensagemAoChat(mensagem, tipo) {
        const divMensagem = document.createElement("div");
        divMensagem.className = `chat-message ${tipo}`;
        
        let conteudoMensagem = "";
        
        if (tipo === 'loading') {
            conteudoMensagem = `
                <div class="spinner-small"></div>
                <p>${mensagem}</p>
            `;
            divMensagem.id = "loading-message"; // ID para remoção posterior
        } else if (tipo === 'bot') {
            // Converte **negrito** de markdown para <strong> HTML
            const mensagemFormatada = mensagem.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            conteudoMensagem = `<p>${mensagemFormatada}</p>`;
        } else {
            conteudoMensagem = `<p>${mensagem}</p>`;
        }
        
        divMensagem.innerHTML = conteudoMensagem;
        chatHistoryContainer.appendChild(divMensagem);
        
        // Rola para o final do chat
        chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
        
        return divMensagem;
    }

    /**
     * Remove a mensagem de "loading..." do chat.
     */
    function removerMensagemLoading() {
        const loadingMsg = document.getElementById("loading-message");
        if (loadingMsg) {
            loadingMsg.remove();
        }
    }

    /**
     * Lida com o envio do formulário de pergunta.
     */
    formPergunta.addEventListener("submit", async (event) => {
        event.preventDefault(); 
        const pergunta = inputPergunta.value.trim();
        if (!pergunta) return;

        // 1. Adiciona a pergunta do usuário ao chat
        adicionarMensagemAoChat(pergunta, 'user');
        inputPergunta.value = ""; // Limpa o input
        btnAnalisar.disabled = true; // Desabilita o botão

        // 2. Adiciona a mensagem de "analisando"
        adicionarMensagemAoChat("Analisando...", 'loading');

        try {
            // 3. Chama a API
            const response = await fetch(`${API_BASE_URL}/api/gerar-insights`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pergunta: pergunta }) 
            });

            removerMensagemLoading(); // 4. Remove o "analisando"
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.erro || `Erro na API: ${response.statusText}`);
            }
            
            // 5. Adiciona a resposta do bot ao chat
            // (Usando a correção 'insight.dados' que fizemos)
            adicionarMensagemAoChat(data.insights[0].dados, 'bot');

        } catch (error) {
            console.error("Falha ao buscar insights:", error);
            removerMensagemLoading(); // 4. Remove o "analisando" (em caso de erro)
            // 5. Adiciona a mensagem de erro ao chat
            adicionarMensagemAoChat(error.message, 'error');
        } finally {
            btnAnalisar.disabled = false; // Reabilita o botão
        }
    });

    /**
     * Lida com o clique no botão de limpar chat.
     */
    btnLimparChat.addEventListener("click", () => {
        chatHistoryContainer.innerHTML = "";
        adicionarMensagemAoChat("Chat limpo. Pronto para uma nova análise!", 'bot');
    });

    // --- 4. LÓGICA DA SIDEBAR (GERENCIAMENTO) ---

    /**
     * Mostra uma mensagem de status (sucesso ou erro) na área de gerenciamento.
     */
    function mostrarStatusGerenciamento(mensagem, tipo = 'sucesso') {
        gerenciamentoStatus.textContent = mensagem;
        gerenciamentoStatus.className = (tipo === 'sucesso') ? 'status-message status-success' : 'status-message status-error';
        
        setTimeout(() => {
            gerenciamentoStatus.textContent = '';
            gerenciamentoStatus.className = 'status-message';
        }, 5000);
    }

    /**
     * Busca a lista de planilhas da API e as exibe na tela.
     */
    async function carregarListaPlanilhas() {
        planilhasLoading.classList.remove("hidden");
        listaPlanilhasContainer.innerHTML = "";
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/planilhas`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.erro || "Falha ao carregar planilhas.");

            if (data.planilhas && data.planilhas.length > 0) {
                data.planilhas.forEach(nome => {
                    const item = document.createElement("div");
                    item.className = "planilha-item";
                    item.innerHTML = `
                        <span>${nome}</span>
                        <button class="btn-remover-planilha" data-nome="${nome}" title="Remover ${nome}">
                            <i class="ph ph-trash-simple"></i>
                        </button>
                    `;
                    listaPlanilhasContainer.appendChild(item);
                });
                
                // Adiciona "ouvintes" aos botões de remover
                document.querySelectorAll('.btn-remover-planilha').forEach(button => {
                    button.addEventListener('click', () => {
                        const nomeParaRemover = button.getAttribute('data-nome');
                        if (confirm(`Tem certeza que deseja remover a planilha "${nomeParaRemover}"? O bot irá recarregar todos os dados.`)) {
                            removerPlanilha(nomeParaRemover);
                        }
                    });
                });
                
            } else {
                listaPlanilhasContainer.innerHTML = "<p class='sidebar-info-text'>Nenhuma planilha configurada.</p>";
            }
            return true; // Sucesso
        } catch (error) {
            mostrarStatusGerenciamento(error.message, 'erro');
            return false; // Falha
        } finally {
            planilhasLoading.classList.add("hidden");
        }
    }

    /**
     * Lida com o envio do formulário de adicionar planilha.
     */
    formAddPlanilha.addEventListener('submit', async (event) => {
        event.preventDefault();
        const nomePlanilha = inputNomePlanilha.value.trim();
        if (!nomePlanilha) return;

        btnAddPlanilha.disabled = true;
        btnAddPlanilha.innerHTML = '<div class="spinner-small" style="margin: 0 auto;"></div>';

        try {
            const response = await fetch(`${API_BASE_URL}/api/planilhas/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome: nomePlanilha }) 
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.erro || "Falha ao adicionar planilha.");

            mostrarStatusGerenciamento(data.sucesso, 'sucesso');
            inputNomePlanilha.value = ''; // Limpa o campo
            await carregarListaPlanilhas(); // Recarrega a lista
            adicionarMensagemAoChat("Uma nova planilha foi adicionada e os dados foram recarregados.", 'bot');

        } catch (error) {
            mostrarStatusGerenciamento(error.message, 'erro');
        } finally {
            btnAddPlanilha.disabled = false;
            btnAddPlanilha.innerHTML = '<i class="ph ph-plus"></i> Adicionar Planilha';
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
            if (!response.ok) throw new Error(data.erro || "Falha ao remover planilha.");

            mostrarStatusGerenciamento(data.sucesso, 'sucesso');
            await carregarListaPlanilhas(); // Recarrega a lista
            adicionarMensagemAoChat("Uma planilha foi removida e os dados foram recarregados.", 'bot');

        } catch (error) {
            mostrarStatusGerenciamento(error.message, 'erro');
        } finally {
            planilhasLoading.classList.add("hidden");
        }
    }

    // --- 5. CARREGAMENTO INICIAL ---
    
    async function iniciarApp() {
        // Mostra o "Carregando" no chat, como na sua imagem
        adicionarMensagemAoChat("Carregando dados das planilhas...", 'loading');
        
        const sucesso = await carregarListaPlanilhas();
        
        removerMensagemLoading();
        
        if (sucesso) {
            adicionarMensagemAoChat("Dados carregados com sucesso! Estou pronto para suas perguntas.", 'bot');
        } else {
            adicionarMensagemAoChat("Falha ao carregar os dados das planilhas. Verifique a barra lateral e os logs do backend.", 'error');
        }
    }
    
    iniciarApp();
});
