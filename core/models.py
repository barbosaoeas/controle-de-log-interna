from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class Empresa(models.Model):
    """Modelo para empresas terceirizadas e a própria empresa"""
    TIPO_CHOICES = [
        ('PROPRIA', 'Empresa Própria'),
        ('TERCEIRIZADA', 'Empresa Terceirizada'),
    ]

    nome = models.CharField(max_length=200, unique=True, help_text="Nome da empresa")
    cnpj = models.CharField(max_length=18, blank=True, help_text="CNPJ da empresa (formato: 00.000.000/0000-00)")
    contrato = models.CharField(max_length=100, blank=True, help_text="Número do contrato")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='TERCEIRIZADA', help_text="Tipo da empresa")
    contato = models.CharField(max_length=100, blank=True, help_text="Nome do contato principal")
    telefone = models.CharField(max_length=20, blank=True, help_text="Telefone de contato")
    email = models.EmailField(blank=True, help_text="E-mail de contato")
    observacoes = models.TextField(blank=True, help_text="Observações sobre a empresa")
    ativo = models.BooleanField(default=True, help_text="Empresa ativa no sistema")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Setor(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    responsavel = models.CharField(max_length=100, blank=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Area(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    localizacao = models.CharField(max_length=200, blank=True)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    documento = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class CategoriaEquipamento(models.Model):
    """Modelo para categorias de equipamentos"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=20, default='primary', help_text="Cor do badge (primary, success, warning, danger, info, secondary, dark)")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoria de Equipamento'
        verbose_name_plural = 'Categorias de Equipamentos'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Equipamento(models.Model):
    CATEGORIA_CHOICES = [
        ('TRATOR', 'Trator'),
        ('PRANCHA_REBOQUE', 'Prancha Reboque'),
        ('EMPILHADEIRA', 'Empilhadeira'),
        ('CAMINHAO_MUNCK', 'Caminhão Munck'),
        ('CARRETA_HIDRAULICA', 'Carreta Hidráulica'),
        ('GUINDASTE_RODOVIARIO', 'Guindaste Rodoviário'),
        ('CAVALO_MECANICO', 'Cavalo Mecânico'),
        ('OUTROS', 'Outros'),
    ]

    STATUS_CHOICES = [
        ('OPERACIONAL', 'Operacional'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('FORA_SERVICO', 'Fora de Serviço'),
        ('INATIVO', 'Inativo'),
    ]

    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='MATERIAL')
    status_operacional = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPERACIONAL',
        help_text="OPERACIONAL=disponível, MANUTENCAO=em reparo (aparece desabilitado), FORA_SERVICO=temporariamente indisponível, INATIVO=permanentemente inativo"
    )
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True, help_text="Desmarcado = equipamento excluído do sistema")

    # Campos específicos para veículos/diesel
    placa = models.CharField(max_length=10, blank=True, help_text="Placa do veículo (se aplicável)")
    modelo = models.CharField(max_length=100, blank=True, help_text="Modelo do equipamento/veículo")
    ano = models.IntegerField(null=True, blank=True, help_text="Ano de fabricação")
    capacidade_tanque = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Capacidade do tanque em litros (para veículos)"
    )
    consumo_medio = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Consumo médio em km/litro (para veículos)"
    )
    quantidade_litros = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Quantidade de litros que o equipamento pode armazenar ou consumir"
    )
    tem_agenda = models.BooleanField(
        default=True,
        verbose_name="Com Agenda",
        help_text="Se marcado, o equipamento aparecerá nas opções de agendamento de pedidos"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}" if self.codigo else self.nome

    @property
    def is_operacional(self):
        """Verifica se o equipamento está operacional e disponível"""
        return self.status_operacional == 'OPERACIONAL' and self.ativo

    @property
    def is_em_manutencao(self):
        """Verifica se o equipamento está em manutenção"""
        return self.status_operacional == 'MANUTENCAO'

    @property
    def is_fora_servico(self):
        """Verifica se o equipamento está fora de serviço"""
        return self.status_operacional == 'FORA_SERVICO'

    @property
    def aparece_no_select(self):
        """
        Verifica se o equipamento deve aparecer no select de pedidos.
        Aparece: OPERACIONAL ou MANUTENCAO (desabilitado)
        Não aparece: FORA_SERVICO, INATIVO ou ativo=False
        """
        if not self.ativo:
            return False
        return self.status_operacional in ['OPERACIONAL', 'MANUTENCAO']

    @property
    def disponivel_para_pedido(self):
        """
        Verifica se o equipamento pode ser selecionado para pedido.
        Só OPERACIONAL pode ser selecionado.
        """
        return self.ativo and self.status_operacional == 'OPERACIONAL'

    @property
    def status_display(self):
        """Retorna o status formatado para exibição"""
        if not self.ativo:
            return "Excluído"
        return self.get_status_operacional_display()

    @property
    def status_css_class(self):
        """Retorna a classe CSS baseada no status"""
        if not self.ativo:
            return "text-muted"
        status_classes = {
            'OPERACIONAL': 'text-success',
            'MANUTENCAO': 'text-warning',
            'FORA_SERVICO': 'text-danger',
            'INATIVO': 'text-muted',
        }
        return status_classes.get(self.status_operacional, 'text-secondary')

    @property
    def status_badge_class(self):
        """Retorna a classe CSS para badge"""
        if not self.ativo:
            return "bg-secondary"
        badge_classes = {
            'OPERACIONAL': 'bg-success',
            'MANUTENCAO': 'bg-warning text-dark',
            'FORA_SERVICO': 'bg-danger',
            'INATIVO': 'bg-secondary',
        }
        return badge_classes.get(self.status_operacional, 'bg-secondary')

    @property
    def status_icon(self):
        """Retorna o ícone baseado no status"""
        if not self.ativo:
            return "bi-x-circle"
        icons = {
            'OPERACIONAL': 'bi-check-circle-fill',
            'MANUTENCAO': 'bi-tools',
            'FORA_SERVICO': 'bi-pause-circle-fill',
            'INATIVO': 'bi-dash-circle',
        }
        return icons.get(self.status_operacional, 'bi-question-circle')

    @property
    def is_veiculo(self):
        """Verifica se é um veículo (tem placa)"""
        return bool(self.placa)

    @property
    def pode_ser_abastecido(self):
        """Verifica se pode ser abastecido (veículos ativos)"""
        return self.is_veiculo and self.ativo

    @property
    def pode_ser_agendado(self):
        """Verifica se pode aparecer no agendamento"""
        return self.is_operacional and self.tem_agenda

    # Propriedade de compatibilidade (será removida após migração)
    @property
    def em_servico(self):
        """DEPRECATED: Use status_operacional. Mantido para compatibilidade."""
        return self.status_operacional not in ['FORA_SERVICO', 'INATIVO']

    def tem_agenda_display(self):
        """Retorna uma representação visual do status de agenda"""
        return "✅ Com Agenda" if self.tem_agenda else "❌ Sem Agenda"


class TipoPerfil(models.Model):
    """Modelo para tipos de perfil de acesso - substitui PERFIL_CHOICES hardcoded"""
    codigo = models.CharField(
        max_length=50,
        unique=True,
        help_text='Código único do perfil (ex: ADMIN, SUPERVISOR)'
    )
    nome = models.CharField(
        max_length=200,
        help_text='Nome do perfil'
    )
    descricao = models.TextField(
        blank=True,
        help_text='Descrição detalhada do perfil e suas permissões'
    )
    permissoes_resumo = models.TextField(
        blank=True,
        help_text='Resumo das permissões do perfil'
    )

    # Flags de permissões
    is_admin = models.BooleanField(
        default=False,
        help_text='Perfil tem privilégios de administrador'
    )
    is_supervisor = models.BooleanField(
        default=False,
        help_text='Perfil tem privilégios de supervisor'
    )
    is_terceiro = models.BooleanField(
        default=False,
        help_text='Perfil é de terceiro (requer empresa vinculada)'
    )

    # Controle
    ativo = models.BooleanField(
        default=True,
        help_text='Perfil está ativo e disponível para uso'
    )
    is_sistema = models.BooleanField(
        default=False,
        help_text='Perfil do sistema (não pode ser excluído pelo usuário)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tipo de Perfil'
        verbose_name_plural = 'Tipos de Perfis'
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    @property
    def is_admin_ou_supervisor(self):
        """Verifica se é admin ou supervisor"""
        return self.is_admin or self.is_supervisor

    def pode_ser_excluido(self):
        """Verifica se o perfil pode ser excluído"""
        if self.is_sistema:
            return False, "Perfis do sistema não podem ser excluídos"

        # Verificar se há usuários usando este perfil
        usuarios_count = self.perfilusuario_set.count()
        if usuarios_count > 0:
            return False, f"Existem {usuarios_count} usuário(s) usando este perfil"

        return True, "Pode ser excluído"


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)

    # ForeignKey para TipoPerfil (substitui CharField com choices)
    tipo_perfil = models.ForeignKey(
        TipoPerfil,
        on_delete=models.PROTECT,  # Não permite excluir tipo se houver usuários
        related_name='perfilusuario_set',
        help_text='Tipo de perfil do usuário'
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True,
                                help_text="Empresa à qual o usuário pertence (obrigatório para terceiros)")
    telefone = models.CharField(max_length=20, blank=True)
    disponivel = models.BooleanField(default=True, help_text="Técnico disponível para atender chamados")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Controle de primeira senha
    precisa_alterar_senha = models.BooleanField(default=True, help_text="Usuário precisa alterar senha no primeiro login")
    senha_alterada_em = models.DateTimeField(null=True, blank=True, help_text="Data da última alteração de senha")

    # Campos para localização em tempo real
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, help_text="Latitude da localização atual")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, help_text="Longitude da localização atual")
    ultima_localizacao = models.DateTimeField(null=True, blank=True, help_text="Última vez que a localização foi atualizada")
    status_online = models.BooleanField(default=False, help_text="Usuário está online e compartilhando localização")
    precisao_gps = models.FloatField(null=True, blank=True, help_text="Precisão do GPS em metros")

    # Configurações de localização
    DISTANCIA_MAXIMA_METROS = 50  # Margem de erro aceitável em metros

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.setor.nome}"

    def clean(self):
        """Validação customizada do modelo"""
        from django.core.exceptions import ValidationError

        # Validar que terceiros tenham empresa vinculada
        if self.tipo_perfil and self.tipo_perfil.is_terceiro and not self.empresa:
            raise ValidationError({
                'empresa': 'Empresa é obrigatória para usuários terceirizados.'
            })

    def save(self, *args, **kwargs):
        """Override save para executar validação"""
        self.clean()
        super().save(*args, **kwargs)

    # ===== PROPRIEDADES BASEADAS EM tipo_perfil =====

    @property
    def codigo_perfil(self):
        """Retorna o código do perfil"""
        return self.tipo_perfil.codigo

    @property
    def nome_perfil(self):
        """Retorna o nome do perfil"""
        return self.tipo_perfil.nome

    @property
    def is_transportes(self):
        return self.tipo_perfil.codigo == 'TRANSPORTES'

    @property
    def is_demandante(self):
        return self.tipo_perfil.codigo == 'DEMANDANTE'

    @property
    def is_supervisor(self):
        return self.tipo_perfil.is_supervisor

    @property
    def is_admin(self):
        return self.tipo_perfil.is_admin

    @property
    def is_manutencao(self):
        """Verifica se é qualquer tipo de manutenção (interna ou terceiro)"""
        codigo = self.tipo_perfil.codigo
        return codigo.startswith('MANUTENCAO') or codigo.startswith('TERCEIRO_MANUTENCAO')

    @property
    def is_manutencao_interna(self):
        """Verifica se é manutenção interna (funcionário)"""
        return self.tipo_perfil.codigo.startswith('MANUTENCAO')

    @property
    def is_terceiro(self):
        """Verifica se é terceiro credenciado"""
        return self.tipo_perfil.is_terceiro

    @property
    def especialidade_manutencao(self):
        """Retorna a especialidade de manutenção"""
        codigo = self.tipo_perfil.codigo
        if codigo.startswith('MANUTENCAO_'):
            return codigo.replace('MANUTENCAO_', '')
        elif codigo.startswith('TERCEIRO_MANUTENCAO_'):
            return codigo.replace('TERCEIRO_MANUTENCAO_', '')
        elif codigo == 'MANUTENCAO':
            return 'GERAL'
        return None

    @property
    def is_admin_ou_supervisor(self):
        """Verifica se é admin, supervisor, transportes ou manutenção"""
        return self.tipo_perfil.is_admin_ou_supervisor

    @property
    def is_empresa_propria(self):
        """Verifica se pertence à empresa própria"""
        return self.empresa is None or self.empresa.tipo == 'PROPRIA'

    @property
    def is_empresa_terceirizada(self):
        """Verifica se pertence a empresa terceirizada"""
        return self.empresa is not None and self.empresa.tipo == 'TERCEIRIZADA'

    def marcar_senha_alterada(self):
        """Marca que o usuário alterou a senha"""
        from django.utils import timezone
        self.precisa_alterar_senha = False
        self.senha_alterada_em = timezone.now()
        self.save()

    @property
    def nome_empresa(self):
        """Retorna o nome da empresa ou 'Estaleiro Atlântico Sul' se for própria"""
        if self.empresa:
            return self.empresa.nome
        return 'Estaleiro Atlântico Sul'

    def get_chamados_manutencao_abertos_count(self):
        """Retorna quantidade de chamados de MANUTENÇÃO (frota_locada) abertos atribuídos ao usuário"""
        try:
            from frota_locada.models import ChamadoManutencao
            return ChamadoManutencao.objects.filter(
                mecanico=self.user,
                status__in=['AGUARDANDO', 'EM_ATENDIMENTO']
            ).count()
        except:
            return 0

    @property
    def pode_cadastrar(self):
        """Admins, Supervisores, Transportes e Manutenção podem cadastrar"""
        codigo = self.tipo_perfil.codigo
        return codigo in ['ADMIN', 'SUPERVISOR', 'TRANSPORTES'] or self.is_manutencao

    @property
    def pode_gerenciar_pedidos(self):
        """Admins, Supervisores, Transportes e Manutenção podem gerenciar todos os pedidos"""
        codigo = self.tipo_perfil.codigo
        return codigo in ['ADMIN', 'SUPERVISOR', 'TRANSPORTES'] or self.is_manutencao

    @property
    def pode_iniciar_finalizar(self):
        """Transportes, Manutenção, Admins e Supervisores podem iniciar e finalizar atendimentos"""
        codigo = self.tipo_perfil.codigo
        return codigo in ['TRANSPORTES', 'ADMIN', 'SUPERVISOR'] or self.is_manutencao

    @property
    def tem_localizacao(self):
        """Verifica se o usuário tem localização definida"""
        return self.latitude is not None and self.longitude is not None

    @property
    def localizacao_atualizada(self):
        """Verifica se a localização foi atualizada recentemente (últimos 5 minutos)"""
        if not self.ultima_localizacao:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.ultima_localizacao < timedelta(minutes=5)

    @property
    def status_localizacao(self):
        """Retorna o status da localização do usuário"""
        if not self.tem_localizacao:
            return 'sem_localizacao'
        elif self.localizacao_atualizada and self.status_online:
            return 'online'
        elif self.localizacao_atualizada:
            return 'recente'
        else:
            return 'desatualizada'

    def atualizar_localizacao(self, latitude, longitude, precisao=None):
        """Atualiza a localização do usuário com validação de precisão"""
        from django.utils import timezone

        # Só atualiza se a precisão for boa (menor que 50m) ou se for a primeira localização
        if precisao and precisao > 50 and self.tem_localizacao:
            print(f"⚠️ Localização rejeitada para {self.user.username}: precisão {precisao}m muito baixa")
            return False

        # Se a nova localização tem melhor precisão, sempre atualiza
        if precisao and self.precisao_gps and precisao < self.precisao_gps:
            print(f"✅ Melhor precisão para {self.user.username}: {precisao}m (era {self.precisao_gps}m)")

        self.latitude = latitude
        self.longitude = longitude
        self.precisao_gps = precisao
        self.ultima_localizacao = timezone.now()
        self.status_online = True
        self.save(update_fields=['latitude', 'longitude', 'precisao_gps', 'ultima_localizacao', 'status_online'])

        print(f"📍 Localização atualizada para {self.user.username}: {latitude}, {longitude} (±{precisao}m)")
        return True

    def calcular_distancia(self, lat2, lng2):
        """Calcula a distância em metros entre a localização atual e um ponto"""
        if not self.tem_localizacao:
            return None

        import math

        # Converter para radianos
        lat1_rad = math.radians(float(self.latitude))
        lng1_rad = math.radians(float(self.longitude))
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)

        # Fórmula de Haversine
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Raio da Terra em metros
        raio_terra = 6371000

        return raio_terra * c

    def esta_proximo_de(self, lat2, lng2, distancia_maxima=None):
        """Verifica se está próximo de um local (dentro da margem de erro)"""
        if distancia_maxima is None:
            distancia_maxima = self.DISTANCIA_MAXIMA_METROS

        distancia = self.calcular_distancia(lat2, lng2)
        if distancia is None:
            return False

        return distancia <= distancia_maxima

    @property
    def pode_editar_pedidos(self):
        """Admins e Supervisores podem editar/excluir pedidos. Transportes só visualizam e controlam status"""
        return self.tipo_perfil.codigo in ['ADMIN', 'SUPERVISOR']

    @property
    def pode_criar_pedidos(self):
        """Verifica se é um perfil que pode criar pedidos (não transportes)"""
        return self.tipo_perfil.codigo in ['ADMIN', 'SUPERVISOR', 'DEMANDANTE']

    @property
    def pode_abrir_chamados_manutencao(self):
        """Perfis que podem abrir chamados de manutenção de PTAs"""
        return self.tipo_perfil.codigo in ['ADMIN', 'SUPERVISOR', 'MANUTENCAO_CONT_PTA', 'CONTROLE_MAN_PTA', 'CONTROLE_PROD_PTA']

    def resetar_senha_padrao(self):
        """Reseta a senha do usuário para 123456"""
        self.user.set_password('123456')
        self.user.save()
        self.precisa_alterar_senha = True
        self.senha_alterada_em = None
        self.save()

    def marcar_senha_alterada(self):
        """Marca que o usuário alterou a senha"""
        from django.utils import timezone
        self.precisa_alterar_senha = False
        self.senha_alterada_em = timezone.now()
        self.save()


# DescricaoPerfil foi removido - agora usamos TipoPerfil


class LocalTrabalho(models.Model):
    """Locais onde os operadores devem trabalhar - Estaleiro Atlântico Sul"""
    nome = models.CharField(max_length=100, help_text="Nome do local de trabalho")
    descricao = models.TextField(blank=True, help_text="Descrição do local")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, help_text="Latitude do local")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, help_text="Longitude do local")
    raio_metros = models.IntegerField(default=50, help_text="Raio de tolerância em metros")
    ativo = models.BooleanField(default=True, help_text="Local está ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Local de Trabalho'
        verbose_name_plural = 'Locais de Trabalho'

    def __str__(self):
        return f"{self.nome} - Estaleiro Atlântico Sul"

    def operador_esta_no_local(self, operador):
        """Verifica se um operador está neste local"""
        if not operador.tem_localizacao:
            return False
        return operador.esta_proximo_de(float(self.latitude), float(self.longitude), self.raio_metros)


class Pedido(models.Model):
    TIPO_CHOICES = [
        ('ENTREGA', 'Entrega'),
        ('RECOLHIMENTO', 'Recolhimento'),
    ]

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]

    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('KG', 'Quilograma'),
        ('M', 'Metro'),
        ('M2', 'Metro Quadrado'),
        ('M3', 'Metro Cúbico'),
        ('L', 'Litro'),
        ('CX', 'Caixa'),
        ('PC', 'Peça'),
    ]

    # Campos principais
    setor_solicitante = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='pedidos')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    area_origem = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_origem')
    area_destino = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_destino')
    equipamento = models.ForeignKey(Equipamento, on_delete=models.SET_NULL, null=True, blank=True)

    # Detalhes do pedido
    tipo_pedido = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField()
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unidade_medida = models.CharField(max_length=5, choices=UNIDADE_CHOICES, default='UN')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='MEDIA')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')

    # Datas
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    # 📅 Data de agendamento - quando o serviço deve ser executado
    data_agendamento = models.DateField(
        default=timezone.now,
        help_text="Data para execução do serviço. Padrão: hoje"
    )

    # ⏰ Hora desejada para o atendimento (opcional)
    hora_agendamento = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora desejada para execução do serviço (opcional)"
    )

    # Observações e controle
    observacoes = models.TextField(blank=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos_criados')
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_atualizados')

    # Nome do requisitante (usuário que fez o pedido)
    nome_requisitante = models.CharField(max_length=200, blank=True)

    # Ordem manual para priorização
    ordem_manual = models.IntegerField(default=0)

    # 📸 Foto do material a ser transportado (opcional)
    foto_material = models.ImageField(
        upload_to='materiais/',
        null=True,
        blank=True,
        help_text="Foto do material a ser transportado (opcional)"
    )

    # Foto de comprovação do serviço
    foto_comprovacao = models.ImageField(upload_to='comprovacoes/', null=True, blank=True, help_text="Foto para comprovar a conclusão do serviço")

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-prioridade', 'ordem_manual', 'data_solicitacao']

    def __str__(self):
        return f"#{self.id} - {self.setor_solicitante.nome} - {self.get_tipo_pedido_display()}"

    def save(self, *args, **kwargs):
        # Atualizar datas baseado no status
        if self.status == 'EM_ANDAMENTO' and not self.data_inicio:
            self.data_inicio = timezone.now()
        elif self.status == 'CONCLUIDO' and not self.data_conclusao:
            self.data_conclusao = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_agendado_hoje(self):
        """Verifica se o pedido está agendado para hoje"""
        return self.data_agendamento == timezone.now().date()

    @property
    def is_agendado_futuro(self):
        """
        Verifica se o horário agendado ainda não chegou.
        Considera data + hora (ou 7:30 se hora não informada).
        """
        from datetime import datetime, time as dt_time

        if not self.data_agendamento:
            return False

        # Se a data é futura, é futuro
        if self.data_agendamento > timezone.now().date():
            return True

        # Se a data é hoje, verifica a hora
        if self.data_agendamento == timezone.now().date():
            hora_ref = self.hora_agendamento if self.hora_agendamento else dt_time(7, 30)
            datetime_agendado = timezone.make_aware(
                datetime.combine(self.data_agendamento, hora_ref)
            )
            return datetime_agendado > timezone.now()

        return False

    @property
    def tempo_pendente(self):
        """Tempo que o pedido está pendente (em horas)"""
        if self.status == 'PENDENTE':
            delta = timezone.now() - self.data_solicitacao
            return delta.total_seconds() / 3600  # Retorna em horas
        return None

    # Hora padrão de início do turno (quando não informar hora)
    HORA_INICIO_TURNO = 7  # 7:30 da manhã
    MINUTO_INICIO_TURNO = 30

    @property
    def datetime_agendamento(self):
        """
        Retorna o datetime completo do agendamento (data + hora).
        Se não tiver hora, usa 7:30 (início do turno).
        """
        from datetime import datetime, time as dt_time

        if not self.data_agendamento:
            return self.data_solicitacao

        # Se tem hora agendada, usa ela; senão usa 7:30 (início do turno)
        if self.hora_agendamento:
            hora_ref = self.hora_agendamento
        else:
            hora_ref = dt_time(self.HORA_INICIO_TURNO, self.MINUTO_INICIO_TURNO)

        return timezone.make_aware(
            datetime.combine(self.data_agendamento, hora_ref)
        )

    @property
    def tempo_ate_inicio(self):
        """
        Tempo entre o início da contagem e início do atendimento (em horas).

        REGRA: O tempo de espera começa a contar do MAIOR entre:
        - datetime_agendamento (data + hora agendada)
        - data_solicitacao (quando o pedido foi criado)

        Isso evita que pedidos criados APÓS o horário agendado mostrem tempo inflado.
        Ex: Se agendado para 07:30 mas criado às 15:21, conta a partir de 15:21.
        """
        agora = timezone.now()
        datetime_agendado = self.datetime_agendamento

        # Usar o MAIOR entre data_agendamento e data_solicitacao
        # Isso evita contar tempo antes do pedido ser criado
        inicio_contagem = max(datetime_agendado, self.data_solicitacao)

        # Se ainda não chegou o horário de início da contagem, não conta tempo de espera
        if inicio_contagem > agora:
            return None

        if self.data_inicio:
            # Se já iniciou, calcula tempo entre início da contagem e início real
            if self.data_inicio >= inicio_contagem:
                delta = self.data_inicio - inicio_contagem
            else:
                # Se iniciou antes do horário de contagem (adiantado), tempo = 0
                return 0
            return delta.total_seconds() / 3600  # Retorna em horas
        elif self.status == 'PENDENTE':
            # Se ainda está pendente, mostra tempo desde início da contagem até agora
            delta = agora - inicio_contagem
            return max(0, delta.total_seconds() / 3600)  # Não retorna negativo
        return None

    @property
    def tempo_ate_inicio_formatado(self):
        """Tempo até início formatado como string"""
        from datetime import time as dt_time

        # Se agendado para o futuro, mostrar mensagem especial
        if self.is_agendado_futuro and self.status == 'PENDENTE':
            hoje = timezone.now().date()
            dias_ate = (self.data_agendamento - hoje).days

            # Hora agendada (ou 7:30 padrão)
            hora_ref = self.hora_agendamento if self.hora_agendamento else dt_time(7, 30)
            hora_str = hora_ref.strftime("%H:%M")

            if dias_ate == 0:
                # É hoje, mas ainda não chegou a hora
                return f"Às {hora_str}"
            elif dias_ate == 1:
                return f"Amanhã {hora_str}"
            else:
                return f"Em {dias_ate}d às {hora_str}"

        tempo = self.tempo_ate_inicio
        if tempo is None:
            return "-"

        if tempo < 1:
            minutos = int(tempo * 60)
            return f"{minutos}min"
        elif tempo < 24:
            horas = int(tempo)
            minutos = int((tempo - horas) * 60)
            if minutos > 0:
                return f"{horas}h {minutos}min"
            else:
                return f"{horas}h"
        else:
            dias = int(tempo / 24)
            horas_restantes = int(tempo % 24)
            if horas_restantes > 0:
                return f"{dias}d {horas_restantes}h"
            else:
                return f"{dias}d"

    @property
    def cor_tempo_espera(self):
        """Retorna classes CSS baseadas no tempo de espera"""
        # Se agendado para o futuro, cor neutra (azul info)
        if self.is_agendado_futuro and self.status == 'PENDENTE':
            return "text-info"

        tempo = self.tempo_ate_inicio
        if tempo is None:
            return "text-muted"

        if tempo < 2:  # Menos de 2 horas - verde
            return "text-success tempo-indicator"
        elif tempo < 8:  # Menos de 8 horas - amarelo
            return "text-warning tempo-indicator"
        elif tempo < 24:  # Menos de 24 horas - laranja
            return "text-orange tempo-indicator"
        elif tempo < 48:  # Menos de 48 horas - vermelho
            return "text-danger tempo-indicator"
        else:  # Mais de 48 horas - vermelho piscando
            return "text-danger tempo-indicator tempo-critico"

    @property
    def tempo_atendimento(self):
        """Tempo de atendimento entre início e conclusão (em horas)"""
        if self.data_inicio and self.data_conclusao:
            delta = self.data_conclusao - self.data_inicio
            return delta.total_seconds() / 3600  # Retorna em horas
        elif self.data_inicio and self.status == 'EM_ANDAMENTO':
            # Se está em andamento, mostra tempo atual desde o início
            delta = timezone.now() - self.data_inicio
            return delta.total_seconds() / 3600  # Retorna em horas
        return None

    @property
    def tempo_atendimento_formatado(self):
        """Tempo de atendimento formatado como string"""
        tempo = self.tempo_atendimento
        if tempo is None:
            return "-"

        if tempo < 1:
            minutos = int(tempo * 60)
            return f"{minutos}min"
        elif tempo < 24:
            horas = int(tempo)
            minutos = int((tempo - horas) * 60)
            if minutos > 0:
                return f"{horas}h {minutos}min"
            else:
                return f"{horas}h"
        else:
            dias = int(tempo / 24)
            horas_restantes = int(tempo % 24)
            if horas_restantes > 0:
                return f"{dias}d {horas_restantes}h"
            else:
                return f"{dias}d"

    @property
    def cor_tempo_atendimento(self):
        """Retorna classes CSS baseadas no tempo de atendimento"""
        tempo = self.tempo_atendimento
        if tempo is None:
            return "text-muted"

        if self.status == 'EM_ANDAMENTO':
            # Para pedidos em andamento, usar cores de alerta baseado no tempo
            if tempo < 4:  # Menos de 4 horas - azul (normal)
                return "text-primary tempo-indicator"
            elif tempo < 8:  # Menos de 8 horas - amarelo (atenção)
                return "text-warning tempo-indicator"
            else:  # Mais de 8 horas - vermelho (crítico)
                return "text-danger tempo-indicator"
        else:
            # Para pedidos concluídos, usar verde
            return "text-success tempo-indicator"

    @property
    def is_urgente(self):
        return self.prioridade == 'URGENTE'


class HistoricoPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=20, blank=True)
    status_novo = models.CharField(max_length=20)
    observacao = models.TextField(blank=True)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Histórico do Pedido'
        verbose_name_plural = 'Histórico dos Pedidos'
        ordering = ['-data_alteracao']

    def __str__(self):
        return f"Pedido #{self.pedido.id} - {self.status_anterior} → {self.status_novo}"


# ===== MODELOS PARA CONTROLE DE DIESEL =====

class Veiculo(models.Model):
    """Modelo para veículos da frota"""
    TIPO_CHOICES = [
        ('CAMINHAO', 'Caminhão'),
        ('CARRETA', 'Carreta'),
        ('TRATOR', 'Trator'),
        ('EMPILHADEIRA', 'Empilhadeira'),
        ('MUNCK', 'Munck'),
        ('GUINDASTE', 'Guindaste'),
        ('OUTROS', 'Outros'),
    ]

    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('INATIVO', 'Inativo'),
    ]

    # Informações básicas
    nome = models.CharField(max_length=200, help_text="Nome/identificação do veículo")
    placa = models.CharField(max_length=10, unique=True, help_text="Placa do veículo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='CAMINHAO')
    modelo = models.CharField(max_length=100, blank=True, help_text="Modelo do veículo")
    ano = models.IntegerField(null=True, blank=True, help_text="Ano de fabricação")

    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    tem_agenda = models.BooleanField(
        default=True,
        verbose_name="Com Agenda",
        help_text="Se marcado, o veículo aparecerá nas opções de agendamento de pedidos"
    )

    # Informações técnicas para diesel
    capacidade_tanque = models.DecimalField(
        max_digits=8, decimal_places=2, default=200.00,
        help_text="Capacidade do tanque do veículo em litros"
    )
    consumo_medio = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Consumo médio em km/litro"
    )

    # Controle
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.placa})"

    def tem_agenda_display(self):
        """Retorna uma representação visual do status de agenda"""
        return "✅ Com Agenda" if self.tem_agenda else "❌ Sem Agenda"
    tem_agenda_display.short_description = 'Status Agenda'

    @property
    def is_ativo(self):
        """Verifica se o veículo está ativo"""
        return self.status == 'ATIVO' and self.ativo

    @property
    def pode_ser_agendado(self):
        """Verifica se pode aparecer no agendamento"""
        return self.is_ativo and self.tem_agenda

    @property
    def pode_ser_abastecido(self):
        """Verifica se pode ser abastecido"""
        return self.ativo  # Todos os veículos ativos podem ser abastecidos

    @property
    def status_display(self):
        """Status formatado para exibição"""
        if not self.ativo:
            return "Inativo"
        return self.get_status_display()

    @property
    def status_css_class(self):
        """Classe CSS baseada no status"""
        if not self.ativo:
            return "text-muted"
        elif self.status == 'ATIVO':
            return "text-success"
        elif self.status == 'MANUTENCAO':
            return "text-warning"
        else:
            return "text-danger"


class ConfiguracaoTanque(models.Model):
    """Configuração do tanque principal de diesel"""
    capacidade_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=15000.00,
        help_text="Capacidade total do tanque em litros"
    )
    capacidade_extra = models.DecimalField(
        max_digits=10, decimal_places=2, default=5000.00,
        help_text="Capacidade do tanque extra para recebimento"
    )
    nivel_atual = models.DecimalField(
        max_digits=10, decimal_places=2, default=15000.00,
        help_text="Nível atual de diesel no tanque"
    )
    nivel_alerta = models.DecimalField(
        max_digits=10, decimal_places=2, default=5000.00,
        help_text="Nível de alerta (amarelo) em litros"
    )
    nivel_critico = models.DecimalField(
        max_digits=10, decimal_places=2, default=2000.00,
        help_text="Nível crítico (vermelho) em litros"
    )
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Configuração do Tanque'
        verbose_name_plural = 'Configurações do Tanque'

    def __str__(self):
        return f"Tanque Principal - {self.nivel_atual}L / {self.capacidade_total}L"

    @property
    def percentual_atual(self):
        """Percentual atual do tanque"""
        if self.capacidade_total > 0:
            return (float(self.nivel_atual) / float(self.capacidade_total)) * 100
        return 0

    @property
    def status_nivel(self):
        """Status do nível do tanque baseado nos níveis configuráveis"""
        if self.nivel_atual > self.nivel_alerta:
            return 'VERDE'
        elif self.nivel_atual >= self.nivel_critico:
            return 'AMARELO'
        else:
            return 'VERMELHO'

    @property
    def status_css_class(self):
        """Classe CSS baseada no status"""
        status = self.status_nivel
        if status == 'VERDE':
            return 'text-success'
        elif status == 'AMARELO':
            return 'text-warning'
        else:
            return 'text-danger'

    def pode_abastecer(self, quantidade):
        """Verifica se há diesel suficiente para abastecer"""
        return self.nivel_atual >= quantidade

    def abastecer_veiculo(self, quantidade):
        """Subtrai a quantidade abastecida do tanque"""
        if self.pode_abastecer(quantidade):
            self.nivel_atual -= quantidade
            self.save()
            return True
        return False

    @property
    def capacidade_total_recebimento(self):
        """Capacidade total para recebimento (tanque principal + extra)"""
        return float(self.capacidade_total) + float(self.capacidade_extra)

    @property
    def espaco_disponivel_recebimento(self):
        """Espaço disponível para recebimento considerando tanque extra"""
        return float(self.capacidade_total_recebimento) - float(self.nivel_atual)

    def pode_receber(self, quantidade):
        """Verifica se pode receber a quantidade considerando tanque extra"""
        return self.nivel_atual + quantidade <= self.capacidade_total_recebimento

    def verificar_e_enviar_alertas(self):
        """Verifica o nível e envia alertas por email se necessário"""
        from datetime import timedelta

        # Importar aqui para evitar import circular
        AlertaDiesel = self.__class__._meta.apps.get_model('core', 'AlertaDiesel')

        agora = timezone.now()
        alertas_ativos = AlertaDiesel.objects.filter(ativo=True)

        for alerta in alertas_ativos:
            # Verificar alerta crítico
            if (self.status_nivel == 'VERMELHO' and alerta.alerta_critico and
                (not alerta.ultimo_alerta_critico or
                 agora - alerta.ultimo_alerta_critico > timedelta(hours=2))):

                self._enviar_email_alerta(alerta, 'critico')
                alerta.ultimo_alerta_critico = agora
                alerta.save()

            # Verificar alerta de atenção
            elif (self.status_nivel == 'AMARELO' and alerta.alerta_alerta and
                  (not alerta.ultimo_alerta_alerta or
                   agora - alerta.ultimo_alerta_alerta > timedelta(hours=4))):

                self._enviar_email_alerta(alerta, 'alerta')
                alerta.ultimo_alerta_alerta = agora
                alerta.save()

    def _enviar_email_alerta(self, alerta_config, tipo):
        """Envia email de alerta"""
        try:
            if tipo == 'critico':
                assunto = f"🚨 ALERTA CRÍTICO - Diesel em Nível Crítico ({self.nivel_atual}L)"
                template = 'emails/alerta_diesel_critico.html'
            else:
                assunto = f"⚠️ ATENÇÃO - Diesel em Nível de Alerta ({self.nivel_atual}L)"
                template = 'emails/alerta_diesel_alerta.html'

            contexto = {
                'destinatario': alerta_config.nome_destinatario,
                'nivel_atual': self.nivel_atual,
                'capacidade_total': self.capacidade_total,
                'percentual': self.percentual_atual,
                'status': self.status_nivel,
                'nivel_critico': self.nivel_critico,
                'nivel_alerta': self.nivel_alerta,
                'tipo_alerta': tipo
            }

            # Renderizar template HTML
            html_message = render_to_string(template, contexto)
            plain_message = strip_tags(html_message)

            send_mail(
                subject=assunto,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alerta_config.email_destinatario],
                html_message=html_message,
                fail_silently=False,
            )

            print(f"✅ Email de alerta {tipo} enviado para {alerta_config.email_destinatario}")

        except Exception as e:
            print(f"❌ Erro ao enviar email para {alerta_config.email_destinatario}: {e}")

    def save(self, *args, **kwargs):
        # Salvar primeiro
        super().save(*args, **kwargs)

        # Depois verificar alertas
        self.verificar_e_enviar_alertas()


class AbastecimentoTanque(models.Model):
    """Registro de chegada de diesel no tanque principal"""
    quantidade_litros = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantidade de diesel recebida em litros")
    valor_por_litro = models.DecimalField(max_digits=8, decimal_places=4, help_text="Valor pago por litro (R$)")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor total da compra (R$)")
    data_chegada = models.DateTimeField(help_text="Data e hora da chegada do diesel")
    fornecedor = models.CharField(max_length=200, blank=True, help_text="Nome do fornecedor")
    numero_nota_fiscal = models.CharField(max_length=50, blank=True, help_text="Número da nota fiscal")
    observacoes = models.TextField(blank=True, help_text="Observações sobre o abastecimento")
    operador = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que registrou a chegada")
    data_registro = models.DateTimeField(auto_now_add=True)

    # Campos para controle do tanque
    nivel_anterior = models.DecimalField(max_digits=10, decimal_places=2, help_text="Nível do tanque antes do abastecimento")
    nivel_posterior = models.DecimalField(max_digits=10, decimal_places=2, help_text="Nível do tanque após o abastecimento")

    class Meta:
        verbose_name = "Abastecimento do Tanque"
        verbose_name_plural = "Abastecimentos do Tanque"
        ordering = ['-data_chegada']

    def __str__(self):
        return f"{self.quantidade_litros}L - {self.data_chegada.strftime('%d/%m/%Y %H:%M')} - R$ {self.valor_total}"

    def save(self, *args, **kwargs):
        # Calcular valor total se não foi informado
        if not self.valor_total:
            self.valor_total = self.quantidade_litros * self.valor_por_litro

        # Atualizar nível do tanque
        tanque = ConfiguracaoTanque.objects.first()
        if tanque:
            if not self.pk:  # Novo registro
                self.nivel_anterior = tanque.nivel_atual
                tanque.nivel_atual += self.quantidade_litros
                self.nivel_posterior = tanque.nivel_atual
                tanque.save()

        super().save(*args, **kwargs)


class AlertaDiesel(models.Model):
    """Configuração de alertas por email para níveis críticos de diesel"""
    email_destinatario = models.EmailField(help_text="Email que receberá os alertas")
    nome_destinatario = models.CharField(max_length=100, help_text="Nome do destinatário")
    ativo = models.BooleanField(default=True, help_text="Se deve receber alertas")
    alerta_critico = models.BooleanField(default=True, help_text="Receber alerta de nível crítico")
    alerta_alerta = models.BooleanField(default=True, help_text="Receber alerta de nível de atenção")
    ultimo_alerta_critico = models.DateTimeField(null=True, blank=True, help_text="Último alerta crítico enviado")
    ultimo_alerta_alerta = models.DateTimeField(null=True, blank=True, help_text="Último alerta de atenção enviado")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Alerta de Diesel"
        verbose_name_plural = "Alertas de Diesel"
        ordering = ['nome_destinatario']

    def __str__(self):
        status = "✅" if self.ativo else "❌"
        return f"{status} {self.nome_destinatario} ({self.email_destinatario})"


class AbastecimentoVeiculo(models.Model):
    """Registro de abastecimento de veículos"""
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='abastecimentos')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, help_text="Cliente relacionado ao abastecimento")
    data_abastecimento = models.DateTimeField(default=timezone.now)
    quantidade_litros = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Quantidade de litros abastecida"
    )

    # Controle de odômetro
    odometro_atual = models.IntegerField(
        null=True, blank=True,
        help_text="Quilometragem atual do veículo"
    )
    odometro_anterior = models.IntegerField(
        null=True, blank=True,
        help_text="Quilometragem anterior (calculado automaticamente)"
    )
    km_rodados = models.IntegerField(
        null=True, blank=True,
        help_text="Quilômetros rodados desde o último abastecimento"
    )
    consumo_calculado = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Consumo calculado em km/litro"
    )

    # Controle
    operador = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuário que fez o abastecimento")
    observacoes = models.TextField(blank=True, help_text="Observações sobre o abastecimento")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Abastecimento de Veículo'
        verbose_name_plural = 'Abastecimentos de Veículos'
        ordering = ['-data_abastecimento']

    def __str__(self):
        return f"{self.veiculo.nome} - {self.quantidade_litros}L - {self.data_abastecimento.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        """Calcular dados automaticamente ao salvar"""
        # Buscar último abastecimento para calcular consumo
        if self.odometro_atual:
            ultimo_abastecimento = AbastecimentoVeiculo.objects.filter(
                veiculo=self.veiculo,
                odometro_atual__isnull=False
            ).exclude(id=self.id).order_by('-data_abastecimento').first()

            if ultimo_abastecimento and ultimo_abastecimento.odometro_atual:
                self.odometro_anterior = ultimo_abastecimento.odometro_atual
                self.km_rodados = self.odometro_atual - ultimo_abastecimento.odometro_atual

                # Calcular consumo (km rodados / litros do abastecimento anterior)
                if ultimo_abastecimento.quantidade_litros > 0 and self.km_rodados > 0:
                    self.consumo_calculado = self.km_rodados / ultimo_abastecimento.quantidade_litros

        super().save(*args, **kwargs)

        # Atualizar nível do tanque principal
        try:
            tanque = ConfiguracaoTanque.objects.first()
            if tanque:
                tanque.abastecer_veiculo(self.quantidade_litros)
        except Exception as e:
            print(f"Erro ao atualizar tanque: {e}")

    @property
    def consumo_display(self):
        """Consumo formatado para exibição"""
        if self.consumo_calculado:
            return f"{self.consumo_calculado:.2f} km/L"
        return "N/A"

    @property
    def eficiencia_css_class(self):
        """Classe CSS baseada na eficiência"""
        if not self.consumo_calculado:
            return "text-muted"
        elif self.consumo_calculado >= 8:
            return "text-success"  # Bom consumo
        elif self.consumo_calculado >= 5:
            return "text-warning"  # Consumo médio
        else:
            return "text-danger"   # Consumo alto
