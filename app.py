import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import re
import unicodedata

st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# Banco de Dados Geral e Auditado (202 Itens Cozinha | 169 Itens Bar | 81 Itens Salão)
DADOS_SISTEMA = {
    "RESTAURANTE / COZINHA": {
        "CARNES / AVES": ["COSTELA BOI KG", "FILÉ MIGNON PEÇA KG", "HAMBURGER BOVINO 160 G", "CUPIM KG", "COXA SOBRECOXA KG", "FILE FRANGO KG", "RABADA KG", "MOCOTÔ KG", "PICANHA PEÇA", "BIFE ANCHO KG"],
        "PEIXES / FRUTOS DO MAR": ["FILÉ DE CAMARÃO TAINHA UND", "CAMARAO VG FILE PORÇÃO", "FILÉ DE PEIXE UND", "FILÉ DE ATUM UND", "LAGOSTA PARA 01 PESSOA UND", "LAGOSTA PARA 02 PESSOA UND", "PEIXE MEDIO INTEIRO UND", "PEIXE PARA MOQUECA UND", "CATADO SIRI KG", "CAMARAO ROSA KG", "POLVO KG"],
        "FRIOS / LATICINIOS": ["BACON KG", "CREAM CHEESE 150G UND", "LEITE LEITÍSSIMO (L)", "MANTEIGA 500G", "MANTEIGA DE GARRAFA (L)", "PRESUNTO PARMA KG", "QUEIJO BRANCO M. FRESCAL KG", "QUEIJO COALHO KG", "QUEIJO GORGONZOLA KG", "QUEIJO GRANA PADANO 250G", "QUEIJO MUSSARELA KG", "QUEIJO PARMESÃO KG", "REQUEIJÃO CREMOSO UND"],
        "MANTIMENTOS SECOS": ["ACUCAR REFINADO UNIAO", "AÇÚCAR MASCAVO", "AMEIXA SECA KG", "AMENDOA CACAU S/CASCA KG", "AMIDO DE MILHO", "ARROZ BRANCO KG", "ARROZ NEGRO", "ARROZ VERMELHO ORIENTAL", "BISCOITO DE MAIZENA", "CAFÉ EM PÓ 500G", "CANJIQUINHA MILHO BRANCO 200G", "CASTANHA DO PARÁ", "SEMENTE DE CHIA", "CHOCOLATE AMMA BARRA 500G", "CHOCOLATE BRANCO", "COUSCOUS MARROQUINO (KG)", "FARINHA DE MANDIOCA KG", "FARINHA TAPIOCA GRANULADA", "FARINHA DE TRIGO", "FARINHA DE TRIGO INTEGRAL", "FARINHA PANKO", "FEIJAO FRADINHO SEM CASCA", "FEIJÃO PRETO", "FERMENTO BIOLÓGICO", "FERMENTO EM PÓ QUIMICO", "FLOCÃO DE MILHO", "FLOR DE SAL", "FUBÁ DE MILHO", "GERGELIM BRANCO", "GERGELIM NEGRO", "GRÃO DE BICO KG", "LEITE EM PÓ 200G", "LINHAÇA DOURADA", "MASSA TAGLIATELLE RISCOSSA", "NOZES", "PÁPRICA", "QUINOA GRÃOS", "SÊMOLA GRANO DURO 500GR", "SPAGHETTI SEM GLÚTEN", "UVA PASSA", "XAROPE DE GLUCOSE", "PASTA DE AMENDOIM", "PASTA BAUNILHA"],
        "HORTIFRUTI / TEMPEROS": ["ABACATE UND", "ABACAXI UND", "ABOBORA KG", "ABOBRINHA KG", "AGRIÃO UND", "AIPIM KG", "POLPA DE FRUTAS KG", "ALECRIM UND", "ALECRIM DO MATO", "ALFACE AMERICANA", "ALFACE CRESPA UND", "ALFACE ROXA", "ALHO KG", "ALHO PORÓ UND", "BANANA DA PRATA UND", "BANANA DA TERRA UND", "BATATA BAROA", "BATATA DOCE KG", "BATATA INGLESA KG", "BERINGELA KG", "BETERRABA KG", "BRÓCOLIS JAPONÊS UND", "CACAU VERDE UND", "CAJÚ UND", "CAPIM SANTO UND", "CEBOLA BRANCA KG", "AÇAFRÃO EM PÓ KG", "ACETO BALSÂMICO", "ALCAPARRAS KG", "ALCAPARRONES 180G", "AZEITE DENDÊ (L)", "AZEITE EXTRA VIRGEM ANDORINHA", "AZEITE TRUFADO", "AZEITONA PRETA SEM CAROÇO", "AZEITONA VERDE SEM CAROÇO", "CANELA EM PÓ", "CASTANHA DE CAJU", "CATCHUP 395G", "COGUMELO CHAMPIGNON FRESCO", "COGUMELO SHIMEJI FRESCO", "COGUMELO SHITAKE FRESCO", "CREME DE LEITE", "EXTRATO DE TOMATE", "FOLHA DE LOURO", "FOLHA DE ALGAS", "FOLHA DE ARROZ", "GELATINA SEM SABOR", "LEITE CONDENSADO", "LEITE CONDENSADO MOÇA LATA", "LEITE DE COCO", "MILHO VERDE ESPIGA", "MOLHO AJI NO SHOYU", "MOLHO TABASCO", "MOSTARDA DJON 1KG", "ÓLEO DE COCO", "ÓLEO DE GERGELIN", "ÓLEO DE GIRASSOL", "ÓLEO DE SOJA 900ML", "ORÉGANO", "PALMITO FRESCO SEM CASCA", "PIMENTA CAIENA KG", "PIMENTA CALABRESA KG", "SAL GROSSO", "SAL MOÍDO KG", "TAHINE 330G", "TOMATE PELADO 400G", "VINAGRE DE CEREAL ARROZ UND", "VINHO BRANCO COZINHA", "VINHO TINTO COZINHA", "MELACO DE CANA", "BICARBONATO DE SODIO", "HORTELÃ", "LARANJA PERA UND", "LIMÃO TAHITI KG", "LIMÃO SICILIANO KG", "MAÇÃ VERDE KG", "MAMÃO KG", "MANGA KG", "MANJERICÃO", "MARACUJÁ KG", "MAXIXE", "MELANCIA UND", "OVO BRANCO/VERMELHO UND", "OVO DE GALINHA CAIPIRA UND", "PEPINO KG", "PIMENTA ARDIDA KG", "PIMENTA DOCE VERMELHA KG", "QUIABO KG", "RABANETE KG", "REPOLHO ROXO", "RÚCULA UND", "SALSA UND", "SALSÃO UND", "TOMATE KG", "TOMATE CEREJA KG", "TOMILHO", "VAGEM", "PEPINO JAPONES", "CANELA EM PAU", "CEBOLA ROXA KG", "CEBOLINHA UND", "CENOURA KG", "COCO SECO UND", "COENTRO UND", "COUVE UND", "COUVE FLOR UND", "ERVA DOCE", "ESPINAFRE", "FEIJÃO VERDE KG", "FLORES COMESTÍVEIS", "FOLHA DE VINAGREIRA", "GENGIBRE KG"],
        "DIVERSOS": ["PAPEL ALUMÍNIO", "PAPEL TOALHA INSTIT. C/ 06 UND", "BOBINA P ALIMENTOS", "MASCARA DESCARTAVEL DOBRAVEL", "SACO DE LIXO 200L", "FIBRACO SCOTCH BRITE", "FILME PVC 400MT", "ESCOVA DE ACO", "LAVA LOUCAS CONC. P. DILUIR 500ML", "DESENGORDURANTE ALCALINO CHEF", "ESPONJA DUPLA FACE", "AVENTAL BRANCO EM PVC", "CARVAO", "PAPEL MANTEIGA", "GAS PARA MASSARICO UND"]
    },
    "BAR": {
        "WHISKY": ["BALLANTINES 8", "BUCHANAN'S", "BULLEIT (BOURBON)", "GLENFIDDICH 12", "JACK DANIELS", "JACK DANIELS GENTLEMAN", "JACK DANIELS SINGLE BARREL", "JW BLACK LABEL 12", "JW BLUE LABEL", "JW RED LABEL", "WOODFORD RESERVE (BOURBON)", "MACALLAN 12 ANOS", "JAMESON", "CHIVAS REGAL"],
        "DESTILADOS / APERITIVOS": ["HENNESSY VS", "PISCO CAPEL", "BACARDI PRATA", "ZACAPA 23", "HAVANA CLUB 7 ANOS", "HAVANA CLUB 3 AÑOS", "RIO DO ENGENHO OURO", "RIO DO ENGENHO PRATA", "SERRA DAS ALMAS OURO", "SERRA DAS ALMAS PRATA", "WEBER HAUS PRATA", "MATRIARCA JAQUEIRA", "MATRIARCA BÁLSAMO", "MATRIARCA 4 MADEIRAS", "MATRIARCA AMBURANA", "HERRADURA PLATA", "HERRADURA REPOSADO", "JOSE CUERVO SILVER", "JOSE CUERVO GOLD", "ABSOLUT", "BELVEDERE", "GREY GOOSE", "VODKA YVY", "AMAZZONI", "ARAPURU", "BOMBAY SAPPHIRE", "HENDRICKS", "TANQUERAY", "THE BOTANIST", "JUN DAITI", "GEKKEIKAN SILVER", "APEROL", "CAMPARI", "FERNET BRANCA", "JAGERMEINSTER", "LILLET BLANC", "LUCANO (AMARO)", "DOLIN BLANC", "DOLIN DRY", "DOLIN ROUGE", "PUNT E MES", "AMARULA", "BAILEYS", "BOLS CASSIS", "COINTREAU", "LICOR 43", "MOLINARI CAFÉ", "VILLA MASSA (LIMONCELLO)", "ANGOSTURA AROMATIC BITTER", "ANGOSTURA ORANGE BITTER", "JEREZ", "VINHO BRANCO FANTINI PINOT GRIGIO", "ESPUMANTE OMNIUM"],
        "CERVEJAS": ["CORONA LN", "HEINEKEN LN", "PROA ACAPULCO HOP LAGER", "PROA IRIS APA", "PROA CARRIE NATION IPA"],
        "CHÁS / CAFÉ / SOFTS": ["INDIAN CHAI - TWININGS", "EARL GREY - TWININGS", "ENGLISH BREAKFEST - TWININGS", "FRUTAS SILVESTRES - TWININGS", "CAMOMILA - TWININGS", "CHÁ VERDE - TWININGS", "ÁGUA SEM GÁS MINALBA", "ÁGUA COM GÁS MINALBA", "ÁGUA TÔNICA ANTARCTICA", "ÁGUA TÔNICA ZERO ANTARCTICA", "COCA-COLA 350ML", "COCA-COLA ZERO 350ML", "GUARANÁ ANTARTICA 350ML", "GUARANÁ ZERO ANTARTICA 350ML", "MEL DE CACAU CONGELADO 200ML", "SUCO DE TOMATE 1LT", "POTE AÇAI"],
        "CONSUMÍVEIS": ["AÇÚCAR DEMERARA", "AÇÚCAR REFINADO", "CANUDO BIODEGRADÁVEL", "CAPSULA NO2", "COCO DESIDRATADO, LASCAS", "FLOR DE SAL", "PIMENTA DO REINO", "LEITE EM PÓ", "LEITE CONDENSADO", "LEITE DE COCO", "ESPETO BAMBU DECORAÇÃO", "CLORO GEL", "CAPSULA CO2 SODASTREAM", "SHOYU", "MOLHO INGLÊS", "TABASCO", "CASTANHA DE CAJU", "PAPEL TOALHA", "POLPA DE FRUTAS (CAJU)", "POLPA DE CAJÁ NATURAL", "POLPA DE CUPUAÇU NATURAL", "MEL", "AÇÚCAR SACHÊ", "ADOÇANTE SACHÊ", "PORTA COPO (CASTANHA DO CAFÉ)", "GUARDANAPO COM LOGO B", "LIMPA INOX", "DETERGENTE MÁQUINA LAVA COPOS", "SECANTE MÁQUINA LAVA COPOS", "ACHOCOLATADO", "CAFÉ EM PÓ", "FILTRO DE CAFÉ", "BOBINA PARA ALIMENTOS (ETIQUETA)", "DETERGENTE CONCENTRADO", "BUCHA", "SACO DE LIXO 200L", "AÇÚCAR MASCAVO", "PEPITA CACAU DENGO", "GRANOLA"],
        "HORTIFRUTI": ["ABACAXI", "AZEITONA", "CAPIM SANTO", "CUMARÚ", "COCO VERDE", "PIMENTA DEDO DE MOÇA", "BANANA DA TERRA", "BETERRABA", "GRAO DE BICO", "MANJERICÃO", "GENGIBRE", "HIBISCO", "HORTELÃ", "LARANJA PERA", "LARANJA BAHIA", "LIMÃO SICILIANO", "LIMÃO ROSA", "LIMÃO TAITI", "MARACUJÁ", "MEL", "NIBS DE CACAU", "PEPINO", "PIMENTA ROSA", "FRUTAS DA ÉPOCA (SERIGUELA)", "TOMILHO", "ZIMBRO", "CRAVO DA ÍNDIA", "CAJU", "CACAU", "TANGERINA", "PITANGA", "CARDAMOMO", "MAÇÃ VERMELHA", "LOURO", "LEITE", "LEITE VEGETAL", "MANGA", "MAMÃO", "MELÃO", "BANANA PRATA", "FLORES COMESTIVEIS"]
    },
    "SALÃO": {
        "VINHOS / ADEGA": ["DOMAINE DE LA SOLITUDE CHATEAUNEUF DU PAPE 2021", "DOMAINE SÉGUINOT-BORDET CHABLIS 2022", "ALMAVIVA 2020", "BAROLO GIANNI GAGLIARDO DOCG 2019", "BRUNELLO DI MONTALCINO PODERE BRIZIO 2013", "PORTAL DA CALÇADA LOUREIRA", "MONTE DA PECEGUINA", "CALABUIG TEMPRANILLO", "BARONE PAULINE SAUTERNES", "SACRAMENTO DOLCE FAR NIENTE NATURE CHENIN BLANC", "THERA AUGURI EXTRA BRUT", "VIVENTE PÉT-NAT MEL DE CACAU & PINOT NOIR", "UVVA EXTRA BRUT", "PROSECCO BERNARDI BRUT PRA SEI SALT DOCG", "DRAPPIER MILLÉSIME EXCEPTION EXTRA BRUT", "MÖET & CHANDON BRUT IMPERIAL", "MÖET & CHANDON ROSÉ IMPERIAL", "VEUVE CLIQUOT BRUT YELLOW LABEL", "ERA DOS VENTOS PEVERELLA", "THERA SAUVIGNON BLANC", "UVVA CHARDONNAY", "UVVA SAUVIGNON BLANC", "OTRONIA 45 RUGIENTES CORTES BLANCAS", "RUTINI CHARDONNAY", "VALLISTO TORRONTÉS", "BAETTIG LOS PARIENTES CHARDONNAY ORGÂNICO", "DOMAINE CHAUVEAU COTEAUX DI GIENNOIS CALCAIRE", "FAMILLE BOUGRIER CONFIDENCES VOUVRAY", "FAMILLE HIGEL CLASSIC GEWÜRZTRAMINER", "DONNAFUGATA ANTÍLIA DOC", "POGGIOTONDO VERMENTINO IGT", "FANTINI PINOT GRIGIO IGP", "MORGADIO DA TORRE ALVARINHO", "PORTAL DA CALÇADA LOUREIRA", "THERA ROSÉ", "VIVENTE ROSÉ TRANQUILO", "ABBOTS & DELAUNAY GRENACHE ROSÉ", "CHATEAU LAFOUX", "DAI TERRA ROSSA A.MARE ROSATO PUGLIA IGP", "MONTE DA PECEGUINA", "GUASPARI VISTA DA MATA CABERNET Franc", "MANUS CLÁSSICO NEBBIOLO", "SACRAMENTO SABINA SYRAH", "UVVA CORDEL", "UVVA DIAMÃ", "RUTINI MALBEC", "SOPHENIA ESTATE WINE CABERNET SAUVIGNON", "ODJFELL CAPÍTULO BLEND ORGÂNICO", "DOMAINE DE ROCHEBIN PINOT NOIR DE BOURGOGNE", "CALABUIG TEMPRANILLO", "FANTINI MONTEPULCIANO D'ABRUZZO COLLINE TERAMANE DOCG", "GARZON SINGLE VINEYARD TANNAT"],
        "CONSUMÍVEIS / DIVERSOS": ["SORO FISIOLOGICO", "ALGODÃO", "BAND-AID", "CANETA ESFEROGRÁFICA", "CANETA PILOTO AZUL", "CANETA PILOTO PRETA", "CANELA PILOTO VERMELHO", "ESPARADRAPO", "GASE", "GUARDANAPO 40 X 40", "PAPEL RECICLADO TAMANHO A4", "PILHA AA", "PILHA AAA", "PISTOLA DE ISQUEIRO", "REPELENTE LOÇÃO", "REPELENTE OFF SPRAY", "VELAS DE ANIVERSÁRIO", "VELAS GRANDES 10X15", "VELAS MÉDIAS 5,5X15", "VELAS PEQUENAS 3X6", "ABACAXI VERDE", "AMENDOIM 500G", "AZEITE EXTRA VIRGEM EA 500ML", "AZEITONAS PRETAS", "CACHO DE BANANA VERDE", "CASTANHA DE CAJÚ", "COCO SECO", "COCO VERDE", "FLOR DE SAL", "GRAVIOLA (ESCREVER A FRUTA)", "SAL GROSSO", "SAL REFINADO"]
    }
}

def remover_acentos(texto):
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

def separar_unidade(texto_item):
    texto = texto_item.strip().upper()
    for uni in ['KG', 'UND', 'LATA', 'PORÇÃO', 'BARRA', 'LT', 'ML', 'POTE', 'G', 'L']:
        if texto.endswith(" " + uni):
            return texto[:-len(uni)].strip(), uni
        if texto.endswith("(" + uni + ")"):
            return texto[:-len(uni)-2].strip(), uni
    match = re.search(r'\s+(\d+(?:G|ML|LT|MT|UND|K|KG|L))$', texto)
    if match:
        sufixo = match.group(1)
        if not sufixo.isdigit():
            return texto[:-len(sufixo)].strip(), sufixo
    return texto, "UND"

if 'carrinho_df' not in st.session_state:
    st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])

if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

st.title("📝 Sistema de Requisição Diária")

nome_solicitante = st.text_input("Nome do Solicitante:", placeholder="Ex: João Silva")
setor_selecionado = st.selectbox("Selecione o seu Setor:", list(DADOS_SISTEMA.keys()))

lista_itens_plana = []
for subcat, itens in DADOS_SISTEMA[setor_selecionado].items():
    lista_itens_plana.extend(itens)
lista_itens_plana = sorted(list(set(lista_itens_plana)))

# ➔ CRIAÇÃO DAS OPÇÕES COM HISTÓRICO DE BUSCA EMBUTIDO
opcoes_selectbox = []
mapeamento_reverso = {}

for item in lista_itens_plana:
    item_sem = remover_acentos(item)
    if item_sem != item:
        label = f"{item} ({item_sem})" # Ex: ÁGUA TÔNICA (AGUA TONICA)
    else:
        label = item
    opcoes_selectbox.append(label)
    mapeamento_reverso[label] = item

st.write("---")

item_nao_cadastrado = st.checkbox("⚠️ O item NÃO está na lista? Marque aqui para digitar manualmente", key=f"manual_{st.session_state.reset_counter}")

if item_nao_cadastrado:
    item_bruto = st.text_input("Digite o nome completo do Item:", placeholder="Ex: NOVO PRODUTO", key=f"item_manual_{st.session_state.reset_counter}")
    unidade_medida = st.selectbox("Selecione a Unidade:", ["UND", "KG", "L", "LATA", "PORÇÃO", "G", "ML"], key=f"uni_manual_{st.session_state.reset_counter}")
    item_nome_limpo = item_bruto.upper().strip()
    subcategoria_detectada = "MANUAL / NOVO ITEM"
else:
    # ➔ APENAS UM CAMPO DE SELEÇÃO COMO VOCÊ PEDIU!
    item_bruto = st.selectbox("Busque e selecione o Item:", opcoes_selectbox, key=f"item_select_{st.session_state.reset_counter}")
    
    # Recupera o nome original blindado do banco (com acentos)
    item_original = mapeamento_reverso[item_bruto]
    item_nome_limpo, unidade_medida = separar_unidade(item_original)
    
    subcategoria_detectada = "OUTROS"
    for subcat, itens in DADOS_SISTEMA[setor_selecionado].items():
        if item_original in itens:
            subcategoria_detectada = subcat
            break

st.info(f"⚖️ Unidade de medida: **{unidade_medida}**")

quantidade = st.number_input(f"Quantidade necessária:", min_value=1, value=1, step=1, key=f"qtd_{st.session_state.reset_counter}")
observacao = st.text_input("Observação (Opcional):", placeholder="Ex: Urgente, Marca específica...", key=f"obs_{st.session_state.reset_counter}")

if st.button("➕ Adicionar Item ao Pedido", use_container_width=True):
    if nome_solicitante.strip() == "":
        st.error("Por favor, preencha o seu nome antes de adicionar itens.")
    elif item_nome_limpo == "":
        st.error("Por favor, selecione ou digite um item válido antes de adicionar.")
    else:
        texto_obs = observacao.strip() if observacao.strip() != "" else "-"
        
        novo_registro = pd.DataFrame([{
            "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Solicitante": nome_solicitante,
            "Setor": setor_selecionado,
            "Categoria": subcategoria_detectada,
            "Item": item_nome_limpo,
            "Quantidade": int(quantidade),
            "Unidade": unidade_medida,
            "Observacao": texto_obs
        }])
        
        st.session_state.carrinho_df = pd.concat([st.session_state.carrinho_df, novo_registro], ignore_index=True)
        st.success(f"Adicionado: {quantidade} {unidade_medida} de {item_nome_limpo}")
        
        st.session_state.reset_counter += 1
        time.sleep(0.5)
        st.rerun()

if not st.session_state.carrinho_df.empty:
    st.write("### 🛒 Itens no Pedido Atual")
    st.caption("💡 Dica: Dê dois cliques na **Quantidade** ou **Observação** para alterar. Selecione a linha e clique na lixeira no canto da tabela para remover.")
    
    st.session_state.carrinho_df = st.data_editor(
        st.session_state.carrinho_df,
        column_config={
            "Data_Hora": None,
            "Solicitante": None,
            "Setor": st.column_config.TextColumn("Setor", disabled=True),
            "Categoria": st.column_config.TextColumn("Categoria", disabled=True),
            "Item": st.column_config.TextColumn("Item", disabled=True),
            "Unidade": st.column_config.TextColumn("Unidade", disabled=True),
            "Quantidade": st.column_config.NumberColumn("Quantidade", min_value=1, step=1, required=True),
            "Observacao": st.column_config.TextColumn("Observação (Clique para editar)")
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if st.button("🗑️ Limpar Todo o Pedido", type="secondary"):
        st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
        st.rerun()
        
    st.write("---")
    
    if st.button("🚀 ENVIAR REQUISIÇÃO PARA A CENTRAL", type="primary", use_container_width=True):
        if "COLE_AQUI" in URL_WEB_APP:
            st.error("Erro: Falta colocar a sua URL do Google Script na linha 13!")
        else:
            with st.spinner("Enviando dados diretamente para o Google Sheets..."):
                try:
                    lista_pedidos = st.session_state.carrinho_df.to_dict(orient='records')
                    
                    req = urllib.request.Request(URL_WEB_APP, method="POST")
                    req.add_header('Content-Type', 'application/json')
                    payload = json.dumps(lista_pedidos).encode('utf-8')
                    
                    with urllib.request.urlopen(req, data=payload) as response:
                        resultado = response.read().decode('utf-8')
                    
                    if "Error" in resultado:
                        st.error(f"Erro no Google Sheets: {resultado}")
                    else:
                        st.balloons()
                        st.success(f"🎉 Pedido enviado com sucesso para a central!")
                        st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro na transmissão: {e}")
