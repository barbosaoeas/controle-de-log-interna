# Generated manually for changing AbastecimentoVeiculo to reference Equipamento

from django.db import migrations, models
import django.db.models.deletion


def migrar_abastecimentos_para_equipamento(apps, schema_editor):
    """Migra referências de abastecimentos para equipamentos"""
    AbastecimentoVeiculo = apps.get_model('core', 'AbastecimentoVeiculo')
    Veiculo = apps.get_model('core', 'Veiculo')
    Equipamento = apps.get_model('core', 'Equipamento')
    
    # Para cada abastecimento, encontrar o equipamento correspondente
    for abastecimento in AbastecimentoVeiculo.objects.all():
        try:
            veiculo = abastecimento.veiculo
            # Encontrar equipamento com a mesma placa
            equipamento = Equipamento.objects.filter(placa=veiculo.placa).first()
            
            if equipamento:
                # Atualizar o campo veiculo_id diretamente
                AbastecimentoVeiculo.objects.filter(id=abastecimento.id).update(veiculo_id=equipamento.id)
            else:
                print(f"Equipamento não encontrado para veículo {veiculo.placa}")
        except Exception as e:
            print(f"Erro ao migrar abastecimento {abastecimento.id}: {e}")


def reverter_migracao(apps, schema_editor):
    """Reverter migração (não implementado por segurança)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_migrar_dados_veiculo_para_equipamento'),
    ]

    operations = [
        # Primeiro migrar os dados
        migrations.RunPython(migrar_abastecimentos_para_equipamento, reverter_migracao),
        
        # Depois alterar o campo
        migrations.AlterField(
            model_name='abastecimentoveiculo',
            name='veiculo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='abastecimentos', to='core.equipamento'),
        ),
    ]
