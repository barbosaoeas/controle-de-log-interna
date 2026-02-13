from django.db import models
from django.contrib.auth.models import User
from core.models import Cliente


class TipoGas(models.Model):
    """Modelo para tipos de gases"""
    nome_gas = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome do Gás"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Gás"
        verbose_name_plural = "Tipos de Gases"
        ordering = ['nome_gas']

    def __str__(self):
        return self.nome_gas


class MovimentacaoGas(models.Model):
    """Modelo para movimentação de gases"""

    # Choices para unidade
    UNIDADE_CHOICES = [
        ('KG', 'Quilograma (KG)'),
        ('M3', 'Metro Cúbico (M³)'),
    ]

    # Choices para categoria de gás
    CATEGORIA_GAS_CHOICES = [
        ('ACETILENO', 'Acetileno'),
        ('ARGONIO', 'Argônio'),
        ('DIOXIDO_CARBONO', 'Dioxido Carbono'),
        ('GLP', 'GLP'),
        ('NITROGENIO', 'Nitrogênio'),
        ('OXIGENIO_MEDICINAL', 'Oxigênio Medicinal'),
        ('OXIGENIO', 'Oxigênio'),
        ]

    # Choices para fornecedor
    FORNECEDOR_CHOICES = [
        ('WHITE_MARTINS', 'White Martins'),
        ('ULTRA_GAS', 'Ultra Gas'),
        ('ULTRAGAZ_BAHIANA', 'Ultragaz/Bahiana'),
    ]

    data_entrega = models.DateField(verbose_name="Data de Entrega")
    nf = models.CharField(
        max_length=50,
        verbose_name="Nota Fiscal"
    )
    tipo_gas = models.ForeignKey(
        TipoGas,
        on_delete=models.CASCADE,
        verbose_name="Tipo de Gás"
    )
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantidade"
    )
    unidade = models.CharField(
        max_length=3,
        choices=UNIDADE_CHOICES,
        verbose_name="Unidade"
    )
    categoria_gas = models.CharField(
        max_length=50,
        choices=CATEGORIA_GAS_CHOICES,
        verbose_name="Categoria do Gás"
    )
    fornecedor = models.CharField(
        max_length=20,
        choices=FORNECEDOR_CHOICES,
        verbose_name="Fornecedor"
    )

    # Novos campos adicionados
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cliente"
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Unitário"
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Total"
    )

    # Campos de auditoria
    criado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Criado por"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Movimentação de Gás"
        verbose_name_plural = "Movimentações de Gases"
        ordering = ['-data_entrega', '-criado_em']

    def save(self, *args, **kwargs):
        """Calcular valor total automaticamente antes de salvar"""
        if self.valor_unitario and self.quantidade:
            self.valor_total = self.valor_unitario * self.quantidade
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_gas.nome_gas} - {self.quantidade} {self.unidade} - {self.data_entrega}"
