"""
Script para criar usuário mecânico de teste
Execute: python manage.py shell < criar_mecanico_teste.py
"""

from django.contrib.auth.models import User
from core.models import PerfilUsuario, Empresa

# Verificar se empresa Lokar existe, senão criar
try:
    empresa_lokar = Empresa.objects.get(nome__icontains='Lokar')
    print(f"✅ Empresa encontrada: {empresa_lokar.nome}")
except Empresa.DoesNotExist:
    # Criar empresa Lokar
    empresa_lokar = Empresa.objects.create(
        nome='Lokar Locações',
        tipo='TERCEIRIZADA',
        ativo=True
    )
    print(f"✅ Empresa criada: {empresa_lokar.nome}")

# Verificar se usuário já existe
if User.objects.filter(username='joao.lokar').exists():
    print("⚠️  Usuário 'joao.lokar' já existe. Atualizando senha...")
    user = User.objects.get(username='joao.lokar')
    user.set_password('123456')
    user.save()
    print("✅ Senha atualizada para '123456'")
else:
    # Criar usuário
    user = User.objects.create_user(
        username='joao.lokar',
        email='joao@lokar.com.br',
        password='123456',
        first_name='João',
        last_name='Silva'
    )
    print(f"✅ Usuário criado: {user.username}")

# Verificar se perfil existe
if hasattr(user, 'perfil'):
    print(f"⚠️  Perfil já existe. Atualizando...")
    perfil = user.perfil
    perfil.perfil = 'TERCEIRO_MANUTENCAO_PTA'
    perfil.empresa = empresa_lokar
    perfil.disponivel = True
    perfil.save()
    print(f"✅ Perfil atualizado: {perfil.get_perfil_display()}")
else:
    # Criar perfil
    perfil = PerfilUsuario.objects.create(
        usuario=user,
        perfil='TERCEIRO_MANUTENCAO_PTA',
        empresa=empresa_lokar,
        disponivel=True
    )
    print(f"✅ Perfil criado: {perfil.get_perfil_display()}")

print("\n" + "="*60)
print("🎉 USUÁRIO MECÂNICO CRIADO COM SUCESSO!")
print("="*60)
print(f"Username: joao.lokar")
print(f"Senha: 123456")
print(f"Nome: {user.get_full_name()}")
print(f"Perfil: {perfil.get_perfil_display()}")
print(f"Empresa: {perfil.empresa.nome}")
print(f"Disponível: {'Sim' if perfil.disponivel else 'Não'}")
print("="*60)
print("\n✅ Agora você pode fazer login com:")
print("   Username: joao.lokar")
print("   Senha: 123456")
print("\n🔧 Acesse: Menu → Meus Chamados")
print("="*60)

