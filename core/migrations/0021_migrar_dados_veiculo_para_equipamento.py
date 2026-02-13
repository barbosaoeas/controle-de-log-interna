# Generated manually for migrating data from Veiculo to Equipamento

from django.db import migrations


def migrar_veiculos_para_equipamentos(apps, schema_editor):
    """Migra dados da tabela Veiculo para Equipamento"""
    Veiculo = apps.get_model('core', 'Veiculo')
    Equipamento = apps.get_model('core', 'Equipamento')
    
    # Mapear tipos de veículo para categorias de equipamento
    tipo_para_categoria = {
        'CAMINHAO': 'OUTROS',
        'CARRETA': 'CARRETA_HIDRAULICA',
        'TRATOR': 'TRATOR',
        'EMPILHADEIRA': 'EMPILHADEIRA',
        'MUNCK': 'CAMINHAO_MUNCK',
        'GUINDASTE': 'GUINDASTE_RODOVIARIO',
        'OUTROS': 'OUTROS',
    }
    
    # Mapear status de veículo para status operacional
    status_para_operacional = {
        'ATIVO': 'OPERACIONAL',
        'MANUTENCAO': 'MANUTENCAO',
        'INATIVO': 'INATIVO',
    }
    
    for veiculo in Veiculo.objects.all():
        # Verificar se já existe um equipamento com a mesma placa
        equipamento_existente = Equipamento.objects.filter(placa=veiculo.placa).first()
        
        if equipamento_existente:
            # Atualizar equipamento existente com dados do veículo
            equipamento_existente.modelo = veiculo.modelo or ''
            equipamento_existente.ano = veiculo.ano
            equipamento_existente.capacidade_tanque = veiculo.capacidade_tanque
            equipamento_existente.consumo_medio = veiculo.consumo_medio
            equipamento_existente.tem_agenda = veiculo.tem_agenda
            equipamento_existente.categoria = tipo_para_categoria.get(veiculo.tipo, 'OUTROS')
            equipamento_existente.status_operacional = status_para_operacional.get(veiculo.status, 'OPERACIONAL')
            equipamento_existente.ativo = veiculo.ativo
            equipamento_existente.save()
        else:
            # Criar novo equipamento baseado no veículo
            Equipamento.objects.create(
                nome=veiculo.nome,
                codigo=veiculo.placa,  # Usar placa como código
                categoria=tipo_para_categoria.get(veiculo.tipo, 'OUTROS'),
                status_operacional=status_para_operacional.get(veiculo.status, 'OPERACIONAL'),
                descricao=f'Migrado de veículo: {veiculo.modelo or ""}',
                ativo=veiculo.ativo,
                em_servico=True,
                placa=veiculo.placa,
                modelo=veiculo.modelo or '',
                ano=veiculo.ano,
                capacidade_tanque=veiculo.capacidade_tanque,
                consumo_medio=veiculo.consumo_medio,
                tem_agenda=veiculo.tem_agenda,
            )


def reverter_migracao(apps, schema_editor):
    """Reverter migração (não implementado por segurança)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_unificar_equipamentos_veiculos'),
    ]

    operations = [
        migrations.RunPython(migrar_veiculos_para_equipamentos, reverter_migracao),
    ]
