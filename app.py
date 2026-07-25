import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import unicodedata
import os

from streamlit_mic_recorder import mic_recorder
from google import genai
from google.genai import types

st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# ==============================================================================
# CONFIGURAÇÃO SEGURA DA CHAVE API DO GEMINI
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        GEMINI_API_KEY = ""

with st.sidebar:
    st.header("⚙️ Configurações de IA")
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = st.text_input("Insira sua Gemini API Key:", type="password")
        st.caption("Obtenha uma chave gratuita em: https://aistudio.google.com/")
    else:
        st.success("✅ Chave da IA configurada!")

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

NOVOS_ITENS = buscar_itens_nuvem()
SETORES = ["RESTAURANTE / COZINHA", "BAR", "SALÃO"]

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
# SISTEMA DE RECUPERAÇÃO DE BACKUP
# ==============================================================================
nome_limpo_idx = remover_acentos(nome_solicitante).replace(" ", "_") if nome_solicitante.strip() else ""

if nome_limpo_idx and st.session_state.usuario_anterior != nome_solicitante:
    arquivo_backup = f"backup_{nome_limpo_idx}.csv"
    if os.path.exists(arquivo_backup):
        try:
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

# ==============================================================================
# 🎙️ MÓDULO: PEDIDO POR VOZ COM IA
# ==============================================================================
with st.expander("🎙️ **Ditar Pedido Completo por Voz (IA)**", expanded=False):
    st.caption("Clique no botão abaixo, fale todos os itens e quantidades e a IA preencherá seu carrinho.")
    
    audio = mic_recorder(
        start_prompt="🎙️ Clique para Começar a Falar",
        stop_prompt="⏹️ Parar e Enviar para IA",
        key='gravador_voz_ia'
    )
    
    if audio and 'bytes' in audio:
        if not GEMINI_API_KEY:
            st.error("⚠️ Insira sua API Key do Gemini na barra lateral para habilitar o recurso de voz.")
        else:
            with st.spinner("🧠 A IA está interpretando seu áudio..."):
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    catalogo_str = "\n".join(opcoes_itens)
                    
                    prompt = f"""
                    Você é um assistente de almoxarifado. Analise o áudio enviado e extraia os itens e quantidades solicitados.
                    
                    Lista de produtos disponíveis no catálogo:
                    ---
                    {catalogo_str}
                    ---
                    
                    Instruções:
                    1. Para cada produto citado no áudio, encontre o NOME EXATO correspondente no catálogo acima.
                    2. Se a quantidade não for dita, considere 1.
                    3. Responda ESTRITAMENTE em formato JSON (array de objetos) sem marcações de código markdown:
                    [
                      {{
                        "item": "NOME EXATO DO CATÁLOGO",
                        "quantidade": 1,
                        "observacao": "obs se houver ou -"
                      }}
                    ]
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(data=audio['bytes'], mime_type='audio/wav'),
                            prompt
                        ],
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    
                    itens_interpretados = json.loads(response.text)
                    novos_registros = []
                    
                    for it in itens_interpretados:
                        nome_item_ia = str(it.get("item", "")).strip().upper()
                        qtd_ia = int(it.get("quantidade", 1))
                        obs_ia = str(it.get("observacao", "-")).strip()
                        if not obs_ia: obs_ia = "-"
                        
                        if nome_item_ia in mapeamento_itens:
                            dados = mapeamento_itens[nome_item_ia]
                            cod, cat, uni = dados["codigo"], dados["categoria"], dados["unidade"]
                        else:
                            cod, cat, uni = "MANUAL", "VOZ_IA", "UND"
                            
                        novos_registros.append({
                            "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "Solicitante": nome_solicitante if nome_solicitante else "Atendimento Voz",
                            "Setor": setor_selecionado,
                            "Codigo": cod,
                            "Categoria": cat,
                            "Item": nome_item_ia if nome_item_ia else "ITEM_NAO_IDENTIFICADO",
                            "Quantidade": qtd_ia,
                            "Unidade": uni,
                            "Observacao": obs_ia
                        })
                        
                    if novos_registros:
                        df_novos = pd.DataFrame(novos_registros)
                        st.session_state.carrinho_df = pd.concat([st.session_state.carrinho_df, df_novos], ignore_index=True)
                        
                        if nome_limpo_idx:
                            st.session_state.carrinho_df.to_csv(f"backup_{nome_limpo_idx}.csv", index=False)
                            
                        st.toast(f"✅ {len(novos_registros)} item(ns) adicionados pela IA!")
                        time.sleep(1)
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Erro ao processar áudio: {e}")

st.write("---")

# ==============================================================================
# 3. DIGITAÇÃO MANUAL / FORMULÁRIO TRADICIONAL
# ==============================================================================
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
        
        item_bruto_display = st.selectbox(
            "Selecione o Item:", 
            opcoes_display, 
            index=None, 
            placeholder="Digite o nome do item para buscar...", 
            key=f"item_select_{st.session_state.reset_counter}"
        )
        
        if item_bruto_display:
            item_original_desc = mapeamento_display[item_bruto_display]
            dados_item = mapeamento_itens[item_original_desc]
            item_nome_limpo = item_original_desc
            unidade_medida = dados_item["unidade"]
            codigo_detectado = dados_item["codigo"]
            subcategoria_detectada = dados_item["categoria"]
            
            st.markdown(f"⚖️ **Unidade de Medida Padrão:** `{unidade_medida}`")
        else:
            item_nome_limpo = ""
            unidade_medida = "UND"
            codigo_detectado = "-"
            subcategoria_detectada = "OUTROS"
    else:
        st.warning("Carregando lista de produtos ou a planilha na nuvem está vazia...")
        item_nome_limpo = ""
        unidade_medida = "UND"
        codigo_detectado = "-"
        subcategoria_detectada = "OUTROS"

quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1, key=f"qtd_{st.session_state.reset_counter}")
observacao = st.text_input("Observação:", key=f"obs_{st.session_state.reset_counter}")

# ==============================================================================
# 4. LÓGICA DO CARRINHO E ENVIO
# ==============================================================================
if st.button("➕ Adicionar ao Pedido", width="stretch"):
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
        width="stretch", 
        num_rows="dynamic"
    )
    
    if nome_limpo_idx:
        st.session_state.carrinho_df.to_csv(f"backup_{nome_limpo_idx}.csv", index=False)
    
    if st.button("🚀 ENVIAR PARA A CENTRAL", type="primary", width="stretch"):
        try:
            req = urllib.request.Request(
                URL_WEB_APP, 
                method="POST", 
                data=json.dumps(st.session_state.carrinho_df.to_dict(orient='records')).encode('utf-8'), 
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as res:
                if "Success" in res.read().decode('utf-8'):
                    st.balloons()
                    st.success("Enviado com sucesso!")
                    
                    if nome_limpo_idx and os.path.exists(f"backup_{nome_limpo_idx}.csv"):
                        os.remove(f"backup_{nome_limpo_idx}.csv")
                        
                    st.session_state.carrinho_df = pd.DataFrame(
                        columns=["Data_Hora", "Solicitante", "Setor", "Codigo", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"]
                    )
                    time.sleep(2); st.rerun()
        except Exception as e: st.error(f"Erro: {e}")
