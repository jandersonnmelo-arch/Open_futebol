import streamlit as st
import requests
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO
# ==============================
st.set_page_config(page_title="⚽ Análise OpenFootball", page_icon="⚽", layout="wide")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
HORARIO_ALERTA = "08:30"

CAMPEONATOS = {
    "🇧🇷 Brasileirão Série A": "br.1",
    "🇧🇷 Brasileirão Série B": "br.2",
    "🇧🇷 Copa do Brasil": "br.cup",
    "🏆 Libertadores": "conmebol.libertadores",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "en.1",
    "🇪🇸 La Liga": "es.1",
    "🇩🇪 Bundesliga": "de.1",
    "🇮🇹 Serie A": "it.1",
    "🇫🇷 Ligue 1": "fr.1",
    "🇵🇹 Primeira Liga": "pt.1"
}

MEDIAS = {
    "br.1": (9.0, 8.5, 4.7, 9.5, 4.0, 26.5, 3.8),
    "br.2": (8.5, 9.0, 5.0, 9.0, 3.5, 27.5, 4.2),
    "br.cup": (9.2, 8.8, 4.8, 9.3, 4.2, 27.0, 3.9),
    "conmebol.libertadores": (9.5, 7.2, 4.3, 11.0, 4.8, 23.5, 3.4),
    "en.1": (10.2, 6.8, 4.0, 11.5, 5.2, 22.0, 3.1),
    "es.1": (9.0, 7.8, 4.5, 10.5, 4.5, 24.0, 3.6),
    "de.1": (9.8, 6.5, 3.7, 12.5, 5.8, 21.0, 2.8),
    "it.1": (8.7, 9.2, 5.0, 9.5, 3.8, 25.5, 4.0),
    "fr.1": (9.5, 7.0, 4.2, 10.8, 4.8, 23.0, 3.3),
    "pt.1": (8.8, 7.8, 4.6, 10.2, 4.3, 24.5, 3.7)
}

# ==============================
# 📤 TELEGRAM
# ==============================
def enviar_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                     data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        return True
    except:
        return False

# ==============================
# 🔍 BUSCA COM DATA SEGURA
# ==============================
@st.cache_data(ttl=3600)
def buscar_jogos(chave, dias):
    hoje = datetime.now().date()
    lista = []
    for temp in ["2026-27", "2025-26"]:
        try:
            url = f"https://raw.githubusercontent.com/openfootball/football.json/master/{chave}/{temp}.json"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            dados = r.json()
            for jogo in dados.get("matches", []):
                data_texto = jogo.get("date", "").strip()
                if not data_texto:
                    continue
                # ✅ TRATA ERRO DE DATA SEM TRAVAR
                try:
                    data_jogo = datetime.strptime(data_texto, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if hoje <= data_jogo <= hoje + timedelta(days=dias):
                    lista.append({
                        "casa": jogo["team1"],
                        "fora": jogo["team2"],
                        "data": data_jogo,
                        "hora": jogo.get("time", "00:00"),
                        "liga": chave
                    })
            if lista:
                break
        except:
            continue
    return lista

# ==============================
# 🧮 CÁLCULOS
# ==============================
def calcular(liga):
    med = MEDIAS.get(liga, MEDIAS["br.1"])
    return {
        "v": 33.3, "e": 33.3, "d": 33.4,
        "mg": 2.5, "ma25": 50, "amb": 50,
        "esc": med[0], "lat": med[1], "meta": med[2],
        "fin": med[3], "gol": med[4], "fal": med[5], "def": med[6]
    }

def dupla(v,e,d):
    return {"1X": round(v+e,1), "X2": round(e+d,1), "12": round(v+d,1)}

# ==============================
# 🤖 ROTINA AUTOMÁTICA
# ==============================
def alerta():
    while True:
        if datetime.now().strftime("%H:%M") == HORARIO_ALERTA:
            mensagem = f"🔔 *RELATÓRIO AUTOMÁTICO*\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            total = 0
            for nome, chave in CAMPEONATOS.items():
                jogos = buscar_jogos(chave, DIAS_BUSCA)
                if not jogos:
                    continue
                mensagem += f"🏆 {nome}\n"
                for j in jogos:
                    total += 1
                    dt = datetime.combine(j["data"], datetime.strptime(j["hora"],"%H:%M").time()) - timedelta(hours=4)
                    c = calcular(j["liga"])
                    f = calcular(j["liga"])
                    dup = dupla(c["v"],c["e"],c["d"])
                    mensagem += f"⚽ {j['casa']} x {j['fora']} | {dt.strftime('%d/%m %H:%M')}\n✅ {c['v']}% | ⚖️ {round((c['e']+f['e'])/2,1)}% | ✅ {f['d']}%\n🔀 1X:{dup['1X']}% X2:{dup['X2']}% 12:{dup['12']}%\n---\n"
            if total > 0:
                enviar_telegram(mensagem)
            threading.Event().wait(120)
        threading.Event().wait(30)

threading.Thread(target=alerta, daemon=True).start()

# ==============================
# 🖥️ INTERFACE
# ==============================
st.title("⚽ Análise de Jogos | OpenFootball")
liga_esc = st.selectbox("Escolha a competição", list(CAMPEONATOS.keys()))
dias = st.number_input("Buscar quantos dias?", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar Agora"):
    st.cache_data.clear()
    jogos = buscar_jogos(CAMPEONATOS[liga_esc], dias)
    
    if not jogos:
        st.warning("ℹ️ Nenhum jogo encontrado nesse período.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        msg_rel = f"🔔 *RELATÓRIO SOLICITADO*\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n📅 {liga_esc} - {dias} dias\n\n"
        
        for j in jogos:
            dt = datetime.combine(j["data"], datetime.strptime(j["hora"],"%H:%M").time()) - timedelta(hours=4)
            c = calcular(j["liga"])
            f = calcular(j["liga"])
            dup = dupla(c["v"],c["e"],c["d"])
            
            msg_rel += f"⚽ {j['casa']} x {j['fora']} | {dt.strftime('%d/%m %H:%M')}\n✅ {c['v']}% | ⚖️ {round((c['e']+f['e'])/2,1)}% | ✅ {f['d']}%\n🔀 1X:{dup['1X']}% X2:{dup['X2']}% 12:{dup['12']}%\n---\n"
            
            st.subheader(f"⚽ {j['casa']} 🆚 {j['fora']} | {dt.strftime('%d/%m %H:%M')}")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"✅ {j['casa']}: {c['v']}%")
                st.write(f"⚖️ Empate: {round((c['e']+f['e'])/2,1)}%")
                st.write(f"✅ {j['fora']}: {f['d']}%")
                st.divider()
                st.write(f"🔀 Dupla Chance:")
                st.write(f"1X: {dup['1X']}% | X2: {dup['X2']}% | 12: {dup['12']}%")
            with col2:
                st.write(f"⚽ Média Gols: {round((c['mg']+f['mg'])/2,2)}")
                st.write(f"Mais de 2.5: {round((c['ma25']+f['ma25'])/2,0)}%")
                st.write(f"📐 Escanteios: {round((c['esc']+f['esc'])/2,1)} | Faltas: {round((c['fal']+f['fal'])/2,1)}")
            st.markdown("---")
        
        enviar_telegram(msg_rel)
        st.success("✅ Relatório enviado ao Telegram!")
        
