# Imagem base leve do Python
FROM python:3.11-slim

# Define variáveis de ambiente para o Python não gerar pyc e logs não ficarem presos no buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho no container
WORKDIR /usr/src/app

# Instala dependências do sistema necessárias para o PostGIS (caso use no futuro) e compilação
RUN apt-get update && apt-get install -y     gcc     libpq-dev     && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia o projeto
COPY . .

# Comando padrão (será substituído pelo docker-compose em dev, mas útil para prod)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
