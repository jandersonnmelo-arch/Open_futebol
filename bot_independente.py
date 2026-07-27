import requests
import time
from datetime import datetime

# ==============================
# APENAS SEUS DADOS DO BOT
# ==============================
TOKEN = "8932712311:AAFDqOitkP_tay5IE97B3EUJUi0p45RsRJk"
MEU_ID = "1100260912"
LIMITE = 75

LIGAS = {
    "🇧🇷 Série A": "br.1",
    "🇧🇷 Série B": "br.2",
    "🏆 Libertadores": "cu.libertadores"
}

def enviar(msg):
    requests.get(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        params={"chat_id":MEU_ID,"text":msg,"parse_mode":"Markdown"}
    )

def buscar(cod):
    url = f"https://raw.githubusercontent.com/openfootball/football.json/master/2025/{cod}.json"
    try:
        return requests.get(url, timeout=15).json().get("matches",[])
    except:
        return []

def calc(times, lista):
    v=e=d=0
    for j in lista:
        if j["team1"] not in times and j["team2"] not in times:
            continue
        p = j.get("score",{}).get("ft",[0,0])
        if j["team1"] in times:
            if p[0]>p[1]:v+=1
            elif p[0]==p[1]:e+=1
            else:d+=1
        else:
            if p[1]>p[0]:v+=1
            elif p[1]==p[0]:e+=1
            else:d+=1
    t=v+e+d
    if t==0:return {"pV":50,"pE":33,"pD":17}
    return {"pV":round((v/t)*100,1),"pE":round((e/t)*100,1),"pD":round((d/t)*100,1)}

# ==============================
# EXECUÇÃO
# ==============================
if __name__ == "__main__":
    enviar("🔒 SISTEMA INDEPENDENTE INICIADO")
    for nome,cod in LIGAS.items():
        jogos = buscar(cod)
        if not jogos: continue
        enviar(f"\n🏆 {nome}")
        for j in jogos:
            if datetime.strptime(j["date"],"%Y-%m-%d").date() < datetime.utcnow().date():
                continue
            casa = j["team1"]
            fora = j["team2"]
            dc = calc([casa], jogos)
            df = calc([fora], jogos)
            enviar(f"""
⚽ {casa} vs {fora}
📅 {j["date"]}
✅ {casa}: {dc['pV']}% | ✅ {fora}: {df['pD']}%
            """.strip())
            if max(dc['pV'],df['pD'])>=LIMITE:
                enviar("🚨 ALTA CONFIANÇA!")
            time.sleep(0.8)
    enviar("\n✅ Concluído!")
