"""
Script para resetar senha do usuário joao.lokar
Execute: python manage.py shell
Depois copie e cole este código
"""

from django.contrib.auth.models import User

# Buscar usuário
user = User.objects.get(username='joao.lokar')

# Resetar senha
user.set_password('123456')
user.save()

print("="*60)
print("✅ SENHA RESETADA COM SUCESSO!")
print("="*60)
print(f"Username: {user.username}")
print(f"Senha: 123456")
print("="*60)
print("\nAgora tente fazer login novamente!")

