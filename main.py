import csv
import os
import time
import threading
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

# Configuración
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = 60  # cada minuto
CSV_FILE = 'alertas_corners.csv'

IDIOMA = {'code': 'es'}
IDIOMAS = {
    'es': {
        'alert': '[ALERTA DE CÓRNER]',
        'match': 'Partido',
        'minute': 'Minuto',
        'corners': 'Córners',
        'entry': '=> Posible entrada Over 9.5',
        'summary': '[RESUMEN DEL DÍA]',
        'date': 'Fecha',
        'total': 'Total alertas',
        'hits': 'Aciertos',
        'misses': 'Fallos',
        'accuracy': 'Efectividad',
        'set_lang': 'Idioma cambiado a Español',
        'current_lang': 'Idioma actual: Español. Para cambiar usa /idioma es | en | pt',
        'no_file': 'Resumen no encontrado para ese mes.'
    }
}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo"

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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': mensaje}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error enviando mensaje: {e}")

def enviar_archivo_telegram(path, caption=''):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
            requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"Error enviando archivo: {e}")

# --- Scraping SofaScore (ejemplo básico) ---
def obtener_partidos_destacados():
    url = "https://www.sofascore.com/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    partidos = []

    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')

        # Simulación de datos reales
        partidos.append({
            'equipo_local': 'Team A',
