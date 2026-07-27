    import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import threading

# ==============================
# ⚙️ CONFIGURAÇÃO GERAL
# ==============================
st.set_page_config(page_title="⚽ Análise OpenFootball", page_icon="⚽", layout="wide")
st.title("⚽ Análise de Jogos + Copa do Brasil + Telegram | OpenFootball")

# 🔒 CHAVES DIRETO DOS SECRETS
BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

try:
    DIAS_BUSCA = int(st.secrets.get("DIAS_BUSCA", 7))
except:
    DIAS_BUSCA = 7

# ⏰ Alerta às 08:30 (horário Manaus UTC-4)
HORARIO_ALERTA = "08:30"
URL_BASE = "https://raw.githubusercontent.com/openfootball/football.json/master"

# ==============================
# 📤 ENVIO TELEGRAM
# ==============================
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=10)
        return True
    except Exception as e:
        print(f"Erro envio: {e}")
        return False

# ==============================
# 🏆 CAMPEONATOS DISPONÍVEIS
# ==============================
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

MEDIAS_LIGA = {
    "br.1": {"esc":9.0,"laterais":8.5,"tiro_meta":4.7,"fin":9.5,"chute_gol":4.0,"fal":26.5,"defesa":3.8},
    "br.2": {"esc":8.5,"laterais":9.0,"tiro_meta":5.0,"fin":9.0,"chute_gol":3.5,"fal":27.5,"defesa":4.2},
    "br.cup": {"esc":9.2,"laterais":8.8,"tiro_meta":4.8,"fin":9.3,"chute_gol":4.2,"fal":27.0,"defesa":3.9},
    "conmebol.libertadores": {"esc":9.5,"laterais":7.2,"tiro_meta":4.3,"fin":11.0,"chute_gol":4.8,"fal":23.5,"defesa":3.4},
    "en.1": {"esc":10.2,"laterais":6.8,"tiro_meta":4.0,"fin":11.5,"chute_gol":5.2,"fal":22.0,"defesa":3.1},
    "es.1": {"esc":9.0,"laterais":7.8,"tiro_meta":4.5,"fin":10.5,"chute_gol":4.5,"fal":24.0,"defesa":3.6},
    "de.1": {"esc":9.8,"laterais":6.5,"tiro_meta":3.7,"fin":12.5,"chute_gol":5.8,"fal":21.0,"defesa":2.8},
    "it.1": {"esc":8.7,"laterais":9.2,"tiro_meta":5.0,"fin":9.5,"chute_gol":3.8,"fal":25.5,"defesa":4.0},
    "fr.1": {"esc":9.5,"laterais":7.0,"tiro_meta":4.2,"fin":10.8,"chute_gol":4.8,"fal":23.0,"defesa":3.3},
    "pt.1": {"esc":8.8,"laterais":7.8,"tiro_meta":4.6,"fin":10.2,"chute_gol":4.3,"fal":24.5,"defesa":3.7}
}

# ==============================
# 🔍 BUSCA E CÁLCULOS
# ==============================
@st.cache_data(ttl=21600) # Cache de 6 horas
def buscar_jogos(chave_liga, dias):
    time.sleep(0.3)
    hoje = datetime.now().date()
    lista = []
    try:
        # Busca dados da temporada atual
        r = requests.get(f"{URL_BASE}/{chave_liga}/2025-26.json", timeout=15)
        if r.status_code != 200:
            r = requests.get(f"{URL_BASE}/{chave_liga}/2026-27.json", timeout=15)
            if r.status_code != 200:
                return []
        
        dados = r.json()
        for rodada in dados.get("matches", []):
            data_jogo = datetime.strptime(rodada["date"], "%Y-%m-%d").date()
            horario = rodada.get("time", "00:00")
            if data_jogo >= hoje and data_jogo <= hoje + timedelta(days=dias):
                lista.append({
                    "casa": rodada["team1"],
                    "fora": rodada["team2"],
                    "data": data_jogo,
                    "horario": horario,
                    "liga": chave_liga
                })
    except Exception as e:
        print(f"Erro na liga {chave_liga}: {e}")
    return lista

def calcular_base(time_nome, liga):
    medias = MEDIAS_LIGA.get(liga, MEDIAS_LIGA["br.1"])
    # Sem histórico detalhado, usa médias equilibradas
    return {
        "pV":33.3,"pE":33.3,"pD":33.4,
        "mg":2.5,"ma25":50,"amb":50,
        "esc":medias["esc"],"laterais":medias["laterais"],"tiro_meta":medias["tiro_meta"],
        "fin":medias["fin"],"chute_gol":medias["chute_gol"],"fal":medias["fal"],"defesa":medias["defesa"],
        "resumo":["❔","❔","❔","❔","❔"]
    }

def dupla_chance(pV,pE,pD):
    return {"1X":round(pV+pE,1),"X2":round(pE+pD,1),"12":round(pV+pD,1)}

# ==============================
# 📝 MENSAGEM TELEGRAM
# ==============================
def gerar_mensagem_jogo(casa_nome, fora_nome, dt, dc, df, dup, mg, m25, amb, esc, fal, conf):
    return f"""
⚽ *{casa_nome} 🆚 {fora_nome}*
📅 {dt.strftime('%d/%m às %H:%M')}

📊 Probabilidades:
✅ {casa_nome}: {dc['pV']}%
⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%
✅ {fora_nome}: {df['pD']}%

🔀 Dupla Chance:
1X: {round((dup['1X']+dupla_chance(df['pV'],df['pE'],df['pD'])['1X'])/2,1)}%
X2: {round((dup['X2']+dupla_chance(df['pV'],df['pE'],df['pD'])['X2'])/2,1)}%
12: {round((dup['12']+dupla_chance(df['pV'],df['pE'],df['pD'])['12'])/2,1)}%

📈 Métricas:
⚽ Média Gols: {mg} | Mais 2.5: {m25}% | Ambos Marcam: {amb}%
📐 Escanteios: {esc} | Faltas: {fal}

📋 Dados baseados na média da liga
---
"""

# ==============================
# 🤖 ENVIO AUTOMÁTICO
# ==============================
def servico_automatico():
    while True:
        if datetime.now().strftime("%H:%M") == HORARIO_ALERTA:
            msg = f"🔔 *RELATÓRIO OPENFOOTBALL*\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n📅 {DIAS_BUSCA} dias\n\n"
            total_jogos = 0
            for nome_liga, chave in CAMPEONATOS.items():
                jogos = buscar_jogos(chave, DIAS_BUSCA)
                if not jogos: continue
                msg += f"🏆 {nome_liga}\n"
                for j in jogos:
                    total_jogos +=1
                    dt = datetime.combine(j["data"], datetime.strptime(j["horario"],"%H:%M").time()) - timedelta(hours=4)
                    dc = calcular_base(j["casa"], j["liga"])
                    df = calcular_base(j["fora"], j["liga"])
                    dup = dupla_chance(dc['pV'],dc['pE'],dc['pD'])
                    mg = round((dc['mg']+df['mg'])/2,2)
                    m25 = round((dc['ma25']+df['ma25'])/2,0)
                    amb = round((dc['amb']+df['amb'])/2,0)
                    esc = round((dc['esc']+df['esc'])/2,1)
                    fal = round((dc['fal']+df['fal'])/2,1)
                    conf = max(dc['pV'], df['pD'])
                    msg += gerar_mensagem_jogo(j["casa"], j["fora"], dt, dc, df, dup, mg, m25, amb, esc, fal, conf)
            if total_jogos >0:
                enviar_telegram(msg)
            time.sleep(120)
        time.sleep(30)

threading.Thread(target=servico_automatico, daemon=True).start()

# ==============================
# 🖥️ INTERFACE
# ==============================
escolha = st.selectbox("Escolha a Competição", list(CAMPEONATOS.keys()))
chave_liga = CAMPEONATOS[escolha]
dias_usuario = st.number_input("Buscar quantos dias?", min_value=1, max_value=14, value=DIAS_BUSCA)

if st.button("🔍 Atualizar e Enviar Agora"):
    st.cache_data.clear()
    jogos = buscar_jogos(chave_liga, dias_usuario)
    
    if not jogos:
        st.info("ℹ️ Nenhum jogo encontrado para esse período.")
    else:
        st.success(f"✅ {len(jogos)} jogos encontrados!")
        msg_rel = f"🔔 *RELATÓRIO SOLICITADO*\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n📅 {dias_usuario} dias | {escolha}\n\n"
        
        for j in jogos:
            dt = datetime.combine(j["data"], datetime.strptime(j["horario"],"%H:%M").time()) - timedelta(hours=4)
            dc = calcular_base(j["casa"], j["liga"])
            df = calcular_base(j["fora"], j["liga"])
            dup = dupla_chance(dc['pV'],dc['pE'],dc['pD'])
            mg = round((dc['mg']+df['mg'])/2,2)
            m25 = round((dc['ma25']+df['ma25'])/2,0)
            amb = round((dc['amb']+df['amb'])/2,0)
            esc = round((dc['esc']+df['esc'])/2,1)
            fal = round((dc['fal']+df['fal'])/2,1)
            conf = max(dc['pV'], df['pD'])

            msg_rel += gerar_mensagem_jogo(j["casa"], j["fora"], dt, dc, df, dup, mg, m25, amb, esc, fal, conf)

            st.markdown("---")
            st.subheader(f"⚽ {j['casa']} 🆚 {j['fora']} | {dt.strftime('%d/%m %H:%M')}")

            c1,c2 = st.columns(2)
            with c1:
                st.subheader("📈 Probabilidades")
                st.write(f"✅ {j['casa']}: {dc['pV']}%")
                st.write(f"⚖️ Empate: {round((dc['pE']+df['pE'])/2,1)}%")
                st.write(f"✅ {j['fora']}: {df['pD']}%")
                st.divider()
                st.subheader("🔀 Dupla Chance")
                st.write(f"1X: {dup['1X']}%")
                st.write(f"X2: {dup['X2']}%")
                st.write(f"12: {dup['12']}%")

            with c2:
                st.subheader("📐 Estatísticas")
                st.write(f"⚽ Média Gols: {mg} | Mais 2.5: {m25}%")
                st.write(f"📊 Ambos Marcam: {amb}%")
                st.write(f"📐 Escanteios: {esc} | Faltas: {fal}")
        
        enviar_telegram(msg_rel)
        st.success("✅ Enviado ao Telegram!")
            
