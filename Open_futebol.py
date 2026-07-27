import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ==============================
# CONFIGURAÇÃO EXCLUSIVA
# ==============================
st.set_page_config(
    page_title="Análise Independente",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🔒 Análise Completa | Totalmente Independente")

# ==============================
# DADOS DIRETOS DA FONTE ABERTA
# ==============================
LIGAS = {
    "🇧🇷 Brasileirão Série A": "br.1",
    "🇧🇷 Brasileirão Série B": "br.2",
    "🏆 Libertadores": "cu.libertadores",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "en.1",
    "🇪🇸 La Liga": "es.1",
    "🇩🇪 Bundesliga": "de.1",
    "🇮🇹 Serie A": "it.1"
}

MEDIAS = {
    "br.1": {"esc":9.0,"car":4.3,"fal":26,"fin":10},
    "br.2": {"esc":8.8,"car":4.5,"fal":27,"fin":9},
    "en.1": {"esc":10.5,"car":3.8,"fal":22,"fin":12},
    "es.1": {"esc":9.2,"car":4.2,"fal":24,"fin":11},
    "de.1": {"esc":9.8,"car":3.5,"fal":21,"fin":13},
    "it.1": {"esc":8.7,"car":4.5,"fal":25,"fin":10}
}

# ==============================
# FUNÇÕES PRÓPRIAS
# ==============================
def buscar_partidas(cod_liga):
    ano = "2025"
    url = f"https://raw.githubusercontent.com/openfootball/football.json/master/{ano}/{cod_liga}.json"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json().get("matches", [])
    except:
        return []

def calcular(times, lista_jogos):
    v = e = d = gf = gs = amb = 0
    total = 0
    for j in lista_jogos:
        if j["team1"] not in times and j["team2"] not in times:
            continue
        placar = j.get("score", {}).get("ft", [0,0])
        if j["team1"] in times:
            gf += placar[0]
            gs += placar[1]
            if placar[0] > placar[1]: v +=1
            elif placar[0] == placar[1]: e +=1
            else: d +=1
        else:
            gf += placar[1]
            gs += placar[0]
            if placar[1] > placar[0]: v +=1
            elif placar[1] == placar[0]: e +=1
            else: d +=1
        if placar[0]>0 and placar[1]>0: amb +=1
        total +=1
    if total ==0:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"fA":1,"fD":1}
    return {
        "pV":round((v/total)*100,1),
        "pE":round((e/total)*100,1),
        "pD":round((d/total)*100,1),
        "mg":round((gf+gs)/total,2),
        "ma25":round(70 if (gf+gs)/total>2.5 else 45,0),
        "amb":round((amb/total)*100,0),
        "fA":round((gf/total)/1.5,2),
        "fD":round((gs/total)/1.5,2)
    }

def estimar(d1, d2, cod):
    m = MEDIAS.get(cod, MEDIAS["br.1"])
    return {
        "esc": round(m["esc"] * ((d1["fA"]+d2["fA"])/2),1),
        "car": round(m["car"] * ((d1["fD"]+d2["fD"])/2),1),
        "fal": round(m["fal"] * ((d1["fD"]+d2["fD"])/2),1),
        "fin": round(m["fin"] * ((d1["fA"]+d2["fA"])/2),1)
    }

# ==============================
# INTERFACE
# ==============================
escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
cod = LIGAS[escolha]

dados = buscar_partidas(cod)
if not dados:
    st.warning("ℹ️ Dados não disponíveis no momento — fonte atualiza periodicamente.")
else:
    st.success(f"✅ Sistema carregado — {len(dados)} partidas cadastradas")
    hoje = datetime.utcnow().date()
    for jogo in dados:
        data_j = datetime.strptime(jogo["date"], "%Y-%m-%d").date()
        if data_j < hoje:
            continue
        casa = jogo["team1"]
        fora = jogo["team2"]
        dt = datetime.strptime(jogo["date"], "%Y-%m-%d")
        
        st.markdown("---")
        st.subheader(f"⚽ {casa} 🆚 {fora} | 📅 {dt.strftime('%d/%m')}")

        dc = calcular([casa], dados)
        df = calcular([fora], dados)
        est = estimar(dc, df, cod)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Probabilidades")
            st.write(f"✅ {casa}: {dc['pV']}%")
            st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
            st.write(f"✅ {fora}: {df['pD']}%")
            st.write(f"📊 Média Gols: {round((dc['mg']+df['mg'])/2,2)}")
            st.write(f"🔢 Mais 2.5: {round((dc['ma25']+df['ma25'])/2,0)}%")
            st.write(f"🔄 Ambos Marcam: {round((dc['amb']+df['amb'])/2,0)}%")

        with col2:
            st.subheader("📊 Estimativas")
            st.write(f"📐 Escanteios: {est['esc']}")
            st.write(f"🟨 Cartões: {est['car']}")
            st.write(f"👟 Faltas: {est['fal']}")
            st.write(f"🎯 Finalizações: {est['fin']}")

        if max(dc['pV'], df['pD']) >=75:
            st.error("🚨 ALTA CONFIANÇA ACIMA DE 75%!")
