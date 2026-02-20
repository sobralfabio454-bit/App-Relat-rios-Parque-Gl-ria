import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fillpdf import fillpdfs
import os

# --- LÓGICA DE NEGÓCIO ---
def processar_dados_s21(df_pub, categoria):
    meses_servico = ["Setembro", "Outubro", "Novembro", "Dezembro", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto"]
    resultado = {}
    
    for mes in meses_servico:
        linha_mes = df_pub[df_pub['Mes'] == mes]
        if not linha_mes.empty and str(linha_mes['Participou'].iloc[0]).upper() == 'TRUE':
            resultado[f'Check_{mes}'] = True
            resultado[f'Estudos_{mes}'] = linha_mes['Estudos'].iloc[0]
            # REGRA: Horas apenas para Pioneiros
            if categoria in ['Pioneiro Regular', 'Pioneiro Auxiliar']:
                resultado[f'Horas_{mes}'] = linha_mes['Horas'].iloc[0]
        else:
            resultado[f'Check_{mes}'] = False
            
    return resultado

# --- INTERFACE STREAMLIT ---
st.title("🗂️ Automação de Cartões S-21-T")

sheet_id = st.sidebar.text_input("ID da Planilha Google", value="1q6hhT9wfOOzpBXVdsGe_K5b__GvvHNL6ppgl39ITxCk")
uploaded_pdf = st.sidebar.file_uploader("Template S-21-T (PDF)", type="pdf")

if sheet_id and uploaded_pdf:
    if st.button("Gerar Cartões"):
        # Autenticação
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1
        
        df = pd.DataFrame(sheet.get_all_records())
        nomes_unicos = df['Nome'].unique()

        for nome in nomes_unicos:
            df_individual = df[df['Nome'] == nome]
            cat_atual = df_individual['Categoria'].iloc[0]
            
            # Preenche dados fixos da planilha
            campos_pdf = {
                'Nome': nome,
                'Nascimento': df_individual['Nascimento'].iloc[0],
                'Batismo': df_individual['Batismo'].iloc[0],
                'Sexo': df_individual['Sexo'].iloc[0],
                'Esperanca': df_individual['Esperança'].iloc[0],
                'Designacao': df_individual['Designacao'].iloc[0]
            }
            
            # Adiciona os relatórios mensais
            relatorios = processar_dados_s21(df_individual, cat_atual)
            campos_pdf.update(relatorios)
            
            # Gera o PDF
            output_pdf = f"S21_{nome.replace(' ', '_')}.pdf"
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            
            fillpdfs.write_fillable_pdf("temp.pdf", output_pdf, campos_pdf)
            st.success(f"✅ Cartão de {nome} gerado!")
            
            with open(output_pdf, "rb") as file:
                st.download_button(label="📥 Baixar PDF", data=file, file_name=output_pdf, key=nome)
