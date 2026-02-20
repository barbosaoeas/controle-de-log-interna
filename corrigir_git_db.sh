#!/bin/bash
# Script para corrigir o problema do db.sqlite3 no Git

echo "========================================================================"
echo "🔧 CORRIGINDO PROBLEMA DO db.sqlite3 NO GIT"
echo "========================================================================"

# 1. Fazer backup do banco de dados
echo ""
echo "📦 1. Fazendo backup do banco de dados..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 db.sqlite3.backup
    echo "✅ Backup criado: db.sqlite3.backup"
else
    echo "⚠️  Arquivo db.sqlite3 não encontrado"
fi

# 2. Remover do Git (mas manter localmente)
echo ""
echo "🗑️  2. Removendo db.sqlite3 do controle de versão..."
git rm --cached db.sqlite3 2>/dev/null || echo "⚠️  Arquivo já foi removido ou não está no Git"

# 3. Commitar a remoção
echo ""
echo "💾 3. Commitando a remoção..."
git commit -m "Remove db.sqlite3 do controle de versão" 2>/dev/null || echo "⚠️  Nada para commitar"

# 4. Fazer pull
echo ""
echo "📥 4. Fazendo git pull..."
git pull origin main

# 5. Fazer push
echo ""
echo "📤 5. Fazendo git push..."
git push origin main

echo ""
echo "========================================================================"
echo "✅ CONCLUÍDO!"
echo "========================================================================"
echo ""
echo "📋 Próximos passos:"
echo "   - O arquivo db.sqlite3 agora está apenas localmente"
echo "   - Ele não será mais rastreado pelo Git"
echo "   - Cada ambiente terá seu próprio banco de dados"
echo ""
echo "💡 Dica: Em produção, use PostgreSQL ao invés de SQLite"
echo "========================================================================"

