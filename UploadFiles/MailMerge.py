from generic_app.models import *

class MailMerge(UploadModelMixin, Model):
    
    mailmerge_docx = FileField()
    upload_template = FileField()
    upload_data = FileField()
    zip_docx = FileField()
    
    def update(self):
        # TODO specify what you want to do once the model has been saved
        pass
