# Generated by Django 4.1.1 on 2022-09-28 18:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TblEmployeeTitles',
            fields=[
                ('title_id', models.CharField(max_length=5, primary_key=True, serialize=False)),
                ('title_name', models.CharField(max_length=50)),
                ('rate', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TblParent',
            fields=[
                ('parent_id', models.CharField(max_length=15, primary_key=True, serialize=False)),
                ('parent_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TblProvider',
            fields=[
                ('provider_id', models.CharField(max_length=6, primary_key=True, serialize=False)),
                ('provider_name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.tblparent')),
            ],
        ),
        migrations.CreateModel(
            name='TblEmployee',
            fields=[
                ('employee_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('employee_fname', models.CharField(max_length=25)),
                ('employee_lname', models.CharField(max_length=25)),
                ('employee_title', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.tblemployeetitles')),
            ],
        ),
    ]
