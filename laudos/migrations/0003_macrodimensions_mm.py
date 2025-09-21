from decimal import Decimal

from django.db import migrations, models


def cm_to_mm(apps, schema_editor):
    LaudoMacroscopico = apps.get_model('laudos', 'LaudoMacroscopico')
    multiplier = Decimal('10')
    fields = ['dim_comprimento_mm', 'dim_largura_mm', 'dim_altura_mm']

    for laudo in LaudoMacroscopico.objects.all():
        for field in fields:
            value = getattr(laudo, field)
            if value is not None:
                setattr(laudo, field, value * multiplier)
        laudo.save(update_fields=fields)


def mm_to_cm(apps, schema_editor):
    LaudoMacroscopico = apps.get_model('laudos', 'LaudoMacroscopico')
    divisor = Decimal('10')
    fields = ['dim_comprimento_mm', 'dim_largura_mm', 'dim_altura_mm']

    for laudo in LaudoMacroscopico.objects.all():
        for field in fields:
            value = getattr(laudo, field)
            if value is not None:
                setattr(laudo, field, value / divisor)
        laudo.save(update_fields=fields)


class Migration(migrations.Migration):

    dependencies = [
        ('laudos', '0002_metodopreparo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='laudomacroscopico',
            old_name='dim_comprimento_cm',
            new_name='dim_comprimento_mm',
        ),
        migrations.RenameField(
            model_name='laudomacroscopico',
            old_name='dim_largura_cm',
            new_name='dim_largura_mm',
        ),
        migrations.RenameField(
            model_name='laudomacroscopico',
            old_name='dim_altura_cm',
            new_name='dim_altura_mm',
        ),
        migrations.AlterField(
            model_name='laudomacroscopico',
            name='dim_comprimento_mm',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Comprimento (mm)'),
        ),
        migrations.AlterField(
            model_name='laudomacroscopico',
            name='dim_largura_mm',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Largura (mm)'),
        ),
        migrations.AlterField(
            model_name='laudomacroscopico',
            name='dim_altura_mm',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Altura (mm)'),
        ),
        migrations.RunPython(cm_to_mm, reverse_code=mm_to_cm),
    ]
