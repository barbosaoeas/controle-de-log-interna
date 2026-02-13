"""
Script para gerenciar status dos equipamentos com a NOVA LÓGICA SIMPLIFICADA

NOVA LÓGICA:
- ativo: Boolean (True = existe no sistema, False = excluído)
- status_operacional:
    - OPERACIONAL = disponível (aparece e pode ser selecionado)
    - MANUTENCAO = em reparo (aparece mas desabilitado)
    - FORA_SERVICO = temporariamente indisponível (não aparece)
    - INATIVO = permanentemente inativo (não aparece)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_materiais.settings')
django.setup()

from core.models import Equipamento
from django.db import connection

def verificar_campo_em_servico():
    """Verifica se o campo em_servico ainda existe no banco"""
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_equipamento)")
        columns = [row[1] for row in cursor.fetchall()]
        return 'em_servico' in columns

def migrar_dados():
    """Migra dados de em_servico para status_operacional (se o campo ainda existir)"""
    print("\n" + "=" * 80)
    print("🔄 VERIFICANDO E MIGRANDO DADOS")
    print("=" * 80)

    if not verificar_campo_em_servico():
        print("✅ Campo em_servico já foi removido. Nada a migrar.")
        return 0

    equipamentos = Equipamento.objects.all()
    migrados = 0

    for eq in equipamentos:
        # Verificar se tem o campo em_servico no banco
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT em_servico FROM core_equipamento WHERE id = {eq.id}")
                row = cursor.fetchone()
                em_servico_antigo = bool(row[0]) if row else True
        except:
            em_servico_antigo = True

        status_antigo = eq.status_operacional

        # Se em_servico=False e status é OPERACIONAL, mudar para FORA_SERVICO
        if not em_servico_antigo and status_antigo == 'OPERACIONAL':
            eq.status_operacional = 'FORA_SERVICO'
            eq.save()
            migrados += 1
            print(f"  ✅ {eq.nome}: OPERACIONAL → FORA_SERVICO (em_servico era False)")

        # Se ativo=False, garantir que status seja INATIVO
        elif not eq.ativo and status_antigo not in ['INATIVO']:
            eq.status_operacional = 'INATIVO'
            eq.save()
            migrados += 1
            print(f"  ✅ {eq.nome}: {status_antigo} → INATIVO (ativo era False)")

    print(f"\n✅ {migrados} equipamentos migrados!")
    return migrados

def listar_status():
    """Lista todos os equipamentos com seus status"""
    print("\n" + "=" * 80)
    print("📋 STATUS ATUAL DOS EQUIPAMENTOS")
    print("=" * 80)
    
    equipamentos = Equipamento.objects.all().order_by('nome')
    
    for eq in equipamentos:
        # Determinar status para pedidos
        if not eq.ativo:
            status_pedido = "❌ EXCLUÍDO (não aparece)"
        elif eq.status_operacional == 'OPERACIONAL':
            status_pedido = "🟢 DISPONÍVEL (aparece e selecionável)"
        elif eq.status_operacional == 'MANUTENCAO':
            status_pedido = "🟡 EM MANUTENÇÃO (aparece desabilitado)"
        elif eq.status_operacional == 'FORA_SERVICO':
            status_pedido = "🔴 FORA DE SERVIÇO (não aparece)"
        elif eq.status_operacional == 'INATIVO':
            status_pedido = "⚫ INATIVO (não aparece)"
        else:
            status_pedido = "❓ DESCONHECIDO"
        
        print(f"""
{eq.nome} (ID: {eq.id})
  ├─ Código: {eq.codigo or 'N/A'}
  ├─ Categoria: {eq.categoria}
  ├─ ativo: {eq.ativo}
  ├─ status_operacional: {eq.status_operacional}
  └─ STATUS PARA PEDIDOS: {status_pedido}""")
    
    print("\n" + "=" * 80)

def habilitar_todos():
    """Habilita todos os equipamentos como OPERACIONAL"""
    print("\n🔧 HABILITANDO TODOS OS EQUIPAMENTOS...")
    
    equipamentos = Equipamento.objects.all()
    count = 0
    
    for eq in equipamentos:
        if not eq.ativo or eq.status_operacional != 'OPERACIONAL':
            eq.ativo = True
            eq.status_operacional = 'OPERACIONAL'
            eq.save()
            count += 1
            print(f"   ✅ {eq.nome} - Habilitado como OPERACIONAL")
    
    print(f"\n✅ {count} equipamentos habilitados!")

def corrigir_prancha():
    """Corrige especificamente equipamentos com 'prancha' ou 'carreta' no nome"""
    print("\n🔧 CORRIGINDO CARRETA/PRANCHA...")
    
    equipamentos = Equipamento.objects.filter(nome__icontains='prancha') | \
                   Equipamento.objects.filter(nome__icontains='carreta')
    
    if not equipamentos.exists():
        print("⚠️ Nenhum equipamento com 'prancha' ou 'carreta' encontrado!")
        return
    
    for eq in equipamentos:
        print(f"\n📦 {eq.nome}")
        print(f"   Status atual: ativo={eq.ativo}, status_operacional={eq.status_operacional}")
        
        eq.ativo = True
        eq.status_operacional = 'OPERACIONAL'
        eq.save()
        
        print(f"   ✅ Corrigido: ativo=True, status_operacional=OPERACIONAL")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🔧 GERENCIADOR DE STATUS DE EQUIPAMENTOS (NOVA LÓGICA)")
    print("=" * 80)
    print("\n1. Listar todos os equipamentos")
    print("2. Migrar dados (em_servico → status_operacional)")
    print("3. Habilitar TODOS como OPERACIONAL")
    print("4. Corrigir Carreta/Prancha")
    print("5. Sair")
    
    opcao = input("\nEscolha uma opção: ").strip()
    
    if opcao == '1':
        listar_status()
    elif opcao == '2':
        migrar_dados()
    elif opcao == '3':
        habilitar_todos()
    elif opcao == '4':
        corrigir_prancha()
    elif opcao == '5':
        print("Saindo...")
    else:
        print("Opção inválida!")

