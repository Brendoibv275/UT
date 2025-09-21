"""Workflow helpers centralizando lógica de transição de laudos."""

from __future__ import annotations

from typing import Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    Caso,
    LaudoMacroscopico,
    LaudoMicroscopico,
    LogAtividade,
    MetodoPreparo,
    UsuarioCustomizado,
)

PROFESSOR_ROLES = {"PROFESSOR", "ADMIN"}


def _registrar_log(usuario: Optional[UsuarioCustomizado], acao: str, detalhes: str = "") -> None:
    LogAtividade.objects.create(usuario=usuario, acao=acao, detalhes=detalhes or "")


def _ensure_professor(usuario: UsuarioCustomizado) -> None:
    if usuario.role not in PROFESSOR_ROLES:
        raise PermissionDenied("Somente professores ou administradores podem executar esta operação.")


@transaction.atomic
def registrar_macroscopia(
    caso: Caso,
    usuario: UsuarioCustomizado,
    dados: dict,
    texto_gerado: str = "",
    laudo_existente: Optional[LaudoMacroscopico] = None,
) -> LaudoMacroscopico:
    if caso.macro_status in {"AGUARDANDO_APROVACAO", "APROVADO"}:
        raise ValidationError("Macroscopia já foi submetida para aprovação e não pode ser editada.")

    laudo = laudo_existente or getattr(caso, "laudo_macroscopico", None) or LaudoMacroscopico(caso=caso)

    campos = [
        "num_fragmentos",
        "dim_comprimento_mm",
        "dim_largura_mm",
        "dim_altura_mm",
        "cor",
        "consistencia",
        "forma",
    ]
    for campo in campos:
        if campo in dados:
            setattr(laudo, campo, dados[campo])

    if "texto_editado" in dados:
        laudo.texto_editado = dados["texto_editado"]

    laudo.texto_gerado = texto_gerado or dados.get("texto_gerado", "")
    laudo.save()

    caso.macro_status = "EM_PROGRESSO"
    caso.macro_preenchido_por = usuario
    caso.macro_preenchido_em = timezone.now()

    if caso.status in {"RECEBIDO", "EM_MACROSCOPIA"}:
        caso.status = "EM_MACROSCOPIA"
    elif caso.status == "PENDENTE_MACRO_APROVACAO":
        caso.macro_status = "AGUARDANDO_APROVACAO"

    caso.save()

    _registrar_log(usuario, "MACRO_SALVO", f"Caso {caso.id_laboratorio} macroscopia registrada.")
    return laudo


@transaction.atomic
def solicitar_macroscopia_aprovacao(caso: Caso, usuario: UsuarioCustomizado) -> None:
    if not hasattr(caso, "laudo_macroscopico"):
        raise ValidationError("Registre a macroscopia antes de solicitar aprovação.")
    if caso.macro_status not in {"EM_PROGRESSO", "REPROVADO"}:
        raise ValidationError("Macroscopia precisa estar em progresso para ser submetida.")

    caso.macro_status = "AGUARDANDO_APROVACAO"
    caso.status = "PENDENTE_MACRO_APROVACAO"
    caso.save()

    _registrar_log(usuario, "MACRO_SUBMETIDO", f"Caso {caso.id_laboratorio} macroscopia enviada para aprovação.")


@transaction.atomic
def aprovar_macroscopia(caso: Caso, usuario: UsuarioCustomizado) -> None:
    _ensure_professor(usuario)

    if caso.macro_status != "AGUARDANDO_APROVACAO":
        raise ValidationError("Macroscopia não está aguardando aprovação.")

    caso.macro_status = "APROVADO"
    caso.macro_aprovado_por = usuario
    caso.macro_aprovado_em = timezone.now()
    caso.status = "EM_PREPARO"
    if caso.preparo_status == "PENDENTE":
        caso.preparo_status = "EM_PROGRESSO"
    caso.save()

    _registrar_log(usuario, "MACRO_APROVADO", f"Caso {caso.id_laboratorio} macroscopia aprovada.")


@transaction.atomic
def registrar_preparo(
    caso: Caso,
    usuario: UsuarioCustomizado,
    dados: dict,
    preparo_existente: Optional[MetodoPreparo] = None,
) -> MetodoPreparo:
    if caso.macro_status != "APROVADO":
        raise ValidationError("Macroscopia precisa ser aprovada antes do registro do preparo.")
    if caso.preparo_status in {"AGUARDANDO_APROVACAO", "APROVADO"}:
        raise ValidationError("Preparo já foi submetido para aprovação e não pode ser editado.")

    preparo = preparo_existente or getattr(caso, "metodo_preparo", None) or MetodoPreparo(caso=caso)

    for campo in ["metodo_padrao_he", "notas_adicionais"]:
        if campo in dados:
            setattr(preparo, campo, dados[campo])
    preparo.save()

    caso.preparo_status = "EM_PROGRESSO"
    caso.preparo_preenchido_por = usuario
    caso.preparo_preenchido_em = timezone.now()

    if caso.status in {"EM_PREPARO", "PENDENTE_PREPARO_APROVACAO"}:
        caso.status = "EM_PREPARO"
    elif caso.status in {"EM_MACROSCOPIA", "PENDENTE_MACRO_APROVACAO"}:
        caso.status = "EM_PREPARO"

    caso.save()

    _registrar_log(usuario, "PREPARO_SALVO", f"Caso {caso.id_laboratorio} preparo registrado.")
    return preparo


@transaction.atomic
def solicitar_preparo_aprovacao(caso: Caso, usuario: UsuarioCustomizado) -> None:
    if not hasattr(caso, "metodo_preparo"):
        raise ValidationError("Registre o preparo antes de solicitar aprovação.")
    if caso.macro_status != "APROVADO":
        raise ValidationError("Macroscopia precisa estar aprovada antes de solicitar aprovação do preparo.")
    if caso.preparo_status not in {"EM_PROGRESSO", "REPROVADO"}:
        raise ValidationError("Preparo precisa estar em progresso para ser submetido.")

    caso.preparo_status = "AGUARDANDO_APROVACAO"
    caso.status = "PENDENTE_PREPARO_APROVACAO"
    caso.save()

    _registrar_log(usuario, "PREPARO_SUBMETIDO", f"Caso {caso.id_laboratorio} preparo enviado para aprovação.")


@transaction.atomic
def aprovar_preparo(caso: Caso, usuario: UsuarioCustomizado) -> None:
    _ensure_professor(usuario)

    if caso.macro_status != "APROVADO":
        raise ValidationError("Macroscopia precisa estar aprovada antes de aprovar o preparo.")
    if caso.preparo_status != "AGUARDANDO_APROVACAO":
        raise ValidationError("Preparo não está aguardando aprovação.")

    caso.preparo_status = "APROVADO"
    caso.preparo_aprovado_por = usuario
    caso.preparo_aprovado_em = timezone.now()
    caso.status = "EM_MICROSCOPIA"
    if caso.micro_status == "PENDENTE":
        caso.micro_status = "EM_PROGRESSO"
    caso.save()

    _registrar_log(usuario, "PREPARO_APROVADO", f"Caso {caso.id_laboratorio} preparo aprovado.")


@transaction.atomic
def registrar_microscopia(
    caso: Caso,
    usuario: UsuarioCustomizado,
    dados: dict,
    laudo_existente: Optional[LaudoMicroscopico] = None,
) -> LaudoMicroscopico:
    if caso.macro_status != "APROVADO" or caso.preparo_status != "APROVADO":
        raise ValidationError("A microscopia só pode ser registrada após macroscopia e preparo aprovados.")
    if caso.micro_status in {"AGUARDANDO_APROVACAO", "APROVADO"}:
        raise ValidationError("Microscopia já foi submetida para aprovação e não pode ser editada.")

    laudo = laudo_existente or getattr(caso, "laudo_microscopico", None) or LaudoMicroscopico(caso=caso)

    for campo in ["texto_final", "conclusao", "notas"]:
        if campo in dados:
            setattr(laudo, campo, dados[campo])

    if "tags_selecionadas" in dados:
        laudo.tags_selecionadas = list(dados["tags_selecionadas"])
    if "texto_base_gerado" in dados:
        laudo.texto_base_gerado = dados["texto_base_gerado"]

    laudo.save()

    caso.micro_status = "EM_PROGRESSO"
    caso.micro_preenchido_por = usuario
    caso.micro_preenchido_em = timezone.now()

    if caso.status in {"EM_MICROSCOPIA", "PENDENTE_MICRO_APROVACAO"}:
        caso.status = "EM_MICROSCOPIA"
    elif caso.status in {"EM_PREPARO", "PENDENTE_PREPARO_APROVACAO"}:
        caso.status = "EM_MICROSCOPIA"

    caso.save()

    _registrar_log(usuario, "MICRO_SALVO", f"Caso {caso.id_laboratorio} microscopia registrada.")
    return laudo


@transaction.atomic
def solicitar_microscopia_aprovacao(caso: Caso, usuario: UsuarioCustomizado) -> None:
    if not hasattr(caso, "laudo_microscopico"):
        raise ValidationError("Registre a microscopia antes de solicitar aprovação.")
    if caso.macro_status != "APROVADO" or caso.preparo_status != "APROVADO":
        raise ValidationError("Macroscopia e preparo precisam estar aprovados antes da aprovação da microscopia.")
    if caso.micro_status not in {"EM_PROGRESSO", "REPROVADO"}:
        raise ValidationError("Microscopia precisa estar em progresso para ser submetida.")

    caso.micro_status = "AGUARDANDO_APROVACAO"
    caso.status = "PENDENTE_MICRO_APROVACAO"
    caso.save()

    _registrar_log(usuario, "MICRO_SUBMETIDO", f"Caso {caso.id_laboratorio} microscopia enviada para aprovação.")


@transaction.atomic
def aprovar_microscopia(caso: Caso, usuario: UsuarioCustomizado) -> None:
    _ensure_professor(usuario)

    if caso.macro_status != "APROVADO" or caso.preparo_status != "APROVADO":
        raise ValidationError("Macroscopia e preparo precisam estar aprovados antes de aprovar a microscopia.")
    if caso.micro_status != "AGUARDANDO_APROVACAO":
        raise ValidationError("Microscopia não está aguardando aprovação.")

    caso.micro_status = "APROVADO"
    caso.micro_aprovado_por = usuario
    caso.micro_aprovado_em = timezone.now()
    caso.status = "AGUARDANDO_APROVACAO_FINAL"
    caso.save()

    _registrar_log(usuario, "MICRO_APROVADO", f"Caso {caso.id_laboratorio} microscopia aprovada.")


@transaction.atomic
def aprovar_laudo_final(caso: Caso, usuario: UsuarioCustomizado) -> None:
    _ensure_professor(usuario)

    if any(status != "APROVADO" for status in [caso.macro_status, caso.preparo_status, caso.micro_status]):
        raise ValidationError("Todas as etapas precisam estar aprovadas antes da aprovação final.")

    caso.status = "FINALIZADO"
    caso.responsavel_final = usuario
    caso.data_finalizacao = timezone.now()
    caso.save()

    _registrar_log(usuario, "LAUDO_FINAL_APROVADO", f"Caso {caso.id_laboratorio} laudo final aprovado.")


__all__ = [
    "registrar_macroscopia",
    "solicitar_macroscopia_aprovacao",
    "aprovar_macroscopia",
    "registrar_preparo",
    "solicitar_preparo_aprovacao",
    "aprovar_preparo",
    "registrar_microscopia",
    "solicitar_microscopia_aprovacao",
    "aprovar_microscopia",
    "aprovar_laudo_final",
]
