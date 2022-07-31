# Generated by Django 4.0.6 on 2022-07-31 21:17

import ProcessAdminRestApi.models.fields.XLSX_field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('generic_app', '0008_alter_mail_docx_document_alter_mail_pdf_document_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='docx_document',
            field=models.FileField(blank=True, default='', max_length=300, null=True, upload_to='submodels/MailMerge/docx_document/'),
        ),
        migrations.AlterField(
            model_name='mail',
            name='pdf_document',
            field=models.FileField(blank=True, default='', max_length=300, null=True, upload_to='submodels/MailMerge/pdf_document/'),
        ),
        migrations.AlterField(
            model_name='mailmerge',
            name='mailmerge_docx',
            field=models.FileField(max_length=300, upload_to='submodels/MailMerge/mailmerge_docx/'),
        ),
        migrations.AlterField(
            model_name='mailmerge',
            name='upload_data',
            field=models.FileField(blank=True, default='', max_length=300, null=True, upload_to='submodels/MailMerge/upload_data/'),
        ),
        migrations.AlterField(
            model_name='mailmerge',
            name='upload_template',
            field=ProcessAdminRestApi.models.fields.XLSX_field.XLSXField(blank=True, default='', max_length=300, null=True, upload_to='submodels/MailMerge/upload_template/'),
        ),
        migrations.AlterField(
            model_name='mailmerge',
            name='zip_docx',
            field=models.FileField(blank=True, default='', max_length=300, null=True, upload_to='submodels/MailMerge/zip_docx/'),
        ),
        migrations.AlterField(
            model_name='mailmerge',
            name='zip_pdf',
            field=models.FileField(blank=True, default='', max_length=300, null=True, upload_to='submodels/MailMerge/zip_docx/'),
        ),
    ]