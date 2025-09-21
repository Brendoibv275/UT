from django.contrib import admin
from .models import UsuarioCustomizado, Paciente, Caso, LaudoMacroscopico, LaudoMicroscopico, MetodoPreparo, LogAtividade

@admin.register(UsuarioCustomizado)
class UsuarioCustomizadoAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('numero_prontuario', 'data_nascimento', 'sexo')
    search_fields = ('numero_prontuario',)
    ordering = ('numero_prontuario',)

@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('id_laboratorio', 'paciente', 'data_recebimento', 'solicitante', 'status', 'criado_por')
    list_filter = ('status', 'data_recebimento', 'criado_por__role')
    search_fields = ('id_laboratorio', 'paciente__numero_prontuario', 'solicitante')
    ordering = ('-data_criacao',)
    readonly_fields = ('data_criacao',)

@admin.register(LaudoMacroscopico)
class LaudoMacroscopicoAdmin(admin.ModelAdmin):
    list_display = ('caso', 'num_fragmentos', 'dim_comprimento_mm', 'dim_largura_mm', 'dim_altura_mm', 'cor')
    search_fields = ('caso__id_laboratorio',)
    ordering = ('caso',)

@admin.register(LaudoMicroscopico)
class LaudoMicroscopicoAdmin(admin.ModelAdmin):
    list_display = ('caso', 'conclusao')
    search_fields = ('caso__id_laboratorio',)
    ordering = ('caso',)

@admin.register(MetodoPreparo)
class MetodoPreparoAdmin(admin.ModelAdmin):
    list_display = ('caso', 'metodo_padrao_he', 'notas_adicionais')
    list_filter = ('metodo_padrao_he',)
    search_fields = ('caso__id_laboratorio',)
    ordering = ('caso',)

@admin.register(LogAtividade)
class LogAtividadeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'timestamp')
    list_filter = ('timestamp', 'usuario__role')
    search_fields = ('usuario__username', 'acao')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
