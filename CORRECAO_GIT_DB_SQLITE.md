# 🔧 CORREÇÃO: Conflito do db.sqlite3 no Git

**Data:** 2026-02-19  
**Problema:** Erro ao fazer `git pull` devido a conflito no arquivo `db.sqlite3`

---

## ❌ ERRO ENCONTRADO

```
error: Your local changes to the following files would be overwritten by merge:
        db.sqlite3
Please commit your changes or stash them before you merge.
Aborting
```

---

## 🔍 CAUSA DO PROBLEMA

O arquivo `db.sqlite3` (banco de dados SQLite) está sendo rastreado pelo Git, mas **NÃO DEVERIA**!

### **Por que isso é um problema?**

1. ❌ Bancos de dados são **específicos de cada ambiente**
2. ❌ Cada desenvolvedor/servidor deve ter seu próprio banco
3. ❌ Causa conflitos constantes no Git
4. ❌ Arquivo binário grande que não deveria estar no repositório
5. ❌ Dados de desenvolvimento não devem ir para produção

### **O que DEVE estar no Git:**

- ✅ Código fonte (`.py`, `.html`, `.css`, `.js`)
- ✅ Migrações do Django (`migrations/`)
- ✅ Arquivos de configuração (`.gitignore`, `requirements.txt`)
- ✅ Documentação (`.md`)

### **O que NÃO DEVE estar no Git:**

- ❌ Banco de dados (`db.sqlite3`)
- ❌ Arquivos de mídia (`media/`)
- ❌ Arquivos estáticos coletados (`staticfiles/`)
- ❌ Ambiente virtual (`venv/`)
- ❌ Cache Python (`__pycache__/`)

---

## ✅ SOLUÇÃO

### **Opção 1: Script Automático (Recomendado)**

**Windows (PowerShell):**
```powershell
.\corrigir_git_db.ps1
```

**Linux/Mac:**
```bash
bash corrigir_git_db.sh
```

### **Opção 2: Comandos Manuais**

```bash
# 1. Fazer backup do banco de dados local
cp db.sqlite3 db.sqlite3.backup

# 2. Remover do Git (mas manter localmente)
git rm --cached db.sqlite3

# 3. Commitar a remoção
git commit -m "Remove db.sqlite3 do controle de versão"

# 4. Fazer pull
git pull origin main

# 5. Fazer push
git push origin main
```

### **Opção 3: Solução Rápida (Se não tem dados importantes)**

```bash
# Descartar alterações locais no db.sqlite3
git checkout -- db.sqlite3
git pull origin main
```

**OU**

```bash
# Guardar alterações temporariamente
git stash
git pull origin main
```

---

## 🎯 RESULTADO ESPERADO

Após executar a solução:

✅ O arquivo `db.sqlite3` não será mais rastreado pelo Git  
✅ Cada ambiente terá seu próprio banco de dados  
✅ Não haverá mais conflitos no `git pull`  
✅ O arquivo continua existindo localmente  

---

## 📋 VERIFICAÇÃO

Para confirmar que funcionou:

```bash
# Verificar status do Git
git status

# Não deve aparecer db.sqlite3 na lista de arquivos modificados
```

---

## 🔄 WORKFLOW CORRETO APÓS A CORREÇÃO

### **Desenvolvimento Local:**

```bash
# Fazer alterações no código
git add .
git commit -m "Descrição das alterações"
git push origin main
```

### **Produção (PythonAnywhere):**

```bash
cd ~/controle-de-log-interna
git pull origin main
python manage.py migrate  # Aplicar migrações
python manage.py collectstatic --noinput
# Clicar em "Reload" na aba Web
```

---

## 💡 BOAS PRÁTICAS

### **1. Banco de Dados em Desenvolvimento:**

- Use SQLite localmente (`db.sqlite3`)
- Cada desenvolvedor tem seu próprio banco
- Não commite no Git

### **2. Banco de Dados em Produção:**

- Use PostgreSQL ou MySQL
- Configure via variável de ambiente `DATABASE_URL`
- Faça backups regulares

### **3. Sincronização de Dados:**

Se precisar compartilhar dados entre ambientes:

```bash
# Exportar dados (fixtures)
python manage.py dumpdata > dados.json

# Importar dados
python manage.py loaddata dados.json
```

---

## 🚨 IMPORTANTE

### **Após a correção, NUNCA mais:**

❌ Faça `git add db.sqlite3`  
❌ Commite o banco de dados  
❌ Force o push do db.sqlite3  

### **O .gitignore já está configurado:**

O arquivo `.gitignore` já contém:
```
db.sqlite3
db.sqlite3-journal
```

Isso garante que o Git ignore automaticamente esses arquivos.

---

## 🎓 ENTENDENDO O PROBLEMA

### **Por que o db.sqlite3 estava no Git?**

Provavelmente foi adicionado acidentalmente no início do projeto com:
```bash
git add .  # Isso adiciona TUDO, incluindo o que não deveria
```

### **Como evitar no futuro?**

1. ✅ Sempre verifique o `.gitignore` antes de commitar
2. ✅ Use `git status` para ver o que será commitado
3. ✅ Use `git add` específico ao invés de `git add .`
4. ✅ Revise os arquivos antes de fazer push

---

## 📞 SUPORTE

Se o problema persistir:

1. Verifique se o `.gitignore` contém `db.sqlite3`
2. Execute `git status` e me envie o resultado
3. Execute `git log -1` para ver o último commit
4. Verifique se há outros arquivos em conflito

---

## ✅ CHECKLIST FINAL

Após executar a solução, verifique:

- [ ] `git status` não mostra `db.sqlite3`
- [ ] `git pull` funciona sem erros
- [ ] Arquivo `db.sqlite3` ainda existe localmente
- [ ] Aplicação funciona normalmente
- [ ] `.gitignore` contém `db.sqlite3`

---

**🎉 Problema resolvido! Agora você pode fazer `git pull` sem conflitos!**

