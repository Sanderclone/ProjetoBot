# ===================================================================
# --- ESTA É A VERSÃO SERVIDOR/API DO BOT (PRONTA PARA PRODUÇÃO) ---
# ---    COM GERENCIAMENTO DINÂMICO DE PLANILHAS (V2)      ---
# ===================================================================
print("✅ INICIANDO SERVIDOR API V2...")

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURAÇÃO DE ACESSO AOS DADOS ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# 🚨 NOVO: Nome da sua planilha de configuração
NOME_PLANILHA_CONFIG = "Bot_Config_Vendas"

# --- 2. INICIALIZAÇÃO DO FLASK E VARIÁVEIS GLOBAIS ---
app = Flask(__name__)
CORS(app)

# Variáveis globais
client_google = None
df_vendas_consolidado = pd.DataFrame()
lista_planilhas_atual = []


def autenticar_google():
    """
    Autentica com as APIs do Google e armazena o cliente em uma variável global.
    """
    global client_google
    print("🔄 Autenticando com as APIs do Google...")
    try:
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
        if not GOOGLE_API_KEY:
            print("❌ ERRO: A variável de ambiente 'GOOGLE_API_KEY' não foi definida.")
            return False

        genai.configure(api_key=GOOGLE_API_KEY)
        print("✅ API da Gemini configurada.")

        google_creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not google_creds_json_str:
            print("❌ ERRO: A variável de ambiente 'GOOGLE_CREDENTIALS_JSON' não foi definida.")
            return False
        
        creds_dict = json.loads(google_creds_json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client_google = gspread.authorize(creds)
        print("✅ Autenticação com a API do Google bem-sucedida!")
        return True

    except Exception as e:
        print(f"❌ ERRO na autenticação: {e}")
        return False

def recarregar_dados_completos():
    """
    Lê a planilha de configuração, e então carrega todas as planilhas de dados.
    Esta função agora atualiza as variáveis globais.
    """
    global df_vendas_consolidado, lista_planilhas_atual
    
    if client_google is None:
        print("❌ Cliente Google não autenticado. Abortando recarga.")
        return

    print("🔄 Recarregando lista de planilhas e todos os dados...")
    
    # 1. Ler a planilha de configuração
    try:
        config_sheet = client_google.open(NOME_PLANILHA_CONFIG).sheet1
        # Pega todos os valores da primeira coluna (exceto o cabeçalho)
        nomes_planilhas = config_sheet.col_values(1)[1:]
        lista_planilhas_atual = nomes_planilhas
        print(f"✅ Lista de planilhas lida da configuração: {len(nomes_planilhas)} planilhas.")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: Não foi possível ler a planilha de configuração '{NOME_PLANILHA_CONFIG}'. Erro: {e}")
        lista_planilhas_atual = []
        df_vendas_consolidado = pd.DataFrame()
        return

    # 2. Carregar os dados das planilhas listadas
    lista_de_dataframes = []
    print("\nIniciando a leitura das planilhas de dados...")
    for nome_planilha in nomes_planilhas:
        try:
            planilha = client_google.open(nome_planilha).sheet1
            dados_mes = pd.DataFrame(planilha.get_all_records())
            lista_de_dataframes.append(dados_mes)
            print(f"  > Planilha '{nome_planilha}' lida com sucesso.")
        except Exception as e:
            print(f"⚠ AVISO ao ler '{nome_planilha}': {e}")

    if lista_de_dataframes:
        df_vendas_consolidado = pd.concat(lista_de_dataframes, ignore_index=True)
        print("\n--- Consolidação Finalizada ---")
        print(f"✅ Total de {len(df_vendas_consolidado)} registros de vendas foram carregados.")
    else:
        print("\n❌ NENHUM DADO FOI CARREGADO. O dataframe está vazio.")

# ... (Sua função analisar_com_gemini(...) continua exatamente igual aqui) ...
def analisar_com_gemini(dataframe, pergunta):
    """
    Função que recebe os dados e a pergunta, e retorna a análise da Gemini.
    Otimizada para perguntas simples (com Pandas) e perguntas complexas (com Amostra).
    """
    print(f"Iniciando análise para a pergunta: '{pergunta[:50]}...'")
    
    try:
        pergunta_lower = pergunta.lower()
        
        # --- OTIMIZAÇÃO 1: PERGUNTAS COM PANDAS ---
        if "total de vendas" in pergunta_lower or "venda total" in pergunta_lower:
            print("--> Otimização: Pergunta de 'Total de Vendas' detectada.")
            
            # Usa o nome correto da coluna que descobrimos
            dataframe['Receita_Total'] = pd.to_numeric(dataframe['Receita_Total'], errors='coerce')
            total_vendas = dataframe['Receita_Total'].sum()
            
            resposta_formatada = f"O total de vendas consolidado de todos os 12 meses é de **R$ {total_vendas:,.2f}**."
            print("✅ Resposta calculada via Pandas.")
            return resposta_formatada

        # (Você pode adicionar mais blocos 'elif' aqui para outras perguntas)
        
    except Exception as e:
        print(f"⚠ Erro durante a otimização com Pandas: {e}")
        # Se a otimização falhar, continua para o método de amostragem

    # --- OTIMIZAÇÃO 2: PERGUNTAS GERAIS COM AMOSTRA ---
    print("--> Otimização: Pergunta geral detectada. Enviando AMOSTRA para a Gemini.")
    try:
        # Criamos uma amostra pequena para não estourar o limite
        amostra_dados = dataframe.head(20).to_csv(index=False)
        total_registros = len(dataframe)

        dados_em_string = amostra_dados
        
        prompt = f"""
        Você é um Analista de Vendas Sênior.
        Sua tarefa é analisar uma AMOSTRA de dados de vendas e responder à pergunta.
        AVISO: Você está vendo apenas os 20 primeiros registros de um total de {total_registros} registros. 
        Baseie sua análise APENAS nos dados fornecidos.

        *Amostra dos Dados de Vendas (20 de {total_registros} registros):*
        csv
        {dados_em_string}
        

        *Pergunta do Usuário:* {pergunta}

        *Sua Análise (baseada na amostra):*
        """
        
        print("Enviando AMOSTRA para a Gemini...")
        # Usando o modelo que funcionou no log anterior
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content(prompt)
        print("✅ Resposta da Gemini (baseada em amostra) recebida.")
        return response.text
    
    except Exception as e:
        print(f"❌ Ocorreu um erro ao chamar a API da Gemini: {e}")
        return f"Erro ao processar sua solicitação: {e}"

# --- 3. ENDPOINT DE ANÁLISE (O que já tínhamos) ---
@app.route('/api/gerar-insights', methods=['POST', 'OPTIONS'])
def endpoint_gerar_insights():
    if request.method == 'OPTIONS':
        return jsonify({"message": "CORS preflight OK"}), 200

    if df_vendas_consolidado.empty:
        print("❌ Tentativa de acesso à API, mas os dados não estão carregados.")
        return jsonify({"erro": "Os dados das planilhas não foram carregados no servidor."}), 500

    try:
        dados_requisicao = request.json
        pergunta = dados_requisicao.get('pergunta')

        if not pergunta:
            return jsonify({"erro": "Nenhuma pergunta foi fornecida."}), 400

        resposta_analise = analisar_com_gemini(df_vendas_consolidado, pergunta)

        resposta_json = {
            "insights": [
                {
                    "titulo": f"Análise para: '{pergunta}'",
                    "dados": resposta_analise
                }
            ]
        }
        return jsonify(resposta_json)

    except Exception as e:
        print(f"❌ Erro inesperado no endpoint: {e}")
        return jsonify({"erro": f"Erro interno do servidor: {e}"}), 500

# ===================================================================
# --- 4. NOVOS ENDPOINTS DE GERENCIAMENTO DE PLANILHAS ---
# ===================================================================

@app.route('/api/planilhas', methods=['GET'])
def get_planilhas():
    """Retorna a lista de planilhas atualmente carregadas."""
    return jsonify({"planilhas": lista_planilhas_atual})

@app.route('/api/planilhas/add', methods=['POST'])
def add_planilha():
    """Adiciona uma nova planilha à planilha de configuração."""
    try:
        nome_planilha = request.json.get('nome')
        if not nome_planilha:
            return jsonify({"erro": "Nome da planilha não fornecido."}), 400

        config_sheet = client_google.open(NOME_PLANILHA_CONFIG).sheet1
        config_sheet.append_row([nome_planilha])
        
        # Força a recarga de todos os dados
        recarregar_dados_completos()
        
        return jsonify({"sucesso": f"Planilha '{nome_planilha}' adicionada. Dados recarregados."}), 201

    except Exception as e:
        return jsonify({"erro": f"Erro ao adicionar planilha: {e}"}), 500

@app.route('/api/planilhas/remove', methods=['POST'])
def remove_planilha():
    """Remove uma planilha da planilha de configuração."""
    try:
        nome_planilha = request.json.get('nome')
        if not nome_planilha:
            return jsonify({"erro": "Nome da planilha não fornecido."}), 400

        config_sheet = client_google.open(NOME_PLANILHA_CONFIG).sheet1
        
        # Encontra a célula com o nome e deleta a linha
        cell = config_sheet.find(nome_planilha)
        if not cell:
            return jsonify({"erro": f"Planilha '{nome_planilha}' não encontrada na configuração."}), 404
            
        config_sheet.delete_rows(cell.row)
        
        # Força a recarga de todos os dados
        recarregar_dados_completos()
        
        return jsonify({"sucesso": f"Planilha '{nome_planilha}' removida. Dados recarregados."}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao remover planilha: {e}"}), 500

# ===================================================================
# --- 5. EXECUÇÃO DO SERVIDOR ---
# ===================================================================

# Autentica primeiro
if autenticar_google():
    # Se a autenticação for bem-sucedida, faz a carga inicial de dados
    recarregar_dados_completos()
else:
    print("❌ FALHA NA AUTENTICAÇÃO INICIAL. O servidor será iniciado, mas não carregará dados.")

# Este bloco só é usado para rodar localmente (ex: python app.py)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"\n\n✅ Servidor API (modo local) pronto e ouvindo na porta {port}")
    # A linha abaixo NÃO é usada pelo Gunicorn/Render
    app.run(host="0.0.0.0", port=port)
