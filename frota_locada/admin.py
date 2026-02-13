from django.contrib import admin
from .models import (
    Fornecedor, TipoVeiculo, MarcaVeiculo, VeiculoLocado,
    TipoManutencao, ManutencaoVeiculo, HistoricoHorimetro,
    ChamadoManutencao
)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'empresa', 'telefone', 'email', 'ativo', 'data_cadastro']
    list_filter = ['ativo', 'empresa', 'data_cadastro']
    search_fields = ['nome', 'cnpj', 'email']
    ordering = ['nome']
    autocomplete_fields = ['empresa']


@admin.register(TipoVeiculo)
class TipoVeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']
    ordering = ['nome']


@admin.register(MarcaVeiculo)
class MarcaVeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'data_cadastro']
    list_filter = ['ativo', 'data_cadastro']
    search_fields = ['nome']
    ordering = ['nome']


@admin.register(VeiculoLocado)
class VeiculoLocadoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'marca', 'modelo', 'tipo_veiculo', 'fornecedor', 'status', 'locado_para', 'valor_mensal', 'horimetro_atual', 'data_cadastro']
    list_filter = ['status', 'locado_para', 'tipo_veiculo', 'fornecedor', 'data_cadastro']
    search_fields = ['placa', 'marca__nome', 'modelo', 'fornecedor__nome']
    ordering = ['-data_cadastro']
    readonly_fields = ['cadastrado_por', 'data_cadastro', 'horas_trabalhadas', 'dias_locacao', 'valor_total_estimado']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('placa', 'marca', 'modelo', 'ano_fabricacao', 'cor', 'tipo_veiculo')
        }),
        ('Fornecedor e Contrato', {
            'fields': ('fornecedor', 'numero_contrato', 'data_inicio_locacao', 'data_fim_locacao')
        }),
        ('Valores', {
            'fields': ('valor_mensal',)
        }),
        ('Status e Controle', {
            'fields': ('status', 'locado_para', 'horimetro_inicial', 'horimetro_atual', 'observacoes')
        }),
        ('Informações Calculadas', {
            'fields': ('horas_trabalhadas', 'dias_locacao', 'valor_total_estimado'),
            'classes': ('collapse',)
        }),
        ('Controle do Sistema', {
            'fields': ('cadastrado_por', 'data_cadastro'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.cadastrado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(TipoManutencao)
class TipoManutencaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']
    ordering = ['nome']


@admin.register(ManutencaoVeiculo)
class ManutencaoVeiculoAdmin(admin.ModelAdmin):
    list_display = ['veiculo', 'tipo_manutencao', 'data_agendamento', 'status', 'oficina', 'valor_final', 'data_cadastro']
    list_filter = ['status', 'tipo_manutencao', 'data_agendamento', 'data_cadastro']
    search_fields = ['veiculo__placa', 'tipo_manutencao__nome', 'oficina', 'descricao']
    ordering = ['-data_agendamento']
    readonly_fields = ['cadastrado_por', 'data_cadastro', 'duracao_manutencao']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('veiculo', 'tipo_manutencao', 'descricao')
        }),
        ('Agendamento', {
            'fields': ('data_agendamento', 'data_inicio', 'data_conclusao', 'oficina', 'km_veiculo')
        }),
        ('Valores', {
            'fields': ('valor_orcamento', 'valor_final')
        }),
        ('Status e Observações', {
            'fields': ('status', 'observacoes')
        }),
        ('Informações Calculadas', {
            'fields': ('duracao_manutencao',),
            'classes': ('collapse',)
        }),
        ('Controle do Sistema', {
            'fields': ('cadastrado_por', 'data_cadastro'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.cadastrado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistoricoHorimetro)
class HistoricoHorimetroAdmin(admin.ModelAdmin):
    list_display = ['veiculo', 'horimetro_anterior', 'horimetro_atual', 'horas_trabalhadas', 'data_registro', 'registrado_por']
    list_filter = ['data_registro', 'veiculo']
    search_fields = ['veiculo__placa', 'observacoes']
    ordering = ['-data_registro']
    readonly_fields = ['registrado_por', 'data_registro', 'horas_trabalhadas']

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChamadoManutencao)
class ChamadoManutencaoAdmin(admin.ModelAdmin):
    list_display = ['numero_chamado', 'get_equipamento', 'tipo_equipamento', 'status', 'prioridade', 'solicitante', 'mecanico', 'data_abertura']
    list_filter = ['status', 'prioridade', 'tipo_equipamento', 'data_abertura']
    search_fields = ['numero_chamado', 'maquina__nome', 'veiculo_locado__placa', 'descricao_problema', 'solicitante__username']
    ordering = ['-data_abertura']
    readonly_fields = ['numero_chamado', 'data_abertura']

    def get_equipamento(self, obj):
        """Retorna o equipamento (Máquina ou Veículo Locado)"""
        return obj.equipamento_nome
    get_equipamento.short_description = 'Equipamento'

    fieldsets = (
        ('Informações do Chamado', {
            'fields': ('numero_chamado', 'maquina', 'veiculo_locado', 'tipo_equipamento', 'tipo_problema', 'descricao_problema', 'foto_problema')
        }),
        ('Status e Prioridade', {
            'fields': ('status', 'prioridade')
        }),
        ('Responsáveis', {
            'fields': ('solicitante', 'mecanico')
        }),
        ('Datas', {
            'fields': ('data_abertura', 'data_inicio_atendimento', 'data_fim_atendimento')
        }),
        ('Solução', {
            'fields': ('solucao', 'observacoes')
        }),
    )
