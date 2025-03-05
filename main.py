import googleapiclient.discovery
from datetime import datetime
import csv
import re
import os  # Adicione esta linha

def coletar_videos_populares(youtube):
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode="BR",
        maxResults=50
    )
    response = request.execute()
    return response["items"]

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
        print(f"Erro ao buscar guideCategory: {e}")
        return "N/A"

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

def exportar_para_csv(dados, nome_arquivo="dados_videos.csv"):
    campos = [
        "Posicao na coleta", "Gênero do vídeo", "Tipo de produtor", "Categoria do vídeo", "guideCategory",
        "Taxa de engajamento", "Idioma", "Posicao Geral", "Id do canal", "Canal", "Inscritos no canal",
        "Id do vídeo", "Data de publicação", "Diferenca de horas entre postagem e coleta", "Título do vídeo",
        "Descrição do vídeo", "Tags do video", "Duração do vídeo", "Visualizações", "Gostei", "Comentários",
        "thumbnail_maxres"
    ]
    with open(nome_arquivo, mode="w", newline="", encoding="utf-8") as arquivo_csv:
        escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=campos)
        escritor_csv.writeheader()
        escritor_csv.writerows(dados)
    print(f"✅ Dados coletados e salvos em {nome_arquivo}")

def main():
    API_KEY = os.environ.get("API_KEY")  # Use a chave de API do segredo
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
    videos = coletar_videos_populares(youtube)
    dados_coletados = processar_dados(youtube, videos)
    exportar_para_csv(dados_coletados)

if __name__ == "__main__":
    main()
