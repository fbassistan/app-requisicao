
import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time
import re
import unicodedata
import os

st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# ➔ SUA URL DO APP DA WEB DO GOOGLE SCRIPTS (Terminada em /exec)
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# Banco de Dados Final - 100% Padronizado com Unidades Técnicas de Mercado
DADOS_SISTEMA = {
    "RESTAURANTE / COZINHA": {
        "CARNES / AVES": ["COSTELA BOI KG", "FILÉ MIGNON PEÇA KG", "HAMBURGER BOVINO 160 G", "CUPIM KG", "COXA SOBRECOXA KG", "FILE FRANGO KG", "RABADA KG", "MOCOTÔ KG", "PICANHA PEÇA", "BIFE ANCHO KG"],
        "PEIXES / FRUTOS DO MAR": ["FILÉ DE CAMARÃO TAINHA UND", "CAMARAO VG FILE PORÇÃO", "FILÉ DE PEIXE UND", "FILÉ DE ATUM UND", "LAGOSTA PARA 01 PESSOA UND", "LAGOSTA PARA 02 PESSOA UND", "PEIXE MEDIO INTEIRO UND", "PEIXE PARA MOQUECA UND", "CATADO SIRI KG", "CAMARAO ROSA KG", "POLVO KG"],
        "FRIOS / LATICINIOS": ["BACON KG", "CREAM CHEESE 150G UND", "LEITE LEITÍSSIMO L", "MANTEIGA 500G", "MANTEIGA DE GARRAFA L", "PRESUNTO PARMA KG", "QUEIJO BRANCO M. FRESCAL KG", "QUEIJO COALHO KG", "QUEIJO GORGONZOLA KG", "QUEIJO GRANA PADANO 250G", "QUEIJO MUSSARELA KG", "QUEIJO PARMESÃO KG", "REQUEIJÃO CREMOSO UND"],
        "MANTIMENTOS SECOS": ["ACUCAR REFINADO UNIAO PCT", "AÇÚCAR MASCAVO KG", "AMEIXA SECA KG", "AMENDOA CACAU S/CASCA KG", "AMIDO DE MILHO KG", "ARROZ BRANCO KG", "ARROZ NEGRO KG", "ARROZ VERMELHO ORIENTAL KG", "BISCOITO DE MAIZENA PCT", "CAFÉ EM PÓ 500G", "CANJIQUINHA MILHO BRANCO 200G", "CASTANHA DO PARÁ KG", "SEMENTE DE CHIA KG", "CHOCOLATE AMMA BARRA 500G", "CHOCOLATE BRANCO KG", "COUSCOUS MARROQUINO KG", "FARINHA DE MANDIOCA KG", "FARINHA TAPIOCA GRANULADA KG", "FARINHA DE TRIGO KG", "FARINHA DE TRIGO INTEGRAL KG", "FARINHA PANKO PCT", "FEIJAO FRADINHO SEM CASCA KG", "FEIJÃO PRETO KG", "FERMENTO BIOLÓGICO PCT", "FERMENTO EM PÓ QUIMICO UND", "FLOCÃO DE MILHO PCT", "FLOR DE SAL PCT", "FUBÁ DE MILHO KG", "GERGELIM BRANCO KG", "GERGELIM NEGRO KG", "GRÃO DE BICO KG", "LEITE EM PÓ 200G", "LINHAÇA DOURADA KG", "MASSA TAGLIATELLE RISCOSSA PCT", "NOZES KG", "PÁPRICA KG", "QUINOA GRÃOS KG", "SÊMOLA GRANO DURO 500GR", "SPAGHETTI SEM GLÚTEN PCT", "UVA PASSA KG", "XAROPE DE GLUCOSE KG", "PASTA DE AMENDOIM POTE", "PASTA BAUNILHA KG"],
        "HORTIFRUTI / TEMPEROS": ["ABACATE UND", "ABACAXI UND", "ABOBORA KG", "ABOBRINHA KG", "AGRIÃO MAÇO", "AIPIM KG", "POLPA DE FRUTAS KG", "ALECRIM MAÇO", "ALECRIM DO MATO MAÇO", "ALFACE AMERICANA UND", "ALFACE CRESPA UND", "ALFACE ROXA UND", "ALHO KG", "ALHO PORÓ UND", "BANANA DA PRATA UND", "BANANA DA TERRA UND", "BATATA BAROA KG", "BATATA DOCE KG", "BATATA INGLESA KG", "BERINGELA KG", "BETERRABA KG", "BRÓCOLIS JAPONÊS UND", "CACAU VERDE UND", "CAJÚ UND", "CAPIM SAN MAÇO", "CEBOLA BRANCA KG", "AÇAFRÃO EM PÓ KG", "ACETO BALSÂMICO GFA", "ALCAPARRAS KG", "ALCAPARRONES 180G", "AZEITE DENDÊ L", "AZEITE EXTRA VIRGEM ANDORINHA GFA", "AZEITE TRUFADO GFA", "AZEITONA PRETA SEM CAROÇO KG", "AZEITONA VERDE SEM CAROÇO KG", "CANELA EM PÓ PCT", "CASTANHA DE CAJU KG", "CATCHUP 395G UND", "COGUMELO CHAMPIGNON FRESCO KG", "COGUMELO SHIMEJI FRESCO KG", "COGUMELO SHITAKE FRESCO KG", "CREME DE LEITE LATA", "EXTRATO DE TOMATE LATA", "FOLHA DE LOURO PCT", "FOLHA DE ALGAS PCT", "FOLHA DE ARROZ PCT", "GELATINA SEM SABOR PCT", "LEITE CONDENSADO LATA", "LEITE CONDENSADO MOÇA LATA", "LEITE DE COCO GFA", "MILHO VERDE ESPIGA UND", "MOLHO AJI NO SHOYU GFA", "MOLHO TABASCO GFA", "MOSTARDA DJON 1KG GFA", "ÓLEO DE COCO POTE", "ÓLEO DE GERGELIN GFA", "ÓLEO DE GIRASSOL GFA", "ÓLEO DE SOJA 900ML", "ORÉGANO PCT", "PALMITO FRESCO SEM CASCA KG", "PIMENTA CAIENA KG", "PIMENTA CALABRESA KG", "SAL GROSSO KG", "SAL MOÍDO KG", "TAHINE 330G POTE", "TOMATE PELADO 400G LATA", "VINAGRE DE CEREAL ARROZ GFA", "VINHO BRANCO COZINHA GFA", "VINHO TINTO COZINHA GFA", "MELACO DE CANA GFA", "BICARBONATO DE SODIO PCT", "HORTELÃ MAÇO", "LARANJA PERA UND", "LIMÃO TAHITI KG", "LIMÃO SICILIANO KG", "MAÇÃ VERDE KG", "MAMÃO KG", "MANGA KG", "MANJERICÃO MAÇO", "MARACUJÁ KG", "MAXIXE KG", "MELANCIA UND", "OVO BRANCO/VERMELHO UND", "OVO DE GALINHA CAIPIRA UND", "PEPINO KG", "PIMENTA ARDIDA KG", "PIMENTA DOCE VERMELHA KG", "QUIABO KG", "RABANETE KG", "REPOLHO ROXO UND", "RÚCULA MAÇO", "SALSA MAÇO", "SALSÃO MAÇO", "TOMATE KG", "TOMATE CEREJA KG", "TOMILHO MAÇO", "VAGEM KG", "PEPINO JAPONES KG", "CANELA EM PAU PCT", "CEBOLA ROXA KG", "CEBOLINHA MAÇO", "CENOURA KG", "COCO SECO UND", "COENTRO MAÇO", "COUVE MAÇO", "COUVE FLOR UND", "ERVA DOCE MAÇO", "ESPINAFRE MAÇO", "FEIJÃO VERDE KG", "FLORES COMESTÍVEIS BDJ", "FOLHA DE VINAGREIRA MAÇO", "GENGIBRE KG"],
        "DIVERSOS": ["PAPEL ALUMÍNIO ROLO", "PAPEL TOALHA INSTIT. C/ 06 UND", "BOBINA P ALIMENTOS ROLO", "MASCARA DESCARTAVEL DOBRAVEL UND", "SACO DE LIXO 200L PCT", "FIBRACO SCOTCH BRITE UND", "FILME PVC 400MT ROLO", "ESCOVA DE ACO UND", "LAVA LOUCAS CONC. P. DILUIR 500ML", "DESENGORDURANTE ALCALINO CHEF L", "ESPONJA DUPLA FACE UND", "AVENTAL BRANCO EM PVC UND", "CARVAO SAC", "PAPEL MANTEIGA ROLO", "GAS PARA MASSARICO UND"]
    },
    "BAR": {
        "WHISKY": ["BALLANTINES 8 GFA", "BUCHANAN'S GFA", "BULLEIT (BOURBON) GFA", "GLENFIDDICH 12 GFA", "JACK DANIELS GFA", "JACK DANIELS GENTLEMAN GFA", "JACK DANIELS SINGLE BARREL GFA", "JW BLACK LABEL 12 GFA", "JW BLUE LABEL GFA", "JW RED LABEL GFA", "WOODFORD RESERVE (BOURBON) GFA", "MACALLAN 12 ANOS GFA", "JAMESON GFA", "CHIVAS REGAL GFA"],
        "DESTILADOS / APERITIVOS": ["HENNESSY VS GFA", "PISCO CAPEL GFA", "BACARDI PRATA GFA", "ZACAPA 23 GFA", "HAVANA CLUB 7 ANOS GFA", "HAVANA CLUB 3 AÑOS GFA", "RIO DO ENGENHO OURO GFA", "RIO DO ENGENHO PRATA GFA", "SERRA DAS ALMAS OURO GFA", "SERRA DAS ALMAS PRATA GFA", "WEBER HAUS PRATA GFA", "MATRIARCA JAQUEIRA GFA", "MATRIARCA BÁLSAMO GFA", "MATRIARCA 4 MADEIRAS GFA", "MATRIARCA AMBURANA GFA", "HERRADURA PLATA GFA", "HERRADURA REPOSADO GFA", "JOSE CUERVO SILVER GFA", "JOSE CUERVO GOLD GFA", "ABSOLUT GFA", "BELVEDERE GFA", "GREY GOOSE GFA", "VODKA YVY GFA", "AMAZZONI GFA", "ARAPURU GFA", "BOMBAY SAPPHIRE GFA", "HENDRICKS GFA", "TANQUERAY GFA", "THE BOTANIST GFA", "JUN DAITI GFA", "GEKKEIKAN SILVER GFA", "APEROL GFA", "CAMPARI GFA", "FERNET BRANCA GFA", "JAGERMEINSTER GFA", "LILLET BLANC GFA", "LUCANO (AMARO) GFA", "DOLIN BLANC GFA", "DOLIN DRY GFA", "DOLIN ROUGE GFA", "PUNT E MES GFA", "AMARULA GFA", "BAILEYS GFA", "BOLS CASSIS GFA", "COINTREAU GFA", "LICOR 43 GFA", "MOLINARI CAFÉ GFA", "VILLA MASSA (LIMONCELLO) GFA", "ANGOSTURA AROMATIC BITTER GFA", "ANGOSTURA ORANGE BITTER GFA", "JEREZ GFA", "VINHO BRANCO FANTINI PINOT GRIGIO GFA", "ESPUMANTE OMNIUM GFA"],
        "CERVEJAS": ["CORONA LN UND", "HEINEKEN LN UND", "PROA ACAPULCO HOP LAGER UND", "PROA IRIS APA UND", "PROA CARRIE NATION IPA UND"],
        "CHÁS / CAFÉ / SOFTS": ["INDIAN CHAI - TWININGS CX", "EARL GREY - TWININGS CX", "ENGLISH BREAKFEST - TWININGS CX", "FRUTAS SILVESTRES - TWININGS CX", "CAMOMILA - TWININGS CX", "CHÁ VERDE - TWININGS CX", "ÁGUA SEM GÁS MINALBA UND", "ÁGUA COM GÁS MINALBA UND", "ÁGUA TÔNICA ANTARCTICA UND", "ÁGUA TÔNICA ZERO ANTARCTICA UND", "COCA-COLA 350ML LATA", "COCA-COLA ZERO 350ML LATA", "GUARANÁ ANTARTICA 350ML LATA", "GUARANÁ ZERO ANTARTICA 350ML LATA", "MEL DE CACAU CONGELADO 200ML", "SUCO DE TOMATE 1LT", "POTE AÇAI UND"],
        "CONSUMÍVEIS": ["AÇÚCAR DEMERARA KG", "AÇÚCAR REFINADO KG", "CANUDO BIODEGRADÁVEL PCT", "CAPSULA NO2 CX", "COCO DESIDRATADO, LASCAS PCT", "FLOR DE SAL KG", "PIMENTA DO REINO PCT", "LEITE EM PÓ KG", "LEITE CONDENSADO LATA", "LEITE DE COCO GFA", "ESPETO BAMBU DECORAÇÃO PCT", "CLORO GEL GFA", "CAPSULA CO2 SODASTREAM UND", "SHOYU GFA", "MOLHO INGLÊS GFA", "TABASCO GFA", "CASTANHA DE CAJU KG", "PAPEL TOALHA PCT", "POLPA DE FRUTAS (CAJU) KG", "POLPA DE CAJÁ NATURAL KG", "POLPA DE CUPUAÇU NATURAL KG", "MEL GFA", "AÇÚCAR SACHÊ CX", "ADOÇANTE SACHÊ CX", "PORTA COPO (CASTANHA DO CAFÉ) PCT", "GUARDANAPO COM LOGO B PCT", "LIMPA INOX GFA", "DETERGENTE MÁQUINA LAVA COPOS L", "SECANTE MÁQUINA LAVA COPOS L", "ACHOCOLATADO KG", "CAFÉ EM PÓ PCT", "FILTRO DE CAFÉ PCT", "BOBINA PARA ALIMENTOS (ETIQUETA) ROLO", "DETERGENTE CONCENTRADO GFA", "BUCHA UND", "SACO DE LIXO 200L PCT", "AÇÚCAR MASCAVO KG", "PEPITA CACAU DENGO KG", "GRANOLA KG"],
        "HORTIFRUTI": ["ABACAXI UND", "AZEITONA KG", "CAPIM SANTO MAÇO", "CUMARÚ PCT", "COCO VERDE UND", "PIMENTA DEDO DE MOÇA KG", "BANANA DA TERRA KG", "BETERRABA KG", "GRAO DE BICO KG", "MANJERICÃO MAÇO", "GENGIBRE KG", "HIBISCO PCT", "HORTELÃ MAÇO", "LARANJA PERA UND", "LARANJA BAHIA UND", "LIMÃO SICILIANO KG", "LIMÃO ROSA KG", "LIMÃO TAITI KG", "MARACUJÁ KG", "MEL KG", "NIBS DE CACAU KG", "PEPINO KG", "PIMENTA ROSA PCT", "FRUTAS DA ÉPOCA (SERIGUELA) KG", "TOMILHO MAÇO", "ZIMBRO PCT", "CRAVO DA ÍNDIA PCT", "CAJU KG", "CACAU UND", "TANGERINA KG", "PITANGA KG", "CARDAMOMO PCT", "MAÇÃ VERMELHA UND", "LOURO PCT", "LEITE L", "LEITE VEGETAL L", "MANGA KG", "MAMÃO UND", "MELÃO UND", "BANANA PRATA KG", "FLORES COMESTIVEIS BDJ"]
    },
    "SALÃO": {
        "VINHOS / ADEGA": ["DOMAINE DE LA SOLITUDE CHATEAUNEUF DU PAPE 2021 GFA", "DOMAINE SÉGUINOT-BORDET CHABLIS 2022 GFA", "ALMAVIVA 2020 GFA", "BAROLO GIANNI GAGLIARDO DOCG 2019 GFA", "BRUNELLO DI MONTALCINO PODERE BRIZIO 2013 GFA", "PORTAL DA CALÇADA LOUREIRA GFA", "MONTE DA PECEGUINA GFA", "CALABUIG TEMPRANILLO GFA", "BARONE PAULINE SAUTERNES GFA", "SACRAMENTO DOLCE FAR NIENTE NATURE CHENIN BLANC GFA", "THERA AUGURI EXTRA BRUT GFA", "VIVENTE PÉT-NAT MEL DE CACAU & PINOT NOIR GFA", "UVVA EXTRA BRUT GFA", "PROSECCO BERNARDI BRUT PRA SEI SALT DOCG GFA", "DRAPPIER MILLÉSIME EXCEPTION EXTRA BRUT GFA", "MÖET & CHANDON BRUT IMPERIAL GFA", "MÖET & CHANDON ROSÉ IMPERIAL GFA", "VEUVE CLIQUOT BRUT YELLOW LABEL GFA", "ERA DOS VENTOS PEVERELLA GFA", "THERA SAUVIGNON BLANC GFA", "UVVA CHARDONNAY GFA", "UVVA SAUVIGNON BLANC GFA", "OTRONIA 45 RUGIENTES CORTES BLANCAS GFA", "RUTINI CHARDONNAY GFA", "VALLISTO TORRONTÉS GFA", "BAETTIG LOS PARIENTES CHARDONNAY ORGÂNICO GFA", "DOMAINE CHAUVEAU COTEAUX DI GIENNOIS CALCAIRE GFA", "FAMILLE BOUGRIER CONFIDENCES VOUVRAY GFA", "FAMILLE HIGEL CLASSIC GEWÜRZTRAMINER GFA", "DONNAFUGATA ANTÍLIA DOC GFA", "POGGIOTONDO VERMENTINO IGT GFA", "FANTINI PINOT GRIGIO IGP GFA", "MORGADIO DA TORRE ALVARINHO GFA", "PORTAL DA CALÇADA LOUREIRA GFA", "THERA ROSÉ GFA", "VIVENTE ROSÉ TRANQUILO GFA", "ABBOTS & DELAUNAY GRENACHE ROSÉ GFA", "CHATEAU LAFOUX GFA", "DAI TERRA ROSSA A.MARE ROSATO PUGLIA IGP GFA", "MONTE DA PECEGUINA GFA", "GUASPARI VISTA DA MATA CABERNET Franc GFA", "MANUS CLÁSSICO NEBBIOLO GFA", "SACRAMENTO SABINA SYRAH GFA", "UVVA CORDEL GFA", "UVVA DIAMÃ GFA", "RUTINI MALBEC GFA", "SOPHENIA ESTATE WINE CABERNET SAUVIGNON GFA", "ODJFELL CAPÍTULO BLEND ORGÂNICO GFA", "DOMAINE DE ROCHEBIN PINOT NOIR DE BOURGOGNE GFA", "CALABUIG TEMPRANILLO GFA", "FANTINI MONTEPULCIANO D'ABRUZZO COLLINE TERAMANE DOCG GFA", "GARZON SINGLE VINEYARD TANNAT GFA"],
        "CONSUMÍVEIS / DIVERSOS": ["SORO FISIOLOGICO GFA", "ALGODÃO PCT", "BAND-AID CX", "CANETA ESFEROGRÁFICA UND", "CANETA PILOTO AZUL UND", "CANETA PILOTO PRETA UND", "CANELA PILOTO VERMELHO UND", "ESPARADRAPO ROLO", "GASE PCT", "GUARDANAPO 40 X 40 PCT", "PAPEL RECICLADO TAMANHO A4 PCT", "PILHA AA PCT", "PILHA AAA PCT", "PISTOLA DE ISQUEIRO UND", "REPELENTE LOÇÃO UND", "REPELENTE OFF SPRAY UND", "VELAS DE ANIVERSÁRIO CX", "VELAS GRANDES 10X15 UND", "VELAS MÉDIAS 5,5X15 UND", "VELAS PEQUENAS 3X6 UND", "ABACAXI VERDE UND", "AMENDOIM 500G PCT", "AZEITE EXTRA VIRGEM EA 500ML GFA", "AZEITONAS PRETAS KG", "CACHO DE BANANA VERDE UND", "CASTANHA DE CAJÚ KG", "COCO SECO UND", "COCO VERDE UND", "FLOR DE SAL KG", "GRAVIOLA (ESCREVER A FRUTA) KG", "SAL GROSSO KG", "SAL REFINADO KG"]
    }
}

if 'usuario_anterior' not in st.session_state:
    st.session_state.usuario_anterior = ""

def remover_acentos(texto):
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

# ➔ FUNÇÃO EXPANDIDA COM TODAS AS SIGLAS TÉCNICAS DA HOTELARIA E RESTAURAÇÃO
def separar_unidade(texto_item):
    texto = texto_item.strip().upper()
    unidades_suportadas = ['KG', 'UND', 'LATA', 'PORÇÃO', 'BARRA', 'LT', 'ML', 'POTE', 'G', 'L', 'GFA', 'PCT', 'MAÇO', 'ROLO', 'CX', 'SAC', 'RESMA', 'BDJ', 'PEÇA']
    for uni in unidades_suportadas:
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

arquivo_rascunho = None
if nome_solicitante.strip():
    nome_slug = re.sub(r'[^a-zA-Z0-9]', '_', nome_solicitante.strip().lower())
    arquivo_rascunho = f"rascunho_{nome_slug}.json"
    
    if st.session_state.usuario_anterior != nome_solicitante.strip():
        if os.path.exists(arquivo_rascunho):
            try:
                with open(arquivo_rascunho, "r", encoding="utf-8") as f:
                    dados_salvos = json.load(f)
                st.session_state.carrinho_df = pd.DataFrame(dados_salvos)
                st.toast(f"🔄 Rascunho de {nome_solicitante} recuperado com sucesso!", icon="💾")
            except:
                pass
        st.session_state.usuario_anterior = nome_solicitante.strip()

lista_itens_plana = []
for subcat, itens in DADOS_SISTEMA[setor_selecionado].items():
    lista_itens_plana.extend(itens)
lista_itens_plana = sorted(list(set(lista_itens_plana)))

opcoes_selectbox = []
mapeamento_reverso = {}
for item in lista_itens_plana:
    item_sem = remover_acentos(item)
    label = f"{item} ({item_sem})" if item_sem != item else item
    opcoes_selectbox.append(label)
    mapeamento_reverso[label] = item

st.write("---")
item_nao_cadastrado = st.checkbox("⚠️ O item NÃO está na lista? Marque aqui para digitar manualmente", key=f"manual_{st.session_state.reset_counter}")

if item_nao_cadastrado:
    item_bruto = st.text_input("Digite o nome completo do Item:", placeholder="Ex: NOVO PRODUTO", key=f"item_manual_{st.session_state.reset_counter}")
    unidade_medida = st.selectbox("Selecione a Unidade:", ["UND", "KG", "L", "LATA", "PORÇÃO", "G", "ML", "GFA", "PCT", "MAÇO", "CX"], key=f"uni_manual_{st.session_state.reset_counter}")
    item_nome_limpo = item_bruto.upper().strip()
    subcategoria_detectada = "MANUAL / NOVO ITEM"
else:
    item_bruto = st.selectbox("Busque e selecione o Item:", opcoes_selectbox, key=f"item_select_{st.session_state.reset_counter}")
    item_original = mapeamento_reverso[item_bruto]
    item_nome_limpo, unidade_medida = separar_unidade(item_original)
    
    subcategoria_detectada = "OUTROS"
    for subcat, itens in DADOS_SISTEMA[setor_selecionADO].items():
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
            "Data_Hora": None, "Solicitante": None, "Setor": None, "Categoria": None,
            "Item": st.column_config.TextColumn("Item", disabled=True),
            "Unidade": st.column_config.TextColumn("Unidade", disabled=True),
            "Quantidade": st.column_config.NumberColumn("Quantidade", min_value=1, step=1, required=True),
            "Observacao": st.column_config.TextColumn("Observação (Clique para editar)")
        },
        use_container_width=True, num_rows="dynamic"
    )
    
    if arquivo_rascunho:
        if not st.session_state.carrinho_df.empty:
            with open(arquivo_rascunho, "w", encoding="utf-8") as f:
                json.dump(st.session_state.carrinho_df.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
        else:
            if os.path.exists(arquivo_rascunho): os.remove(arquivo_rascunho)

    if st.button("🗑️ Limpar Todo o Pedido", type="secondary"):
        st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
        if arquivo_rascunho and os.path.exists(arquivo_rascunho): os.remove(arquivo_rascunho)
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
                        if arquivo_rascunho and os.path.exists(arquivo_rascunho): os.remove(arquivo_rascunho)
                        st.session_state.carrinho_df = pd.DataFrame(columns=["Data_Hora", "Solicitante", "Setor", "Categoria", "Item", "Quantidade", "Unidade", "Observacao"])
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro na transmissão: {e}")

```
