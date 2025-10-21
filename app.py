# ===================================================================
# --- ESTA É A VERSÃO SERVIDOR/API DO BOT (PRONTA PARA PRODUÇÃO) ---
# ===================================================================
print("✅ INICIANDO SERVIDOR API...")

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os
import json # Importante para ler as credenciais
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. CONFIGURAÇÃO DE ACESSO AOS DADOS ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
NOMES_DAS_PLANILHAS = [
    "vendas_january_2024", "vendas_february_2024", "vendas_march_2024",
    "vendas_april_2024", "vendas_may_2024", "vendas_june_2024",
    "vendas_july_2024", "vendas_august_2024", "vendas_september_2024",
    "vendas_october_2024", "vendas_november_2024", "vendas_december_2024"
]
# As chaves de API e credenciais foram removidas daqui!

# --- 2. INICIALIZAÇÃO DO FLASK E AUTENTICAÇÃO ---
app = Flask(__name__)
CORS(app)

# Variável global para armazenar os dados carregados
df_vendas_consolidado = pd.DataFrame()

def carregar_dados_google():
    """
    Função para carregar e consolidar os dados das planilhas.
    Será executada uma vez quando o servidor iniciar, usando variáveis de ambiente.
    """
    global df_vendas_consolidado
    try:
        # **MUDANÇA 1: Ler a chave da API Gemini da variável de ambiente**
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
        if not GOOGLE_API_KEY:
            print("❌ ERRO: A variável de ambiente 'GOOGLE_API_KEY' não foi definida.")
            return

        genai.configure(api_key=GOOGLE_API_KEY)
        print("✅ API da Gemini configurada.")

        # **MUDANÇA 2: Ler as credenciais do Google da variável de ambiente**
        google_creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not google_creds_json_str:
            print("❌ ERRO: A variável de ambiente 'GOOGLE_CREDENTIALS_JSON' não foi definida.")
            return
        
        # Converte a string JSON (que veio da variável de ambiente) em um dicionário Python
        creds_dict = json.loads(google_creds_json_str)
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
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
    try:
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
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        print("✅ Resposta da Gemini recebida.")
        return response.text
    except Exception as e:
        print(f"❌ Ocorreu um erro ao chamar a API da Gemini: {e}")
        return f"Erro ao processar sua solicitação: {e}"

# --- 3. CRIAÇÃO DO ENDPOINT DA API ---
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

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    carregar_dados_google()
    # A linha app.run() é usada para desenvolvimento. O Render usará o Gunicorn.
    port = int(os.environ.get("PORT", 5000))
    print(f"\n\n✅ Servidor API pronto e ouvindo na porta {port}")
    app.run(host="0.0.0.0", port=port)
