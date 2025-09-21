from django.contrib.auth.models import AbstractUser
from django.db import models

class UsuarioCustomizado(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('PROFESSOR', 'Professor'),
        ('ALUNO_N2', 'Aluno Nível 2'),
        ('ALUNO', 'Aluno'),
        ('FUNCIONARIO_LAB', 'Funcionário do Laboratório'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='ALUNO')

class Paciente(models.Model):
    numero_prontuario = models.CharField(max_length=50, unique=True, primary_key=True)
    data_nascimento = models.DateField()
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)

class Caso(models.Model):
    STATUS_CHOICES = [
        ('RECEBIDO', 'Recebido'),
        ('EM_MACROSCOPIA', 'Em Macroscopia'),
        ('PENDENTE_MACRO_APROVACAO', 'Pendente de Aprovacao Macroscopica'),
        ('EM_PREPARO', 'Em Preparo/Coloracao'),
        ('PENDENTE_PREPARO_APROVACAO', 'Pendente de Aprovacao do Preparo'),
        ('EM_MICROSCOPIA', 'Em Microscopia'),
        ('PENDENTE_MICRO_APROVACAO', 'Pendente de Aprovacao Microscopica'),
        ('AGUARDANDO_APROVACAO_FINAL', 'Aguardando Aprovacao Final'),
        ('FINALIZADO', 'Finalizado'),
    ]
    ETAPA_STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('EM_PROGRESSO', 'Em progresso'),
        ('AGUARDANDO_APROVACAO', 'Aguardando aprovacao'),
        ('APROVADO', 'Aprovado'),
        ('REPROVADO', 'Reprovado'),
    ]
    id_laboratorio = models.CharField(max_length=20, unique=True, primary_key=True)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='casos')
    data_recebimento = models.DateField()
    solicitante = models.CharField(max_length=255)
    diagnostico_sugerido = models.TextField(blank=True, null=True)
    observacoes_clinicas = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='RECEBIDO')
    criado_por = models.ForeignKey(UsuarioCustomizado, on_delete=models.SET_NULL, null=True, related_name='casos_criados')
    responsavel_final = models.ForeignKey(UsuarioCustomizado, on_delete=models.SET_NULL, null=True, blank=True, related_name='casos_finalizados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_finalizacao = models.DateTimeField(null=True, blank=True)
    macro_status = models.CharField(max_length=30, choices=ETAPA_STATUS_CHOICES, default='PENDENTE')
    macro_preenchido_por = models.ForeignKey(
        UsuarioCustomizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='macros_preenchidas'
    )
    macro_preenchido_em = models.DateTimeField(null=True, blank=True)
    macro_aprovado_por = models.ForeignKey(
        UsuarioCustomizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='macros_aprovadas'
    )
    macro_aprovado_em = models.DateTimeField(null=True, blank=True)
    preparo_status = models.CharField(max_length=30, choices=ETAPA_STATUS_CHOICES, default='PENDENTE')
    preparo_preenchido_por = models.ForeignKey(
        UsuarioCustomizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preparos_preenchidos'
    )
    preparo_preenchido_em = models.DateTimeField(null=True, blank=True)
    preparo_aprovado_por = models.ForeignKey(
        UsuarioCustomizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preparos_aprovados'
    )
    preparo_aprovado_em = models.DateTimeField(null=True, blank=True)
    micro_status = models.CharField(max_length=30, choices=ETAPA_STATUS_CHOICES, default='PENDENTE')
    micro_preenchido_por = models.ForeignKey(
        UsuarioCustomizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='micros_preenchidos'
    )
    micro_preenchido_em = models.DateTimeField(null=True, blank=True)
    micro_aprovado_por = models.ForeignKey(
        UsuarioCustomizado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='micros_aprovados'
    )
    micro_aprovado_em = models.DateTimeField(null=True, blank=True)


class LaudoMacroscopico(models.Model):
    caso = models.OneToOneField(Caso, on_delete=models.CASCADE, related_name='laudo_macroscopico')
    num_fragmentos = models.PositiveIntegerField(default=1)
    dim_comprimento_mm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Comprimento (mm)')
    dim_largura_mm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Largura (mm)')
    dim_altura_mm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Altura (mm)')
    cor = models.CharField(max_length=100)
    consistencia = models.CharField(max_length=100)
    forma = models.CharField(max_length=100)
    texto_gerado = models.TextField()
    texto_editado = models.TextField(blank=True, null=True)

class LaudoMicroscopico(models.Model):
    caso = models.OneToOneField(Caso, on_delete=models.CASCADE, related_name='laudo_microscopico')
    tags_selecionadas = models.JSONField(default=list)
    texto_base_gerado = models.TextField()
    texto_final = models.TextField()
    conclusao = models.TextField()
    notas = models.TextField(blank=True, null=True)

class MetodoPreparo(models.Model):
    caso = models.OneToOneField(Caso, on_delete=models.CASCADE, related_name='metodo_preparo')
    metodo_padrao_he = models.BooleanField(default=True, verbose_name='Método Padrão H&E')
    notas_adicionais = models.TextField(blank=True, null=True, verbose_name='Notas Adicionais')

class LogAtividade(models.Model):
    ACTION_CHOICES = [
        ('CASO_CRIADO', 'Caso criado'),
        ('MACRO_SALVO', 'Macroscopia salva'),
        ('MACRO_SUBMETIDO', 'Macroscopia submetida'),
        ('MACRO_APROVADO', 'Macroscopia aprovada'),
        ('PREPARO_SALVO', 'Preparo salvo'),
        ('PREPARO_SUBMETIDO', 'Preparo submetido'),
        ('PREPARO_APROVADO', 'Preparo aprovado'),
        ('MICRO_SALVO', 'Microscopia salva'),
        ('MICRO_SUBMETIDO', 'Microscopia submetida'),
        ('MICRO_APROVADO', 'Microscopia aprovada'),
        ('LAUDO_FINAL_APROVADO', 'Laudo final aprovado'),
        ('OUTRA', 'Outra acao'),
    ]
    usuario = models.ForeignKey(UsuarioCustomizado, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=50, choices=ACTION_CHOICES, default='OUTRA')
    timestamp = models.DateTimeField(auto_now_add=True)
    detalhes = models.TextField(blank=True)


