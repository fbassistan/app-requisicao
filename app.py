import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import unicodedata
import os  # ➔ REATIVADO: Necessário para salvar e deletar os arquivos de backup

st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# ==============================================================================
# 1. FUNÇÃO PARA BUSCAR OS ITENS DIRETO DA NUVEM (GOOGLE SHEETS)
# ==============================================================================
@st.cache_data(ttl=300)
def buscar_itens_nuvem():
    try:
        with urllib.request.urlopen(URL_WEB_APP, timeout=10) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        st.error(f"Erro ao carregar produtos da nuvem: {e}")
        return []

# Carrega os itens dinamicamente da nuvem
NOVOS_ITENS = buscar_itens_nuvem()

# Lista fixa de Setores
SETORES = ["RESTAURANTE / COZINHA", "BAR", "SALÃO"]

# Inicialização do Session State
if 'usuario_anterior' not in st.session_state: st.session_state.usuario_anterior = ""
if 'carrinho_df' not in st.session_state: 
    st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Codigo", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

def remover_acentos(texto): 
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

st.title("📝 Sistema de Requisição")
nome_solicitante = st.text_input("Nome do Solicitante:")
setor_selecionado = st.selectbox("Selecione o seu Setor:", SETORES)

# ==============================================================================
# SISTEMA DE RECUPERAÇÃO DE BACKUP (CASO A PÁGINA FECHE)
# ==============================================================================
nome_limpo_idx = remover_acentos(nome_solicitante).replace(" ", "_") if nome_solicitante.strip() else ""

# Se o solicitante digitou o nome e mudou em relação ao estado anterior
if nome_limpo_idx and st.session_state.usuario_anterior != nome_solicitante:
    arquivo_backup = f"backup_{nome_limpo_idx}.csv"
    if os.path.exists(arquivo_backup):
        try:
            # Recupera o arquivo CSV e joga de volta no carrinho do app
            df_backup = pd.read_csv(arquivo_backup)
            st.session_state.carrinho_df = df_backup
            st.toast(f"🔄 Pedido anterior de {nome_solicitante} foi recuperado!")
        except Exception:
            pass
    st.session_state.usuario_anterior = nome_solicitante

# ==============================================================================
# 2. PROCESSAMENTO E MAPEAMENTO DA LISTA GLOBAL
# ==============================================================================
mapeamento_itens = {}
for item in NOVOS_ITENS:
    desc = item.get("descricao", "").strip().upper()
    if desc:
        mapeamento_itens[desc] = {
            "codigo": str(item.get("codigo", "")).strip() if item.get("codigo") else "-",
            "categoria": str(item.get("categoria", "")).strip().upper() if item.get("categoria") else "OUTROS",
            "unidade": str(item.get("unidade", "")).strip().upper() if item.get("unidade") else "UND"
        }

opcoes_itens = sorted(list(mapeamento_itens.keys()))

item_nao_cadastrado = st.checkbox("⚠️ Item NÃO está na lista?", key=f"manual_{st.session_state.reset_counter}")

if item_nao_cadastrado:
    item_bruto = st.text_input("Nome do Item:", key=f"item_manual_{st.session_state.reset_counter}")
    unidade_medida = st.selectbox("Unidade:", ["UND", "KG", "L", "LATA", "PORÇÃO", "G", "ML", "GFA", "PCT", "MAÇO", "CX"], key=f"uni_manual_{st.session_state.reset_counter}")
    codigo_detectado = st.text_input("Código (Se houver):", value="-", key=f"cod_manual_{st.session_state.reset_counter}")
    item_nome_limpo = item_bruto.upper().strip()
    subcategoria_detectada = "MANUAL"
else:
    if opcoes_itens:
        opcoes_display = [f"{i} ({remover_acentos(i)})" if remover_acentos(i) != i else i for i in opcoes_itens]
        mapeamento_display = {f"{i} ({remover_acentos(i)})" if remover_acentos(i) != i else i: i for i in opcoes_itens}
        
        item_bruto_display = st.selectbox("Selecione o Item:", opcoes_display, key=f"item_select_{st.session_state.reset_counter}")
        item_original_desc = mapeamento_display[item_bruto_display]
        
        dados_item = mapeamento_itens[item_original_desc]
        item_nome_limpo = item_original_desc
        unidade_medida = dados_item["unidade"]
        codigo_detectado = dados_item["codigo"]
        subcategoria_detectada = dados_item["categoria"]
        
        st.markdown(f"⚖️ **Unidade de Medida Padrão:** `{unidade_medida}`")
    else:
        st.warning("Carregando lista de produtos ou a planilha na nuvem está vazia...")
        item_nome_limpo = ""
        unidade_medida = "UND"
        codigo_detectado = "-"
        subcategoria_detectada = "OUTROS"

quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1, key=f"qtd_{st.session_state.reset_counter}")
observacao = st.text_input("Observação:", key=f"obs_{st.session_state.reset_counter}")

# ==============================================================================
# 3. LÓGICA DO CARRINHO E ENVIO
# ==============================================================================
if st.button("➕ Adicionar ao Pedido", use_container_width=True):
    if not nome_solicitante.strip(): st.error("Preencha seu nome.")
    elif not item_nome_limpo: st.error("Selecione ou digite um item válido.")
    else:
        texto_obs = observacao.strip() if observacao.strip() else "-"
        
        mask = (st.session_state.carrinho_df["Item"] == item_nome_limpo) & \
               (st.session_state.carrinho_df["Codigo"] == codigo_detectado) & \
               (st.session_state.carrinho_df["Observacao"] == texto_obs)
               
        if mask.any():
            idx = st.session_state.carrinho_df[mask].index[0]
            st.session_state.carrinho_df.at[idx, "Quantidade"] += int(quantidade)
        else:
            novo = pd.DataFrame([{
                "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                "Solicitante": nome_solicitante, 
                "Setor": setor_selecionado, 
                "Codigo": codigo_detectado,
                "Categoria": subcategoria_detectada, 
                "Item": item_nome_limpo, 
                "Quantidade": int(quantidade), 
                "Unidade": unidade_medida, 
                "Observacao": texto_obs
            }])
            st.session_state.carrinho_df = pd.concat([st.session_state.carrinho_df, novo], ignore_index=True)
        
        # ➔ SALVAMENTO AUTOMÁTICO: Salva o backup local sempre que um item for adicionado
        if nome_limpo_idx:
            st.session_state.carrinho_df.to_csv(f"backup_{nome_limpo_idx}.csv", index=False)
            
        st.session_state.reset_counter += 1
        st.rerun()

if not st.session_state.carrinho_df.empty:
    st.write("### 🛒 Pedido Atual")
    st.session_state.carrinho_df = st.data_editor(
        st.session_state.carrinho_df, 
        column_config={
            "Data_Hora": None, 
            "Solicitante": None, 
            "Setor": None, 
            "Codigo": st.column_config.TextColumn(disabled=True),
            "Categoria": None, 
            "Item": st.column_config.TextColumn(disabled=True), 
            "Unidade": st.column_config.TextColumn(disabled=True)
        }, 
        use_container_width=True, 
        num_rows="dynamic"
    )
    
    # ➔ SALVAMENTO AUTOMÁTICO: Atualiza o backup caso o usuário delete ou mude a quantidade direto na tabela
    if nome_limpo_idx:
        st.session_state.carrinho_df.to_csv(f"backup_{nome_limpo_idx}.csv", index=False)
    
    if st.button("🚀 ENVIAR PARA A CENTRAL", type="primary", use_container_width=True):
        try:
            req = urllib.request.Request(URL_WEB_APP, method="POST", data=json.dumps(st.session_state.carrinho_df.to_dict(orient='records')).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as res:
                if "Success" in res.read().decode('utf-8'):
                    st.balloons()
                    st.success("Enviado com sucesso!")
                    
                    # ➔ LIMPEZA DO BACKUP: Como o envio deu certo, deletamos o arquivo temporário
                    if nome_limpo_idx and os.path.exists(f"backup_{nome_limpo_idx}.csv"):
                        os.remove(f"backup_{nome_limpo_idx}.csv")
                        
                    st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Codigo", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
                    time.sleep(2); st.rerun()
        except Exception as e: st.error(f"Erro: {e}")
