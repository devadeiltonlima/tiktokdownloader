# Usar imagem leve do Python
FROM python:3.9-slim

# Instalar dependências do sistema (necessário para o moviepy/ffmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Variáveis de ambiente
ENV PORT=8080

# Comando para iniciar o servidor com o Gunicorn (Produção)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "app:app"]
