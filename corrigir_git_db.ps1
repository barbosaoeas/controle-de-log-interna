# Script PowerShell para corrigir o problema do db.sqlite3 no Git

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🔧 CORRIGINDO PROBLEMA DO db.sqlite3 NO GIT" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Fazer backup do banco de dados
Write-Host ""
Write-Host "📦 1. Fazendo backup do banco de dados..." -ForegroundColor Yellow
if (Test-Path "db.sqlite3") {
    Copy-Item "db.sqlite3" "db.sqlite3.backup"
    Write-Host "✅ Backup criado: db.sqlite3.backup" -ForegroundColor Green
} else {
    Write-Host "⚠️  Arquivo db.sqlite3 não encontrado" -ForegroundColor Yellow
}

# 2. Remover do Git (mas manter localmente)
Write-Host ""
Write-Host "🗑️  2. Removendo db.sqlite3 do controle de versão..." -ForegroundColor Yellow
git rm --cached db.sqlite3 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Arquivo removido do Git" -ForegroundColor Green
} else {
    Write-Host "⚠️  Arquivo já foi removido ou não está no Git" -ForegroundColor Yellow
}

# 3. Commitar a remoção
Write-Host ""
Write-Host "💾 3. Commitando a remoção..." -ForegroundColor Yellow
git commit -m "Remove db.sqlite3 do controle de versão" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Commit realizado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Nada para commitar" -ForegroundColor Yellow
}

# 4. Fazer pull
Write-Host ""
Write-Host "📥 4. Fazendo git pull..." -ForegroundColor Yellow
git pull origin main

# 5. Fazer push
Write-Host ""
Write-Host "📤 5. Fazendo git push..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "✅ CONCLUÍDO!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "   - O arquivo db.sqlite3 agora está apenas localmente"
Write-Host "   - Ele não será mais rastreado pelo Git"
Write-Host "   - Cada ambiente terá seu próprio banco de dados"
Write-Host ""
Write-Host "💡 Dica: Em produção, use PostgreSQL ao invés de SQLite" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

