#!/bin/bash

# =========================
# Configurações
# =========================
VERSION=$1
DATE=$(date +%Y-%m-%d)

if [ -z "$VERSION" ]; then
  echo "Uso: ./generate-release.sh vX.Y.Z"
  exit 1
fi

LAST_TAG=$(git tag --sort=-creatordate | head -n 1)

if [ -z "$LAST_TAG" ]; then
  RANGE="HEAD"
else
  RANGE="$LAST_TAG..HEAD"
fi

OUTPUT="RELEASE_${VERSION}.md"

echo "# 🚀 Release ${VERSION} — ${DATE}" > $OUTPUT
echo "" >> $OUTPUT

# =========================
# Função para seção
# =========================
add_section () {
  TITLE=$1
  PREFIX=$2

  COMMITS=$(git log $RANGE --pretty=format:"- %s" | grep "^- ${PREFIX}:")

  if [ -n "$COMMITS" ]; then
    echo "## ${TITLE}" >> $OUTPUT
    echo "$COMMITS" >> $OUTPUT
    echo "" >> $OUTPUT
  fi
}

add_section "✨ Novas Funcionalidades" "feat"
add_section "🐛 Correções" "fix"
add_section "🔧 Melhorias Técnicas" "refactor"
add_section "⚡ Performance" "perf"
add_section "🧹 Manutenção" "chore"
add_section "📚 Documentação" "docs"

echo "## 📦 Commit range" >> $OUTPUT
echo "\`${RANGE}\`" >> $OUTPUT

echo ""
echo "Release gerado em: ${OUTPUT}"
echo ""
