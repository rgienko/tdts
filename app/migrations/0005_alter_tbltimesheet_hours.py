# Generated by Django 4.1.1 on 2022-09-29 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_tbltimesheet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tbltimesheet',
            name='hours',
            field=models.DecimalField(decimal_places=2, max_digits=4),
        ),
    ]
