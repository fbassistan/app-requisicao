import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.request
import json
import time

# Configuração da página
st.set_page_config(page_title="Requisição Diária", page_icon="📝", layout="centered")

# ➔ COLOQUE AQUI A SUA URL DO APP DA WEB DO GOOGLE SCRIPTS
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbzcNped3ftP-9FkLcWC-u65kl0RlX-rW2Z_8AHLGKgrw2ETjkoKJI2CHqisiSQnoUUb/exec"

# Dicionário com os itens organizados por setor
DADOS_ITENS = {
    "RESTAURANTE ATUAL": [
        "763 - COSTELA BOI KG", "247 - FILÉ MIGNON PEÇA KG", "836 - HAMBURGER BOVINO 160 G", "CUPIM KG", "COXA SOBRECOXA KG", "FILE FRANGO KG", "RABADA KG", "MOCOTÔ KG", "248 - PICANHA PEÇA",
        "1945 - FILÉ DE CAMARÃO TAINHA UND", "252 - CAMARAO VG FILE PORÇÃO", "253 - FILÉ DE PEIXE UND", "1021 - FILÉ DE ATUM UND", "249 - LAGOSTA PARA 01 PESSOA UND", "254 - LAGOSTA PARA 02 PESSOA UND", "894 - PEIXE MEDIO INTEIRO UND", "2056 - PEIXE PARA MOQUECA UND", "256 - CATADO SIRI KG", "2094 - CAMARAO ROSA KG", "1498 - POLVO KG",
        "153 - BACON KG", "2243 - CREAM CHEESE 150G UND", "266 - LEITE LEITÍSSIMO (L)", "274 - MANTEIGA 500G", "2000 - MANTEIGA DE GARRAFA (L)", "155 - PRESUNTO PARMA KG", "276 - QUEIJO BRANCO M. FRESCAL KG", "278 - QUEIJO COALHO KG", "808 - QUEIJO GORGONZOLA KG", "767 - QUEIJO GRANA PADANO 250G", "279 - QUEIJO MUSSARELA KG", "280 - QUEIJO PARMESÃO KG", "281 - REQUEIJÃO CREMOSO UND",
        "327 - ACUCAR REFINADO UNIAO", "328 - AÇÚCAR MASCAVO", "330 - AMEIXA SECA KG", "1954 - AMENDOA CACAU S/CASCA KG", "331 - AMIDO DE MILHO", "332 - ARROZ BRANCO KG", "334 - ARROZ NEGRO", "1213 - ARROZ VERMELHO ORIENTAL", "335 - BISCOITO DE MAIZENA", "337 - CAFÉ EM PÓ 500G", "338 - CANJIQUINHA MILHO BRANCO 200G", "340 - CASTANHA DO PARÁ", "400 - SEMENTE DE CHIA", "246 - CHOCOLATE AMMA BARRA 500G", "1502 - CHOCOLATE BRANCO", "242 - COUSCOUS MARROQUINO (Kg)", "404 - FARINHA DE MANDIOCA KG", "407 - FARINHA TAPIOCA GRANULADA", "408 - FARINHA DE TRIGO", "409 - FARINHA DE TRIGO INTEGRAL", "591 - FARINHA PANKO", "1172 - FEIJAO FRADINHO SEM CASCA", "564 - FEIJÃO PRETO", "411 - FERMENTO BIOLÓGICO", "412 - FERMENTO EM PÓ QUIMICO", "557 - FLOCÃO DE MILHO", "413 - FLOR DE SAL", "414 - FUBÁ DE MILHO", "415 - GERGELIM BRANCO", "416 - GERGELIM NEGRO", "695 - GRÃO DE BICO KG", "418 - LEITE EM PÓ 200G", "419 - LINHAÇA DOURADA", "420 - MASSA TAGLIATELLE RISCOSSA", "421 - NOZES", "70 - PÁPRICA", "422 - QUINOA GRÃOS", "744 - SÊMOLA GRANO DURO 500GR", "597 - SPAGHETTI SEM GLÚTEN", "423 - UVA PASSA", "1556 - XAROPE DE GLUCOSE", "984 - PASTA DE AMENDOIM", "428 - PASTA BAUNILHA",
        "556 - AÇAFRÃO EM PÓ KG", "271 - ACETO BALSÂMICO", "578 - ALCAPARRAS KG", "733 - ALCAPARRONES 180G", "868 - AZEITE DENDÊ (L)", "566 - AZEITE EXTRA VIRGEM ANDORINHA", "1640 - AZEITE TRUFADO", "693 - AZEITONA PRETA SEM CAROÇO", "687 - AZEITONA VERDE SEM CAROÇO", "293 - CANELA EM PÓ", "339 - CASTANHA DE CAJU", "691 - CATCHUP 395G", "1221 - COGUMELO CHAMPIGNON FRESCO", "1220 - COGUMELO SHIMEJI FRESCO", "951 - COGUMELO SHITAKE FRESCO", "296 - CREME DE LEITE", "298 - EXTRATO DE TOMATE", "299 - FOLHA DE LOURO", "1423 - FOLHA DE ALGAS", "1419 - FOLHA DE ARROZ", "300 - GELATINA SEM SABOR", "304 - LEITE CONDENSADO", "1584 - LEITE CONDENSADO MOÇA LATA", "305 - LEITE DE COCO", "309 - MILHO VERDE ESPIGA", "160 - MOLHO AJI NO SHOYU", "312 - MOLHO TABASCO", "313 - MOSTARDA DJON 1KG", "316 - ÓLEO DE COCO", "317 - ÓLEO DE GERGELIN", "318 - ÓLEO DE GIRASSOL", "319 - ÓLEO DE SOJA 900ML", "320 - ORÉGANO", "321 - PALMITO FRESCO SEM CASCA", "817 - PIMENTA CAIENA KG", "323 - PIMENTA CALABRESA KG", "324 - SAL GROSSO", "325 - SAL MOÍDO KG", "555 - TAHINE 330G", "326 - TOMATE PELADO 400G", "1591 - VINAGRE DE CEREAL ARROZ UND", "525 - VINHO BRANCO COZINHA", "575 - VINHO TINTO COZINHA", "430 - MELACO DE CANA", "854 - BICARBONATO DE SODIO",
        "554 - PAPEL ALUMÍNIO", "453 - PAPEL TOALHA INSTIT. C/ 06 UND", "532 - BOBINA P ALIMENTOS", "1283 - MASCARA DESCARTAVEL DOBRAVEL", "570 - SACO DE LIXO 200L", "967 - FIBRACO SCOTCH BRITE", "497 - FILME PVC 400MT", "988 - ESCOVA DE ACO", "1887 - LAVA LOUCAS CONC. P. DILUIR 500ML", "439 - DESENGORDURANTE ALCALINO CHEF", "443 - ESPONJA DUPLA FACE", "781 - AVENTAL BRANCO EM PVC", "536 - CARVAO", "220 - PAPEL MANTEIGA",
        "165 - ABACATE UND", "166 - ABACAXI UND", "167 - ABOBORA KG", "168 - ABOBRINHA KG", "169 - AGRIÃO UND", "170 - AIPIM KG", "2268 - POLPA DE FRUTAS KG", "171 - ALECRIM UND", "2051 - ALECRIM DO MATO", "976 - ALFACE AMERICANA", "172 - ALFACE CRESPA UND", "975 - ALFACE ROXA", "173 - ALHO KG", "174 - ALHO PORÓ UND", "175 - BANANA DA PRATA UND", "176 - BANANA DA TERRA UND", "898 - BATATA BAROA", "177 - BATATA DOCE KG", "178 - BATATA INGLESA KG", "180 - BERINGELA KG", "181 - BETERRABA KG", "950 - BRÓCOLIS JAPONÊS UND", "1942 - CACAU VERDE UND", "183 - CAJÚ UND", "184 - CAPIM SANTO UND", "186 - CEBOLA BRANCA KG", "201 - HORTELÃ", "204 - LARANJA PERA UND", "205 - LIMÃO TAHITI KG", "206 - LIMÃO SICILIANO KG", "208 - MAÇÃ VERDE KG", "209 - MAMÃO KG", "210 - MANGA KG", "212 - MANJERICÃO", "213 - MARACUJA KG", "214 - MAXIXE", "215 - MELANCIA UND", "219 - OVO BRANCO/VERMELHO UND", "15508 - OVO DE GALINHA CAIPIRA UND", "221 - PEPINO KG", "1448 - PIMENTA ARDIDA KG", "814 - PIMENTA DOCE VERMELHA KG", "224 - QUIABO KG", "1017 - RABANETE KG", "227 - REPOLHO ROXO", "228 - RÚCULA UND", "229 - SALSA UND", "986 - SALSÃO UND", "156 - TOMATE KG", "235 - TOMATE CEREJA KG", "236 - TOMILHO", "237 - VAGEM", "813 - PEPINO JAPONES", "937 - CANELA EM PAU", "187 - CEBOLA ROXA KG", "188 - CEBOLINHA UND", "189 - CENOURA KG", "190 - COCO SECO UND", "193 - COENTRO UND", "194 - COUVE UND", "2110 - COUVE FLOR UND", "195 - ERVA DOCE", "196 - ESPINAFRE", "197 - FEIJÃO VERDE KG", "1888 - FLORES COMESTÍVEIS", "18 - FOLHA DE VINAGREIRA", "199 - GENGIBRE KG"
    ],
    "BAR": [
        "64 - AGUA COM GAS SAN PELLEGRINO", "63 - AGUA PANNA 505ML", "47 - COCA COLA LATA 350ML", "48 - COCA COLA ZERO LATA 350ML", "49 - GUARANA ANTARTICA LATA 350ML", "50 - GUARANA ANTARTICA ZERO 350ML", "2374 - AGUA TONICA ZERO 350ML", "46 - ÁGUA TÔNICA 350ML", "125 - CERVEJA CORONA LONG 330ML", "124 - CERVEJA HEINEKEN LONG 330ML", "5435 - PROA IRIS APA", "2459 - PROA ACAPULCO HOPLAGER", "2504 - PROA IPA CARRIE NATION",
        "166 - ABACAXI (UND)", "687 - AZEITONA", "937 - CANELA EM PAU", "189 - CENOURA", "194 - COUVE", "182 - CACAU (UND)", "184 - CAPIM SANTO (UNIDADE)", "303 - HIBISCO", "1559 - LIMÃO ROSA", "190 - COCO SECO (UND)", "192 - COCO VERDE (UND)", "1538 - CUPUAÇU (Kg)", "199 - GENGIBRE (Kg)", "201 - HORTELÃ (UNIDADE)", "203 - LARANJA BAHIA (Kg)", "206 - LIMÃO SICILIANO (Kg)", "205 - LIMÃO TAHITI (Kg)", "213 - MARACUJA (Kg)", "230 - MEL DE CACAU (UNIDADES)", "694 - MEL DE ABELHA", "813 - PEPINO JAPONÊS (Kg)", "697 - NIBS DE CACAU", "341 - PIMENTA ROSA", "1081 - ZIMBRO", "236 - TOMILHO (UNIDADES)", "2271 - ANIS ESTRELADO", "938 - UVA SEM CAROÇO (Kg)", "2272 - CRAVO DA ÍNDIA", "183 - CAJU", "233 - TANGERINA", "1497 - CARDAMOMO", "214 - MAXIXE", "299 - LOURO", "222 - PIMENTA DO REINO", "556 - AÇAFRÃO",
        "82 - NÊGA FULÔ", "368 - SERRA DAS ALMAS PRATA", "80 - SERRA DAS ALMAS OURO", "1175 - RIO DO ENGENHO PRATA", "1932 - RIO DO ENGENHO OURO", "2101 - MATRIARCA AMBURANA", "2103 - MATRIARCA JAQUEIRA", "2102 - MATRIARCA BÁLSAMO", "2104 - MATRIARCA 4 MADEIRAS", "97 - BACARDI PRATA", "98 - HAVANA CLUB 3 AÑOS", "99 - ZACAPA 23 AÑOS", "378 - ABSOLUT", "73 - BELVEDERE", "72 - GREY GOOSE", "74 - KETEL ONE", "2364 - YVY", "75 - YVY MAR", "2217 - YVY AR", "2216 - YVY TERRA", "77 - AMAZZONI", "371 - ARAPURU", "403 - SINGLE FIN", "66 - TANQUERAY", "370 - BOMBAY", "432 - BEEFEATER", "67 - HENDRICK´S", "78 - THE BOTANIST",
        "RED LABEL", "BLACK LABEL", "BLUE LABEL", "BUCHANNANS", "CHIVAS REGAL", "GLENFIDDICH", "MACALLAN 12 ANOS", "JAMESON", "93 - JACK DANIEL´S N7", "94 - JACK DANIEL´S SINGLE BARREL", "95 - GENTLEMAN JACK", "1762 - BULLEIT", "96 - WOODFORD RESERVE",
        "376 - JOSE CUERVO PRATA", "375 - JOSE CUERVO OURO", "100 - HERRADURA PRATA", "101 - HERRADURA OURO", "490 - HENNESSY", "121 - JUN DAITI", "122 - GEKKEIKAN", "103 - CAMPARI", "113 - APEROL", "494 - FERNET BRANCA", "707 - DOLIN ROUGE", "831 - DOLIN DRY", "106 - DOLIN BLANC", "112 - AMARO LUCANO", "489 - PUNT E MES", "2407 - LILLET BLANC", "109 - 43", "119 - LIMONCELLO", "108 - COINTREAU", "117 - BAILEYS", "372 - AMARULA", "116 - JAGGERMEISTER", "804 - MOLINARI CAFÉ", "104 - ANGOSTURA AROMATIC", "362 - ANGOSTURA ORANGE",
        "535 - CANUDO PAPEL", "759 - CANUDO TABOCAS", "476 - CAFÉ NESPRESSO", "1064 - DESCANSO DE COPO DE PAPEL (P/ CAFÉ COM LOGO)", "540 - ESPETO DE BAMBÚ DECORAÇÃO", "547 - PALITO DE DENTE", "1393 - CAPSULAS GAS N2O CHANTILLY", "945 - MOLHO INGLÊS (1 LITRO)", "2086 - SUCO DE TOMATE 1L", "706 - ACAI 9,5 KG", "160 - SHOYU", "316 - OLEO DE COCO"
    ],
    "SALÃO": [
        "Domaine de la Solitude Chateauneuf du Pape 2021", "Domaine Séguinot-Bordet Chablis 2022", "Almaviva 2020", "Barolo Gianni Gagliardo DOCG 2019", "Brunello di Montalcino Podere Brizio 2013", "Portal da Calçada Loureira", "Monte da Peceguina", "Calabuig Tempranillo", "Barone Pauline Sauternes", "Sacramento Dolce Far Niente Nature Chenin Blanc", "Thera Auguri Extra Brut", "Vivente Pét-nat Mel de Cacau & Pinot Noir", "Uvva Extra Brut", "Prosecco Bernardi Brut Pra Sei Salt DOCG", "Drappier Millésime Exception Extra Brut", "Möet & Chandon Brut Imperial", "Möet & Chandon Rosé Imperial", "Veuve Cliquot Brut Yellow Label", "Era dos Ventos Peverella", "Thera Sauvignon Blanc", "Uvva Chardonnay", "Uvva Sauvignon Blanc", "Otronia 45 Rugientes Cortes Blancas", "Rutini Chardonnay", "Vallisto Torrontés", "Baettig Los Parientes Chardonnay Orgânico", "Domaine Chauveau Coteaux di Giennois Calcaire", "Famille Bougrier Confidences Vouvray", "Famille Higel Classic Gewürztraminer", "Donnafugata Antília DOC", "Poggiotondo Vermentino IGT", "Fantini Pinot Grigio IGP", "Morgadio da Torre Alvarinho", "Portal da Calçada Loureira (Rosé)", "Thera Rosé", "Vivente Rosé Tranquilo", "Abbots & Delaunay Grenache Rosé", "Chateau Lafoux", "Dai Terra Rossa A.Mare Rosato Puglia IGP", "Monte da Peceguina (Tinto)", "Guaspari Vista da Mata Cabernet Franc", "Manus Clássico Nebbiolo", "Sacramento Sabina Syrah", "Uvva Cordel", "Uvva Diamã", "Rutini Malbec", "Sophenia Estate Wine Cabernet Sauvignon", "Odjfell Capítulo Blend Orgânico", "Domaine de Rochebin Pinot Noir de Bourgogne", "Calabuig Tempranillo (Tinto)", "Fantini Montepulciano d'Abruzzo Colline Teramane DOCG", "Garzon Single Vineyard Tannat",
        "SORO FISIOLOGICO", "ALGODÃO", "BAND-AID", "CANETA ESFEROGRÁFICA", "CANETA PILOTO AZUL", "CANETA PILOTO PRETA", "CANELA PILOTO VERMELHO", "ESPARADRAPO", "GASE", "GUARDANAPO 40 x 40", "PAPEL RECICLADO TAMANHO A4", "PILHA AA", "PILHA AAA", "PISTOLA DE ISQUEIRO", "REPELENTE LOÇÃO", "REPELENTE OFF SPRAY", "VELAS DE ANIVERSÁRIO", "VELAS GRANDES 10X15", "VELAS MÉDIAS 5,5X15", "VELAS PEQUENAS 3X6", "ABACAXI VERDE", "AMENDOIM 500G", "AZEITE EXTRA VIRGEM EA 500ML", "AZEITONAS PRETAS", "CACHO DE BANANA VERDE", "CASTANHA DE CAJÚ", "COCO SECO", "COCO VERDE", "FLOR DE SAL", "GRAVIOLA (ESCREVER A FRUTA)", "SAL GROSSO", "SAL REFINADO"
    ]
}

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

st.title("📝 Sistema de Requisição Diária")

nome_solicitante = st.text_input("Nome do Solicitante:", placeholder="Ex: João Silva")
setor_selecionado = st.selectbox("Selecione o seu Setor:", list(DADOS_ITENS.keys()))

st.write("---")

# ➔ NOVA OPÇÃO: Checkbox para ativar digitação manual
item_nao_cadastrado = st.checkbox("⚠️ O item NÃO está na lista? Marque aqui para digitar manualmente")

if item_nao_cadastrado:
    # Se marcar o checkbox, exibe uma caixa de texto livre
    item_escolhido = st.text_input("Digite o código ou nome completo do Item:", placeholder="Ex: 500 - NOVO ITEM KG")
else:
    # Se não marcar, continua usando a busca inteligente por selectbox
    lista_itens_setor = DADOS_ITENS[setor_selecionado]
    item_escolhido = st.selectbox("Busque e selecione o Item:", lista_itens_setor)

quantidade = st.number_input("Quantidade necessária:", min_value=1, value=1, step=1)

if st.button("➕ Adicionar Item ao Pedido", use_container_width=True):
    if nome_solicitante.strip() == "":
        st.error("Por favor, preencha o seu nome antes de adicionar itens.")
    elif str(item_escolhido).strip() == "":
        st.error("Por favor, digite o nome do item antes de adicionar.")
    else:
        st.session_state.carrinho.append({
            "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Solicitante": nome_solicitante,
            "Setor": setor_selecionado,
            "Item": item_escolhido.upper(), # Salva sempre em MAIÚSCULO para manter o padrão
            "Quantidade": int(quantidade)
        })
        st.success(f"Adicionado: {quantidade}x {item_escolhido.upper()}")

if st.session_state.carrinho:
    st.write("### 🛒 Itens no Pedido Atual")
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.dataframe(df_carrinho[["Item", "Quantidade", "Setor"]], use_container_width=True)
    
    if st.button("🗑️ Limpar Todo o Pedido", type="secondary"):
        st.session_state.carrinho = []
        st.rerun()
        
    st.write("---")
    
    if st.button("🚀 ENVIAR REQUISIÇÃO PARA A CENTRAL", type="primary", use_container_width=True):
        if "COLE_AQUI" in URL_WEB_APP:
            st.error("Erro: Você esqueceu de colocar a sua URL do Google Script na linha 12 do código!")
        else:
            with st.spinner("Enviando dados diretamente para o Google Sheets..."):
                try:
                    req = urllib.request.Request(URL_WEB_APP, method="POST")
                    req.add_header('Content-Type', 'application/json')
                    payload = json.dumps(st.session_state.carrinho).encode('utf-8')
                    
                    with urllib.request.urlopen(req, data=payload) as response:
                        resultado = response.read().decode('utf-8')
                    
                    if "Error" in resultado:
                        st.error(f"Erro no Google Sheets: {resultado}")
                    else:
                        st.balloons()
                        st.success(f"🎉 Pedido enviado com sucesso para a central!")
                        st.session_state.carrinho = []
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro na transmissão: {e}. Verifique se copiou a URL do Apps Script corretamente.")
