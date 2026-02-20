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
    total_horas = 0
    total_estudos = 0
    
    for mes in meses_servico:
        linha_mes = df_pub[df_pub['Mes'] == mes]
        if not linha_mes.empty and str(linha_mes['Participou'].iloc[0]).upper() == 'TRUE':
            resultado[f'Check_{mes}'] = True
            estudos = linha_mes['Estudos'].iloc[0]
            resultado[f'Estudos_{mes}'] = estudos
            total_estudos += int(estudos) if estudos else 0
            
            # REGRA: Horas apenas para Pioneiros
            if categoria in ['Pioneiro Regular', 'Pioneiro Auxiliar']:
                horas = linha_mes['Horas'].iloc[0]
                resultado[f'Horas_{mes}'] = horas
                total_horas += int(horas) if horas else 0
        else:
            resultado[f'Check_{mes}'] = False
            
    resultado['Total_Horas'] = total_horas
    resultado['Total_Estudos'] = total_estudos
    return resultado

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Secretário Virtual S-21", layout="centered")
st.title("🗂️ Gerador Automático de Cartões S-21-T")

# CONFIGURAÇÕES FIXAS (Para não precisar preencher toda vez)
id_padrao = "1q6hhT9wfOOzpBXVdsGe_K5b__GvvHNL6ppgl39ITxCk"
template_path = "S-21_T (1).pdf" # Deve estar no seu GitHub

sheet_id = st.sidebar.text_input("ID da Planilha Google", value=id_padrao)

if sheet_id:
    if st.button("🚀 Gerar Todos os Cartões"):
        if not os.path.exists(template_path):
            st.error(f"❌ Erro: O arquivo '{template_path}' não está no GitHub.")
        else:
            try:
                # Autenticação com as Secrets
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(sheet_id).sheet1
                
                df = pd.DataFrame(sheet.get_all_records())
                nomes_unicos = df['Nome'].unique()

                for nome in nomes_unicos:
                    df_individual = df[df['Nome'] == nome]
                    cat_atual = df_individual['Categoria'].iloc[0]
                    
                    # Dados fixos da planilha
                    campos_pdf = {
                        'Nome': nome,
                        'Nascimento': df_individual['Nascimento'].iloc[0],
                        'Batismo': df_individual['Batismo'].iloc[0],
                        'Sexo': df_individual['Sexo'].iloc[0],
                        'Esperanca': df_individual['Esperança'].iloc[0],
                        'Designacao': df_individual['Designacao'].iloc[0]
                    }
                    
                    relatorios = processar_dados_s21(df_individual, cat_atual)
                    campos_pdf.update(relatorios)
                    
                    output_pdf = f"S21_{nome.replace(' ', '_')}.pdf"
                    fillpdfs.write_fillable_pdf(template_path, output_pdf, campos_pdf)
                    
                    st.success(f"✅ Cartão de {nome} pronto!")
                    with open(output_pdf, "rb") as file:
                        st.download_button(label=f"📥 Baixar Cartão: {nome}", data=file, file_name=output_pdf, key=nome)
            
            except Exception as e:
                st.error(f"Erro: {e}")
