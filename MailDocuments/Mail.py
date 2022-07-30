from generic_app.models import *

from generic_app.submodels.MailMerge.UploadFiles.MailMerge import MailMerge
class Mail(Model):
    
    mail_merge = ForeignKey()
    docx_document = FileField()
    pdf_document = FileField()
    