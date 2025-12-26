#!/bin/bash

# Nome do projeto
PROJECT_NAME="travel_manager"

echo "🚀 Iniciando a criação do projeto: $PROJECT_NAME..."

# 1. Cria a pasta raiz
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# 2. Cria estrutura de pastas básica
mkdir -p app          # Onde ficará o código Python/Django
mkdir -p db_data      # Persistência do Banco de Dados (Volume)

# 3. Cria o arquivo requirements.txt (Dependências Python)
cat <<EOF > app/requirements.txt
Django>=5.0
psycopg2-binary>=2.9
gunicorn>=21.0
python-decouple>=3.8
EOF

# 4. Cria o Dockerfile (Imagem da Aplicação)
cat <<EOF > app/Dockerfile
# Imagem base leve do Python
FROM python:3.11-slim

# Define variáveis de ambiente para o Python não gerar pyc e logs não ficarem presos no buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho no container
WORKDIR /usr/src/app

# Instala dependências do sistema necessárias para o PostGIS (caso use no futuro) e compilação
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia o projeto
COPY . .

# Comando padrão (será substituído pelo docker-compose em dev, mas útil para prod)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
EOF

# 5. Cria o docker-compose.yml (Orquestração dos Containers)
cat <<EOF > docker-compose.yml
services:
  # Container do Banco de Dados
  db:
    image: postgres:15-alpine
    container_name: ${PROJECT_NAME}_db
    volumes:
      - ./db_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=travel_db
      - POSTGRES_USER=travel_user
      - POSTGRES_PASSWORD=travel_pass
    ports:
      - "5432:5432"
    restart: always

  # Container da Aplicação (Backend + Frontend Django)
  web:
    build: ./app
    container_name: ${PROJECT_NAME}_web
    command: python manage.py runserver 0.0.0.0:8080
    volumes:
      - ./app:/usr/src/app
    ports:
      - "8000:8000"
    environment:
      - DEBUG=1
      - SECRET_KEY=changeme
      - DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
      - SQL_ENGINE=django.db.backends.postgresql
      - SQL_DATABASE=travel_db
      - SQL_USER=travel_user
      - SQL_PASSWORD=travel_pass
      - SQL_HOST=db
      - SQL_PORT=5432
    depends_on:
      - db
    restart: always

volumes:
  db_data:
EOF

echo "✅ Estrutura criada com sucesso!"
echo "------------------------------------------------"
echo "PRÓXIMOS PASSOS:"
echo "1. Entre na pasta: cd $PROJECT_NAME"
echo "2. Crie o projeto Django inicial: docker compose run --rm travel_web django-admin startproject config ."
echo "3. Suba os containers: docker compose up -d"
echo "4. Crie as tabelas do projeto Django: docker compose exec travel_web python manage.py migrate"
echo "5. Crie o superusuário: docker compose exec travel_web python manage.py createsuperuser"
echo "6. Acesse a aplicação em: http://localhost:8080"
echo "7. Acesse o admin do Django em: http://localhost:8080/admin"
echo "8. Crie o app dentro do Django: docker compose exec travel_web python manage.py startapp core"
echo "------------------------------------------------"
