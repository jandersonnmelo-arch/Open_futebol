import streamlit as st
import requests
from datetime import datetime

# ==============================
# INICIALIZAÇÃO RÁPIDA
# ==============================
st.set_page_config(
    page_title="Sistema Independente",
    page_icon="🔒",
    layout="wide"
)
st.title("🔒 Sistema Totalmente Independente")

# ==============================
# LIGAS E MÉDIAS
# ==============================
LIGAS = {
    "🇧🇷 Brasileirão Série A": "br.1",
    "🇧🇷 Brasileirão Série B": "br.2",
    "🏆 Libertadores": "cu.libertadores"
}

MEDIAS = {
    "br.1": {"esc":9.0,"car":4.3,"fal":26,"fin":10},
    "br.2": {"esc":8.8,"car":4.5,"fal":27,"fin":9},
    "cu.libertadores": {"esc":9.5,"car":3.7,"fal":23,"fin":11}
}

# ==============================
# BUSCA COM TRATAMENTO DE ERRO
# ==============================
def buscar_partidas(cod_liga):
    ano = "2025"
    url = f"https://raw.githubusercontent.com/openfootball/football.json/master/{ano}/{cod_liga}.json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as e:
        st.error(f"Erro ao buscar dados: {str(e)}")
        return []

def calcular(times, lista_jogos):
    if not lista_jogos:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"fA":1,"fD":1}
    v=e=d=gf=gs=amb=0
    for j in lista_jogos:
        if j.get("team1") not in times and j.get("team2") not in times:
            continue
        placar = j.get("score", {}).get("ft", [0,0])
        if j["team1"] in times:
            gf += placar[0]; gs += placar[1]
            if placar[0]>placar[1]: v+=1
            elif placar[0]==placar[1]: e+=1
            else: d+=1
        else:
            gf += placar[1]; gs += placar[0]
            if placar[1]>placar[0]: v+=1
            elif placar[1]==placar[0]: e+=1
            else: d+=1
        if placar[0]>0 and placar[1]>0: amb+=1
    total = v+e+d
    if total==0:
        return {"pV":50,"pE":33,"pD":17,"mg":2.5,"ma25":50,"amb":50,"fA":1,"fD":1}
    return {
        "pV":round((v/total)*100,1), "pE":round((e/total)*100,1), "pD":round((d/total)*100,1),
        "mg":round((gf+gs)/total,2), "ma25":round(70 if (gf+gs)/total>2.5 else 45,0),
        "amb":round((amb/total)*100,0),
        "fA":round((gf/total)/1.5,2), "fD":round((gs/total)/1.5,2)
    }

def estimar(d1,d2,cod):
    m = MEDIAS.get(cod, MEDIAS["br.1"])
    return {
        "esc":round(m["esc"]*((d1["fA"]+d2["fA"])/2),1),
        "car":round(m["car"]*((d1["fD"]+d2["fD"])/2),1),
        "fal":round(m["fal"]*((d1["fD"]+d2["fD"])/2),1),
        "fin":round(m["fin"]*((d1["fA"]+d2["fA"])/2),1)
    }

# ==============================
# INTERFACE
# ==============================
try:
    escolha = st.selectbox("Escolha a Competição", list(LIGAS.keys()))
    cod = LIGAS[escolha]
    dados = buscar_partidas(cod)

    if not dados:
        st.warning("ℹ️ Nenhum dado disponível no momento — fonte atualiza periodicamente.")
    else:
        st.success(f"✅ Carregado! {len(dados)} partidas cadastradas")
        hoje = datetime.utcnow().date()
        for jogo in dados:
            try:
                data_j = datetime.strptime(jogo["date"], "%Y-%m-%d").date()
            except:
                continue
            if data_j < hoje:
                continue
            casa = jogo["team1"]
            fora = jogo["team2"]
            dt = datetime.strptime(jogo["date"], "%Y-%m-%d")
            
            st.markdown("---")
            st.subheader(f"⚽ {casa} 🆚 {fora} | 📅 {dt.strftime('%d/%m')}")

            dc = calcular([casa], dados)
            df = calcular([fora], dados)
            est = estimar(dc,df,cod)

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

except Exception as geral:
    st.error(f"Erro geral: {str(geral)}")
    st.info("Verifique a conexão ou tente novamente mais tarde.")
    
