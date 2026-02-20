import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fillpdf import fillpdfs
import os

# --- CONFIGURAÇÃO E LÓGICA ---
class S21Automation:
    def __init__(self):
        self.meses = [
            "Setembro", "Outubro", "Novembro", "Dezembro", "Janeiro", 
            "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto"
        ]

    def conectar_google_sheets(self, sheet_id):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
      import json
# ... dentro do __init__ ou da função de conexão:
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        """
        Regra 1: Publicador soma estudos. 
        Pioneiros (Aux/Regular) somam estudos e horas.
        Regra 4: Identifica 'Não relatou'.
        """
        dados_pdf = {}
        total_horas = 0
        total_estudos = 0

        for mes in self.meses:
            # Filtra linha do mês
            row = df_meses[df_meses['Mes'] == mes]
            
            if row.empty or not row['Participou'].iloc[0]:
                dados_pdf[f'Check_{mes}'] = False
                dados_pdf[f'Obs_{mes}'] = "Não relatou"
            else:
                dados_pdf[f'Check_{mes}'] = True
                estudos = int(row['Estudos'].iloc[0])
                dados_pdf[f'Estudos_{mes}'] = estudos
                total_estudos += estudos

                # Lógica de Horas (Apenas Pioneiros)
                if categoria in ['Pioneiro Auxiliar', 'Pioneiro Regular']:
                    horas = int(row['Horas'].iloc[0])
                    dados_pdf[f'Horas_{mes}'] = horas
                    total_horas += horas
                
                # Checkbox Pioneiro Auxiliar específico no mês
                if categoria == 'Pioneiro Auxiliar':
                    dados_pdf[f'Aux_{mes}'] = True

        dados_pdf['Total_Horas'] = total_horas
        dados_pdf['Total_Estudos'] = total_estudos
        return dados_pdf

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Gerador S-21 Automatizado", layout="wide")
st.title("🗂️ Automação de Cartões S-21-T")

with st.sidebar:
    st.header("Configurações")
    sheet_id = st.text_input("ID da Planilha Google")
    uploaded_pdf = st.file_uploader("Template S-21-T (PDF)", type="pdf")

if sheet_id and uploaded_pdf:
    if st.button("Gerar Cartões"):
        automation = S21Automation()
        
        # 1. Obter Dados
        sheet = automation.conectar_google_sheets(sheet_id)
        data = pd.DataFrame(sheet.get_all_records())
        
        # 2. Iterar por Publicador
        for _, pub in data.iterrows():
            st.write(f"Processando: {pub['Nome']}")
            
            # Mapeamento de campos básicos (Regra 3)
            campos = {
                'Nome': pub['Nome'],
                'Nascimento': pub['Nascimento'],
                'Batismo': pub['Batismo'],
                'Sexo_M': True if pub['Sexo'] == 'M' else False,
                'Sexo_F': True if pub['Sexo'] == 'F' else False,
                'Esperança_Ovelhas': True if pub['Esperança'] == 'Outras Ovelhas' else False,
                'Esperança_Ungido': True if pub['Esperança'] == 'Ungido' else False,
                'Designacao_Anciao': True if pub['Designacao'] == 'Ancião' else False,
                'Designacao_Servo': True if pub['Designacao'] == 'Servo Ministerial' else False,
                'Designacao_Pioneiro': True if pub['Categoria'] == 'Pioneiro Regular' else False,
            }

            # Lógica de Relatórios (Ciclo Set-Ago - Regra 2)
            # Aqui supõe-se que você tenha uma aba ou consulta que retorne os meses
            relatorios = automation.processar_relatorios(data[data['Nome'] == pub['Nome']], pub['Categoria'])
            campos.update(relatorios)

            # 3. Preencher PDF
            output_name = f"S21_{pub['Nome'].replace(' ', '_')}.pdf"
            fillpdfs.write_fillable_pdf(uploaded_pdf.name, output_name, campos)
            
            st.success(f"✅ Cartão gerado: {output_name}")

# --- UTILITÁRIO PARA MAPEAR CAMPOS ---
# Use isto uma vez para descobrir os nomes internos das caixas do PDF
if st.checkbox("Debug: Mostrar Nomes dos Campos do PDF"):
    if uploaded_pdf:
        with open("temp.pdf", "wb") as f: f.write(uploaded_pdf.getbuffer())
        fields = fillpdfs.get_form_fields("temp.pdf")
        st.write(fields)
