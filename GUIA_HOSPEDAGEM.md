# 🚀 GUIA COMPLETO PARA HOSPEDAGEM DO SISTEMA

## ✅ **PREPARAÇÕES JÁ FEITAS**

O sistema já foi configurado para produção com:
- ✅ Configurações dinâmicas baseadas em variáveis de ambiente
- ✅ Suporte a PostgreSQL e SQLite
- ✅ Configuração de arquivos estáticos
- ✅ Sistema de alertas por email
- ✅ Segurança configurada

## 📋 **CHECKLIST PARA HOSPEDAGEM**

### **1. 📧 CONFIGURAR EMAIL (OBRIGATÓRIO)**

#### **Passo 1: Criar conta Gmail**
```
1. Criar: sistema.estaleiro@gmail.com (ou similar)
2. Ativar autenticação de 2 fatores
3. Ir em: Conta Google → Segurança → Senhas de app
4. Gerar senha de app para "Sistema Estaleiro"
5. Anotar a senha gerada (ex: abcd efgh ijkl mnop)
```

#### **Passo 2: Configurar variáveis de ambiente**
```bash
# No servidor, definir estas variáveis:
DJANGO_ENV=production
EMAIL_HOST_USER=sistema.estaleiro@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
```

### **2. 🔒 CONFIGURAR SEGURANÇA**

#### **Variáveis de ambiente obrigatórias:**
```bash
SECRET_KEY=sua-chave-secreta-super-forte-aqui
DEBUG=False
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
DJANGO_ENV=production
```

#### **Gerar nova SECRET_KEY:**
```python
# Execute no Python:
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### **3. 🗄️ BANCO DE DADOS**

#### **Opção A: Continuar com SQLite (Simples)**
- Nenhuma configuração adicional necessária
- Adequado para uso interno da empresa
- Backup: copiar arquivo db.sqlite3

#### **Opção B: PostgreSQL (Recomendado para produção)**
```bash
# Variável de ambiente:
DATABASE_URL=postgres://usuario:senha@host:5432/nome_banco
```

### **4. 📁 ARQUIVOS ESTÁTICOS**

#### **Coletar arquivos estáticos:**
```bash
python manage.py collectstatic --noinput
```

### **5. 🏗️ DEPENDÊNCIAS**

#### **Instalar dependências de produção:**
```bash
pip install dj-database-url gunicorn whitenoise psycopg2-binary
```

#### **Arquivo requirements.txt:**
```
asgiref==3.9.1
Django==4.2.16
django-cors-headers==4.3.1
djangorestframework==3.14.0
et-xmlfile==2.0.0
openpyxl==3.1.5
Pillow==10.4.0
sqlparse==0.5.1
tzdata==2024.2
dj-database-url==2.1.0
gunicorn==21.2.0
whitenoise==6.6.0
psycopg2-binary==2.9.9
```

## 🌐 **OPÇÕES DE HOSPEDAGEM**

### **Opção 1: Heroku (Mais Fácil)**
```bash
# 1. Instalar Heroku CLI
# 2. Criar app
heroku create nome-do-app

# 3. Configurar variáveis
heroku config:set SECRET_KEY="sua-chave-secreta"
heroku config:set DEBUG=False
heroku config:set DJANGO_ENV=production
heroku config:set EMAIL_HOST_USER=sistema.estaleiro@gmail.com
heroku config:set EMAIL_HOST_PASSWORD="sua-senha-de-app"

# 4. Deploy
git push heroku main

# 5. Migrar banco
heroku run python manage.py migrate
heroku run python manage.py collectstatic --noinput
heroku run python manage.py createsuperuser
```

### **Opção 2: DigitalOcean/AWS/VPS**
```bash
# 1. Instalar dependências no servidor
sudo apt update
sudo apt install python3 python3-pip nginx postgresql

# 2. Clonar projeto
git clone seu-repositorio
cd projeto

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
export SECRET_KEY="sua-chave-secreta"
export DEBUG=False
export DJANGO_ENV=production
# ... outras variáveis

# 5. Migrar e coletar estáticos
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 6. Executar com Gunicorn
gunicorn controle_materiais.wsgi:application --bind 0.0.0.0:8000
```

### **Opção 3: Servidor Windows (IIS)**
```bash
# 1. Instalar Python no servidor
# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente no Windows
# 4. Usar wfastcgi ou similar para IIS
```

## 🧪 **TESTES APÓS HOSPEDAGEM**

### **1. Funcionalidades Básicas:**
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Abastecimento de veículos funciona
- [ ] Registrar chegada de diesel funciona
- [ ] Relatórios funcionam
- [ ] Export Excel funciona

### **2. Sistema de Alertas:**
- [ ] Configurar nível crítico (< 5000L)
- [ ] Testar botão "Testar Alerta"
- [ ] Verificar se email chegou em manutencao@easbr.com
- [ ] Testar alerta automático ao abastecer veículo

### **3. Segurança:**
- [ ] DEBUG=False em produção
- [ ] HTTPS configurado
- [ ] Apenas usuários autorizados acessam
- [ ] Backup do banco configurado

## 📞 **SUPORTE PÓS-HOSPEDAGEM**

### **Logs para Debug:**
```bash
# Ver logs do servidor
tail -f /var/log/nginx/error.log
tail -f /var/log/gunicorn/error.log

# Logs do Django
python manage.py shell -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### **Comandos Úteis:**
```bash
# Backup do banco SQLite
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3

# Reiniciar serviços
sudo systemctl restart nginx
sudo systemctl restart gunicorn

# Ver status
sudo systemctl status nginx
sudo systemctl status gunicorn
```

## 🎯 **RESUMO RÁPIDO**

**OBRIGATÓRIO ANTES DE HOSPEDAR:**
1. ✅ Criar email Gmail e gerar senha de app
2. ✅ Gerar nova SECRET_KEY
3. ✅ Definir ALLOWED_HOSTS com seu domínio
4. ✅ Configurar variáveis de ambiente
5. ✅ Testar sistema localmente com DJANGO_ENV=production

**APÓS HOSPEDAR:**
1. ✅ Executar migrações
2. ✅ Coletar arquivos estáticos
3. ✅ Criar superusuário
4. ✅ Testar alertas por email
5. ✅ Configurar backup automático

O sistema está **100% pronto** para hospedagem! 🚀
