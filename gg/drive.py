from abc import ABC, abstractmethod
from os import path

from .api_decorator import APIDecorator
from .service import MediaFileUpload

from typing import Union

FOLDER = "uploads"
FOLDERMIMETYPE = 'application/vnd.google-apps.folder'


def addslashes(string: str):
    return string.replace("'", r"\'")


class DriveBase(ABC):
    def __init__(self):
        self.service = None if not hasattr(self, 'service') else self.service

    @APIDecorator.update_token
    def findFolder(self, name: str) -> str:
        token = None
        folders = []
        while True:
            results = self.service.files().list(
                spaces='drive',
                q="trashed=false and name='%s' and mimeType='%s'" % (addslashes(name), FOLDERMIMETYPE),
                fields='nextPageToken, files(id, name)',
                pageToken=token
            ).execute()
            folders.extend(results.get('files'))
            token = results.get('nextPageToken', None)
            if token is None:
                break
        return None if len(folders) == 0 else folders[0].get('id')

    def createFolder(self, name: str):
        file_metadata = {
            'name': name,
            'mimeType': FOLDERMIMETYPE
        }
        result = self.service.files().create(body=file_metadata,
                                             fields='id').execute()
        assert 'id' in result, 'Fail to create folder'
        return result.get('id')

    @abstractmethod
    def upload(self, file: str, *args, **kwargs) -> str:
        pass


@APIDecorator.service('drive', 'v3')
class Drive(DriveBase):

    def upload(self, file: Union[str], *args, **kwargs) -> str:
        """
        Upload file to google drive

        :param file: string file path
        :return: string file id
        """
        id = self.findFolder(FOLDER)
        id = id if id else self.createFolder(FOLDER)

        obj = MediaFileUpload(file, resumable=True)

        return self.service.files().create(body={
            'name': path.basename(file),
            'parents': [id]
        }, media_body=obj, fields='id').execute().get('id', None)
