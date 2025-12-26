#!/bin/bash

echo "🚀 Executando makemigrations..."
echo "--------------------------------"

docker compose exec travel_web python manage.py makemigrations
STATUS=$?

echo "--------------------------------"

# Verifica se o primeiro comando falhou
if [ $STATUS -ne 0 ]; then
    echo "❌ Erro ao executar makemigrations. Abortando."
    exit 1
fi

echo ""
read -p "✅ Deseja executar o migrate agora? (s/n): " CONFIRM

case "$CONFIRM" in
    s|S|y|Y)
        echo ""
        echo "🚀 Executando migrate..."
        docker compose exec travel_web python manage.py migrate
        ;;
    *)
        echo "⏹️  Migrate cancelado pelo usuário."
        ;;
esac
