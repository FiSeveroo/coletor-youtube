# Usar uma imagem base do Python
FROM python:3.9-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos necessários para o container
COPY main.py .
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Instalar pytz (necessário para o fuso horário)
RUN pip install --no-cache-dir pytz

# Definir o comando que será executado quando o container iniciar
CMD ["python", "main.py"]
