from django import forms
from .models import Caso, Paciente, LaudoMacroscopico, LaudoMicroscopico, MetodoPreparo

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['numero_prontuario', 'data_nascimento', 'sexo']
        widgets = {
            'numero_prontuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: P001'
            }),
            'data_nascimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'sexo': forms.Select(attrs={
                'class': 'form-control'
            })
        }

class CasoForm(forms.ModelForm):
    class Meta:
        model = Caso
        fields = ['id_laboratorio', 'data_recebimento', 'solicitante', 'diagnostico_sugerido', 'observacoes_clinicas']
        widgets = {
            'id_laboratorio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: LAB001'
            }),
            'data_recebimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'solicitante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do médico solicitante'
            }),
            'diagnostico_sugerido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Diagnóstico clínico sugerido'
            }),
            'observacoes_clinicas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações clínicas relevantes'
            })
        }

class LaudoMacroscopicoForm(forms.ModelForm):
    COR_CHOICES = [
        ('', 'Selecione uma cor...'),
        ('amarelada', 'Amarelada'),
        ('esbranquiçada', 'Esbranquiçada'),
        ('acinzentada', 'Acinzentada'),
        ('avermelhada', 'Avermelhada'),
        ('marrom', 'Marrom'),
        ('negra', 'Negra'),
        ('descrever', 'Descrever...')
    ]
    
    CONSISTENCIA_CHOICES = [
        ('', 'Selecione a consistência...'),
        ('firme', 'Firme'),
        ('mole', 'Mole'),
        ('elástica', 'Elástica'),
        ('rígida', 'Rígida'),
        ('friável', 'Friável'),
        ('descrever', 'Descrever...')
    ]
    
    FORMA_CHOICES = [
        ('', 'Selecione a forma...'),
        ('irregular', 'Irregular'),
        ('ovalada', 'Ovalada'),
        ('alongada', 'Alongada'),
        ('arredondada', 'Arredondada'),
        ('poligonal', 'Poligonal'),
        ('descrever', 'Descrever...')
    ]
    
    TIPO_TECIDO_CHOICES = [
        ('', 'Selecione o tipo de tecido...'),
        ('mole', 'Tecido Mole'),
        ('osseo', 'Tecido Ósseo'),
        ('duro', 'Tecido Duro'),
        ('descrever', 'Descrever...')
    ]
    
    tipo_tecido = forms.ChoiceField(
        choices=TIPO_TECIDO_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cor = forms.ChoiceField(
        choices=COR_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    consistencia = forms.ChoiceField(
        choices=CONSISTENCIA_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    forma = forms.ChoiceField(
        choices=FORMA_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cor_personalizada = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descreva a cor...',
            'style': 'display: none;'
        })
    )
    
    consistencia_personalizada = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descreva a consistência...',
            'style': 'display: none;'
        })
    )
    
    forma_personalizada = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descreva a forma...',
            'style': 'display: none;'
        })
    )
    
    tipo_tecido_personalizado = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descreva o tipo de tecido...',
            'style': 'display: none;'
        })
    )
    
    class Meta:
        model = LaudoMacroscopico
        fields = ['num_fragmentos', 'dim_comprimento_mm', 'dim_largura_mm', 'dim_altura_mm']
        labels = {
            'dim_comprimento_mm': 'Comprimento (mm)',
            'dim_largura_mm': 'Largura (mm)',
            'dim_altura_mm': 'Altura (mm)',
        }
        widgets = {
            'num_fragmentos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'dim_comprimento_mm': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0'
            }),
            'dim_largura_mm': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0'
            }),
            'dim_altura_mm': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0'
            })
        }

class LaudoMicroscopicoForm(forms.ModelForm):
    class Meta:
        model = LaudoMicroscopico
        fields = ['texto_final', 'conclusao', 'notas']
        widgets = {
            'texto_final': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'O texto do laudo microscópico será gerado automaticamente...'
            }),
            'conclusao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Conclusão do exame microscópico'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionais (opcional)'
            })
        }

class MetodoPreparoForm(forms.ModelForm):
    class Meta:
        model = MetodoPreparo
        fields = ['metodo_padrao_he', 'notas_adicionais']
        widgets = {
            'metodo_padrao_he': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notas_adicionais': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva métodos especiais de preparo, colorações adicionais, etc.'
            })
        }
