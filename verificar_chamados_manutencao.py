"""
Script para verificar e criar chamados de manutenção de teste
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from django.contrib.auth.models import User
from frota_locada.models import Maquina, ChamadoManutencao
from core.models import Empresa, PerfilUsuario

def verificar_e_criar_chamados():
    print("=" * 80)
    print("VERIFICAÇÃO DE CHAMADOS DE MANUTENÇÃO")
    print("=" * 80)
    
    # 1. Verificar usuário joao.lokar
    print("\n1. VERIFICANDO USUÁRIO JOAO.LOKAR:")
    print("-" * 80)
    try:
        user = User.objects.get(username='joao.lokar')
        perfil = user.perfil
        print(f"✅ Usuário encontrado: {user.username}")
        print(f"   - Nome: {user.get_full_name()}")
        print(f"   - Perfil: {perfil.perfil}")
        print(f"   - Empresa: {perfil.empresa.nome if perfil.empresa else 'SEM EMPRESA'}")
        print(f"   - Disponível: {perfil.disponivel}")
    except User.DoesNotExist:
        print("❌ Usuário joao.lokar não encontrado!")
        return
    
    # 2. Verificar empresa Lokar
    print("\n2. VERIFICANDO EMPRESA LOKAR:")
    print("-" * 80)
    try:
        empresa_lokar = Empresa.objects.get(nome__icontains='lokar')
        print(f"✅ Empresa encontrada: {empresa_lokar.nome}")
        print(f"   - CNPJ: {empresa_lokar.cnpj}")
        print(f"   - Ativa: {empresa_lokar.ativo}")
    except Empresa.DoesNotExist:
        print("❌ Empresa Lokar não encontrada!")
        return
    
    # 3. Verificar máquinas da empresa Lokar
    print("\n3. VERIFICANDO MÁQUINAS DA EMPRESA LOKAR:")
    print("-" * 80)
    maquinas_lokar = Maquina.objects.filter(empresa=empresa_lokar, ativo=True)
    print(f"Total de máquinas ativas: {maquinas_lokar.count()}")
    
    if maquinas_lokar.count() == 0:
        print("\n⚠️  NENHUMA MÁQUINA ENCONTRADA! Criando máquinas de teste...")
        
        # Criar máquinas de teste
        maquinas_teste = [
            {
                'nome': 'Guindaste Lokar 01',
                'codigo': 'GUIN-LOK-001',
                'tipo': 'GUINDASTE',
                'localizacao': 'Pátio A',
                'setor': 'Produção',
                'marca': 'Liebherr',
                'modelo': 'LTM 1100',
            },
            {
                'nome': 'Empilhadeira Lokar 01',
                'codigo': 'EMP-LOK-001',
                'tipo': 'EMPILHADEIRA',
                'localizacao': 'Almoxarifado',
                'setor': 'Logística',
                'marca': 'Toyota',
                'modelo': '8FD25',
            },
            {
                'nome': 'Compressor Lokar 01',
                'codigo': 'COMP-LOK-001',
                'tipo': 'COMPRESSOR',
                'localizacao': 'Oficina',
                'setor': 'Manutenção',
                'marca': 'Atlas Copco',
                'modelo': 'GA 30',
            },
        ]
        
        for maq_data in maquinas_teste:
            maquina = Maquina.objects.create(
                empresa=empresa_lokar,
                **maq_data
            )
            print(f"   ✅ Máquina criada: {maquina.codigo} - {maquina.nome}")
        
        # Recarregar máquinas
        maquinas_lokar = Maquina.objects.filter(empresa=empresa_lokar, ativo=True)
    else:
        for maquina in maquinas_lokar:
            print(f"   - {maquina.codigo}: {maquina.nome} ({maquina.get_tipo_display()})")
    
    # 4. Verificar chamados existentes
    print("\n4. VERIFICANDO CHAMADOS DE MANUTENÇÃO:")
    print("-" * 80)
    chamados_lokar = ChamadoManutencao.objects.filter(
        maquina__empresa=empresa_lokar
    ).order_by('-data_abertura')
    
    print(f"Total de chamados da empresa Lokar: {chamados_lokar.count()}")
    
    if chamados_lokar.count() > 0:
        print("\nChamados existentes:")
        for chamado in chamados_lokar:
            print(f"   - {chamado.numero_chamado}: {chamado.maquina.nome}")
            print(f"     Status: {chamado.get_status_display()}")
            print(f"     Prioridade: {chamado.get_prioridade_display()}")
            print(f"     Problema: {chamado.get_tipo_problema_display()}")
            print(f"     Data: {chamado.data_abertura.strftime('%d/%m/%Y %H:%M')}")
            print()
    
    # 5. Verificar chamados em aberto
    print("\n5. CHAMADOS EM ABERTO (AGUARDANDO/EM_ATENDIMENTO):")
    print("-" * 80)
    chamados_abertos = ChamadoManutencao.objects.filter(
        maquina__empresa=empresa_lokar,
        status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
    )
    
    print(f"Total de chamados em aberto: {chamados_abertos.count()}")
    
    if chamados_abertos.count() == 0:
        print("\n⚠️  NENHUM CHAMADO EM ABERTO! Criando chamados de teste...")
        
        # Criar chamados de teste
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = user  # Usar joao.lokar como solicitante
        
        chamados_teste = [
            {
                'maquina': maquinas_lokar[0],
                'tipo_problema': 'HIDRAULICO',
                'descricao_problema': 'Vazamento de óleo hidráulico no cilindro principal. Equipamento parado.',
                'prioridade': 'ALTA',
                'solicitante': admin_user,
            },
            {
                'maquina': maquinas_lokar[1] if maquinas_lokar.count() > 1 else maquinas_lokar[0],
                'tipo_problema': 'MECANICO',
                'descricao_problema': 'Ruído anormal no motor. Necessita inspeção urgente.',
                'prioridade': 'MEDIA',
                'solicitante': admin_user,
            },
        ]
        
        if maquinas_lokar.count() > 2:
            chamados_teste.append({
                'maquina': maquinas_lokar[2],
                'tipo_problema': 'ELETRICO',
                'descricao_problema': 'Painel de controle não liga. Verificar sistema elétrico.',
                'prioridade': 'CRITICA',
                'solicitante': admin_user,
            })
        
        for chamado_data in chamados_teste:
            chamado = ChamadoManutencao.objects.create(**chamado_data)
            print(f"   ✅ Chamado criado: {chamado.numero_chamado}")
            print(f"      Máquina: {chamado.maquina.nome}")
            print(f"      Problema: {chamado.get_tipo_problema_display()}")
            print(f"      Prioridade: {chamado.get_prioridade_display()}")
            print()
    else:
        for chamado in chamados_abertos:
            print(f"   - {chamado.numero_chamado}: {chamado.maquina.nome}")
            print(f"     Status: {chamado.get_status_display()}")
            print(f"     Prioridade: {chamado.get_prioridade_display()}")
            print()
    
    print("\n" + "=" * 80)
    print("✅ VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print(f"\n📊 RESUMO:")
    print(f"   - Usuário: {user.username} ({perfil.perfil})")
    print(f"   - Empresa: {empresa_lokar.nome}")
    print(f"   - Máquinas ativas: {maquinas_lokar.count()}")
    print(f"   - Chamados em aberto: {ChamadoManutencao.objects.filter(maquina__empresa=empresa_lokar, status__in=['AGUARDANDO', 'EM_ATENDIMENTO']).count()}")
    print("\n🔗 Acesse: http://127.0.0.1:8000/frota-locada/chamados/meus/")
    print("=" * 80)

if __name__ == '__main__':
    verificar_e_criar_chamados()

