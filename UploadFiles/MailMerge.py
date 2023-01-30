from datetime import datetime
from babel.numbers import decimal, format_decimal

from generic_app.models import *
from ProcessAdminRestApi.models.upload_model import UploadModelMixin, ConditionalUpdateMixin
from mailmerge import MailMerge as Merge
import pandas as pd
import shutil

import requests
import concurrent.futures
from pikepdf import Pdf
from django.core.files.base import ContentFile


class BabelFormatter():
    def __init__(self, format):
        self.format = format

    def format_with_babel(self, string_to_format):
        #TODO implement locale support
        try:
            with decimal.localcontext(decimal.Context(rounding=decimal.ROUND_HALF_UP)):
                txt = format_decimal(string_to_format, format=self.format, locale='de_DE')
        except Exception:
            txt = string_to_format
        return txt

class MailMerge(ConditionalUpdateMixin, UploadModelMixin, Model):
    
    id = AutoField(primary_key=True)
    name = TextField(default='')
    mailmerge_docx = FileField(upload_to="submodels/MailMerge/mailmerge_docx/", max_length=300)
    upload_template = XLSXField(upload_to="submodels/MailMerge/upload_template/", default='', null=True, blank=True, max_length=300)
    upload_data = FileField(upload_to="submodels/MailMerge/upload_data/", default='', null=True, blank=True, max_length=300)
    zip_docx = FileField(upload_to="submodels/MailMerge/zip_docx/", default='', null=True, blank=True, max_length=300)
    zip_pdf = FileField(upload_to="submodels/MailMerge/zip_docx/", default='', null=True, blank=True, max_length=300)
    
    def file_path(self):
        return f"submodels/MailMerge/{self.name}"

    def create_template(self):
        with Merge(self.mailmerge_docx) as document:
            merge_fields = ['document_name'] + list(document.get_merge_fields())
            df = pd.DataFrame(columns=merge_fields)
            XLSXField.create_excel_file_from_dfs(self.upload_template, path= "template.xlsx", data_frames=[df])


    def create_mails(self):
        from generic_app.submodels.MailMerge.MailDocuments.Mail import Mail
        Mail.objects.filter(mail_merge=self).delete()
        shutil.rmtree(settings.MEDIA_ROOT + os.sep + self.file_path(), ignore_errors=True)
        df = pd.read_excel(self.upload_data)
        formatting = pd.read_excel(self.upload_data, sheet_name='formatting')
        for column in df:
            if column in list(formatting['COLUMN']):
                format = BabelFormatter(format=formatting[formatting['COLUMN']==column]['FORMAT'].iloc[0])
                print(column)
                df[column] = df[column].map(format.format_with_babel)
        for index, row in df.iterrows():
            mail = Mail(mail_merge=self, file_name=row['document_name'])
            mail.save()
            mail.create_documents(row, formatting=formatting)
            mail.save()

        # create docx zip
        if os.path.exists(settings.MEDIA_ROOT + os.sep + self.file_path() + '_docx.zip'):
            os.remove(settings.MEDIA_ROOT + os.sep + self.file_path() + '_docx.zip')
        result = shutil.make_archive(settings.MEDIA_ROOT + os.sep + self.file_path()  + '_docx', 'zip', settings.MEDIA_ROOT + os.sep + self.file_path())
        self.zip_docx.name = self.file_path() + "_docx.zip"
        

    def bulk_create_pdfs_for_mail_merge(self):
        token = MailMerge.exchange_jwt()
        from generic_app.submodels.MailMerge.MailDocuments.Mail import Mail
        mails = Mail.objects.filter(mail_merge=self)
        doc_names = []
        for mail in mails:
            if mail.docx_document.name != "":
                doc_names.append(mail.docx_document.name)
            else:
                CalculationLog(datetime.now(), method='MailMerge.create', message=f"No Mail Document found for {mail.file_name}").save()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(doc_names)) as pool:
            results = pool.map(MailMerge.convert_word_to_pdf, doc_names, [token]*len(doc_names))


        shutil.rmtree(settings.MEDIA_ROOT + os.sep + "submodels/MailMerge/pdf_document/" + self.name, ignore_errors=True)

        pdfs = list(results)
        for mail, pdf in zip(mails, pdfs):
            mail.save_pdf(pdf)
            mail.save()

        # create pdf zip
        #if os.path.exists(settings.MEDIA_ROOT + os.sep + "submodels/MailMerge/pdf_document/" + self.name + '_pdf.zip'):
        #    os.remove(settings.MEDIA_ROOT + os.sep + "submodels/MailMerge/pdf_document/" + self.name + '_pdf.zip')
        result = shutil.make_archive(settings.MEDIA_ROOT + os.sep + "submodels/MailMerge/pdf_document/" + self.name + '_pdf', 'zip', settings.MEDIA_ROOT + os.sep + "submodels/MailMerge/pdf_document/" + self.name)
        self.zip_pdf.name = "submodels/MailMerge/pdf_document/" + self.name + '_pdf.zip'


    @ConditionalUpdateMixin.conditional_calculation
    def update(self):

        self.create_template()
        self.create_mails()
        self.bulk_create_pdfs_for_mail_merge()

    @staticmethod
    def convert_word_to_pdf(doc_name, token):
        pdf_created_successfully = False
        try_counter = 0
        while not pdf_created_successfully:
            try_counter = try_counter + 1
            if try_counter >= 3:
                raise RecursionError(f"Creation of {doc_name} failed three times.")
            url = "https://cpf-ue1.adobe.io/ops/:create?respondWith=%7B%22reltype%22%3A%20%22http%3A%2F%2Fns.adobe.com%2Frel%2Fprimary%22%7D"

            payload = {
                'contentAnalyzerRequests': '{"cpf:inputs": {"documentIn": {"cpf:location": "InputFile0","dc:format": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}},"cpf:engine": {"repo:assetId": "urn:aaid:cpf:Service-1538ece812254acaac2a07799503a430"},"cpf:outputs": {"documentOut": {"cpf:location": "multipartLabelOut","dc:format": "application/pdf"}}}'}

            files = [
                (f'InputFile0', (doc_name,
                                open(
                                    os.path.abspath(
                                        f"{settings.MEDIA_ROOT}/{doc_name}"),
                                    'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))

            ]

            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json, text/plain, */*',
                'x-api-key': f'{os.environ.get("CLIENT_ID")}',
                'Prefer': 'respond-async,wait=60'
            }

            print(f"Trying for {doc_name}")
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            #check for response quality
            try:
                pdf = Pdf.open(ContentFile(response.content))
                print(f"Successfully create {doc_name}")
                pdf_created_successfully = True
            except Exception as e:
                print(f"Error for {doc_name} with {response.content}")

        return response.content

    @staticmethod
    def exchange_jwt():
        url = "https://ims-na1.adobelogin.com/ims/exchange/jwt/"

        payload = f'client_id={os.environ.get("CLIENT_ID")}&client_secret={os.environ.get("CLIENT_SECRET")}&jwt_token={os.environ.get("JWT_TOKEN")}'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': 'ftrset=364; relay=f3644234-d35e-428d-80c8-3f3af673b3c7'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        response_text = response.text
        token = response_text.split(',')[1]
        token = token[16: len(token) - 1]
        return token