import logging
import googleapiclient.discovery
from datetime import datetime
import csv
import re
import os
import pytz

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def coletar_videos_populares(youtube):
    try:
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            chart="mostPopular",
            regionCode="BR",
            maxResults=50
        )
        response = request.execute()
        return response["items"]
    except Exception as e:
        logging.error(f"Erro ao coletar vídeos: {e}")
        return []

def main():
    API_KEY = os.environ.get("API_KEY")
    if not API_KEY:
        logging.error("API_KEY não encontrada. Certifique-se de que está configurada.")
        return

    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY, static_discovery=False, credentials=None)
        videos = coletar_videos_populares(youtube)
        if videos:
            dados_coletados = processar_dados(youtube, videos)
            exportar_para_csv(dados_coletados)
        else:
            logging.warning("Nenhum vídeo foi coletado.")
    except Exception as e:
        logging.error(f"Erro durante a execução do script: {e}")

if __name__ == "__main__":
    main()
