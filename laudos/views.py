import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from . import workflow
from .forms import (
    CasoForm,
    LaudoMacroscopicoForm,
    LaudoMicroscopicoForm,
    MetodoPreparoForm,
    PacienteForm,
)
from .models import Caso


STAGE_BADGE_CLASSES = {
    "PENDENTE": "stage-badge stage-pendente",
    "EM_PROGRESSO": "stage-badge stage-progresso",
    "AGUARDANDO_APROVACAO": "stage-badge stage-aguardando",
    "APROVADO": "stage-badge stage-aprovado",
    "REPROVADO": "stage-badge stage-reprovado",
}


def _badge_class(status: str) -> str:
    return STAGE_BADGE_CLASSES.get(status, "stage-badge stage-pendente")


def _disable_form(form) -> None:
    for field in form.fields.values():
        field.disabled = True


def _format_user(user) -> str:
    if not user:
        return "-"
    full_name = user.get_full_name()
    return full_name or user.username


def is_professor_or_admin(user):
    """Retorna True se o usuário for professor ou administrador."""
    return user.role in ["PROFESSOR", "ADMIN"]


@login_required
def dashboard_view(request):
    casos = (
        Caso.objects.select_related("paciente", "criado_por")
        .order_by("-data_recebimento")
    )
    user_role = request.user.role

    for caso in casos:
        if user_role in ["ADMIN", "PROFESSOR"] or caso.criado_por == request.user:
            caso.paciente_anonimizado = {
                "numero_prontuario": caso.paciente.numero_prontuario,
                "data_nascimento": caso.paciente.data_nascimento,
                "sexo": caso.paciente.get_sexo_display(),
            }
        else:
            caso.paciente_anonimizado = {
                "numero_prontuario": "***",
                "data_nascimento": "***",
                "sexo": "***",
            }

        caso.macro_status_display = caso.get_macro_status_display()
        caso.preparo_status_display = caso.get_preparo_status_display()
        caso.micro_status_display = caso.get_micro_status_display()
        caso.macro_badge_class = _badge_class(caso.macro_status)
        caso.preparo_badge_class = _badge_class(caso.preparo_status)
        caso.micro_badge_class = _badge_class(caso.micro_status)

    context = {
        "casos": casos,
        "user_role": user_role,
        "total_casos": casos.count(),
    }
    return render(request, "laudos/dashboard.html", context)


@login_required
def criar_caso_view(request):
    if request.method == "POST":
        paciente_form = PacienteForm(request.POST)
        caso_form = CasoForm(request.POST)
        if paciente_form.is_valid() and caso_form.is_valid():
            paciente = paciente_form.save()
            caso = caso_form.save(commit=False)
            caso.paciente = paciente
            caso.criado_por = request.user
            caso.save()
            messages.success(request, f"Caso {caso.id_laboratorio} criado com sucesso!")
            return redirect("dashboard")
    else:
        paciente_form = PacienteForm()
        caso_form = CasoForm()

    context = {"paciente_form": paciente_form, "caso_form": caso_form}
    return render(request, "laudos/criar_caso.html", context)


@login_required
def laudo_macro_view(request, caso_id):
    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    laudo_macro = getattr(caso, "laudo_macroscopico", None)
    form = LaudoMacroscopicoForm(instance=laudo_macro)

    if request.method == "POST":
        form = LaudoMacroscopicoForm(request.POST, instance=laudo_macro)
        if form.is_valid():
            cor = (
                form.cleaned_data["cor_personalizada"].strip()
                if form.cleaned_data["cor"] == "descrever"
                else form.cleaned_data["cor"]
            )
            consistencia = (
                form.cleaned_data["consistencia_personalizada"].strip()
                if form.cleaned_data["consistencia"] == "descrever"
                else form.cleaned_data["consistencia"]
            )
            forma = (
                form.cleaned_data["forma_personalizada"].strip()
                if form.cleaned_data["forma"] == "descrever"
                else form.cleaned_data["forma"]
            )

            dados_macro = {
                "num_fragmentos": form.cleaned_data["num_fragmentos"],
                "dim_comprimento_mm": form.cleaned_data["dim_comprimento_mm"],
                "dim_largura_mm": form.cleaned_data["dim_largura_mm"],
                "dim_altura_mm": form.cleaned_data["dim_altura_mm"],
                "cor": cor,
                "consistencia": consistencia,
                "forma": forma,
            }
            texto_gerado = request.POST.get("texto_gerado", "")
            workflow.registrar_macroscopia(
                caso,
                request.user,
                dados_macro,
                texto_gerado=texto_gerado,
                laudo_existente=laudo_macro,
            )
            messages.success(request, "Laudo macroscópico salvo com sucesso!")
            return redirect("laudo_micro", caso_id=caso.id_laboratorio)

    context = {"caso": caso, "form": form, "laudo_macro": laudo_macro}
    return render(request, "laudos/laudo_macro.html", context)


@login_required
def laudo_micro_view(request, caso_id):
    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    laudo_micro = getattr(caso, "laudo_microscopico", None)
    form = LaudoMicroscopicoForm(instance=laudo_micro)

    if request.method == "POST":
        form = LaudoMicroscopicoForm(request.POST, instance=laudo_micro)
        if form.is_valid():
            dados_micro = {
                "texto_final": form.cleaned_data["texto_final"],
                "conclusao": form.cleaned_data["conclusao"],
                "notas": form.cleaned_data["notas"],
                "tags_selecionadas": request.POST.getlist("tags"),
                "texto_base_gerado": request.POST.get("texto_base_gerado", ""),
            }
            workflow.registrar_microscopia(
                caso,
                request.user,
                dados_micro,
                laudo_existente=laudo_micro,
            )
            messages.success(request, "Laudo microscópico salvo com sucesso!")
            return redirect("dashboard")

    tags_microscopicas = [
        "Hiperceratose",
        "Acantose",
        "Infiltrado Inflamatório",
        "Atipia Citológica",
        "Displasia",
        "Metaplasia",
        "Necrose",
        "Fibrose",
        "Vasodilatação",
        "Edema",
        "Hemossiderose",
        "Pigmentação",
        "Calcificação",
        "Cistos",
        "Pólipos",
        "Ulceração",
        "Erosão",
        "Hiperplasia",
        "Atrofia",
    ]

    context = {
        "caso": caso,
        "form": form,
        "laudo_micro": laudo_micro,
        "tags_microscopicas": tags_microscopicas,
    }
    return render(request, "laudos/laudo_micro.html", context)



@login_required
def editar_laudo_view(request, caso_id):
    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    is_professor = is_professor_or_admin(request.user)
    if not is_professor and caso.criado_por != request.user:
        messages.error(request, "Permissao negada. Voce so pode editar casos que criou.")
        return redirect("dashboard")

    laudo_macro = getattr(caso, "laudo_macroscopico", None)
    laudo_micro = getattr(caso, "laudo_microscopico", None)
    metodo_preparo = getattr(caso, "metodo_preparo", None)

    macro_form = LaudoMacroscopicoForm(instance=laudo_macro)
    micro_form = LaudoMicroscopicoForm(instance=laudo_micro)
    preparo_form = MetodoPreparoForm(instance=metodo_preparo)

    if request.method == "POST":
        aba_ativa = request.POST.get("aba_ativa", "macro")
        try:
            if aba_ativa == "macro":
                macro_form = LaudoMacroscopicoForm(request.POST, instance=laudo_macro)
                if macro_form.is_valid():
                    cor = (
                        macro_form.cleaned_data["cor_personalizada"].strip()
                        if macro_form.cleaned_data["cor"] == "descrever"
                        else macro_form.cleaned_data["cor"]
                    )
                    consistencia = (
                        macro_form.cleaned_data["consistencia_personalizada"].strip()
                        if macro_form.cleaned_data["consistencia"] == "descrever"
                        else macro_form.cleaned_data["consistencia"]
                    )
                    forma = (
                        macro_form.cleaned_data["forma_personalizada"].strip()
                        if macro_form.cleaned_data["forma"] == "descrever"
                        else macro_form.cleaned_data["forma"]
                    )
                    dados_macro = {
                        "num_fragmentos": macro_form.cleaned_data["num_fragmentos"],
                        "dim_comprimento_mm": macro_form.cleaned_data["dim_comprimento_mm"],
                        "dim_largura_mm": macro_form.cleaned_data["dim_largura_mm"],
                        "dim_altura_mm": macro_form.cleaned_data["dim_altura_mm"],
                        "cor": cor,
                        "consistencia": consistencia,
                        "forma": forma,
                    }
                    texto_gerado = request.POST.get("texto_gerado", "")
                    workflow.registrar_macroscopia(
                        caso,
                        request.user,
                        dados_macro,
                        texto_gerado=texto_gerado,
                        laudo_existente=laudo_macro,
                    )
                    messages.success(request, "Dados macroscopicos salvos com sucesso.")
                else:
                    messages.error(request, "Corrija os erros do formulario de macroscopia.")

            elif aba_ativa == "preparo":
                preparo_form = MetodoPreparoForm(request.POST, instance=metodo_preparo)
                if preparo_form.is_valid():
                    dados_preparo = {
                        "metodo_padrao_he": preparo_form.cleaned_data["metodo_padrao_he"],
                        "notas_adicionais": preparo_form.cleaned_data["notas_adicionais"],
                    }
                    workflow.registrar_preparo(
                        caso,
                        request.user,
                        dados_preparo,
                        preparo_existente=metodo_preparo,
                    )
                    messages.success(request, "Dados de preparo salvos com sucesso.")
                else:
                    messages.error(request, "Corrija os erros do formulario de preparo.")

            elif aba_ativa == "micro":
                micro_form = LaudoMicroscopicoForm(request.POST, instance=laudo_micro)
                if micro_form.is_valid():
                    dados_micro = {
                        "texto_final": micro_form.cleaned_data["texto_final"],
                        "conclusao": micro_form.cleaned_data["conclusao"],
                        "notas": micro_form.cleaned_data["notas"],
                        "tags_selecionadas": request.POST.getlist("tags"),
                        "texto_base_gerado": request.POST.get("texto_base_gerado", ""),
                    }
                    workflow.registrar_microscopia(
                        caso,
                        request.user,
                        dados_micro,
                        laudo_existente=laudo_micro,
                    )
                    messages.success(request, "Dados microscopicos salvos com sucesso.")
                else:
                    messages.error(request, "Corrija os erros do formulario de microscopia.")
            else:
                messages.error(request, "Aba informada invalida.")

        except ValidationError as exc:
            messages.error(request, exc.message)
        except PermissionDenied as exc:
            messages.error(request, str(exc))
            return redirect("dashboard")

        return redirect("editar_laudo", caso_id=caso.id_laboratorio)

    macro_has_data = laudo_macro is not None
    macro_editable_statuses = {"PENDENTE", "EM_PROGRESSO", "REPROVADO"}
    macro_editable = caso.macro_status in macro_editable_statuses
    macro_block_reason = None
    if not macro_editable:
        if caso.macro_status == "AGUARDANDO_APROVACAO":
            macro_block_reason = "Macroscopia aguardando aprovacao."
        elif caso.macro_status == "APROVADO":
            macro_block_reason = "Macroscopia aprovada."
        _disable_form(macro_form)
    macro_can_submit = macro_has_data and caso.macro_status in {"EM_PROGRESSO", "REPROVADO"}
    macro_can_approve = is_professor and caso.macro_status == "AGUARDANDO_APROVACAO"

    preparo_has_data = metodo_preparo is not None
    if caso.macro_status != "APROVADO":
        preparo_editable = False
        preparo_block_reason = "Aguarde a aprovacao da macroscopia."
    else:
        if caso.preparo_status in {"AGUARDANDO_APROVACAO", "APROVADO"}:
            preparo_editable = False
            if caso.preparo_status == "AGUARDANDO_APROVACAO":
                preparo_block_reason = "Preparo aguardando aprovacao."
            else:
                preparo_block_reason = "Preparo aprovado."
        else:
            preparo_editable = True
            preparo_block_reason = None
    if not preparo_editable:
        _disable_form(preparo_form)
    preparo_can_submit = (
        preparo_has_data and preparo_editable and caso.preparo_status in {"EM_PROGRESSO", "REPROVADO"}
    )
    preparo_can_approve = is_professor and caso.preparo_status == "AGUARDANDO_APROVACAO"

    micro_has_data = laudo_micro is not None
    if caso.preparo_status != "APROVADO":
        micro_editable = False
        micro_block_reason = "Aguarde a aprovacao do preparo."
    else:
        if caso.micro_status in {"AGUARDANDO_APROVACAO", "APROVADO"}:
            micro_editable = False
            if caso.micro_status == "AGUARDANDO_APROVACAO":
                micro_block_reason = "Microscopia aguardando aprovacao."
            else:
                micro_block_reason = "Microscopia aprovada."
        else:
            micro_editable = True
            micro_block_reason = None
    if not micro_editable:
        _disable_form(micro_form)
    micro_can_submit = (
        micro_has_data and micro_editable and caso.micro_status in {"EM_PROGRESSO", "REPROVADO"}
    )
    micro_can_approve = is_professor and caso.micro_status == "AGUARDANDO_APROVACAO"

    stage_summary = [
        {
            "slug": "macro",
            "title": "Macroscopia",
            "status": caso.macro_status,
            "status_display": caso.get_macro_status_display(),
            "badge_class": _badge_class(caso.macro_status),
            "preenchido_por": _format_user(caso.macro_preenchido_por),
            "preenchido_em": caso.macro_preenchido_em,
            "aprovado_por": _format_user(caso.macro_aprovado_por),
            "aprovado_em": caso.macro_aprovado_em,
        },
        {
            "slug": "preparo",
            "title": "Preparo e Coloracao",
            "status": caso.preparo_status,
            "status_display": caso.get_preparo_status_display(),
            "badge_class": _badge_class(caso.preparo_status),
            "preenchido_por": _format_user(caso.preparo_preenchido_por),
            "preenchido_em": caso.preparo_preenchido_em,
            "aprovado_por": _format_user(caso.preparo_aprovado_por),
            "aprovado_em": caso.preparo_aprovado_em,
        },
        {
            "slug": "micro",
            "title": "Microscopia",
            "status": caso.micro_status,
            "status_display": caso.get_micro_status_display(),
            "badge_class": _badge_class(caso.micro_status),
            "preenchido_por": _format_user(caso.micro_preenchido_por),
            "preenchido_em": caso.micro_preenchido_em,
            "aprovado_por": _format_user(caso.micro_aprovado_por),
            "aprovado_em": caso.micro_aprovado_em,
        },
    ]

    tags_microscopicas = [
        "Hiperceratose",
        "Acantose",
        "Infiltrado Inflamatorio",
        "Atipia Citologica",
        "Displasia",
        "Metaplasia",
        "Necrose",
        "Fibrose",
        "Vasodilatacao",
        "Edema",
        "Hemossiderose",
        "Pigmentacao",
        "Calcificacao",
        "Cistos",
        "Polipos",
        "Ulceracao",
        "Erosao",
        "Hiperplasia",
        "Atrofia",
    ]

    context = {
        "caso": caso,
        "macro_form": macro_form,
        "micro_form": micro_form,
        "preparo_form": preparo_form,
        "laudo_macro": laudo_macro,
        "laudo_micro": laudo_micro,
        "metodo_preparo": metodo_preparo,
        "tags_microscopicas": tags_microscopicas,
        "stage_summary": stage_summary,
        "macro_editable": macro_editable,
        "macro_block_reason": macro_block_reason,
        "macro_can_submit": macro_can_submit,
        "macro_can_approve": macro_can_approve,
        "macro_has_data": macro_has_data,
        "preparo_editable": preparo_editable,
        "preparo_block_reason": preparo_block_reason,
        "preparo_can_submit": preparo_can_submit,
        "preparo_can_approve": preparo_can_approve,
        "preparo_has_data": preparo_has_data,
        "micro_editable": micro_editable,
        "micro_block_reason": micro_block_reason,
        "micro_can_submit": micro_can_submit,
        "micro_can_approve": micro_can_approve,
        "micro_has_data": micro_has_data,
        "is_professor": is_professor,
    }
    return render(request, "laudos/editar_laudo.html", context)


@login_required
def solicitar_macro_aprovacao_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Metodo nao permitido.")
        return redirect("editar_laudo", caso_id=caso_id)

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.solicitar_macroscopia_aprovacao(caso, request.user)
        messages.success(request, "Macroscopia enviada para aprovacao.")
    except ValidationError as exc:
        messages.error(request, exc.message)

    return redirect("editar_laudo", caso_id=caso.id_laboratorio)


@login_required
def solicitar_preparo_aprovacao_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Metodo nao permitido.")
        return redirect("editar_laudo", caso_id=caso_id)

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.solicitar_preparo_aprovacao(caso, request.user)
        messages.success(request, "Preparo enviado para aprovacao.")
    except ValidationError as exc:
        messages.error(request, exc.message)

    return redirect("editar_laudo", caso_id=caso.id_laboratorio)


@login_required
def solicitar_microscopia_aprovacao_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Metodo nao permitido.")
        return redirect("editar_laudo", caso_id=caso_id)

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.solicitar_microscopia_aprovacao(caso, request.user)
        messages.success(request, "Microscopia enviada para aprovacao.")
    except ValidationError as exc:
        messages.error(request, exc.message)

    return redirect("editar_laudo", caso_id=caso.id_laboratorio)


@login_required
@user_passes_test(is_professor_or_admin)
def aprovar_macroscopia_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Metodo nao permitido.")
        return redirect("editar_laudo", caso_id=caso_id)

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.aprovar_macroscopia(caso, request.user)
        messages.success(request, "Macroscopia aprovada com sucesso.")
    except ValidationError as exc:
        messages.error(request, exc.message)

    return redirect("editar_laudo", caso_id=caso.id_laboratorio)


@login_required
@user_passes_test(is_professor_or_admin)
def aprovar_preparo_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Metodo nao permitido.")
        return redirect("editar_laudo", caso_id=caso_id)

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.aprovar_preparo(caso, request.user)
        messages.success(request, "Preparo aprovado com sucesso.")
    except ValidationError as exc:
        messages.error(request, exc.message)

    return redirect("editar_laudo", caso_id=caso.id_laboratorio)


@login_required
@user_passes_test(is_professor_or_admin)
def aprovar_microscopia_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Metodo nao permitido.")
        return redirect("editar_laudo", caso_id=caso_id)

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.aprovar_microscopia(caso, request.user)
        messages.success(request, "Microscopia aprovada com sucesso.")
    except ValidationError as exc:
        messages.error(request, exc.message)

    return redirect("editar_laudo", caso_id=caso.id_laboratorio)


@login_required
@user_passes_test(is_professor_or_admin)
def aprovar_laudo_view(request, caso_id):
    if request.method != "POST":
        messages.error(request, "Método não permitido.")
        return redirect("dashboard")

    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    try:
        workflow.aprovar_laudo_final(caso, request.user)
        messages.success(request, f"Laudo {caso.id_laboratorio} aprovado e finalizado com sucesso!")
    except ValidationError as exc:
        messages.error(request, exc.message)
    except PermissionDenied as exc:
        messages.error(request, str(exc))
    except Exception as exc:  # pragma: no cover - salvaguarda
        messages.error(request, f"Erro ao aprovar laudo: {exc}")

    return redirect("dashboard")


@login_required
def gerar_pdf_view(request, caso_id):
    caso = get_object_or_404(Caso, id_laboratorio=caso_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def draw_header():
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width / 2.0, height - 2 * cm, "LPB - Laboratório de Patologia Bucal")
        p.setFont("Helvetica", 12)
        p.drawCentredString(width / 2.0, height - 2.6 * cm, "Universidade Federal de Santa Catarina")
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(
            width / 2.0,
            height - 3.5 * cm,
            f"LAUDO ANATOMOPATOLÓGICO - Nº {caso.id_laboratorio}",
        )

    def draw_paciente_info(y_start):
        dados = [
            ["Paciente", caso.paciente.numero_prontuario, "Solicitante", caso.solicitante],
            [
                "Data de nascimento",
                caso.paciente.data_nascimento.strftime("%d/%m/%Y"),
                "Data de recebimento",
                caso.data_recebimento.strftime("%d/%m/%Y"),
            ],
        ]
        tabela = Table(dados, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 6 * cm])
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                ]
            )
        )
        tabela.wrapOn(p, width - 4 * cm, height)
        tabela.drawOn(p, 2 * cm, y_start)
        return y_start - (tabela._height + 0.5 * cm)

    def draw_section(title, text, y_start):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(2 * cm, y_start, title)
        y = y_start - 0.4 * cm
        p.setFont("Helvetica", 11)
        for linha in text.split("\n"):
            p.drawString(2 * cm, y, linha)
            y -= 0.4 * cm
        return y - 0.5 * cm

    draw_header()
    y_cursor = draw_paciente_info(height - 6 * cm)

    if hasattr(caso, "laudo_macroscopico"):
        macro_texto = caso.laudo_macroscopico.texto_editado or caso.laudo_macroscopico.texto_gerado
        y_cursor = draw_section("MACROSCOPIA", macro_texto, y_cursor)

    if hasattr(caso, "metodo_preparo"):
        preparo = caso.metodo_preparo
        preparo_texto = "Processamento histológico padrão, microtomia e coloração de H&E" if preparo.metodo_padrao_he else "Método especial de preparo"
        if preparo.notas_adicionais:
            preparo_texto += f"\nNotas adicionais: {preparo.notas_adicionais}"
        y_cursor = draw_section("PREPARO/COLOCAÇÃO", preparo_texto, y_cursor)

    if hasattr(caso, "laudo_microscopico"):
        micro = caso.laudo_microscopico
        micro_texto = f"{micro.texto_final}\n\nConclusão: {micro.conclusao}"
        if micro.notas:
            micro_texto += f"\nNotas: {micro.notas}"
        y_cursor = draw_section("MICROSCOPIA", micro_texto, y_cursor)

    p.setFont("Helvetica", 10)
    p.drawCentredString(width / 2.0, 4 * cm, "____________________________________")
    responsavel = caso.responsavel_final.get_full_name() if caso.responsavel_final else "Responsável"
    p.drawCentredString(width / 2.0, 3.5 * cm, responsavel)
    p.drawCentredString(width / 2.0, 3.1 * cm, "Professor Responsável")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"laudo_{caso.id_laboratorio}.pdf"
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
