# ⚙️ CONFIGURAÇÃO DE AMBIENTE - DESENVOLVIMENTO vs PRODUÇÃO

**Data:** 2026-02-19  
**Objetivo:** Configurar corretamente o ambiente de desenvolvimento e produção

---

## 🔧 PROBLEMA COMUM

Quando você faz alterações nos templates/arquivos estáticos e eles não aparecem no navegador, geralmente é porque:

1. ❌ O servidor está em modo **produção** (DEBUG=False)
2. ❌ Cache do navegador
3. ❌ Arquivos estáticos não foram coletados

---

## 🏠 DESENVOLVIMENTO (Local)

### **Configuração Recomendada:**

**Opção 1: Sem arquivo .env (mais simples)**

Não precisa fazer nada! O `settings.py` já está configurado com valores padrão para desenvolvimento:
- ✅ `DEBUG = True` (padrão)
- ✅ `ALLOWED_HOSTS = localhost,127.0.0.1`
- ✅ Email vai para console (não envia de verdade)

**Opção 2: Com arquivo .env (mais profissional)**

1. Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

2. Edite o `.env`:
```bash
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1
```

### **Como rodar em desenvolvimento:**

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Rodar servidor
python manage.py runserver
```

### **Características do modo desenvolvimento:**

- ✅ `DEBUG = True` - Mostra erros detalhados
- ✅ Arquivos estáticos servidos automaticamente
- ✅ Alterações em templates aparecem imediatamente
- ✅ Não precisa rodar `collectstatic`
- ✅ Email vai para console (não envia de verdade)
- ✅ Recarregamento automático ao salvar arquivos

---

## 🌐 PRODUÇÃO (PythonAnywhere)

### **Configuração no PythonAnywhere:**

1. Vá para a aba **"Web"**
2. Clique em **"Go to directory"** ao lado de "Source code"
3. Edite o arquivo de configuração WSGI ou configure variáveis de ambiente

### **Opção 1: Configurar no painel Web do PythonAnywhere**

Na aba **"Web"** → seção **"Environment variables"**:

```
DEBUG = False
DJANGO_ENV = production
ALLOWED_HOSTS = easmanutencao.pythonanywhere.com
SECRET_KEY = [gere uma chave secreta forte]
EMAIL_HOST_USER = sistema.estaleiro@gmail.com
EMAIL_HOST_PASSWORD = [sua senha de app do Gmail]
```

### **Opção 2: Criar arquivo .env no servidor**

```bash
cd ~/controle-de-log-interna
nano .env
```

Conteúdo:
```bash
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=easmanutencao.pythonanywhere.com
SECRET_KEY=sua-chave-secreta-forte-aqui
EMAIL_HOST_USER=sistema.estaleiro@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
```

### **Após fazer alterações em produção:**

```bash
# 1. Fazer git pull
cd ~/controle-de-log-interna
git pull origin main

# 2. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 3. Recarregar aplicação
# Vá para aba "Web" e clique em "Reload"
```

### **Características do modo produção:**

- ✅ `DEBUG = False` - Não mostra erros detalhados
- ✅ Arquivos estáticos servidos de `/staticfiles/`
- ✅ Precisa rodar `collectstatic` após alterações
- ✅ Email é enviado de verdade
- ✅ Mais seguro e performático

---

## 🔄 WORKFLOW RECOMENDADO

### **1. Desenvolvimento Local:**

```bash
# Fazer alterações
# Testar localmente
python manage.py runserver

# Commitar
git add .
git commit -m "Descrição das alterações"
git push origin main
```

### **2. Deploy para Produção:**

```bash
# No servidor PythonAnywhere
cd ~/controle-de-log-interna
git pull origin main
python manage.py collectstatic --noinput
# Clicar em "Reload" na aba Web
```

---

## 🐛 TROUBLESHOOTING

### **Problema: Alterações não aparecem no navegador**

**Desenvolvimento:**
- ✅ Verificar se `DEBUG=True`
- ✅ Limpar cache: `Ctrl + Shift + R`
- ✅ Verificar se o servidor está rodando

**Produção:**
- ✅ Rodar `collectstatic`
- ✅ Recarregar aplicação no painel Web
- ✅ Limpar cache: `Ctrl + Shift + R`

### **Problema: Erro 500 em produção**

- ✅ Verificar se `DEBUG=False`
- ✅ Verificar se `ALLOWED_HOSTS` está correto
- ✅ Ver logs de erro no PythonAnywhere

---

## 📋 CHECKLIST

### **Antes de fazer deploy:**

- [ ] Testar localmente com `DEBUG=True`
- [ ] Commitar e fazer push
- [ ] No servidor: `git pull`
- [ ] No servidor: `collectstatic`
- [ ] Recarregar aplicação
- [ ] Testar no navegador com `Ctrl + Shift + R`

---

## 💡 DICAS

1. **Nunca** commite o arquivo `.env` no Git (já está no `.gitignore`)
2. Use `DEBUG=True` apenas em desenvolvimento
3. Em produção, sempre rode `collectstatic` após alterações em CSS/JS
4. Sempre limpe o cache do navegador após deploy
5. Mantenha a `SECRET_KEY` diferente em produção

---

## 🎯 RESUMO RÁPIDO

| Aspecto | Desenvolvimento | Produção |
|---------|----------------|----------|
| DEBUG | `True` | `False` |
| ALLOWED_HOSTS | `localhost,127.0.0.1` | `easmanutencao.pythonanywhere.com` |
| Arquivos estáticos | Automático | Precisa `collectstatic` |
| Email | Console | SMTP real |
| Recarregamento | Automático | Manual (Reload) |
| Segurança | Relaxada | Rigorosa |

