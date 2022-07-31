from generic_app.models import *
from generic_app.submodels.MailMerge.UploadFiles.MailMerge import MailMerge
from mailmerge import MailMerge as Merge
from django.core.files.base import ContentFile

class Mail(Model):
    
    id = AutoField(primary_key=True)
    mail_merge = ForeignKey(to=MailMerge, on_delete=CASCADE)
    file_name = TextField(default='')
    docx_document = FileField(upload_to="submodels/MailMerge/docx_document/", default='', null=True, blank=True, max_length=300)
    pdf_document = FileField(upload_to="submodels/MailMerge/pdf_document/", default='', null=True, blank=True, max_length=300)
    
    def create_documents(self, row, formatting):
        with Merge(self.mail_merge.mailmerge_docx) as document:
            document.merge(**row)

            docx_location = os.path.abspath(f'{settings.MEDIA_ROOT}/{self.mail_merge.file_path()}/docx_document/{self.file_name}.docx')
            os.makedirs(os.path.dirname(docx_location), exist_ok=True)
            document.write(docx_location)
            self.docx_document.name=f"/{self.mail_merge.file_path()}/docx_document/{self.file_name}.docx"

    def save_pdf(self, raw_pdf):
        self.pdf_document.save(f'{self.mail_merge.name}/{self.file_name}.pdf', ContentFile(raw_pdf))
