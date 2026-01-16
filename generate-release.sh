#!/bin/bash

CHANGELOG_PATH="app/CHANGELOG.md"
# Extrai a versão do topo do arquivo
VERSION=$(grep "🚀 Release" "$CHANGELOG_PATH" | head -n 1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')

if [ -z "$VERSION" ]; then
  echo "Erro: Versão não encontrada no topo de $CHANGELOG_PATH"
  exit 1
fi

LAST_TAG=$(git tag --sort=-creatordate | head -n 1)
RANGE="${LAST_TAG:+$LAST_TAG..}HEAD"

OUTPUT="RELEASE_v${VERSION}.md"
echo "" > "$OUTPUT" # Começa com uma linha em branco para espaçamento

add_section () {
  TITLE=$1
  PREFIX=$2
  # Busca commits com o prefixo
  COMMITS=$(git log $RANGE --pretty=format:"- %s" | grep "^- ${PREFIX}:")
  if [ -n "$COMMITS" ]; then
    echo "### ${TITLE}" >> "$OUTPUT"
    echo "$COMMITS" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
}

add_section "✨ Novas Funcionalidades" "feat"
add_section "🐛 Correções" "fix"
add_section "🔧 Melhorias" "refactor"
add_section "🧹 Manutenção" "chore"

# SEÇÃO EXTRA: Pega tudo que NÃO tem os prefixos acima
OTHERS=$(git log $RANGE --pretty=format:"- %s" | grep -vE "^- (feat|fix|refactor|chore|docs|perf):")
if [ -n "$OTHERS" ]; then
  echo "### 📝 Outras Alterações" >> "$OUTPUT"
  echo "$OTHERS" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

echo "### 📦 Commit range" >> "$OUTPUT"
echo "\`$RANGE\`" >> "$OUTPUT"
echo "" >> "$OUTPUT" # Linha em branco final para separar da versão anterior

echo "✅ Gerado: $OUTPUT (Range: $RANGE)"