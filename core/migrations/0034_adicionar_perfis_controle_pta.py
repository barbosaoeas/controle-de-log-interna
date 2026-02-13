# Generated manually - Adicionar perfis de controle de chamados PTA

from django.db import migrations


def adicionar_perfis_controle_pta(apps, schema_editor):
    """Adiciona os perfis de controle de chamados de manutenção PTA"""
    TipoPerfil = apps.get_model('core', 'TipoPerfil')
    
    # Novos perfis de controle de chamados
    novos_perfis = [
        # (codigo, nome, descricao, is_admin, is_supervisor, is_terceiro)
        ('CONTROLE_MAN_PTA', 'Controle de Manutenção - PTA', 
         'Responsável por abrir e gerenciar chamados de manutenção de PTAs. Setor: Manutenção. '
         'Pode criar chamados, visualizar relatórios e acompanhar status dos reparos.', 
         False, False, False),
        
        ('CONTROLE_PROD_PTA', 'Controle de Produção - PTA', 
         'Responsável por abrir e gerenciar chamados de manutenção de PTAs. Setor: Produção. '
         'Pode criar chamados, visualizar relatórios e acompanhar status dos reparos.', 
         False, False, False),
    ]
    
    for codigo, nome, descricao, is_admin, is_supervisor, is_terceiro in novos_perfis:
        # Verificar se já existe antes de criar
        if not TipoPerfil.objects.filter(codigo=codigo).exists():
            TipoPerfil.objects.create(
                codigo=codigo,
                nome=nome,
                descricao=descricao,
                permissoes_resumo='Pode abrir chamados de manutenção, visualizar relatórios e acompanhar reparos.',
                is_admin=is_admin,
                is_supervisor=is_supervisor,
                is_terceiro=is_terceiro,
                ativo=True,
                is_sistema=True  # Marca como perfil do sistema
            )
            print(f"✅ Perfil {codigo} criado com sucesso")
        else:
            print(f"⚠️ Perfil {codigo} já existe, pulando...")
    
    print(f"✅ Perfis de controle PTA adicionados")


def reverter_adicao_perfis(apps, schema_editor):
    """Reverte a adição dos perfis de controle PTA"""
    TipoPerfil = apps.get_model('core', 'TipoPerfil')
    
    codigos_remover = ['CONTROLE_MAN_PTA', 'CONTROLE_PROD_PTA']
    
    for codigo in codigos_remover:
        TipoPerfil.objects.filter(codigo=codigo).delete()
        print(f"❌ Perfil {codigo} removido")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_remover_descricao_perfil'),
    ]

    operations = [
        migrations.RunPython(adicionar_perfis_controle_pta, reverter_adicao_perfis),
    ]

