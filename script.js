document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. Selecione os elementos ---
    const insightsContainer = document.getElementById("insights-container");
    const loadingIndicator = document.getElementById("loading");
    const formPergunta = document.getElementById("form-pergunta");
    const inputPergunta = document.getElementById("input-pergunta");

    // --- 2. Defina o endereço da sua API (o servidor Flask) ---
    // Ele estará rodando localmente na porta 5000
    const API_URL = "http://127.0.0.1:5000/api/gerar-insights"; 

    /**
     * Adiciona um "ouvinte" ao formulário.
     * Isso será disparado quando o usuário clicar no botão "Analisar".
     */
    formPergunta.addEventListener("submit", (event) => {
        event.preventDefault(); // Impede o recarregamento da página
        const pergunta = inputPergunta.value;
        if (pergunta) {
            fetchInsights(pergunta);
        }
    });

    /**
     * Função principal para buscar e exibir os insights
     * Agora ela recebe a "pergunta" como parâmetro
     */
    async function fetchInsights(pergunta) {
        loadingIndicator.classList.remove("hidden");
        insightsContainer.innerHTML = ""; 

        try {
            // --- 3. Chame sua API Flask ---
            const response = await fetch(API_URL, {
                method: 'POST', // Mudamos para POST
                headers: {
                    'Content-Type': 'application/json',
                },
                // Enviamos a pergunta no corpo da requisição
                body: JSON.stringify({ pergunta: pergunta }) 
            });

            if (!response.ok) {
                const erroData = await response.json();
                throw new Error(erroData.erro || `Erro na API: ${response.statusText}`);
            }

            const data = await response.json();

            // --- 4. Renderize os dados na página ---
            if (data.insights && data.insights.length > 0) {
                renderInsights(data.insights);
            } else {
                insightsContainer.innerHTML = "<p>Nenhum insight encontrado.</p>";
            }

        } catch (error) {
            console.error("Falha ao buscar insights:", error);
            insightsContainer.innerHTML = `<p style="color: red;">${error.message}</p>`;
        
        } finally {
            loadingIndicator.classList.add("hidden");
        }
    }

    /**
     * Função para criar os cartões de insight no HTML
     * (Esta função permanece a mesma)
     */
    function renderInsights(insights) {
        insightsContainer.innerHTML = "";
        insights.forEach(insight => {
            const card = document.createElement("div");
            card.className = "insight-card";
            card.innerHTML = `
                <h3>${insight.titulo || 'Insight'}</h3>
                <p>${insight.dado || 'Sem detalhes'}</p>
            `;
            insightsContainer.appendChild(card);
        });
    }
});