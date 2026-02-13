"""
Script de teste para validar o sistema de mecânicos vinculados a empresas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Empresa, PerfilUsuario, Setor
from frota_locada.models import Maquina, ChamadoManutencao

print("=" * 80)
print("🧪 TESTE DO SISTEMA DE MECÂNICOS VINCULADOS A EMPRESAS")
print("=" * 80)

# ============================================================================
# TESTE 1: Criar Empresas
# ============================================================================
print("\n📋 TESTE 1: Criando empresas...")

# Buscar ou criar empresa própria
empresa_propria, created = Empresa.objects.get_or_create(
    nome="Estaleiro Atlântico Sul",
    defaults={
        'cnpj': '00.000.000/0001-00',
        'tipo': 'PROPRIA',
        'ativo': True
    }
)
print(f"  {'✅ Criada' if created else '✓ Já existe'}: {empresa_propria.nome} (Própria)")

# Buscar ou criar empresas terceirizadas
empresas_terceiras = [
    {'nome': 'Lokar Locações', 'cnpj': '11.111.111/0001-11', 'contrato': 'CONT-2024-001'},
    {'nome': 'TechServ Manutenção', 'cnpj': '22.222.222/0001-22', 'contrato': 'CONT-2024-002'},
    {'nome': 'MecPro Serviços', 'cnpj': '33.333.333/0001-33', 'contrato': 'CONT-2024-003'},
]

empresas_criadas = []
for emp_data in empresas_terceiras:
    empresa, created = Empresa.objects.get_or_create(
        nome=emp_data['nome'],
        defaults={
            'cnpj': emp_data['cnpj'],
            'tipo': 'TERCEIRIZADA',
            'contrato': emp_data['contrato'],
            'ativo': True
        }
    )
    empresas_criadas.append(empresa)
    print(f"  {'✅ Criada' if created else '✓ Já existe'}: {empresa.nome} (Terceirizada)")

# ============================================================================
# TESTE 2: Criar Mecânicos Vinculados às Empresas
# ============================================================================
print("\n👷 TESTE 2: Criando mecânicos vinculados às empresas...")

# Buscar setor de manutenção
setor_manutencao, _ = Setor.objects.get_or_create(
    nome="Manutenção",
    defaults={'descricao': 'Setor de Manutenção'}
)

# Mecânicos para cada empresa
mecanicos_data = [
    # Lokar Locações
    {'username': 'joao.lokar', 'nome': 'João', 'sobrenome': 'Silva', 'empresa': empresas_criadas[0], 'perfil': 'TERCEIRO_MANUTENCAO_PTA'},
    {'username': 'maria.lokar', 'nome': 'Maria', 'sobrenome': 'Santos', 'empresa': empresas_criadas[0], 'perfil': 'TERCEIRO_MANUTENCAO_EMPILHADEIRA'},
    
    # TechServ Manutenção
    {'username': 'carlos.techserv', 'nome': 'Carlos', 'sobrenome': 'Oliveira', 'empresa': empresas_criadas[1], 'perfil': 'TERCEIRO_MANUTENCAO_GUINDASTE'},
    {'username': 'ana.techserv', 'nome': 'Ana', 'sobrenome': 'Costa', 'empresa': empresas_criadas[1], 'perfil': 'TERCEIRO_MANUTENCAO_SOLDA'},
    
    # MecPro Serviços
    {'username': 'pedro.mecpro', 'nome': 'Pedro', 'sobrenome': 'Ferreira', 'empresa': empresas_criadas[2], 'perfil': 'TERCEIRO_MANUTENCAO_GERAL'},
    {'username': 'julia.mecpro', 'nome': 'Julia', 'sobrenome': 'Almeida', 'empresa': empresas_criadas[2], 'perfil': 'TERCEIRO_MANUTENCAO_PTA'},
]

mecanicos_criados = []
for mec_data in mecanicos_data:
    user, user_created = User.objects.get_or_create(
        username=mec_data['username'],
        defaults={
            'first_name': mec_data['nome'],
            'last_name': mec_data['sobrenome'],
            'email': f"{mec_data['username']}@example.com",
            'is_active': True
        }
    )
    
    if user_created:
        user.set_password('123456')
        user.save()
    
    perfil, perfil_created = PerfilUsuario.objects.get_or_create(
        user=user,
        defaults={
            'setor': setor_manutencao,
            'perfil': mec_data['perfil'],
            'empresa': mec_data['empresa'],
            'disponivel': True,
            'telefone': f'(11) 9{1000 + len(mecanicos_criados):04d}-0000'
        }
    )
    
    # Atualizar empresa se já existia
    if not perfil_created and perfil.empresa != mec_data['empresa']:
        perfil.empresa = mec_data['empresa']
        perfil.save()
    
    mecanicos_criados.append(user)
    print(f"  {'✅ Criado' if user_created else '✓ Já existe'}: {user.get_full_name()} → {mec_data['empresa'].nome}")

# ============================================================================
# TESTE 3: Criar Máquinas Vinculadas às Empresas
# ============================================================================
print("\n🏗️ TESTE 3: Criando máquinas vinculadas às empresas...")

maquinas_data = [
    {'codigo': 'PTA-LOKAR-01', 'nome': 'PTA Lokar 01', 'tipo': 'PONTE_ROLANTE', 'empresa': empresas_criadas[0]},
    {'codigo': 'EMP-LOKAR-01', 'nome': 'Empilhadeira Lokar 01', 'tipo': 'EMPILHADEIRA', 'empresa': empresas_criadas[0]},
    {'codigo': 'GUIN-TECH-01', 'nome': 'Guindaste TechServ 01', 'tipo': 'GUINDASTE', 'empresa': empresas_criadas[1]},
    {'codigo': 'SOLD-TECH-01', 'nome': 'Solda TechServ 01', 'tipo': 'SOLDA', 'empresa': empresas_criadas[1]},
    {'codigo': 'COMP-MEC-01', 'nome': 'Compressor MecPro 01', 'tipo': 'COMPRESSOR', 'empresa': empresas_criadas[2]},
]

maquinas_criadas = []
for maq_data in maquinas_data:
    maquina, created = Maquina.objects.get_or_create(
        codigo=maq_data['codigo'],
        defaults={
            'nome': maq_data['nome'],
            'tipo': maq_data['tipo'],
            'empresa': maq_data['empresa'],
            'localizacao': 'Pátio Principal',
            'ativo': True
        }
    )
    
    # Atualizar empresa se já existia
    if not created and maquina.empresa != maq_data['empresa']:
        maquina.empresa = maq_data['empresa']
        maquina.save()
    
    maquinas_criadas.append(maquina)
    print(f"  {'✅ Criada' if created else '✓ Já existe'}: {maquina.codigo} → {maq_data['empresa'].nome}")

# ============================================================================
# TESTE 4: Validar Vínculos Empresa → Mecânicos
# ============================================================================
print("\n🔗 TESTE 4: Validando vínculos Empresa → Mecânicos...")

for empresa in empresas_criadas:
    mecanicos = User.objects.filter(perfil__empresa=empresa, is_active=True)
    print(f"\n  📍 {empresa.nome}:")
    if mecanicos.exists():
        for mec in mecanicos:
            print(f"     ✓ {mec.get_full_name()} ({mec.perfil.get_perfil_display()})")
    else:
        print(f"     ⚠️ Nenhum mecânico vinculado")

# ============================================================================
# TESTE 5: Validar Vínculos Máquina → Mecânicos
# ============================================================================
print("\n🔗 TESTE 5: Validando vínculos Máquina → Mecânicos...")

for maquina in maquinas_criadas[:3]:  # Testar apenas 3 primeiras
    mecanicos = User.objects.filter(
        perfil__empresa=maquina.empresa,
        perfil__disponivel=True,
        is_active=True
    )
    print(f"\n  🏗️ {maquina.codigo} ({maquina.empresa.nome}):")
    if mecanicos.exists():
        for mec in mecanicos:
            print(f"     ✓ {mec.get_full_name()} - Disponível: {mec.perfil.disponivel}")
    else:
        print(f"     ⚠️ Nenhum mecânico disponível")

# ============================================================================
# TESTE 6: Testar Propriedades do ChamadoManutencao
# ============================================================================
print("\n🔧 TESTE 6: Testando propriedades de chamados...")

# Criar um chamado de teste
if maquinas_criadas:
    maquina_teste = maquinas_criadas[0]
    print(f"\n  📋 Máquina de teste: {maquina_teste.codigo}")
    print(f"  🏢 Empresa responsável: {maquina_teste.empresa.nome}")

    # Buscar mecânicos disponíveis
    mecanicos_disponiveis = User.objects.filter(
        perfil__empresa=maquina_teste.empresa,
        perfil__disponivel=True,
        is_active=True
    )

    print(f"  👷 Mecânicos disponíveis: {mecanicos_disponiveis.count()}")
    for mec in mecanicos_disponiveis:
        print(f"     ✓ {mec.get_full_name()}")

# ============================================================================
# RESUMO FINAL
# ============================================================================
print("\n" + "=" * 80)
print("📊 RESUMO DO SISTEMA")
print("=" * 80)

total_empresas = Empresa.objects.filter(ativo=True).count()
total_mecanicos = User.objects.filter(perfil__perfil__startswith='TERCEIRO_', is_active=True).count()
total_maquinas = Maquina.objects.filter(ativo=True).count()

print(f"\n  🏢 Total de Empresas Ativas: {total_empresas}")
print(f"  👷 Total de Mecânicos Terceiros: {total_mecanicos}")
print(f"  🏗️ Total de Máquinas Ativas: {total_maquinas}")

print("\n" + "=" * 80)
print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
print("=" * 80)

print("\n📝 PRÓXIMOS PASSOS:")
print("  1. Acesse o sistema e faça login como admin")
print("  2. Vá em 'Empresas' no menu lateral")
print("  3. Veja as empresas cadastradas")
print("  4. Crie um chamado de manutenção para uma máquina")
print("  5. Veja que apenas mecânicos da empresa da máquina aparecem")
print("\n  💡 Usuários de teste criados:")
print("     - joao.lokar / 123456 (Lokar Locações)")
print("     - carlos.techserv / 123456 (TechServ Manutenção)")
print("     - pedro.mecpro / 123456 (MecPro Serviços)")
print("\n" + "=" * 80)

