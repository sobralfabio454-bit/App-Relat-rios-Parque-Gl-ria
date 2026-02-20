import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fillpdf import fillpdfs
import os
import json

# --- CONFIGURAÇÃO E LÓGICA ---
class S21Automation:
    def __init__(self):
        self.meses = [
            "Setembro", "Outubro", "Novembro", "Dezembro", "Janeiro", 
            "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto"
        ]

    def conectar_google_sheets(self, sheet_id):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Puxa as credenciais das Secrets do Streamlit
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id).sheet1

    def processar_relatorios(self, df_meses, categoria):
        dados_pdf = {}
        total_horas = 0
        total_estudos = 0

        for mes in self.meses:
            row = df_meses[df_meses['Mes'] == mes]
            if row.empty or not row['Participou'].iloc[0]:
                dados_pdf[f'Check_{mes}'] = False
            else:
                dados_pdf[f'Check_{mes}'] = True
                estudos = int(row['Estudos'].iloc[0])
                dados_pdf[f'Estudos_{mes}'] = estudos
                total_estudos += estudos
                if categoria in ['Pioneiro Auxiliar', 'Pioneiro Regular']:
                    horas = int(row['Horas'].iloc[0])
                    dados_pdf[f'Horas_{mes}'] = horas
                    total_horas += horas
        
        dados_pdf['Total_Horas'] = total_horas
        dados_pdf['Total_Estudos'] = total_estudos
        return dados_pdf

# --- INTERFACE ---
st.set_page_config(page_title="Gerador S-21 Automatizado", layout="wide")
st.title("🗂️ Automação de Cartões S-21-T")

with st.sidebar:
    st.header("Configurações")
    sheet_id = st.text_input("ID da Planilha Google")
    uploaded_pdf = st.file_uploader("Template S-21-T (PDF)", type="pdf")

if sheet_id and uploaded_pdf:
    if st.button("Gerar Cartões"):
        automation = S21Automation()
        sheet = automation.conectar_google_sheets(sheet_id)
        data = pd.DataFrame(sheet.get_all_records())
        
        for _, pub in data.iterrows():
            st.write(f"Processando: {pub['Nome']}")
            campos = {
                'Nome': pub['Nome'],
                'Nascimento': pub['Nascimento'],
                'Batismo': pub['Batismo'],
            }
            relatorios = automation.processar_relatorios(data[data['Nome'] == pub['Nome']], pub['Categoria'])
            campos.update(relatorios)
            output_name = f"S21_{pub['Nome'].replace(' ', '_')}.pdf"
            fillpdfs.write_fillable_pdf(uploaded_pdf.name, output_name, campos)
            st.success(f"✅ Gerado: {output_name}")
