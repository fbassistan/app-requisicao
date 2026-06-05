import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# COLE AQUI O LINK DA SUA PLANILHA DO GOOGLE SHEETS
URL_DA_PLANILHA = "https://docs.google.com/spreadsheets/d/1BvEklBa3wWgqYHb1TVbEeLSuoAP37bVx4VBHP8uQjT0/edit?gid=0#gid=0"

# Conexão com o Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Erro ao conectar com o banco de dados. Configure as credenciais na nuvem.")

# DADOS_ITENS (Mantenha a sua lista com os 300 itens aqui)
DADOS_ITENS = {
    "RESTAURANTE ATUAL": ["763 - COSTELA BOI KG", "247 - FILÉ MIGNON PEÇA KG"],
    "BAR": ["64 - AGUA COM GAS SAN PELLEGRINO", "47 - COCA COLA LATA 350ML"],
    "SALÃO": ["Domaine de la Solitude Chateauneuf du Pape 2021", "SORO FISIOLOGICO"]
}

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("📝 Sistema de Requisição Diária")

nome_solicitante = st.text_input("Nome do Solicitante:", placeholder="Ex: João Silva")
setor_selecionado = st.selectbox("Selecione o seu Setor:", list(DADOS_ITENS.keys()))

st.write("---")

lista_itens_setor = DADOS_ITENS[setor_selecionado]
item_escolhido = st.selectbox("Busque e selecione o Item:", lista_itens_setor)
quantidade = st.number_input("Quantidade necessária:", min_value=1, value=1, step=1)

if st.button("➕ Adicionar Item ao Pedido", use_container_width=True):
    if nome_solicitante.strip() == "":
        st.error("Por favor, preencha o seu nome antes de adicionar itens.")
    else:
        st.session_state.carrinho.append({
            "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Solicitante": nome_solicitante,
            "Setor": setor_selecionado,
            "Item": item_escolhido,
            "Quantidade": int(quantidade)
        })
        st.success(f"Adicionado: {quantidade}x {item_escolhido}")

if st.session_state.carrinho:
    st.write("### 🛒 Itens no Pedido Atual")
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.dataframe(df_carrinho[["Item", "Quantidade", "Setor"]], use_container_width=True)
    
    if st.button("🗑️ Limpar Todo o Pedido", type="secondary"):
        st.session_state.carrinho = []
        st.rerun()
        
    st.write("---")
    
    # ENVIO PARA O GOOGLE SHEETS
    if st.button("🚀 ENVIAR REQUISIÇÃO PARA A CENTRAL", type="primary", use_container_width=True):
        with st.spinner("Enviando dados para a nuvem..."):
            try:
                # Lê os dados atuais da planilha
                dados_existentes = conn.read(spreadsheet=URL_DA_PLANILHA, worksheet="Página1")
                
                # Junta os dados antigos com o carrinho novo
                dados_atualizados = pd.concat([dados_existentes, df_carrinho], ignore_index=True)
                
                # Grava de volta no Google Sheets
                conn.update(spreadsheet=URL_DA_PLANILHA, worksheet="Página1", data=dados_atualizados)
                
                st.balloons()
                st.success(f"🎉 Pedido enviado com sucesso! As linhas foram gravadas na central.")
                st.session_state.carrinho = []
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar na nuvem: {e}. Garanta que as permissões estão públicas.")