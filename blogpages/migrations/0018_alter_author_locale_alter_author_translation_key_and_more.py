# Generated by Django 5.0.8 on 2024-08-19 03:35

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogpages', '0017_auto_20240818_2230'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='locale',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale'),
        ),
        migrations.AlterField(
            model_name='author',
            name='translation_key',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterUniqueTogether(
            name='author',
            unique_together={('translation_key', 'locale')},
        ),
    ]
