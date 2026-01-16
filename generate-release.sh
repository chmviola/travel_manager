#!/bin/bash

# Caminho para o Changelog dentro da pasta app
CHANGELOG_PATH="app/CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

# 1. Extrai a versão (Lê a primeira linha que contém "🚀 Release")
VERSION=$(grep "🚀 Release" "$CHANGELOG_PATH" | head -n 1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

if [ -z "$VERSION" ]; then
  echo "Erro: Não foi possível encontrar a versão em $CHANGELOG_PATH"
  exit 1
fi

echo "Gerando notas para v$VERSION..."

# 2. Pega a última tag
LAST_TAG=$(git tag --sort=-creatordate | head -n 1)
RANGE="${LAST_TAG:+$LAST_TAG..}HEAD"

OUTPUT="RELEASE_v${VERSION}.md"
echo "" > "$OUTPUT"

add_section () {
  COMMITS=$(git log $RANGE --pretty=format:"- %s" | grep "^- $2:")
  if [ -n "$COMMITS" ]; then
    echo "## $1" >> "$OUTPUT"
    echo "$COMMITS" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
}

add_section "✨ Novas Funcionalidades" "feat"
add_section "🐛 Correções" "fix"
add_section "🔧 Melhorias" "refactor"
add_section "🧹 Manutenção" "chore"

echo "## 📦 Commit range" >> "$OUTPUT"
echo "\`$RANGE\`" >> "$OUTPUT"

echo "✅ Release Note: $OUTPUT"