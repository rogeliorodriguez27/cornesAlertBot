import csv
import os
import threading
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from flask import Flask, request

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = 60
CSV_FILE = 'alertas_corners.csv'
IDIOMA = {'code': 'es'}

IDIOMAS = {
    'es': {'alert': '[ALERTA DE CÓRNER]', 'match': 'Partido', 'tournament': 'Torneo',
           'minute': 'Minuto', 'corners': 'Córners', 'danger': 'Ataques peligrosos',
           'possession': 'Posesión equipo que pierde', 'entry': '=> Posible entrada Over 9.5',
           'summary': '[RESUMEN DEL DÍA]', 'date': 'Fecha', 'total': 'Total alertas',
           'hits': 'Aciertos', 'misses': 'Fallos', 'accuracy': 'Efectividad',
           'set_lang': 'Idioma cambiado a Español',
           'current_lang': 'Idioma actual: Español. Cambiar: /idioma es | /idioma en | /idioma pt',
           'no_file': 'Archivo de resumen no encontrado para ese mes.'},
    'en': {'alert': '[CORNER ALERT]', 'match': 'Match', 'tournament': 'Tournament',
           'minute': 'Minute', 'corners': 'Corners', 'danger': 'Dangerous attacks',
           'possession': 'Losing team possession', 'entry': '=> Possible Over 9.5 Entry',
           'summary': '[DAILY SUMMARY]', 'date': 'Date', 'total': 'Total alerts',
           'hits': 'Hits', 'misses': 'Misses', 'accuracy': 'Accuracy',
           'set_lang': 'Language set to English',
           'current_lang': 'Current language: English. Change: /idioma es | /idioma en | /idioma pt',
           'no_file': 'Summary file not found for that month.'},
    'pt': {'alert': '[ALERTA DE ESCANTEIO]', 'match': 'Partida', 'tournament': 'Torneio',
           'minute': 'Minuto', 'corners': 'Escanteios', 'danger': 'Ataques perigosos',
           'possession': 'Posse do time perdedor', 'entry': '=> Possível entrada Over 9.5',
           'summary': '[RESUMO DO DIA]', 'date': 'Data', 'total': 'Alertas totais',
           'hits': 'Acertos', 'misses': 'Erros', 'accuracy': 'Precisão',
           'set_lang': 'Idioma alterado para Português',
           'current_lang': 'Idioma atual: Português. Mudar: /idioma es | /idioma en | /idioma pt',
           'no_file': 'Arquivo de resumo não encontrado para esse mês.'}
}

app = Flask('')


@app.route('/')
def home():
    return "Bot activo"


@app.route(f"/bot{TELEGRAM_TOKEN}", methods=['POST'])
def recibir_mensaje():
    data = request.get_json()
    if 'message' in data:
        chat_id = str(data['message']['chat']['id'])
        texto = data['message'].get('text', '').lower()
        if chat_id == TELEGRAM_CHAT_ID:
            if texto.startswith('/idioma'):
                codigo = texto.split()[-1]
                if codigo in IDIOMAS:
                    IDIOMA['code'] = codigo
                    enviar_alerta_telegram(IDIOMAS[codigo]['set_lang'])
            elif texto.startswith('/resumen'):
                mes = texto.split()[1] if len(texto.split()) > 1 else datetime.now().strftime('%Y-%m')
                archivo = f"resumen_{mes}.csv"
                if os.path.isfile(archivo):
                    enviar_archivo_telegram(archivo, f"{IDIOMAS[IDIOMA['code']]['summary']} {mes}")
                else:
                    enviar_alerta_telegram(IDIOMAS[IDIOMA['code']]['no_file'])
            else:
                enviar_alerta_telegram(IDIOMAS[IDIOMA['code']]['current_lang'])
    return {'ok': True}


def enviar_alerta_telegram(mensaje):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    try:
        response = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': mensaje})
        response.raise_for_status()
    except Exception as e:
        print(f"Error enviando mensaje: {e}")


def enviar_archivo_telegram(path, caption=''):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument'
    try:
        with open(path, 'rb') as f:
            requests.post(url, files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption})
    except Exception as e:
        print(f"Error enviando archivo: {e}")


def scrapear_sofascore():
    url = 'https://www.sofascore.com/es/football/livescore'
    headers = {'User-Agent': 'Mozilla/5.0'}
    partidos_detectados = []

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        for partido in soup.select('a.styles__MatchLink-sc-1v5lw7f-0'):
            texto = partido.get_text()
            if any(minuto in texto for minuto in ['45', '46', '50', '70', '75', '80', '85']):
                nombre = texto.strip()
                partidos_detectados.append(nombre)

        return partidos_detectados

    except Exception as e:
        print(f"Error en el scraping: {e}")
        return []


def guardar_en_csv(data):
    archivo = CSV_FILE
    existe = os.path.isfile(archivo)
    with open(archivo, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(['Fecha', 'Partido'])
        for partido in data:
            writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), partido])


def main_loop():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Faltan variables de entorno")
        return

    enviar_alerta_telegram("🤖 Bot de córners activo ✅")

    while True:
        partidos = scrapear_sofascore()
        if partidos:
            for p in partidos:
                mensaje = f"{IDIOMAS[IDIOMA['code']]['alert']}\n{IDIOMAS[IDIOMA['code']]['match']}: {p}\n{IDIOMAS[IDIOMA['code']]['entry']}"
                enviar_alerta_telegram(mensaje)
            guardar_en_csv(partidos)
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    threading.Thread(target=main_loop).start()
    app.run(host='0.0.0.0', port=10000)
