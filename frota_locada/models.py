from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from decimal import Decimal


class Fornecedor(models.Model):
    """Fornecedores de veículos locados"""
    nome = models.CharField(max_length=200, verbose_name="Nome do Fornecedor")
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        validators=[RegexValidator(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', 'CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX')],
        verbose_name="CNPJ"
    )
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    endereco = models.TextField(blank=True, verbose_name="Endereço")
    contato_responsavel = models.CharField(max_length=100, blank=True, verbose_name="Contato Responsável")

    # Vínculo com Empresa (para mecânicos que fazem manutenção dos equipamentos deste fornecedor)
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fornecedores_atendidos',
        verbose_name="Empresa Responsável pela Manutenção",
        help_text="Empresa que presta serviço de manutenção para os equipamentos deste fornecedor"
    )

    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoVeiculo(models.Model):
    """Tipos de veículos (Caminhão, Van, Carro, etc.)"""
    nome = models.CharField(max_length=50, unique=True, verbose_name="Tipo de Veículo")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tipo de Veículo"
        verbose_name_plural = "Tipos de Veículos"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class MarcaVeiculo(models.Model):
    """Marcas de veículos (Toyota, Ford, Volkswagen, etc.)"""
    nome = models.CharField(max_length=50, unique=True, verbose_name="Marca")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Marca de Veículo"
        verbose_name_plural = "Marcas de Veículos"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class VeiculoLocado(models.Model):
    """Veículos locados para a empresa"""
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('INATIVO', 'Inativo'),
        ('DEVOLVIDO', 'Devolvido'),
    ]

    LOCADO_PARA_CHOICES = [
        ('PRODUCAO', 'Produção'),
        ('MANUTENCAO', 'Manutenção'),
        ('ADMINISTRATIVO', 'Administrativo'),
    ]

    # Informações básicas
    placa = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Placa/Código",
        help_text="Código de identificação do equipamento (ex: ABC-1234, ABC1D23, EQ001, etc.)"
    )
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    marca = models.ForeignKey(MarcaVeiculo, on_delete=models.PROTECT, verbose_name="Marca")
    ano_fabricacao = models.IntegerField(verbose_name="Ano de Fabricação")
    cor = models.CharField(max_length=30, verbose_name="Cor")
    tipo_veiculo = models.ForeignKey(TipoVeiculo, on_delete=models.PROTECT, verbose_name="Tipo de Veículo")

    # Fornecedor e contrato
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, verbose_name="Fornecedor")
    numero_contrato = models.CharField(max_length=50, blank=True, verbose_name="Número do Contrato")
    data_inicio_locacao = models.DateField(verbose_name="Data de Início da Locação")
    data_fim_locacao = models.DateField(null=True, blank=True, verbose_name="Previsão Fim Locação")

    # Valores
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Mensal (R$)")

    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO', verbose_name="Status")
    locado_para = models.CharField(
        max_length=20,
        choices=LOCADO_PARA_CHOICES,
        default='PRODUCAO',
        verbose_name="Locado Para",
        help_text="Setor para o qual o veículo está locado"
    )
    horimetro_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        default=0,
        verbose_name="Horímetro Inicial",
        help_text="Horímetro do veículo no início da locação"
    )
    horimetro_atual = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        default=0,
        verbose_name="Horímetro Atual",
        help_text="Horímetro atual do veículo"
    )

    # Observações e controle
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    cadastrado_por = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Cadastrado por")

    class Meta:
        verbose_name = "Veículo Locado"
        verbose_name_plural = "Veículos Locados"
        ordering = ['-data_cadastro']

    def __str__(self):
        return f"{self.placa} - {self.marca.nome} {self.modelo}"

    @property
    def horas_trabalhadas(self):
        """Calcula horas trabalhadas desde o início da locação"""
        return self.horimetro_atual - self.horimetro_inicial

    @property
    def horimetro_formatado(self):
        """Retorna horímetro atual formatado"""
        return f"{self.horimetro_atual:.1f}h"

    @property
    def dias_locacao(self):
        """Calcula dias de locação"""
        if not self.data_inicio_locacao:
            return 0
        if self.data_fim_locacao:
            return (self.data_fim_locacao - self.data_inicio_locacao).days
        return (timezone.now().date() - self.data_inicio_locacao).days

    @property
    def valor_total_estimado(self):
        """Calcula valor total estimado (mensal + KM)"""
        meses = self.dias_locacao / 30
        valor_mensal_total = self.valor_mensal * Decimal(str(meses))
        return valor_mensal_total + self.valor_total_km

    @property
    def status_badge_class(self):
        """Retorna classe CSS para o badge de status"""
        status_classes = {
            'ATIVO': 'bg-success',
            'INATIVO': 'bg-secondary',
            'MANUTENCAO': 'bg-warning text-dark',
            'ACIDENTE': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')

    @property
    def is_ativo(self):
        return self.status == 'ATIVO'

    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge do status"""
        classes = {
            'ATIVO': 'bg-success',
            'MANUTENCAO': 'bg-warning',
            'INATIVO': 'bg-secondary',
            'DEVOLVIDO': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')


class TipoManutencao(models.Model):
    """Tipos de manutenção (Preventiva, Corretiva, etc.)"""
    nome = models.CharField(max_length=50, unique=True, verbose_name="Tipo de Manutenção")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tipo de Manutenção"
        verbose_name_plural = "Tipos de Manutenção"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ManutencaoVeiculo(models.Model):
    """Registro de manutenções dos veículos"""
    STATUS_CHOICES = [
        ('AGENDADA', 'Agendada'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]

    veiculo = models.ForeignKey(VeiculoLocado, on_delete=models.CASCADE, related_name='manutencoes', verbose_name="Veículo")
    tipo_manutencao = models.ForeignKey(TipoManutencao, on_delete=models.PROTECT, verbose_name="Tipo de Manutenção")

    # Datas
    data_agendamento = models.DateTimeField(verbose_name="Data de Agendamento")
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Data de Início")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")

    # Detalhes
    descricao = models.TextField(verbose_name="Descrição do Serviço")
    oficina = models.CharField(max_length=200, blank=True, verbose_name="Oficina/Prestador")
    km_veiculo = models.IntegerField(verbose_name="KM do Veículo")

    # Valores
    valor_orcamento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Orçamento (R$)")
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Final (R$)")

    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGENDADA', verbose_name="Status")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    # Controle
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    cadastrado_por = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Cadastrado por")

    class Meta:
        verbose_name = "Manutenção de Veículo"
        verbose_name_plural = "Manutenções de Veículos"
        ordering = ['-data_agendamento']

    def __str__(self):
        return f"{self.veiculo.placa} - {self.tipo_manutencao.nome} - {self.data_agendamento.strftime('%d/%m/%Y')}"

    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge do status"""
        classes = {
            'AGENDADA': 'bg-info',
            'EM_ANDAMENTO': 'bg-warning',
            'CONCLUIDA': 'bg-success',
            'CANCELADA': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')

    @property
    def duracao_manutencao(self):
        """Calcula duração da manutenção em horas"""
        if self.data_inicio and self.data_conclusao:
            delta = self.data_conclusao - self.data_inicio
            return delta.total_seconds() / 3600
        return None


class HistoricoHorimetro(models.Model):
    """Histórico de horímetro dos veículos"""
    veiculo = models.ForeignKey(VeiculoLocado, on_delete=models.CASCADE, related_name='historico_horimetro', verbose_name="Veículo")
    horimetro_anterior = models.DecimalField(max_digits=10, decimal_places=1, verbose_name="Horímetro Anterior (h)")
    horimetro_atual = models.DecimalField(max_digits=10, decimal_places=1, verbose_name="Horímetro Atual (h)")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data do Registro")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    registrado_por = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Registrado por")

    class Meta:
        verbose_name = "Histórico de Horímetro"
        verbose_name_plural = "Histórico de Horímetro"
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.veiculo.placa} - {self.horimetro_atual:.1f}h - {self.data_registro.strftime('%d/%m/%Y')}"

    @property
    def horas_trabalhadas(self):
        """Calcula horas trabalhadas neste período"""
        return self.horimetro_atual - self.horimetro_anterior


# ============================================================================
# MODELOS PARA CHAMADOS DE MANUTENÇÃO DE MÁQUINAS/EQUIPAMENTOS
# ============================================================================

class Maquina(models.Model):
    """Máquinas e equipamentos da empresa"""
    TIPO_CHOICES = [
        ('PTA', 'PTA (Plataforma de Trabalho Aéreo)'),
        ('GUINDASTE', 'Guindaste'),
        ('EMPILHADEIRA', 'Empilhadeira'),
        ('CAMINHAO', 'Caminhão'),
        ('PICKUP', 'Pickup'),
        ('SOLDA', 'Equipamento de Solda'),
        ('CORTE', 'Equipamento de Corte'),
        ('COMPRESSOR', 'Compressor'),
        ('GERADOR', 'Gerador'),
        ('BOMBA', 'Bomba'),
        ('PONTE_ROLANTE', 'Ponte Rolante'),
        ('OUTROS', 'Outros'),
    ]

    # Identificação
    nome = models.CharField(max_length=100, verbose_name="Nome da Máquina")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")

    # Localização
    localizacao = models.CharField(max_length=100, verbose_name="Localização")
    setor = models.CharField(max_length=50, blank=True, verbose_name="Setor")

    # Informações técnicas
    marca = models.CharField(max_length=50, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=50, blank=True, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=50, blank=True, verbose_name="Número de Série")
    ano_fabricacao = models.IntegerField(null=True, blank=True, verbose_name="Ano de Fabricação")

    # Empresa responsável (própria ou terceirizada)
    empresa = models.ForeignKey('core.Empresa', on_delete=models.PROTECT, verbose_name="Empresa Responsável",
                                 help_text="Empresa proprietária ou locadora do equipamento")

    # Status e controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    @property
    def chamados_abertos(self):
        """Retorna quantidade de chamados em aberto"""
        return self.chamados.filter(status__in=['AGUARDANDO', 'EM_ATENDIMENTO']).count()

    @property
    def status_operacional(self):
        """Retorna status operacional baseado em chamados abertos"""
        if self.chamados_abertos > 0:
            return 'EM_MANUTENCAO'
        return 'OPERACIONAL' if self.ativo else 'INATIVO'


# MODELO REMOVIDO - MecanicoFornecedor
# Agora usamos PerfilUsuario.empresa para vincular mecânicos às empresas
# Isso simplifica o sistema e evita duplicação de dados


class ChamadoManutencao(models.Model):
    """Chamados de manutenção para máquinas e equipamentos"""
    STATUS_CHOICES = [
        ('AGUARDANDO', 'Aguardando Atendimento'),
        ('EM_ATENDIMENTO', 'Em Atendimento'),
        ('PAUSADO', 'Pausado'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    TIPO_PROBLEMA_CHOICES = [
        ('ELETRICO', 'Elétrico'),
        ('MECANICO', 'Mecânico'),
        ('HIDRAULICO', 'Hidráulico'),
        ('PNEUMATICO', 'Pneumático'),
        ('SOFTWARE', 'Software'),
        ('ESTRUTURAL', 'Estrutural'),
        ('OUTROS', 'Outros'),
    ]

    # Identificação
    numero_chamado = models.CharField(max_length=20, unique=True, verbose_name="Número do Chamado")
    data_abertura = models.DateTimeField(auto_now_add=True, verbose_name="Data de Abertura")

    # Máquina e problema (PODE SER MAQUINA OU VEICULO LOCADO)
    maquina = models.ForeignKey(Maquina, on_delete=models.PROTECT, related_name='chamados', verbose_name="Máquina", null=True, blank=True)
    veiculo_locado = models.ForeignKey(VeiculoLocado, on_delete=models.PROTECT, related_name='chamados', verbose_name="Veículo/Equipamento Locado", null=True, blank=True)
    tipo_equipamento = models.ForeignKey(TipoVeiculo, on_delete=models.PROTECT, related_name='chamados', verbose_name="Tipo de Equipamento", null=True, blank=True)
    tipo_problema = models.CharField(max_length=20, choices=TIPO_PROBLEMA_CHOICES, verbose_name="Tipo do Problema")
    descricao_problema = models.TextField(verbose_name="Descrição do Problema")
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='MEDIA', verbose_name="Prioridade")
    foto_problema = models.ImageField(upload_to='chamados/fotos/', null=True, blank=True, verbose_name="Foto do Problema")

    # Pessoas
    solicitante = models.ForeignKey(User, on_delete=models.PROTECT, related_name='chamados_solicitados', verbose_name="Solicitante")
    mecanico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados_atendidos', verbose_name="Mecânico")

    # Controle de tempo
    data_inicio_atendimento = models.DateTimeField(null=True, blank=True, verbose_name="Data de Início do Atendimento")
    data_fim_atendimento = models.DateTimeField(null=True, blank=True, verbose_name="Data de Fim do Atendimento")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGUARDANDO', verbose_name="Status")

    # Solução
    descricao_solucao = models.TextField(blank=True, verbose_name="Descrição da Solução")
    pecas_utilizadas = models.TextField(blank=True, verbose_name="Peças Utilizadas")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Chamado de Manutenção"
        verbose_name_plural = "Chamados de Manutenção"
        ordering = ['-data_abertura']

    def __str__(self):
        equipamento = self.equipamento_nome
        return f"{self.numero_chamado} - {equipamento}"

    @property
    def equipamento_nome(self):
        """Retorna o nome do equipamento (Maquina ou VeiculoLocado)"""
        if self.veiculo_locado:
            return f"{self.veiculo_locado.placa} - {self.veiculo_locado.modelo}"
        elif self.maquina:
            return self.maquina.nome
        return "Equipamento não definido"

    @property
    def equipamento(self):
        """Retorna o objeto do equipamento (Maquina ou VeiculoLocado)"""
        return self.veiculo_locado if self.veiculo_locado else self.maquina

    @property
    def empresa_responsavel(self):
        """Retorna a empresa responsável pelo equipamento"""
        if self.veiculo_locado:
            return self.veiculo_locado.fornecedor.empresa if hasattr(self.veiculo_locado.fornecedor, 'empresa') else None
        elif self.maquina:
            return self.maquina.empresa
        return None

    def save(self, *args, **kwargs):
        if not self.numero_chamado:
            # Gerar número do chamado automaticamente
            from datetime import datetime
            ano = datetime.now().year
            ultimo_numero = ChamadoManutencao.objects.filter(
                numero_chamado__startswith=f'MAN-{ano}-'
            ).count() + 1
            self.numero_chamado = f'MAN-{ano}-{ultimo_numero:03d}'
        super().save(*args, **kwargs)

    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge do status"""
        classes = {
            'AGUARDANDO': 'bg-secondary',
            'EM_ATENDIMENTO': 'bg-primary',
            'PAUSADO': 'bg-warning',
            'CONCLUIDO': 'bg-success',
            'CANCELADO': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')

    @property
    def prioridade_badge_class(self):
        """Retorna classe CSS para badge da prioridade"""
        classes = {
            'BAIXA': 'bg-success',
            'MEDIA': 'bg-info',
            'ALTA': 'bg-warning',
            'CRITICA': 'bg-danger',
        }
        return classes.get(self.prioridade, 'bg-secondary')

    @property
    def tempo_atendimento(self):
        """Calcula tempo de atendimento em horas"""
        if self.data_inicio_atendimento and self.data_fim_atendimento:
            delta = self.data_fim_atendimento - self.data_inicio_atendimento
            return delta.total_seconds() / 3600
        return None

    @property
    def tempo_atendimento_formatado(self):
        """Retorna tempo de atendimento formatado"""
        tempo = self.tempo_atendimento
        if tempo is None:
            return "N/A"

        horas = int(tempo)
        minutos = int((tempo - horas) * 60)

        if horas > 0:
            return f"{horas}h {minutos}min"
        return f"{minutos}min"

    @property
    def tempo_aguardando(self):
        """Calcula tempo aguardando atendimento"""
        if self.status == 'AGUARDANDO':
            delta = timezone.now() - self.data_abertura
            return delta.total_seconds() / 3600
        elif self.data_inicio_atendimento:
            delta = self.data_inicio_atendimento - self.data_abertura
            return delta.total_seconds() / 3600
        return None

    @property
    def tempo_aguardando_formatado(self):
        """Retorna tempo aguardando formatado"""
        tempo = self.tempo_aguardando
        if tempo is None:
            return "N/A"

        if tempo < 1:
            minutos = int(tempo * 60)
            return f"{minutos}min"

        horas = int(tempo)
        minutos = int((tempo - horas) * 60)

        if horas > 24:
            dias = horas // 24
            horas_restantes = horas % 24
            return f"{dias}d {horas_restantes}h"

        return f"{horas}h {minutos}min"

    @property
    def tempo_total_indisponibilidade(self):
        """
        Calcula tempo total de indisponibilidade do equipamento.
        Tempo Total = Tempo de Espera + Tempo de Atendimento
        Usado para calcular MTTR e disponibilidade do equipamento.
        """
        tempo_espera = self.tempo_aguardando
        tempo_reparo = self.tempo_atendimento

        # Se o chamado está concluído, soma espera + reparo
        if tempo_espera is not None and tempo_reparo is not None:
            return tempo_espera + tempo_reparo

        # Se ainda está em atendimento, calcula desde abertura até agora
        elif self.status == 'EM_ATENDIMENTO' and self.data_abertura:
            delta = timezone.now() - self.data_abertura
            return delta.total_seconds() / 3600

        # Se ainda está aguardando, retorna apenas tempo de espera
        elif tempo_espera is not None:
            return tempo_espera

        return None

    @property
    def tempo_total_indisponibilidade_formatado(self):
        """Retorna tempo total de indisponibilidade formatado"""
        tempo = self.tempo_total_indisponibilidade
        if tempo is None:
            return "N/A"

        if tempo < 1:
            minutos = int(tempo * 60)
            return f"{minutos}min"

        horas = int(tempo)
        minutos = int((tempo - horas) * 60)

        if horas > 24:
            dias = horas // 24
            horas_restantes = horas % 24
            return f"{dias}d {horas_restantes}h {minutos}min"

        return f"{horas}h {minutos}min"

    @property
    def pode_iniciar_atendimento(self):
        """Verifica se o chamado pode ter atendimento iniciado"""
        return self.status == 'AGUARDANDO'

    @property
    def pode_finalizar_atendimento(self):
        """Verifica se o chamado pode ser finalizado"""
        return self.status == 'EM_ATENDIMENTO'

    @property
    def esta_em_atendimento(self):
        """Verifica se o chamado está em atendimento"""
        return self.status == 'EM_ATENDIMENTO'

    @property
    def empresa_responsavel(self):
        """Retorna a empresa responsável pela máquina ou None para veículos locados"""
        if self.maquina:
            return self.maquina.empresa
        # Veículos locados não têm empresa (são de fornecedores externos)
        return None

    @property
    def mecanicos_disponiveis(self):
        """Retorna mecânicos da empresa responsável ou todos os mecânicos se for veículo locado"""
        from django.contrib.auth.models import User
        from django.db.models import Q

        # Se for veículo locado (sem empresa), retornar todos os mecânicos disponíveis
        if self.empresa_responsavel is None:
            return User.objects.filter(
                Q(perfil__tipo_perfil__codigo__startswith='MANUTENCAO') |
                Q(perfil__tipo_perfil__codigo__startswith='TERCEIRO_MANUTENCAO'),
                perfil__disponivel=True,
                is_active=True
            ).select_related('perfil', 'perfil__tipo_perfil')

        # Se for máquina, retornar apenas mecânicos da empresa
        return User.objects.filter(
            perfil__empresa=self.empresa_responsavel,
            perfil__disponivel=True,
            is_active=True
        ).select_related('perfil', 'perfil__tipo_perfil')

    def pode_ser_atendido_por(self, usuario):
        """Verifica se o usuário pode atender este chamado"""
        # Admin e Supervisor podem atender qualquer chamado
        if hasattr(usuario, 'perfil') and usuario.perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR']:
            return True

        # Verificar se é mecânico da empresa responsável
        return self.mecanicos_disponiveis.filter(id=usuario.id).exists()


class AtendimentoChamado(models.Model):
    """
    Registro de atendimentos realizados em um chamado de manutenção.
    Permite múltiplos atendimentos por chamado (vários mecânicos podem trabalhar no mesmo chamado).
    """
    TIPO_MANUTENCAO_CHOICES = [
        ('MECANICA', 'Manutenção Mecânica'),
        ('ELETRICA', 'Manutenção Elétrica'),
        ('HIDRAULICA', 'Manutenção Hidráulica'),
        ('PNEUMATICA', 'Manutenção Pneumática'),
        ('PREVENTIVA', 'Manutenção Preventiva'),
        ('CORRETIVA', 'Manutenção Corretiva'),
        ('PREDITIVA', 'Manutenção Preditiva'),
        ('LUBRIFICACAO', 'Lubrificação'),
        ('LIMPEZA', 'Limpeza'),
        ('AJUSTE', 'Ajuste/Calibração'),
        ('TROCA_PNEU', 'Troca/Reparo de Pneu'),
        ('SOLDAGEM', 'Soldagem'),
        ('OUTROS', 'Outros'),
    ]

    STATUS_ATENDIMENTO_CHOICES = [
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('PAUSADO', 'Pausado'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    # Relacionamentos
    chamado = models.ForeignKey(
        ChamadoManutencao,
        on_delete=models.CASCADE,
        related_name='atendimentos',
        verbose_name="Chamado"
    )
    mecanico = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='atendimentos_realizados',
        verbose_name="Mecânico Responsável"
    )

    # Datas e horas
    data_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data/Hora de Início"
    )
    data_finalizacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data/Hora de Finalização"
    )

    # Tipo de manutenção realizada
    tipo_manutencao = models.CharField(
        max_length=20,
        choices=TIPO_MANUTENCAO_CHOICES,
        verbose_name="Tipo de Manutenção"
    )

    # Detalhes do atendimento
    descricao_servico = models.TextField(
        blank=True,
        verbose_name="Descrição do Serviço Realizado",
        help_text="Descreva detalhadamente o que foi feito"
    )
    pecas_trocadas = models.TextField(
        blank=True,
        verbose_name="Peças Trocadas/Utilizadas",
        help_text="Liste as peças trocadas ou utilizadas (uma por linha)"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Observações adicionais sobre o atendimento"
    )

    # Causa da falha
    mau_uso = models.BooleanField(
        default=False,
        verbose_name="Mau Uso do Equipamento",
        help_text="Marque se a falha foi causada por mau uso do equipamento pelo usuário"
    )

    # Status do atendimento
    status = models.CharField(
        max_length=20,
        choices=STATUS_ATENDIMENTO_CHOICES,
        default='EM_ANDAMENTO',
        verbose_name="Status do Atendimento"
    )

    # Tempo calculado automaticamente
    tempo_atendimento = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Tempo de Atendimento",
        help_text="Calculado automaticamente ao finalizar"
    )

    # Fotos do atendimento
    foto_antes = models.ImageField(
        upload_to='atendimentos/fotos/antes/',
        null=True,
        blank=True,
        verbose_name="Foto Antes do Reparo"
    )
    foto_depois = models.ImageField(
        upload_to='atendimentos/fotos/depois/',
        null=True,
        blank=True,
        verbose_name="Foto Depois do Reparo"
    )

    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atendimento de Chamado"
        verbose_name_plural = "Atendimentos de Chamados"
        ordering = ['-data_inicio']

    def __str__(self):
        return f"Atendimento {self.id} - {self.chamado.numero_chamado} - {self.mecanico.get_full_name()}"

    def save(self, *args, **kwargs):
        """Calcula tempo de atendimento ao finalizar"""
        if self.data_finalizacao and self.data_inicio:
            self.tempo_atendimento = self.data_finalizacao - self.data_inicio
        super().save(*args, **kwargs)

    @property
    def tempo_atendimento_formatado(self):
        """Retorna tempo de atendimento formatado"""
        if not self.tempo_atendimento:
            return "N/A"

        total_seconds = self.tempo_atendimento.total_seconds()
        horas = int(total_seconds // 3600)
        minutos = int((total_seconds % 3600) // 60)

        if horas > 24:
            dias = horas // 24
            horas_restantes = horas % 24
            return f"{dias}d {horas_restantes}h {minutos}min"
        elif horas > 0:
            return f"{horas}h {minutos}min"
        else:
            return f"{minutos}min"

    @property
    def tempo_decorrido(self):
        """Calcula tempo decorrido desde o início (para atendimentos em andamento)"""
        if self.status == 'FINALIZADO' and self.tempo_atendimento:
            return self.tempo_atendimento
        elif self.data_inicio:
            from django.utils import timezone
            return timezone.now() - self.data_inicio
        return None

    @property
    def tempo_decorrido_formatado(self):
        """Retorna tempo decorrido formatado"""
        tempo = self.tempo_decorrido
        if not tempo:
            return "N/A"

        total_seconds = tempo.total_seconds()
        horas = int(total_seconds // 3600)
        minutos = int((total_seconds % 3600) // 60)

        if horas > 24:
            dias = horas // 24
            horas_restantes = horas % 24
            return f"{dias}d {horas_restantes}h {minutos}min"
        elif horas > 0:
            return f"{horas}h {minutos}min"
        else:
            return f"{minutos}min"

    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge do status"""
        classes = {
            'EM_ANDAMENTO': 'bg-primary',
            'PAUSADO': 'bg-warning',
            'FINALIZADO': 'bg-success',
            'CANCELADO': 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')

    def pode_ser_editado_por(self, usuario):
        """Verifica se o usuário pode editar este atendimento"""
        # Admin e Supervisor podem editar qualquer atendimento
        if hasattr(usuario, 'perfil') and usuario.perfil.codigo_perfil in ['ADMIN', 'SUPERVISOR']:
            return True

        # Mecânico que criou pode editar
        if self.mecanico == usuario:
            return True

        # Outros mecânicos da mesma empresa podem editar/finalizar
        if hasattr(usuario, 'perfil') and hasattr(self.mecanico, 'perfil'):
            return usuario.perfil.empresa == self.mecanico.perfil.empresa

        return False
