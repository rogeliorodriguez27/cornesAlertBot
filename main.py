import csv
import os
import threading
import time
from datetime import datetime

from flask import Flask, request
import requests

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = 60
CSV_FILE = 'alertas_corners.csv'
IDIOMA = {'code': 'es'}

IDIOMAS = {
    'es': {
        'alert': '[ALERTA DE CÓRNER]',
        'match': 'Partido',
        'tournament': 'Torneo',
        'minute': 'Minuto',
        'corners': 'Córners',
        'danger': 'Ataques peligrosos',
        'possession': 'Posesión equipo que pierde',
        'entry': '=> Posible entrada Over 9.5',
        'summary': '[RESUMEN DEL DÍA]',
        'date': 'Fecha',
        'total': 'Total alertas',
        'hits': 'Aciertos',
        'misses': 'Fallos',
        'accuracy': 'Efectividad',
        'set_lang': 'Idioma cambiado a Español',
        'current_lang':
        'Idioma actual: Español. Para cambiar el idioma envía uno de estos comandos: /idioma es | /idioma en | /idioma pt',
        'no_file': 'Archivo de resumen no encontrado para ese mes.'
    },
    'en': {
        'alert': '[CORNER ALERT]',
        'match': 'Match',
        'tournament': 'Tournament',
        'minute': 'Minute',
        'corners': 'Corners',
        'danger': 'Dangerous attacks',
        'possession': 'Losing team possession',
        'entry': '=> Possible Over 9.5 Entry',
        'summary': '[DAILY SUMMARY]',
        'date': 'Date',
        'total': 'Total alerts',
        'hits': 'Hits',
        'misses': 'Misses',
        'accuracy': 'Accuracy',
        'set_lang': 'Language set to English',
        'current_lang':
        'Current language: English. To change, send /idioma es | /idioma en | /idioma pt',
        'no_file': 'Summary file not found for that month.'
    },
    'pt': {
        'alert': '[ALERTA DE ESCANTEIO]',
        'match': 'Partida',
        'tournament': 'Torneio',
        'minute': 'Minuto',
        'corners': 'Escanteios',
        'danger': 'Ataques perigosos',
        'possession': 'Posse do time perdedor',
        'entry': '=> Possível entrada Over 9.5',
        'summary': '[RESUMO DO DIA]',
        'date': 'Data',
        'total': 'Alertas totais',
        'hits': 'Acertos',
        'misses': 'Erros',
        'accuracy': 'Precisão',
        'set_lang': 'Idioma alterado para Português',
        'current_lang':
        'Idioma atual: Português. Para mudar envie: /idioma es | /idioma en | /idioma pt',
        'no_file': 'Arquivo de resumo não encontrado para esse mês.'
    }
}

app = Flask(__name__)


@app.route('/')
def home():
    return "✅ Bot está activo"


@app.route(f"/bot{TELEGRAM_TOKEN}", methods=['POST'])
def recibir_mensaje():
    data = request.get_json()
    if 'message' in data:
        chat_id = str(data['message']['chat']['id'])
        texto = data['message'].get('text', '').lower()
        if str(chat_id) == str(TELEGRAM_CHAT_ID):
            if texto.startswith('/idioma'):
                codigo = texto.split()[-1]
                if codigo in IDIOMAS:
                    IDIOMA['code'] = codigo
                    enviar_alerta_telegram(IDIOMAS[codigo]['set_lang'])
            elif texto.startswith('/resumen'):
                partes = texto.split()
                mes = datetime.now().strftime('%Y-%m') if len(partes) == 1 else partes[1]
                archivo = f"resumen_{mes}.csv"
                if os.path.isfile(archivo):
                    enviar_archivo_telegram(archivo, f"{IDIOMAS[IDIOMA['code']]['summary']} {mes}")
                else:
                    enviar_alerta_telegram(IDIOMAS[IDIOMA['code']]['no_file'])
            else:
                enviar_alerta_telegram(IDIOMAS[IDIOMA['code']]['current_lang'])
    return {'ok': True}


def enviar_alerta_telegram(mensaje):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': mensaje}
        response = requests.post(url, data=data)
        return True
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return False


def enviar_archivo_telegram(path, caption=''):
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument'
        with open(path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"Error enviando archivo: {e}")


def main_loop():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN y TELEGRAM_CHAT_ID son requeridos")
        return

    mensaje_prueba = "🤖 Bot iniciado correctamente - " + datetime.now().strftime("%H:%M:%S")
    enviar_alerta_telegram(mensaje_prueba)

    while True:
        try:
            mensaje = f"[ALERTA DE PRUEBA]\nPartido: Barcelona vs Real Madrid\nMinuto: 75\nCórners: 8\nAtaques peligrosos: 60%\nPosesión: 65%"
            enviar_alerta_telegram(mensaje)
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Error en el loop: {e}")
            time.sleep(10)


if __name__ == '__main__':
    threading.Thread(target=main_loop).start()
    app.run(host='0.0.0.0', port=10000)
