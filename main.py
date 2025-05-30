import googleapiclient.discovery
from datetime import datetime
import csv
import re
import os
import pytz
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para coletar vídeos populares
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

# Função para converter duração ISO 8601 para HH:MM:SS
def formatar_duracao(duracao_iso):
    try:
        padrao = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = padrao.match(duracao_iso)
        horas = int(match.group(1)) if match.group(1) else 0
        minutos = int(match.group(2)) if match.group(2) else 0
        segundos = int(match.group(3)) if match.group(3) else 0
        return f"{horas:02}:{minutos:02}:{segundos:02}"
    except:
        return "00:00:00"

# Função para buscar o guideCategory do canal
def buscar_guide_category(youtube, channel_id):
    try:
        channel_request = youtube.channels().list(
            part="topicDetails",
            id=channel_id
        )
        channel_response = channel_request.execute()
        if "items" in channel_response and channel_response["items"]:
            topic_categories = channel_response["items"][0].get("topicDetails", {}).get("topicCategories", [])
            guide_categories = [cat.split("/")[-1] for cat in topic_categories if "wikipedia.org" in cat]
            return ", ".join(guide_categories) if guide_categories else "N/A"
        else:
            return "N/A"
    except Exception as e:
        logging.error(f"Erro ao buscar guideCategory: {e}")
        return "N/A"

# Função para buscar o país do canal
def buscar_pais(youtube, channel_id):
    try:
        channel_request = youtube.channels().list(
            part="snippet",
            id=channel_id
        )
        channel_response = channel_request.execute()
        if "items" in channel_response and channel_response["items"]:
            country = channel_response["items"][0].get("snippet", {}).get("country", "N/A")
            return country
        else:
            return "N/A"
    except Exception as e:
        logging.error(f"Erro ao buscar país: {e}")
        return "N/A"

# Função para processar os dados dos vídeos
def processar_dados(youtube, videos):
    dados_coletados = []
    for index, item in enumerate(videos):
        video_id = item["id"]
        snippet = item["snippet"]
        statistics = item["statistics"]
        content_details = item["contentDetails"]
        data = {
            "Posicao na coleta": index + 1,
            "Gênero do vídeo": "",
            "Tipo de produtor": "",
            "Categoria do vídeo": snippet.get("categoryId", ""),
            "guideCategory": buscar_guide_category(youtube, snippet.get("channelId", "")),
            "Taxa de engajamento": "",
            "Idioma": snippet.get("defaultAudioLanguage", snippet.get("defaultLanguage", "")),
            "Posicao Geral": index + 1,
            "Id do canal": snippet.get("channelId", ""),
            "Canal": snippet.get("channelTitle", ""),
            "Inscritos no canal": 0,
            "Id do vídeo": video_id,
            "Data de publicação": snippet.get("publishedAt", ""),
            "Diferenca de horas entre postagem e coleta": "",
            "Título do vídeo": snippet.get("title", ""),
            "Descrição do vídeo": snippet.get("description", ""),
            "Tags do video": ", ".join(snippet.get("tags", [])),
            "Duração do vídeo": formatar_duracao(content_details.get("duration", "")),
            "Visualizações": statistics.get("viewCount", 0),
            "Gostei": statistics.get("likeCount", 0),
            "Comentários": statistics.get("commentCount", 0),
            "thumbnail_maxres": snippet.get("thumbnails", {}).get("maxres", {}).get("url", ""),
            "Pais": buscar_pais(youtube, snippet.get("channelId", "")),
        }
        try:
            views = int(data["Visualizações"])
            likes = int(data["Gostei"])
            comments = int(data["Comentários"])
            data["Taxa de engajamento"] = f"{(likes + comments) / views * 100:.2f}%" if views > 0 else "0%"
        except (ValueError, TypeError):
            data["Taxa de engajamento"] = "0%"
        try:
            post_date = datetime.fromisoformat(data["Data de publicação"].replace("Z", ""))
            current_date = datetime.utcnow()
            diff_hours = (current_date - post_date).total_seconds() / 3600
            data["Diferenca de horas entre postagem e coleta"] = f"{diff_hours:.2f} horas"
        except (ValueError, TypeError):
            data["Diferenca de horas entre postagem e coleta"] = "0 horas"
        channel_request = youtube.channels().list(
            part="statistics",
            id=data["Id do canal"]
        )
        channel_response = channel_request.execute()
        if channel_response["items"]:
            data["Inscritos no canal"] = int(channel_response["items"][0]["statistics"].get("subscriberCount", 0))
        else:
            data["Inscritos no canal"] = 0
        dados_coletados.append(data)
    return dados_coletados

# Função para exportar os dados para CSV
def exportar_para_csv(dados):
    tz = pytz.timezone('America/Sao_Paulo')
    hora_atual = datetime.now(tz)
    nome_arquivo = hora_atual.strftime("%Y-%m-%d_%Hh%Mm") + ".csv"  # Nome do arquivo com data e hora
    caminho_arquivo = os.path.abspath(nome_arquivo)

    campos = [
        "Posicao na coleta", "Gênero do vídeo", "Tipo de produtor", "Categoria do vídeo", "guideCategory",
        "Taxa de engajamento", "Idioma", "Posicao Geral", "Id do canal", "Canal", "Inscritos no canal",
        "Id do vídeo", "Data de publicação", "Diferenca de horas entre postagem e coleta", "Título do vídeo",
        "Descrição do vídeo", "Tags do video", "Duração do vídeo", "Visualizações", "Gostei", "Comentários",
        "thumbnail_maxres", "Pais"
    ]
    with open(nome_arquivo, mode="w", newline="", encoding="utf-8") as arquivo_csv:
        escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=campos)
        escritor_csv.writeheader()
        escritor_csv.writerows(dados)
    logging.info(f"✅ Dados coletados e salvos em {caminho_arquivo}")

# Função principal
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
