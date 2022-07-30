from generic_app.models import *
from ProcessAdminRestApi.models.upload_model import UploadModelMixin, ConditionalUpdateMixin
from mailmerge import MailMerge as Merge
import pandas as pd

class MailMerge(ConditionalUpdateMixin, UploadModelMixin, Model):
    
    name = TextField(default='')
    mailmerge_docx = FileField(upload_to="submodels/MailMerge/mailmerge_docx/")
    upload_template = XLSXField(upload_to="submodels/MailMerge/upload_template/")
    upload_data = FileField(upload_to="submodels/MailMerge/upload_data/")
    zip_docx = FileField(upload_to="submodels/MailMerge/zip_docx/")
    
    def file_path(self):
        return f"submodels/MailMerge/{self.name}"

    def create_template(self):
        with Merge(self.mailmerge_docx) as document:
            merge_fields = ['document_name'] + list(document.get_merge_fields())
            df = pd.DataFrame(columns=merge_fields)
            XLSXField.create_excel_file_from_dfs(self.upload_template, path= "template.xlsx", data_frames=[df])
            
    def create_mails(self):
        from generic_app.submodels.MailMerge.MailDocuments.Mail import Mail
        columns = pd.read_excel(self.upload_data).columns
        df = pd.read_excel(self.upload_data, converters={c:str for c in columns})
        for index, row in df.iterrows():
            mail = Mail(mail_merge=self, file_name=row['document_name'])
            mail.save()
            mail.create_documents(row)
            mail.save()

        # create zip
        result = shutil.make_archive(MEDIA_ROOT + os.sep + self.file_path(), 'zip', MEDIA_ROOT + os.sep + self.file_path())
        self.zip_file.name = self.file_path() + ".zip"


    @ConditionalUpdateMixin.conditional_calculation
    def update(self):
        
        self.create_template()
        self.create_mails()
        
