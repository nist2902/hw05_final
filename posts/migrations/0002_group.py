# Generated by Django 3.1.5 on 2021-01-13 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок сообщества')),
                ('slug', models.SlugField(unique=True, verbose_name='Адрес сообщества в интернете')),
                ('description', models.TextField(verbose_name='Описание сообщества')),
            ],
        ),
    ]
