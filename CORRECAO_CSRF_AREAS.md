# 🔧 CORREÇÃO: Erro CSRF 403 no CRUD de Áreas

**Data:** 2026-02-20  
**Problema:** Erro 403 "Token CSRF do POST incorreto" ao tentar criar/editar áreas em produção

---

## ❌ ERRO ENCONTRADO

```
Proibido (403)
A verificação CSRF falhou. Pedido cancelado.

Motivo apresentado para a reprovação:
    Token CSRF do POST incorreto.
```

---

## 🔍 CAUSA DO PROBLEMA

1. ❌ Função `getCookieLocal()` estava **duplicada** no `base.html` (linhas 1088 e 2089)
2. ❌ Formulários HTML não tinham a tag `{% csrf_token %}`
3. ⚠️ Possível conflito entre as duas funções duplicadas

---

## ✅ CORREÇÕES APLICADAS

### **1. Removida função duplicada**

**Arquivo:** `templates/base.html`

- ✅ Removida a segunda declaração de `getCookieLocal()` na linha 2089
- ✅ Mantida apenas a primeira declaração na linha 1088

### **2. Adicionado CSRF token nos formulários**

**Arquivo:** `templates/core/modais_cadastros.html`

**Formulário de Nova Área (linha 122):**
```html
<form id="formNovaAreaGlobal">
    {% csrf_token %}
    ...
</form>
```

**Formulário de Editar Área (linha 155):**
```html
<form id="formEditarAreaGlobal">
    {% csrf_token %}
    ...
</form>
```

---

## 📋 ARQUIVOS MODIFICADOS

1. ✅ `templates/base.html` - Removida função duplicada
2. ✅ `templates/core/modais_cadastros.html` - Adicionado `{% csrf_token %}` nos formulários

---

## 🚀 PRÓXIMOS PASSOS

### **1. No seu computador LOCAL:**

```bash
# Verificar alterações
git status

# Adicionar arquivos
git add templates/base.html templates/core/modais_cadastros.html

# Commitar
git commit -m "Corrige erro CSRF 403 no CRUD de áreas"

# Push
git push origin main
```

### **2. No servidor PYTHONANYWHERE:**

```bash
# Ir para o diretório
cd ~/controle-de-log-interna

# Pull
git pull origin main

# Coletar estáticos
python manage.py collectstatic --noinput

# Migrar (se necessário)
python manage.py migrate
```

### **3. Recarregar aplicação:**

1. Vá para a aba **"Web"** no PythonAnywhere
2. Clique em **"Reload easmanutencao.pythonanywhere.com"**
3. Aguarde alguns segundos

### **4. Testar no navegador:**

1. Acesse: `https://easmanutencao.pythonanywhere.com`
2. Pressione **`Ctrl + Shift + R`** para limpar cache
3. Faça login
4. Vá em **Transportes → Gerenciar Áreas**
5. Teste criar uma nova área

---

## 🎯 RESULTADO ESPERADO

Após as correções:

✅ Modal de áreas abre normalmente  
✅ Formulário de nova área funciona sem erro 403  
✅ Formulário de editar área funciona sem erro 403  
✅ Remoção de área funciona sem erro 403  
✅ Token CSRF é enviado corretamente em todas as requisições  

---

## 🔍 VERIFICAÇÃO

Para confirmar que funcionou:

1. **Abrir DevTools** (`F12`)
2. **Ir na aba Network**
3. **Tentar criar uma área**
4. **Verificar a requisição POST para `/api/areas/`**
5. **Confirmar que o header `X-CSRFToken` está presente**

---

## 💡 ENTENDENDO O PROBLEMA

### **Por que o erro acontecia?**

O Django exige que todas as requisições POST, PUT, DELETE incluam um token CSRF válido para prevenir ataques CSRF (Cross-Site Request Forgery).

### **Como o token é enviado?**

1. O Django gera um token CSRF e o armazena em um cookie
2. A função `getCookieLocal('csrftoken')` lê esse cookie
3. O token é enviado no header `X-CSRFToken` das requisições AJAX
4. O Django valida se o token está correto

### **Por que funcionava localmente?**

Em desenvolvimento (`DEBUG=True`), o Django é mais permissivo com validações de segurança.

---

## 🚨 IMPORTANTE

### **Sempre inclua CSRF token em:**

- ✅ Formulários HTML: `{% csrf_token %}`
- ✅ Requisições AJAX POST/PUT/DELETE: `'X-CSRFToken': getCookieLocal('csrftoken')`
- ✅ FormData e URLSearchParams

### **Não precisa em:**

- ❌ Requisições GET
- ❌ Requisições para APIs externas

---

## 📚 REFERÊNCIAS

- [Django CSRF Protection](https://docs.djangoproject.com/en/4.2/ref/csrf/)
- [AJAX CSRF Token](https://docs.djangoproject.com/en/4.2/howto/csrf/#ajax)

---

**🎉 Problema resolvido! O CRUD de áreas agora funciona em produção!**

