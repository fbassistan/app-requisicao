import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import unicodedata
import os
import re
import difflib

# Componente leve para gravação de áudio do navegador
from streamlit_mic_recorder import speech_to_text

st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# ==============================================================================
# 1. FUNÇÃO COM RETRY AUTOMÁTICO PARA CARREGAR PRODUTOS DA NUVEM
# ==============================================================================
@st.cache_data(ttl=300, show_spinner=False)
def buscar_itens_nuvem():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Tenta até 3 vezes se a conexão com o Google Sheets oscilar ou demorar
    for tentativa in range(3):
        try:
            req = urllib.request.Request(URL_WEB_APP, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as res:
                dados = json.loads(res.read().decode('utf-8'))
                if isinstance(dados, list) and len(dados) > 0:
                    return dados
        except Exception:
            time.sleep(1) # Aguarda 1 segundo antes de tentar novamente
            
    return []

# ==============================================================================
# 2. ALGORITMO LEVE DE TRATAMENTO DE TEXTO E BUSCA POR VOZ
# ==============================================================================
def remover_acentos(texto): 
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

def normalizar_texto(texto):
    texto_nfd = unicodedata.normalize('NFD', str(texto))
    texto_sem_acento = "".join(c for c in texto_nfd if unicodedata.category(c) != 'Mn').upper()
    texto_limpo = re.sub(r'[^A-Z0-9\s]', ' ', texto_sem_acento)
    return " ".join(texto_limpo.split())

NUMEROS_EXTENSO = {
    "UM": 1, "UMA": 1, "DOIS": 2, "DUAS": 2, "TRES": 3, "TRÊS": 3, "QUATRO": 4, "CINCO": 5,
    "SEIS": 6, "SETE": 7, "OITO": 8, "NOVE": 9, "DEZ": 10, "ONZE": 11, "DOZE": 12,
    "QUINZE": 15, "VINTE": 20, "TRINTA": 30, "CINQUENTA": 50
}

STOP_WORDS = {
    "QUERO", "ME", "DA", "VEJA", "POR", "FAVOR", "MANDA", "COLOCA", "ADICIONA", 
    "PRECISO", "DE", "DO", "DA", "DOS", "DAS", "E", "MAIS", "TAMBEM", "GOSTARIA",
    "UNIDADE", "UNIDADES", "KILO", "KILOS", "QUILO", "QUILOS", "PACOTE", "PACOTES", 
    "GARRAFA", "GARRAFAS", "CAIXA", "CAIXAS", "ITEM", "ITENS"
}

# Extrai quantidade mantendo especificações protegidas (350ml, 500g, etc.)
def extrair_qtd_e_item(texto):
    texto_upper = remover_acentos(texto)
    
    medidas_encontradas = {}
    def salvar_medida(m):
        idx = f"__MEDIDA_{len(medidas_encontradas)}__"
        medidas_encontradas[idx] = m.group(0)
        return f" {idx} "

    padrão_specs = r'\b(?:\d+\s*(?:ML|G|GR|KG|L|CL)|C/\s*\d+(?:\s*UND)?)\b'
    texto_protegido = re.sub(padrão_specs, salvar_medida, texto_upper)
    
    palavras = texto_protegido.split()
    palavras_conv = [str(NUMEROS_EXTENSO[p]) if p in NUMEROS_EXTENSO else p for p in palavras]
    texto_tratado = " ".join(palavras_conv)
    
    match_qtd = re.search(r'\b(\d+)\s*(?:X|\*|UNIDADES|UND|LATAS|GARRAFAS|CAIXAS|PACOTES)?\b', texto_tratado)
    quantidade = 1
    if match_qtd:
        quantidade = int(match_qtd.group(1))
        texto_tratado = texto_tratado[:match_qtd.start()] + texto_tratado[match_qtd.end():]
        
    for key, val in medidas_encontradas.items():
        texto_tratado = texto_tratado.replace(key, val)
        
    tokens = normalizar_texto(texto_tratado).split()
    termos_finais = [t for t in tokens if t not in STOP_WORDS]
    
    return quantidade, " ".join(termos_finais)

def fatiar_texto_multiplos_itens(texto_completo):
    texto_upper = remover_acentos(texto_completo)
    palavras = texto_upper.split()
    palavras_conv = [str(NUMEROS_EXTENSO[p]) if p in NUMEROS_EXTENSO else p for p in palavras]
    texto_tratado = " ".join(palavras_conv)
    
    clausulas = re.split(r'\b(?:E|MAIS|TAMBEM)\b|[,;\n\r]', texto_tratado)
    
    sub_frases = []
    for c in clausulas:
        c = c.strip()
        if not c: continue
        tokens = c.split()
        corrente = []
        for token in tokens:
            if token.isdigit() and corrente:
                palavras_uteis = [w for w in corrente if w not in STOP_WORDS and not w.isdigit()]
                if palavras_uteis:
                    sub_frases.append(" ".join(corrente))
                    corrente = [token]
                else:
                    corrente.append(token)
            else:
                corrente.append(token)
        if corrente:
            sub_frases.append(" ".join(corrente))
            
    resultados = []
    for sf in sub_frases:
        qtd, termo = extrair_qtd_e_item(sf)
        if termo.strip():
            resultados.append((sf, qtd, termo))
            
    return resultados

# Algoritmo de busca por palavras-chave e similaridade matemática
def encontrar_item_mais_parecido(termo_busca, catalogo_itens):
    if not termo_busca or not catalogo_itens:
        return None, 0.0
        
    termo_norm = normalizar_texto(termo_busca)
    words_busca = termo_norm.split()
    
    if not words_busca:
        return None, 0.0
        
    melhor_item = None
    melhor_score_final = 0.0
    
    for item in catalogo_itens:
        item_norm = normalizar_texto(item)
        words_item = item_norm.split()
        
        score_substring = 1.0 if termo_norm in item_norm else 0.0
        
        scores_palavras = []
        for pb in words_busca:
            best_p = 0.0
            for pi in words_item:
                if pb == pi:
                    best_p = 1.0
                    break
                elif pb in pi or pi in pb:
                    ratio_sub = min(len(pb), len(pi)) / max(len(pb), len(pi))
                    best_p = max(best_p, 0.85 * ratio_sub)
                else:
                    ratio_seq = difflib.SequenceMatcher(None, pb, pi).ratio()
                    best_p = max(best_p, ratio_seq)
            scores_palavras.append(best_p)
            
        score_cobertura = sum(scores_palavras) / len(scores_palavras) if scores_palavras else 0.0
        ratio_global = difflib.SequenceMatcher(None, termo_norm, item_norm).ratio()
        
        # Ponderação Combinada
        score_final = (score_cobertura * 0.60) + (score_substring * 0.25) + (ratio_global * 0.15)
        
        if all(any(pb == pi or pb in pi for pi in words_item) for pb in words_busca):
            score_final += 0.15
            
        if "ZERO" in words_item and "ZERO" not in words_busca:
            score_final -= 0.15
        elif "ZERO" in words_busca and "ZERO" not in words_item:
            score_final -= 0.25
            
        if score_final > melhor_score_final:
            melhor_score_final = score_final
            melhor_item = item
            
    if melhor_score_final >= 0.30:
        return melhor_item, melhor_score_final
    return None, melhor_score_final

# ==============================================================================
# 3. CARREGAMENTO DOS DADOS E NAVEGAÇÃO
# ==============================================================================
NOVOS_ITENS = buscar_itens_nuvem()
SETORES = ["RESTAURANTE / COZINHA", "BAR", "SALÃO"]

if 'usuario_anterior' not in st.session_state: st.session_state.usuario_anterior = ""
if 'carrinho_df' not in st.session_state: 
    st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Codigo", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

st.title("📝 Sistema de Requisição")

# Botão de emergência caso precise forçar a busca da planilha na nuvem
col_sol, col_btn = st.columns([3, 1])
with col_sol:
    nome_solicitante = st.text_input("Nome do Solicitante:")
with col_btn:
    st.write("")
    st.write("")
    if st.button("🔄 Atualizar Lista", help="Clique para recarregar os produtos da nuvem"):
        st.cache_data.clear()
        st.rerun()

setor_selecionado = st.selectbox("Selecione o seu Setor:", SETORES)

# Backup local por usuário
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

# Mapeamento dos Itens
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
# 🎙️ MÓDULO DE FALA MULTI-ITENS
# ==============================================================================
st.write("### 🎙️ Ditar Múltiplos Itens por Voz")
st.caption("Exemplo: *'Quero 3 filé mignon, 2 heineken e 5 coca cola'*")

texto_falado = speech_to_text(
    language='pt-BR',
    start_prompt="🎙️ Clique para Ditar Vários Itens",
    stop_prompt="⏹️ Parar Gravação",
    just_once=True,
    key=f'stt_{st.session_state.reset_counter}'
)

if texto_falado:
    if not nome_solicitante.strip():
        st.error("⚠️ Preencha seu nome no campo acima antes de ditar os itens!")
    elif not opcoes_itens:
        st.error("⚠️ A lista de produtos está vazia ou ainda sendo carregada. Clique em '🔄 Atualizar Lista'.")
    else:
        with st.spinner("⚡ Identificando produtos..."):
            itens_extraidos = fatiar_texto_multiplos_itens(texto_falado)
            
            adicionados = []
            nao_encontrados = []
            
            for orig, qtd_detectada, termo_busca in itens_extraidos:
                item_encontrado, score = encontrar_item_mais_parecido(termo_busca, opcoes_itens)
                
                if item_encontrado:
                    dados = mapeamento_itens[item_encontrado]
                    cod, cat, uni = dados["codigo"], dados["categoria"], dados["unidade"]
                    texto_obs = "-"
                    
                    mask = (st.session_state.carrinho_df["Item"] == item_encontrado) & \
                           (st.session_state.carrinho_df["Codigo"] == cod) & \
                           (st.session_state.carrinho_df["Observacao"] == texto_obs)
                           
                    if mask.any():
                        idx = st.session_state.carrinho_df[mask].index[0]
                        st.session_state.carrinho_df.at[idx, "Quantidade"] += qtd_detectada
                    else:
                        novo = pd.DataFrame([{
                            "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                            "Solicitante": nome_solicitante, 
                            "Setor": setor_selecionado, 
                            "Codigo": cod,
                            "Categoria": cat, 
                            "Item": item_encontrado, 
                            "Quantidade": qtd_detectada, 
                            "Unidade": uni, 
                            "Observacao": texto_obs
                        }])
                        st.session_state.carrinho_df = pd.concat([st.session_state.carrinho_df, novo], ignore_index=True)
                    
                    adicionados.append(f"{qtd_detectada}x {item_encontrado}")
                else:
                    nao_encontrados.append(termo_busca)
                    
            if adicionados:
                if nome_limpo_idx:
                    st.session_state.carrinho_df.to_csv(f"backup_{nome_limpo_idx}.csv", index=False)
                for item_msg in adicionados:
                    st.toast(f"✅ Adicionado: {item_msg}")
                    
            if nao_encontrados:
                st.warning(f"⚠️ Não foi possível identificar o(s) termo(s): {', '.join(nao_encontrados)}")
                
            if adicionados:
                st.session_state.reset_counter += 1
                time.sleep(1)
                st.rerun()

st.write("---")

# ==============================================================================
# 4. SELEÇÃO MANUAL / FORMULÁRIO
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
        st.warning("⚠️ Carregando lista de produtos da nuvem...")
        item_nome_limpo = ""
        unidade_medida = "UND"
        codigo_detectado = "-"
        subcategoria_detectada = "OUTROS"

quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1, key=f"qtd_{st.session_state.reset_counter}")
observacao = st.text_input("Observação:", key=f"obs_{st.session_state.reset_counter}")

# ==============================================================================
# 5. LÓGICA DO CARRINHO E ENVIO PARA A CENTRAL
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
    
    if nome_limpo_idx:
        st.session_state.carrinho_df.to_csv(f"backup_{nome_limpo_idx}.csv", index=False)
    
    if st.button("🚀 ENVIAR PARA A CENTRAL", type="primary", use_container_width=True):
        try:
            req = urllib.request.Request(
                URL_WEB_APP, 
                method="POST", 
                data=json.dumps(st.session_state.carrinho_df.to_dict(orient='records')).encode('utf-8'), 
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=15) as res:
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
