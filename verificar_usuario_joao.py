"""
Script para verificar e corrigir usuário joao.lokar
Execute: python manage.py shell < verificar_usuario_joao.py
"""

from django.contrib.auth.models import User
from core.models import PerfilUsuario, Empresa

print("="*60)
print("🔍 VERIFICANDO USUÁRIO: joao.lokar")
print("="*60)

# Verificar se usuário existe
try:
    user = User.objects.get(username='joao.lokar')
    print(f"\n✅ Usuário encontrado!")
    print(f"   ID: {user.id}")
    print(f"   Username: {user.username}")
    print(f"   Nome: {user.get_full_name() or '(não definido)'}")
    print(f"   Email: {user.email or '(não definido)'}")
    print(f"   Ativo: {'✅ Sim' if user.is_active else '❌ Não'}")
    print(f"   Staff: {'✅ Sim' if user.is_staff else '❌ Não'}")
    print(f"   Superuser: {'✅ Sim' if user.is_superuser else '❌ Não'}")
    
    # Ativar usuário se estiver inativo
    if not user.is_active:
        user.is_active = True
        user.save()
        print("\n⚠️  Usuário estava inativo. ATIVADO agora!")
    
    # Resetar senha para 123456
    user.set_password('123456')
    user.save()
    print(f"\n✅ Senha resetada para: 123456")
    
    # Verificar perfil
    print("\n" + "-"*60)
    print("🔍 VERIFICANDO PERFIL")
    print("-"*60)
    
    if hasattr(user, 'perfil'):
        perfil = user.perfil
        print(f"\n✅ Perfil encontrado!")
        print(f"   Perfil: {perfil.perfil} ({perfil.get_perfil_display()})")
        print(f"   Empresa: {perfil.empresa.nome if perfil.empresa else '❌ NÃO VINCULADO'}")
        print(f"   Disponível: {'✅ Sim' if perfil.disponivel else '❌ Não'}")
        
        # Verificar se precisa atualizar
        precisa_atualizar = False
        
        # Verificar empresa
        if not perfil.empresa:
            print("\n⚠️  PROBLEMA: Usuário não está vinculado a nenhuma empresa!")
            print("   Buscando empresa Lokar...")
            
            try:
                empresa_lokar = Empresa.objects.filter(nome__icontains='Lokar').first()
                if empresa_lokar:
                    perfil.empresa = empresa_lokar
                    precisa_atualizar = True
                    print(f"   ✅ Empresa encontrada: {empresa_lokar.nome}")
                else:
                    print("   ❌ Empresa Lokar não encontrada!")
                    print("   📝 Empresas disponíveis:")
                    for emp in Empresa.objects.filter(ativo=True):
                        print(f"      - {emp.nome} ({emp.tipo})")
            except Exception as e:
                print(f"   ❌ Erro ao buscar empresa: {e}")
        
        # Verificar se é perfil de terceiro
        if not perfil.perfil.startswith('TERCEIRO_'):
            print(f"\n⚠️  PROBLEMA: Perfil atual é '{perfil.perfil}', não é TERCEIRO!")
            print("   Deseja alterar para TERCEIRO_MANUTENCAO_PTA? (será alterado automaticamente)")
            perfil.perfil = 'TERCEIRO_MANUTENCAO_PTA'
            precisa_atualizar = True
        
        # Verificar disponibilidade
        if not perfil.disponivel:
            print("\n⚠️  PROBLEMA: Mecânico marcado como INDISPONÍVEL!")
            perfil.disponivel = True
            precisa_atualizar = True
        
        # Salvar alterações
        if precisa_atualizar:
            perfil.save()
            print("\n✅ Perfil atualizado com sucesso!")
        
    else:
        print("\n❌ PROBLEMA: Usuário não tem perfil!")
        print("   Criando perfil...")
        
        # Buscar empresa Lokar
        empresa_lokar = Empresa.objects.filter(nome__icontains='Lokar').first()
        
        if not empresa_lokar:
            print("   ⚠️  Empresa Lokar não encontrada. Criando...")
            empresa_lokar = Empresa.objects.create(
                nome='Lokar Locações',
                tipo='TERCEIRIZADA',
                ativo=True
            )
            print(f"   ✅ Empresa criada: {empresa_lokar.nome}")
        
        # Criar perfil
        perfil = PerfilUsuario.objects.create(
            usuario=user,
            perfil='TERCEIRO_MANUTENCAO_PTA',
            empresa=empresa_lokar,
            disponivel=True
        )
        print(f"   ✅ Perfil criado: {perfil.get_perfil_display()}")
    
    # Resumo final
    print("\n" + "="*60)
    print("🎉 CONFIGURAÇÃO FINAL")
    print("="*60)
    print(f"Username: {user.username}")
    print(f"Senha: 123456")
    print(f"Nome: {user.get_full_name() or user.username}")
    print(f"Ativo: {'✅ Sim' if user.is_active else '❌ Não'}")
    print(f"Perfil: {perfil.get_perfil_display()}")
    print(f"Empresa: {perfil.empresa.nome if perfil.empresa else '❌ Não vinculado'}")
    print(f"Disponível: {'✅ Sim' if perfil.disponivel else '❌ Não'}")
    print("="*60)
    
    # Verificar se pode acessar "Meus Chamados"
    print("\n🔍 VERIFICANDO ACESSO À PÁGINA 'MEUS CHAMADOS'")
    print("-"*60)
    
    pode_acessar = True
    problemas = []
    
    if not user.is_active:
        pode_acessar = False
        problemas.append("❌ Usuário inativo")
    
    if not hasattr(user, 'perfil'):
        pode_acessar = False
        problemas.append("❌ Sem perfil")
    elif not (perfil.perfil.startswith('TERCEIRO_') or perfil.perfil in ['ADMIN', 'SUPERVISOR']):
        pode_acessar = False
        problemas.append(f"❌ Perfil '{perfil.perfil}' não tem acesso")
    
    if perfil.perfil.startswith('TERCEIRO_') and not perfil.empresa:
        pode_acessar = False
        problemas.append("❌ Sem empresa vinculada")
    
    if pode_acessar:
        print("✅ PODE ACESSAR 'MEUS CHAMADOS'!")
        print("\n📝 Instruções:")
        print("   1. Acesse: http://127.0.0.1:8000/")
        print("   2. Faça login:")
        print(f"      Username: {user.username}")
        print("      Senha: 123456")
        print("   3. Clique no menu: 🔧 Meus Chamados")
    else:
        print("❌ NÃO PODE ACESSAR 'MEUS CHAMADOS'!")
        print("\n⚠️  Problemas encontrados:")
        for problema in problemas:
            print(f"   {problema}")
    
    print("="*60)

except User.DoesNotExist:
    print("\n❌ ERRO: Usuário 'joao.lokar' não encontrado!")
    print("\n📝 Usuários disponíveis:")
    for u in User.objects.all()[:10]:
        print(f"   - {u.username} ({u.get_full_name() or 'sem nome'})")
    print("\n💡 Dica: Crie o usuário através do admin ou cadastro de usuários")
    print("="*60)

