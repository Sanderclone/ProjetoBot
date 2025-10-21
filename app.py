# ===================================================================
# --- ESTA É A VERSÃO SERVIDOR/API DO BOT ---
# ===================================================================
print("✅ INICIANDO SERVIDOR API...")

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS # Importante para permitir a comunicação

# --- 1. CONFIGURAÇÃO DE ACESSO AOS DADOS ---
# (Mesma configuração que você já tinha)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
NOME_ARQUIVO_CREDENCIAL = 'projeto-bot-475402-b8c0cd9edb26.json'
NOMES_DAS_PLANILHAS = [
    "vendas_january_2024", "vendas_february_2024", "vendas_march_2024",
    "vendas_april_2024", "vendas_may_2024", "vendas_june_2024",
    "vendas_july_2024", "vendas_august_2024", "vendas_september_2024",
    "vendas_october_2024", "vendas_november_2024", "vendas_december_2024"
]
# 🚨 *INSIRA SUA NOVA CHAVE DE API AQUI* 🚨
GOOGLE_API_KEY = 'AIzaSyDntfKygrswc3rbrzh9h9XTiL1aB6rjC5w' # Chave do seu arquivo

# --- 2. INICIALIZAÇÃO DO FLASK E AUTENTICAÇÃO ---
app = Flask(__name__)
CORS(app) # Habilita o CORS para permitir que o front-end acesse esta API

# Variável global para armazenar os dados carregados
df_vendas_consolidado = pd.DataFrame()

def carregar_dados_google():
    """
    Função para carregar e consolidar os dados das planilhas.
    Será executada uma vez quando o servidor iniciar.
    """
    global df_vendas_consolidado # Modifica a variável global
    try:
        caminho_credencial = os.path.join(os.path.dirname(__file__), NOME_ARQUIVO_CREDENCIAL)
        creds = Credentials.from_service_account_file(caminho_credencial, scopes=SCOPES)
        client = gspread.authorize(creds)
        print("✅ Autenticação com a API do Google bem-sucedida!")
    except Exception as e:
        print(f"❌ ERRO na autenticação: {e}")
        return

    lista_de_dataframes = []
    print("\nIniciando a leitura das planilhas...")
    for nome_planilha in NOMES_DAS_PLANILHAS:
        try:
            planilha = client.open(nome_planilha).sheet1
            dados_mes = pd.DataFrame(planilha.get_all_records())
            lista_de_dataframes.append(dados_mes)
        except Exception as e:
            print(f"⚠ AVISO ao ler '{nome_planilha}': {e}")

    if lista_de_dataframes:
        df_vendas_consolidado = pd.concat(lista_de_dataframes, ignore_index=True)
        print("\n--- Consolidação Finalizada ---")
        print(f"Total de {len(df_vendas_consolidado)} registros de vendas foram carregados.")
    else:
        print("\nNenhum dado foi carregado.")

def analisar_com_gemini(dataframe, pergunta):
    """
    Função que recebe os dados e a pergunta, e retorna a análise da Gemini.
    """
    print(f"Iniciando análise para a pergunta: '{pergunta[:50]}...'")
    if GOOGLE_API_KEY == 'SUA_NOVA_CHAVE_DE_API_AQUI':
        return "ERRO: Chave de API da Gemini não configurada no servidor."

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        dados_em_string = dataframe.to_csv(index=False)
        prompt = f"""
        Você é um Analista de Vendas Sênior da empresa "Alpha Insights".
        Sua tarefa é analisar os dados de vendas anuais e responder à pergunta em português.

        *Dados de Vendas:*
        csv
        {dados_em_string}
        

        *Pergunta do Usuário:* {pergunta}

        *Sua Análise:*
        """
        
        print("Enviando dados para a Gemini...")
        model = genai.GenerativeModel('gemini-1.5-pro') # Usando um modelo robusto
        response = model.generate_content(prompt)
        print("✅ Resposta da Gemini recebida.")
        return response.text
    except Exception as e:
        print(f"❌ Ocorreu um erro ao chamar a API da Gemini: {e}")
        return f"Erro ao processar sua solicitação: {e}"

# --- 3. CRIAÇÃO DO ENDPOINT DA API ---
@app.route('/api/gerar-insights', methods=['POST'])
def endpoint_gerar_insights():
    """
    Este é o endpoint que o seu front-end (JavaScript) vai chamar.
    Ele espera um JSON com a chave "pergunta".
    """
    if df_vendas_consolidado.empty:
        print("❌ Tentativa de acesso à API, mas os dados não estão carregados.")
        return jsonify({"erro": "Os dados das planilhas não foram carregados no servidor."}), 500

    try:
        # Pega a pergunta que veio do front-end (JSON)
        dados_requisicao = request.json
        pergunta = dados_requisicao.get('pergunta')

        if not pergunta:
            return jsonify({"erro": "Nenhuma pergunta foi fornecida."}), 400

        # Chama a função de análise
        resposta_analise = analisar_com_gemini(df_vendas_consolidado, pergunta)

        # Retorna a resposta da análise para o front-end
        # Estrutura de resposta que o front-end espera
        resposta_json = {
            "insights": [
                {
                    "titulo": f"Análise para: '{pergunta}'",
                    "dado": resposta_analise
                }
            ]
        }
        return jsonify(resposta_json)

    except Exception as e:
        print(f"❌ Erro inesperado no endpoint: {e}")
        return jsonify({"erro": f"Erro interno do servidor: {e}"}), 500

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Carrega os dados uma vez ao iniciar
    carregar_dados_google()
    # Inicia o servidor Flask
    # 'host="0.0.0.0"' permite que ele seja acessado de fora do container (se aplicável)
    # 'port=5000' é a porta padrão
    print("\n\n✅ Servidor API pronto e ouvindo na porta 5000")
    print("Acesse http://127.0.0.1:5000 para testar (embora o endpoint seja /api/gerar-insights)")
    app.run(host="0.0.0.0", port=5000, debug=True)