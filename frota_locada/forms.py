from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    VeiculoLocado, Fornecedor, TipoVeiculo, MarcaVeiculo, ManutencaoVeiculo,
    TipoManutencao, HistoricoHorimetro, Maquina, ChamadoManutencao
)


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'empresa', 'telefone', 'email', 'endereco', 'contato_responsavel', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do fornecedor',
                'maxlength': '100'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XX.XXX.XXX/XXXX-XX',
                'maxlength': '18',
                'inputmode': 'numeric'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(XX) XXXXX-XXXX',
                'maxlength': '15',
                'inputmode': 'tel'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com',
                'maxlength': '100'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Endereço completo',
                'maxlength': '200'
            }),
            'contato_responsavel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável',
                'maxlength': '100'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        if cnpj:
            # Remove formatação para armazenar apenas números se necessário
            # Mas retorna com formatação para exibição
            return cnpj
        return cnpj

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove formatação
            telefone_limpo = ''.join(filter(str.isdigit, telefone))

            # Verifica se tem pelo menos 10 dígitos
            if len(telefone_limpo) < 10:
                raise ValidationError('Telefone deve ter pelo menos 10 dígitos.')

            # Verifica se tem no máximo 11 dígitos
            if len(telefone_limpo) > 11:
                raise ValidationError('Telefone deve ter no máximo 11 dígitos.')

            return telefone
        return telefone




class TipoVeiculoForm(forms.ModelForm):
    class Meta:
        model = TipoVeiculo
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Caminhão, Van, Carro'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do tipo de veículo'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MarcaVeiculoForm(forms.ModelForm):
    class Meta:
        model = MarcaVeiculo
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Toyota, Ford, Volkswagen',
                'maxlength': '50'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip().title()  # Remove espaços e capitaliza
            # Verifica se já existe (exceto se for edição)
            if MarcaVeiculo.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError('Esta marca já está cadastrada.')
        return nome


class VeiculoLocadoForm(forms.ModelForm):
    class Meta:
        model = VeiculoLocado
        fields = [
            'placa', 'modelo', 'marca', 'ano_fabricacao', 'cor', 'tipo_veiculo',
            'fornecedor', 'numero_contrato', 'data_inicio_locacao', 'data_fim_locacao',
            'valor_mensal', 'status', 'locado_para', 'horimetro_inicial', 'horimetro_atual', 'observacoes'
        ]
        widgets = {
            'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ABC-1234, ABC1D23, EQ001, etc.', 'style': 'text-transform: uppercase;'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Hilux, Sprinter'}),
            'marca': forms.Select(attrs={'class': 'form-select'}),
            'ano_fabricacao': forms.NumberInput(attrs={'class': 'form-control', 'min': 1990, 'max': 2030}),
            'cor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Branco, Prata'}),
            'tipo_veiculo': forms.Select(attrs={'class': 'form-select'}),
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'numero_contrato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do contrato'}),
            'data_inicio_locacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'maxlength': '10'
            }),
            'data_fim_locacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'maxlength': '10'
            }),
            'valor_mensal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: R$ 5.000,00',
                'inputmode': 'numeric'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'locado_para': forms.Select(attrs={'class': 'form-select'}),
            'horimetro_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Ex: 1250.5'
            }),
            'horimetro_atual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Ex: 1350.2'
            }),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre o veículo'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True)
        self.fields['tipo_veiculo'].queryset = TipoVeiculo.objects.filter(ativo=True)
        self.fields['marca'].queryset = MarcaVeiculo.objects.filter(ativo=True)

    def clean_valor_mensal(self):
        """Limpa e converte o valor monetário formatado"""
        valor = self.cleaned_data.get('valor_mensal')

        if isinstance(valor, str):
            # Remove formatação monetária (R$, pontos, espaços)
            valor_limpo = valor.replace('R$', '').replace('.', '').replace(' ', '')
            # Troca vírgula por ponto para conversão decimal
            valor_limpo = valor_limpo.replace(',', '.')

            try:
                valor = float(valor_limpo)
            except (ValueError, TypeError):
                raise ValidationError('Valor monetário inválido.')

        if valor is not None and valor < 0:
            raise ValidationError('Valor mensal não pode ser negativo.')

        return valor

    def clean_data_inicio_locacao(self):
        """Converte data brasileira (dd/mm/aaaa) para formato ISO"""
        data = self.cleaned_data.get('data_inicio_locacao')

        if isinstance(data, str) and data:
            try:
                # Se está no formato dd/mm/aaaa, converte
                if '/' in data:
                    from datetime import datetime
                    data_obj = datetime.strptime(data, '%d/%m/%Y').date()
                    return data_obj
            except ValueError:
                raise ValidationError('Data de início inválida. Use o formato dd/mm/aaaa.')

        return data

    def clean_data_fim_locacao(self):
        """Converte data brasileira (dd/mm/aaaa) para formato ISO"""
        data = self.cleaned_data.get('data_fim_locacao')

        if isinstance(data, str) and data:
            try:
                # Se está no formato dd/mm/aaaa, converte
                if '/' in data:
                    from datetime import datetime
                    data_obj = datetime.strptime(data, '%d/%m/%Y').date()
                    return data_obj
            except ValueError:
                raise ValidationError('Data de fim inválida. Use o formato dd/mm/aaaa.')

        return data

    def clean(self):
        cleaned_data = super().clean()
        km_inicial = cleaned_data.get('km_inicial')
        km_atual = cleaned_data.get('km_atual')
        data_inicio = cleaned_data.get('data_inicio_locacao')
        data_fim = cleaned_data.get('data_fim_locacao')

        # Validar KM
        if km_inicial is not None and km_atual is not None:
            if km_atual < km_inicial:
                raise ValidationError('KM atual não pode ser menor que KM inicial.')

        # Validar datas
        if data_inicio and data_fim:
            if data_fim <= data_inicio:
                raise ValidationError('Data de fim deve ser posterior à data de início.')

        return cleaned_data


# FORM REMOVIDO - MecanicoFornecedorForm
# Agora usamos PerfilUsuario.empresa para vincular mecânicos às empresas
# O vínculo é feito diretamente no cadastro de usuário


class TipoManutencaoForm(forms.ModelForm):
    class Meta:
        model = TipoManutencao
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Preventiva, Corretiva'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ManutencaoVeiculoForm(forms.ModelForm):
    class Meta:
        model = ManutencaoVeiculo
        fields = [
            'veiculo', 'tipo_manutencao', 'data_agendamento', 'data_inicio', 'data_conclusao',
            'descricao', 'oficina', 'km_veiculo', 'valor_orcamento', 'valor_final',
            'status', 'observacoes'
        ]
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_manutencao': forms.Select(attrs={'class': 'form-select'}),
            'data_agendamento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'data_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'data_conclusao': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição detalhada do serviço'}),
            'oficina': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da oficina ou prestador'}),
            'km_veiculo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_orcamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'valor_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['veiculo'].queryset = VeiculoLocado.objects.filter(status__in=['ATIVO', 'MANUTENCAO'])
        self.fields['tipo_manutencao'].queryset = TipoManutencao.objects.filter(ativo=True)


class HistoricoHorimetroForm(forms.ModelForm):
    class Meta:
        model = HistoricoHorimetro
        fields = ['veiculo', 'horimetro_atual', 'observacoes']
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select'}),
            'horimetro_atual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': 'Ex: 1350.5'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre o registro'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['veiculo'].queryset = VeiculoLocado.objects.filter(status__in=['ATIVO', 'MANUTENCAO'])

    def clean_horimetro_atual(self):
        horimetro_atual = self.cleaned_data.get('horimetro_atual')
        veiculo = self.cleaned_data.get('veiculo')

        if veiculo and horimetro_atual:
            if horimetro_atual < veiculo.horimetro_atual:
                raise ValidationError(f'Horímetro atual ({horimetro_atual:.1f}h) não pode ser menor que o último horímetro registrado ({veiculo.horimetro_atual:.1f}h).')

        return horimetro_atual


# ============================================================================
# FORMULÁRIOS PARA CHAMADOS DE MANUTENÇÃO DE MÁQUINAS/EQUIPAMENTOS
# ============================================================================

class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = [
            'nome', 'codigo', 'tipo', 'localizacao', 'setor',
            'marca', 'modelo', 'numero_serie', 'ano_fabricacao', 'ativo', 'observacoes'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Guindaste Principal'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: EQ-001', 'style': 'text-transform: uppercase;'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Setor A, Oficina 2'}),
            'setor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Produção, Manutenção'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Caterpillar, Komatsu'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 320D, PC200'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de série'}),
            'ano_fabricacao': forms.NumberInput(attrs={'class': 'form-control', 'min': 1980, 'max': 2030}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre a máquina'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.strip().upper()
            # Verifica se já existe (exceto se for edição)
            if Maquina.objects.filter(codigo__iexact=codigo).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError('Este código já está cadastrado.')
        return codigo


class ChamadoManutencaoForm(forms.ModelForm):
    class Meta:
        model = ChamadoManutencao
        fields = [
            'veiculo_locado', 'tipo_equipamento', 'tipo_problema', 'descricao_problema', 'prioridade', 'foto_problema'
        ]
        widgets = {
            'veiculo_locado': forms.Select(attrs={'class': 'form-select'}),
            'tipo_equipamento': forms.Select(attrs={'class': 'form-select'}),
            'tipo_problema': forms.Select(attrs={'class': 'form-select'}),
            'descricao_problema': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva detalhadamente o problema encontrado...'
            }),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'foto_problema': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'capture': 'environment'  # Para abrir câmera em dispositivos móveis
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar apenas veículos/equipamentos locados ativos
        from .models import VeiculoLocado, TipoVeiculo
        self.fields['veiculo_locado'].queryset = VeiculoLocado.objects.filter(status='ATIVO').order_by('placa')
        self.fields['tipo_equipamento'].queryset = TipoVeiculo.objects.filter(ativo=True).order_by('nome')

        # Alterar labels dos campos
        self.fields['veiculo_locado'].label = "Equipamento/Veículo Locado"
        self.fields['tipo_equipamento'].label = "Tipo de Equipamento"

        # Adicionar informação no placeholder
        self.fields['veiculo_locado'].empty_label = "Selecione um equipamento..."
        self.fields['veiculo_locado'].widget.attrs.update({
            'class': 'form-select',
            'data-bs-toggle': 'tooltip',
            'title': 'Apenas equipamentos ativos aparecem na lista'
        })

        self.fields['tipo_equipamento'].empty_label = "Selecione o tipo..."
        self.fields['tipo_equipamento'].widget.attrs.update({
            'class': 'form-select',
            'data-bs-toggle': 'tooltip',
            'title': 'Tipo do equipamento (PTA, Guindaste, etc)'
        })

        # Adicionar classes CSS específicas para prioridade
        self.fields['prioridade'].widget.attrs.update({
            'onchange': 'updatePriorityColor(this)'
        })


class FinalizarChamadoForm(forms.ModelForm):
    class Meta:
        model = ChamadoManutencao
        fields = ['descricao_solucao', 'pecas_utilizadas', 'observacoes']
        widgets = {
            'descricao_solucao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva a solução aplicada...',
                'required': True
            }),
            'pecas_utilizadas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Liste as peças utilizadas (opcional)...'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais (opcional)...'
            }),
        }

    def clean_descricao_solucao(self):
        descricao = self.cleaned_data.get('descricao_solucao')
        if not descricao or not descricao.strip():
            raise ValidationError('A descrição da solução é obrigatória.')
        return descricao.strip()
