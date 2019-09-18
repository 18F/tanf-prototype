# Generated by Django 2.2.4 on 2019-09-16 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0006_auto_20190830_2058'),
    ]

    operations = [
        migrations.AddField(
            model_name='adult',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='has record passed validation checks'),
        ),
        migrations.AddField(
            model_name='aggregateddata',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='has record passed validation checks'),
        ),
        migrations.AddField(
            model_name='child',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='has record passed validation checks'),
        ),
        migrations.AddField(
            model_name='closedperson',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='has record passed validation checks'),
        ),
        migrations.AddField(
            model_name='familiesbystratumdata',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='has record passed validation checks'),
        ),
        migrations.AddField(
            model_name='family',
            name='valid',
            field=models.BooleanField(default=True, verbose_name='has record passed validation checks'),
        ),
    ]