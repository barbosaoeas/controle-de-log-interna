# 🚀 GUIA SIMPLES DE DEPLOY

**Use este guia SEMPRE que fizer alterações no código!**

---

## 📋 CHECKLIST RÁPIDO

### ✅ **PASSO 1: NO SEU COMPUTADOR (LOCAL)**

```bash
# 1. Ver o que mudou
git status

# 2. Adicionar tudo
git add .

# 3. Commitar
git commit -m "Descrição do que você fez"

# 4. Enviar para o GitHub
git push origin main
```

---

### ✅ **PASSO 2: NO PYTHONANYWHERE (PRODUÇÃO)**

```bash
# 1. Ir para a pasta do projeto
cd ~/controle-de-log-interna

# 2. Ativar ambiente virtual
source ~/.virtualenvs/venv/bin/activate

# 3. Puxar alterações do GitHub
git pull origin main

# 4. Coletar arquivos estáticos (CSS, JS, imagens)
python manage.py collectstatic --noinput

# 5. Aplicar mudanças no banco de dados
python manage.py migrate
```

---

### ✅ **PASSO 3: RECARREGAR O SITE**

1. Vá para a aba **"Web"** no PythonAnywhere
2. Clique no botão verde **"Reload easmanutencao.pythonanywhere.com"**
3. Aguarde 5-10 segundos

---

### ✅ **PASSO 4: TESTAR NO NAVEGADOR**

1. Abra: `https://easmanutencao.pythonanywhere.com`
2. Pressione **`Ctrl + Shift + R`** (limpa o cache)
3. Teste suas alterações

---

## 🆘 PROBLEMAS COMUNS

### ❌ **Problema 1: "error: Your local changes would be overwritten"**

**Solução:**
```bash
git reset --hard origin/main
git pull origin main
```

---

### ❌ **Problema 2: Alterações não aparecem no site**

**Solução:**
```bash
# No PythonAnywhere
python manage.py collectstatic --noinput

# Depois: Reload na aba Web
# Depois: Ctrl + Shift + R no navegador
```

---

### ❌ **Problema 3: Erro 403 CSRF**

**Solução:**
- Verifique se tem `{% csrf_token %}` nos formulários HTML
- Verifique se tem `'X-CSRFToken': getCookieLocal('csrftoken')` nas requisições AJAX

---

### ❌ **Problema 4: Erro 500 no site**

**Solução:**
```bash
# Ver os logs de erro
tail -n 50 /var/log/easmanutencao.pythonanywhere.com.error.log
```

---

## 🎯 RESUMO ULTRA-RÁPIDO

### **LOCAL (seu computador):**
```bash
git add .
git commit -m "mensagem"
git push origin main
```

### **PYTHONANYWHERE (servidor):**
```bash
cd ~/controle-de-log-interna
source ~/.virtualenvs/venv/bin/activate
git pull origin main
python manage.py collectstatic --noinput
python manage.py migrate
```

### **PAINEL WEB:**
- Clicar em **"Reload"**

### **NAVEGADOR:**
- **`Ctrl + Shift + R`**

---

## 💡 DICAS IMPORTANTES

### ✅ **SEMPRE faça nesta ordem:**

1. **LOCAL** → Commit e Push
2. **PYTHONANYWHERE** → Pull e Collectstatic
3. **PAINEL WEB** → Reload
4. **NAVEGADOR** → Ctrl + Shift + R

### ✅ **NUNCA pule o collectstatic**

Se você alterou:
- Templates HTML
- Arquivos CSS
- Arquivos JavaScript
- Imagens

**SEMPRE rode:** `python manage.py collectstatic --noinput`

### ✅ **SEMPRE limpe o cache do navegador**

Depois de fazer Reload, **SEMPRE** pressione `Ctrl + Shift + R` no navegador.

---

## 📱 COMANDOS SALVOS (COPIAR E COLAR)

### **Para o seu computador:**
```bash
git add . && git commit -m "Atualização" && git push origin main
```

### **Para o PythonAnywhere:**
```bash
cd ~/controle-de-log-interna && source ~/.virtualenvs/venv/bin/activate && git pull origin main && python manage.py collectstatic --noinput && python manage.py migrate
```

---

## 🎓 ENTENDENDO O PROCESSO

### **Por que preciso fazer tudo isso?**

1. **`git add .`** - Prepara os arquivos para serem salvos
2. **`git commit`** - Salva as alterações localmente
3. **`git push`** - Envia para o GitHub (nuvem)
4. **`git pull`** - Baixa do GitHub para o servidor
5. **`collectstatic`** - Copia CSS/JS para a pasta correta
6. **`migrate`** - Atualiza o banco de dados
7. **Reload** - Reinicia o servidor web
8. **Ctrl+Shift+R** - Limpa cache do navegador

---

## ✅ CHECKLIST FINAL

Antes de considerar o deploy completo:

- [ ] Fiz `git push` no meu computador?
- [ ] Fiz `git pull` no PythonAnywhere?
- [ ] Rodei `collectstatic`?
- [ ] Rodei `migrate`?
- [ ] Cliquei em "Reload" no painel Web?
- [ ] Pressionei `Ctrl + Shift + R` no navegador?
- [ ] Testei a funcionalidade que alterei?

---

## 🎉 PRONTO!

**Salve este arquivo e consulte sempre que precisar fazer deploy!**

**Dica:** Imprima ou deixe aberto em outra aba enquanto faz deploy! 📌

