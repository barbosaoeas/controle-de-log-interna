# Generated manually for unifying Equipamento and Veiculo models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_alter_perfilusuario_perfil'),
    ]

    operations = [
        # Add new fields to Equipamento model
        migrations.AddField(
            model_name='equipamento',
            name='placa',
            field=models.CharField(blank=True, help_text='Placa do veículo (se aplicável)', max_length=10),
        ),
        migrations.AddField(
            model_name='equipamento',
            name='modelo',
            field=models.CharField(blank=True, help_text='Modelo do equipamento/veículo', max_length=100),
        ),
        migrations.AddField(
            model_name='equipamento',
            name='ano',
            field=models.IntegerField(blank=True, help_text='Ano de fabricação', null=True),
        ),
        migrations.AddField(
            model_name='equipamento',
            name='capacidade_tanque',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Capacidade do tanque em litros (para veículos)', max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='equipamento',
            name='consumo_medio',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Consumo médio em km/litro (para veículos)', max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='equipamento',
            name='tem_agenda',
            field=models.BooleanField(default=True, help_text='Se marcado, o equipamento aparecerá nas opções de agendamento de pedidos', verbose_name='Com Agenda'),
        ),
    ]
