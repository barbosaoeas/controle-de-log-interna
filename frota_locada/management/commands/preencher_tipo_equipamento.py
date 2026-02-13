from django.core.management.base import BaseCommand
from frota_locada.models import ChamadoManutencao


class Command(BaseCommand):
    help = 'Preenche o campo tipo_equipamento nos chamados existentes'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("PREENCHENDO CAMPO tipo_equipamento NOS CHAMADOS EXISTENTES")
        self.stdout.write("=" * 80)

        # Buscar todos os chamados
        chamados = ChamadoManutencao.objects.all()
        total = chamados.count()
        atualizados = 0
        sem_equipamento = 0

        self.stdout.write(f"\nTotal de chamados: {total}")

        for chamado in chamados:
            # Se já tem tipo_equipamento, pular
            if chamado.tipo_equipamento:
                continue

            # Se tem veiculo_locado, pegar o tipo do veículo
            if chamado.veiculo_locado and chamado.veiculo_locado.tipo_veiculo:
                chamado.tipo_equipamento = chamado.veiculo_locado.tipo_veiculo
                chamado.save()
                atualizados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {chamado.numero_chamado}: tipo_equipamento = {chamado.tipo_equipamento.nome}"
                    )
                )
            else:
                sem_equipamento += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  {chamado.numero_chamado}: SEM tipo_equipamento (sem veiculo_locado)"
                    )
                )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS(f"✅ Chamados atualizados: {atualizados}"))
        self.stdout.write(self.style.WARNING(f"⚠️  Chamados sem equipamento: {sem_equipamento}"))
        self.stdout.write("=" * 80)

