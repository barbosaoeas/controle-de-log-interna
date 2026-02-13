from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Empresa, Setor, Area, Cliente, Equipamento, PerfilUsuario, TipoPerfil, Pedido, HistoricoPedido,
    Veiculo, ConfiguracaoTanque, AbastecimentoVeiculo, AbastecimentoTanque, AlertaDiesel
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'tipo', 'contato', 'telefone', 'ativo', 'created_at']
    list_filter = ['tipo', 'ativo', 'created_at']
    search_fields = ['nome', 'cnpj', 'contato', 'email']
    list_editable = ['ativo']
    ordering = ['nome']


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    actions = ['resetar_senha_padrao']

    def resetar_senha_padrao(self, request, queryset):
        """Ação para resetar senha dos usuários selecionados para 123456"""
        count = 0
        for user in queryset:
            try:
                if hasattr(user, 'perfil'):
                    user.perfil.resetar_senha_padrao()
                    count += 1
                else:
                    # Usuário sem perfil, apenas resetar senha
                    user.set_password('123456')
                    user.save()
                    count += 1
            except Exception as e:
                self.message_user(request, f'Erro ao resetar senha do usuário {user.username}: {str(e)}', level='ERROR')

        if count > 0:
            self.message_user(request, f'Senha de {count} usuário(s) foi resetada para 123456')

    resetar_senha_padrao.short_description = "Resetar senha para 123456"


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'responsavel', 'ativo', 'created_at']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'responsavel']
    list_editable = ['ativo']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'localizacao', 'ativa', 'created_at']
    list_filter = ['ativa', 'created_at']
    search_fields = ['nome', 'localizacao']
    list_editable = ['ativa']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'documento', 'telefone', 'email', 'ativo']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'documento', 'email']
    list_editable = ['ativo']


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'categoria', 'status_operacional', 'ativo', 'tem_agenda', 'status_para_pedidos']
    list_filter = ['categoria', 'status_operacional', 'ativo', 'tem_agenda']
    search_fields = ['nome', 'codigo']
    list_editable = ['status_operacional', 'ativo', 'tem_agenda']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'codigo', 'categoria', 'descricao')
        }),
        ('Status e Disponibilidade', {
            'fields': ('ativo', 'status_operacional', 'tem_agenda'),
            'description': '''
                <strong>Lógica de disponibilidade SIMPLIFICADA:</strong><br>
                • <b>ativo</b>: Equipamento existe no sistema (desmarcado = excluído)<br>
                • <b>status_operacional</b>:<br>
                  &nbsp;&nbsp;🟢 OPERACIONAL = Disponível (aparece e pode ser selecionado)<br>
                  &nbsp;&nbsp;🟡 MANUTENCAO = Em reparo (aparece mas desabilitado)<br>
                  &nbsp;&nbsp;🔴 FORA_SERVICO = Temporariamente indisponível (não aparece)<br>
                  &nbsp;&nbsp;⚫ INATIVO = Permanentemente inativo (não aparece)<br>
                • <b>tem_agenda</b>: Aparece nas opções de agendamento
            '''
        }),
        ('Dados do Veículo (se aplicável)', {
            'fields': ('placa', 'modelo', 'ano', 'capacidade_tanque', 'consumo_medio', 'quantidade_litros'),
            'classes': ('collapse',)
        }),
    )

    def status_para_pedidos(self, obj):
        """Mostra se o equipamento aparece nos pedidos"""
        if not obj.ativo:
            return '❌ Excluído'
        status_map = {
            'OPERACIONAL': '🟢 Disponível',
            'MANUTENCAO': '🟡 Em Manutenção (bloqueado)',
            'FORA_SERVICO': '🔴 Fora de Serviço',
            'INATIVO': '⚫ Inativo',
        }
        return status_map.get(obj.status_operacional, '❓ Desconhecido')
    status_para_pedidos.short_description = 'Status p/ Pedidos'


@admin.register(TipoPerfil)
class TipoPerfilAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'is_admin', 'is_supervisor', 'is_terceiro', 'ativo', 'is_sistema', 'created_at']
    list_filter = ['is_admin', 'is_supervisor', 'is_terceiro', 'ativo', 'is_sistema', 'created_at']
    search_fields = ['codigo', 'nome', 'descricao', 'permissoes_resumo']
    list_editable = ['ativo']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Identificação do Perfil', {
            'fields': ('codigo', 'nome'),
            'description': 'Código único e nome do perfil de acesso'
        }),
        ('Descrição e Permissões', {
            'fields': ('descricao', 'permissoes_resumo')
        }),
        ('Flags de Permissões', {
            'fields': ('is_admin', 'is_supervisor', 'is_terceiro'),
            'description': 'Defina as permissões especiais deste perfil'
        }),
        ('Status', {
            'fields': ('ativo', 'is_sistema'),
            'description': 'Perfis do sistema não podem ser excluídos'
        }),
        ('Controle', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['ativar_perfis', 'desativar_perfis', 'excluir_perfis_seguros']

    def ativar_perfis(self, request, queryset):
        """Ativa os perfis selecionados"""
        count = queryset.update(ativo=True)
        self.message_user(request, f'{count} perfil(is) ativado(s) com sucesso.')
    ativar_perfis.short_description = "✅ Ativar perfis selecionados"

    def desativar_perfis(self, request, queryset):
        """Desativa os perfis selecionados"""
        count = queryset.update(ativo=False)
        self.message_user(request, f'{count} perfil(is) desativado(s) com sucesso.')
    desativar_perfis.short_description = "❌ Desativar perfis selecionados"

    def excluir_perfis_seguros(self, request, queryset):
        """Exclui perfis que não são do sistema e não têm usuários"""
        excluidos = 0
        erros = []

        for perfil in queryset:
            pode_excluir, mensagem = perfil.pode_ser_excluido()
            if pode_excluir:
                perfil.delete()
                excluidos += 1
            else:
                erros.append(f"{perfil.codigo}: {mensagem}")

        if excluidos > 0:
            self.message_user(request, f'{excluidos} perfil(is) excluído(s) com sucesso.')

        if erros:
            for erro in erros:
                self.message_user(request, f'❌ {erro}', level='WARNING')

    excluir_perfis_seguros.short_description = "🗑️ Excluir perfis (apenas sem usuários)"


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_nome_completo', 'get_tipo_perfil', 'empresa', 'setor', 'disponivel', 'get_user_ativo', 'created_at']
    list_filter = ['tipo_perfil', 'empresa', 'setor', 'disponivel', 'user__is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'senha_alterada_em', 'ultima_localizacao']

    fieldsets = (
        ('Usuário', {
            'fields': ('user', 'setor')
        }),
        ('Perfil de Acesso', {
            'fields': ('tipo_perfil', 'empresa'),
            'description': 'Defina o tipo de perfil e a empresa vinculada (obrigatório para terceiros)'
        }),
        ('Contato', {
            'fields': ('telefone',)
        }),
        ('Status', {
            'fields': ('disponivel', 'precisa_alterar_senha', 'senha_alterada_em')
        }),
        ('Localização', {
            'fields': ('latitude', 'longitude', 'ultima_localizacao', 'status_online', 'precisao_gps'),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['ativar_usuarios', 'desativar_usuarios', 'marcar_disponivel', 'marcar_indisponivel', 'resetar_senha_usuarios']

    def get_username(self, obj):
        """Retorna o username do usuário"""
        return obj.user.username
    get_username.short_description = 'Usuário'
    get_username.admin_order_field = 'user__username'

    def get_nome_completo(self, obj):
        """Retorna o nome completo do usuário"""
        return obj.user.get_full_name() or obj.user.username
    get_nome_completo.short_description = 'Nome Completo'
    get_nome_completo.admin_order_field = 'user__first_name'

    def get_tipo_perfil(self, obj):
        """Retorna o tipo de perfil do usuário"""
        return obj.tipo_perfil.nome
    get_tipo_perfil.short_description = 'Perfil'
    get_tipo_perfil.admin_order_field = 'tipo_perfil__nome'

    def get_user_ativo(self, obj):
        """Retorna se o usuário está ativo"""
        return obj.user.is_active
    get_user_ativo.short_description = 'Usuário Ativo'
    get_user_ativo.boolean = True
    get_user_ativo.admin_order_field = 'user__is_active'

    def ativar_usuarios(self, request, queryset):
        """Ativa os usuários dos perfis selecionados"""
        count = 0
        for perfil in queryset:
            perfil.user.is_active = True
            perfil.user.save()
            count += 1
        self.message_user(request, f'{count} usuário(s) ativado(s) com sucesso.')
    ativar_usuarios.short_description = "✅ Ativar usuários selecionados"

    def desativar_usuarios(self, request, queryset):
        """Desativa os usuários dos perfis selecionados"""
        count = 0
        for perfil in queryset:
            perfil.user.is_active = False
            perfil.user.save()
            count += 1
        self.message_user(request, f'{count} usuário(s) desativado(s) com sucesso.')
    desativar_usuarios.short_description = "❌ Desativar usuários selecionados"

    def marcar_disponivel(self, request, queryset):
        """Marca os perfis como disponíveis"""
        count = queryset.update(disponivel=True)
        self.message_user(request, f'{count} perfil(is) marcado(s) como disponível(is).')
    marcar_disponivel.short_description = "✅ Marcar como disponível"

    def marcar_indisponivel(self, request, queryset):
        """Marca os perfis como indisponíveis"""
        count = queryset.update(disponivel=False)
        self.message_user(request, f'{count} perfil(is) marcado(s) como indisponível(is).')
    marcar_indisponivel.short_description = "❌ Marcar como indisponível"

    def resetar_senha_usuarios(self, request, queryset):
        """Reseta a senha dos usuários selecionados para 123456"""
        count = 0
        for perfil in queryset:
            try:
                perfil.resetar_senha_padrao()
                count += 1
            except Exception as e:
                self.message_user(request, f'Erro ao resetar senha do usuário {perfil.user.username}: {str(e)}', level='ERROR')

        if count > 0:
            self.message_user(request, f'Senha de {count} usuário(s) foi resetada para 123456')
    resetar_senha_usuarios.short_description = "🔑 Resetar senha para 123456"


class HistoricoPedidoInline(admin.TabularInline):
    model = HistoricoPedido
    extra = 0
    readonly_fields = ['data_alteracao']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'setor_solicitante', 'tipo_pedido', 'status', 'prioridade', 'data_solicitacao', 'criado_por']
    list_filter = ['status', 'tipo_pedido', 'prioridade', 'setor_solicitante', 'data_solicitacao']
    search_fields = ['descricao', 'setor_solicitante__nome', 'criado_por__username']
    list_editable = ['status', 'prioridade']
    readonly_fields = ['data_solicitacao', 'criado_por']
    inlines = [HistoricoPedidoInline]

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('setor_solicitante', 'tipo_pedido', 'status', 'prioridade')
        }),
        ('Detalhes do Pedido', {
            'fields': ('descricao', 'quantidade', 'unidade_medida', 'equipamento')
        }),
        ('Localização', {
            'fields': ('area_origem', 'area_destino', 'cliente')
        }),
        ('Datas', {
            'fields': ('data_solicitacao', 'data_inicio', 'data_conclusao')
        }),
        ('Controle', {
            'fields': ('observacoes', 'criado_por', 'atualizado_por', 'ordem_manual')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistoricoPedido)
class HistoricoPedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'status_anterior', 'status_novo', 'data_alteracao', 'usuario']
    list_filter = ['status_novo', 'data_alteracao']
    readonly_fields = ['data_alteracao']


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ===== ADMIN PARA CONTROLE DE DIESEL =====

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'placa', 'tipo', 'status', 'tem_agenda', 'capacidade_tanque', 'ativo']
    list_filter = ['tipo', 'status', 'tem_agenda', 'ativo']
    search_fields = ['nome', 'placa', 'modelo']
    list_editable = ['status', 'tem_agenda', 'ativo']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'placa', 'tipo', 'modelo', 'ano')
        }),
        ('Status e Controle', {
            'fields': ('status', 'tem_agenda', 'ativo'),
            'description': 'Configure o status do veículo e se ele aparece no agendamento de pedidos'
        }),
        ('Informações Técnicas', {
            'fields': ('capacidade_tanque', 'consumo_medio')
        }),
    )


@admin.register(ConfiguracaoTanque)
class ConfiguracaoTanqueAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'percentual_atual', 'status_nivel', 'data_ultima_atualizacao']
    readonly_fields = ['data_ultima_atualizacao', 'created_at']

    fieldsets = (
        ('Configuração do Tanque', {
            'fields': ('capacidade_total', 'capacidade_extra', 'nivel_atual')
        }),
        ('Níveis de Alerta', {
            'fields': ('nivel_alerta', 'nivel_critico')
        }),
        ('Controle', {
            'fields': ('data_ultima_atualizacao', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def percentual_atual(self, obj):
        return f"{obj.percentual_atual:.1f}%"
    percentual_atual.short_description = 'Percentual'


@admin.register(AbastecimentoVeiculo)
class AbastecimentoVeiculoAdmin(admin.ModelAdmin):
    list_display = ['veiculo', 'cliente', 'data_abastecimento', 'quantidade_litros', 'odometro_atual', 'consumo_display', 'operador']
    list_filter = ['data_abastecimento', 'veiculo__tipo', 'cliente', 'operador']
    search_fields = ['veiculo__nome', 'veiculo__placa', 'cliente__nome', 'operador__username']
    date_hierarchy = 'data_abastecimento'
    readonly_fields = ['odometro_anterior', 'km_rodados', 'consumo_calculado', 'created_at']

    fieldsets = (
        ('Abastecimento', {
            'fields': ('veiculo', 'cliente', 'data_abastecimento', 'quantidade_litros', 'operador')
        }),
        ('Controle de Odômetro', {
            'fields': ('odometro_atual', 'odometro_anterior', 'km_rodados', 'consumo_calculado')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.operador = request.user
        super().save_model(request, obj, form, change)


@admin.register(AbastecimentoTanque)
class AbastecimentoTanqueAdmin(admin.ModelAdmin):
    list_display = ('data_chegada', 'quantidade_litros', 'valor_por_litro', 'valor_total', 'fornecedor', 'operador')
    list_filter = ('data_chegada', 'fornecedor', 'operador')
    search_fields = ('fornecedor', 'numero_nota_fiscal', 'observacoes')
    readonly_fields = ('nivel_anterior', 'nivel_posterior', 'valor_total', 'data_registro')
    date_hierarchy = 'data_chegada'

    fieldsets = (
        ('Informações da Chegada', {
            'fields': ('data_chegada', 'quantidade_litros', 'fornecedor', 'numero_nota_fiscal')
        }),
        ('Valores', {
            'fields': ('valor_por_litro', 'valor_total')
        }),
        ('Controle do Tanque', {
            'fields': ('nivel_anterior', 'nivel_posterior'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('operador', 'data_registro'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo objeto
            obj.operador = request.user
        super().save_model(request, obj, form, change)


@admin.register(AlertaDiesel)
class AlertaDieselAdmin(admin.ModelAdmin):
    list_display = ('nome_destinatario', 'email_destinatario', 'ativo', 'alerta_critico', 'alerta_alerta', 'ultimo_alerta_critico', 'ultimo_alerta_alerta')
    list_filter = ('ativo', 'alerta_critico', 'alerta_alerta', 'created_at')
    search_fields = ('nome_destinatario', 'email_destinatario')
    list_editable = ('ativo', 'alerta_critico', 'alerta_alerta')
    readonly_fields = ('ultimo_alerta_critico', 'ultimo_alerta_alerta', 'created_at')

    fieldsets = (
        ('Destinatário', {
            'fields': ('nome_destinatario', 'email_destinatario', 'ativo')
        }),
        ('Tipos de Alerta', {
            'fields': ('alerta_critico', 'alerta_alerta')
        }),
        ('Histórico de Alertas', {
            'fields': ('ultimo_alerta_critico', 'ultimo_alerta_alerta'),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['testar_alerta_critico', 'testar_alerta_alerta']

    def testar_alerta_critico(self, request, queryset):
        """Ação para testar envio de alerta crítico"""
        from core.models import ConfiguracaoTanque
        tanque = ConfiguracaoTanque.objects.first()
        if tanque:
            for alerta in queryset.filter(ativo=True):
                tanque._enviar_email_alerta(alerta, 'critico')
            self.message_user(request, f"Teste de alerta crítico enviado para {queryset.count()} destinatários.")
        else:
            self.message_user(request, "Erro: Configuração do tanque não encontrada.", level='ERROR')

    def testar_alerta_alerta(self, request, queryset):
        """Ação para testar envio de alerta de atenção"""
        from core.models import ConfiguracaoTanque
        tanque = ConfiguracaoTanque.objects.first()
        if tanque:
            for alerta in queryset.filter(ativo=True):
                tanque._enviar_email_alerta(alerta, 'alerta')
            self.message_user(request, f"Teste de alerta de atenção enviado para {queryset.count()} destinatários.")
        else:
            self.message_user(request, "Erro: Configuração do tanque não encontrada.", level='ERROR')

    testar_alerta_critico.short_description = "🚨 Testar alerta crítico"
    testar_alerta_alerta.short_description = "⚠️ Testar alerta de atenção"


# Customização do admin
admin.site.site_header = 'Sistema de Controle de Log Interna'
admin.site.site_title = 'Controle de Log Interna'
admin.site.index_title = 'Administração do Sistema'
