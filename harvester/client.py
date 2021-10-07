from email.parser import Parser
from enum import Enum
from io import BytesIO
from typing import Optional
from zipfile import ZipFile

import requests


class CountryCode(Enum):
    AE = 'Dubai'
    ARE = 'Dubai'
    BR = 'Sao Paulo'
    BRA = 'Sao Paulo'
    DE = 'Frankfurt'
    DEU = 'Frankfurt'
    SG = 'Singapore'
    SGP = 'Singapore'
    UAE = 'Dubai'
    US = 'New York City'
    USA = 'New York City'
    ZA = 'Johannesburg'
    ZAF = 'Johannesburg'

    @classmethod
    def has_member_key(cls, key):
        return key in cls.__members__


class HarvesterAsyncClient(object):
    """
    Provide a set of async methods for interacting with Authentic8 Harvester.
    """
    # Harvester will replace these values with the information derived from
    # the submitted task.
    CREATE_TASK_COMMAND = 'create_harvest_task'
    DELETE_FILE_COMMAND = 'deletefile'
    DELETE_TASK_COMMAND = 'delete_harvest_task'
    FIND_TASK_COMMAND = 'find_harvest_task'
    HARVEST_TASK_DEST_STR = '<taskid>.<auto-ext>'
    IMAGE_OUTPUT = 'output_image'
    MHTML_ARCHIVE_PATH = 'contents/output.mhtml'
    MHTML_CONTENT_LOCATION = 'Content-Location'
    MHTML_HTML_CONTENT_TYPE = 'text/html'
    MHTML_ORIGINAL_SOURCE_HEADER = 'Snapshot-Content-Location'
    MIME_HTML_OUTPUT = 'output_mhtml'
    PNG_ARCHIVE_PATH = 'contents/output.png'
    SET_AUTH_COMMAND = 'setauth'
    VISUAL_REQUEST_TYPE = 'visual'
    ALREADY_DELETED_ERROR = 'KeyError: Did not find any matching records'

    # Key definitions.
    KEY_AUTH = 'auth'
    KEY_COMMAND = 'command'
    KEY_DATA = 'data'
    KEY_DELETED = 'deleted'
    KEY_DEST_AUTH = 'dest_auth_token'
    KEY_DEST_BUCKET = 'dest_bucket_id'
    KEY_DEST_NAME = 'dest_name'
    KEY_DEST_PATH = 'dest_path'
    KEY_EGRESS = 'egress_tag'
    KEY_ERROR = 'error'
    KEY_FILE_ID = 'file_id'
    KEY_FINISHED = 'finished'
    KEY_ID = 'id'
    KEY_NAME = 'name'
    KEY_REQUEST_TYPE = 'request_type'
    KEY_RESULT = 'result'
    KEY_TASK_ID = 'task_id'
    KEY_TASK_PARAMS = 'task_params'
    KEY_URLS = 'urls'
    KEY_VIS_PARAMS = 'vis_params'

    def __init__(self, token: str, storage_token: str, s3_bucket: str, path: str, url: str) -> None:
        super().__init__()
        self._api_token = token
        self._storage_token = storage_token
        self._s3_bucket = s3_bucket
        self._dest_path = path
        self._api_url = f'{url}/api/'
        self._getfile_url = f'{url}/getfile/'

    def __run_api_command(self, command: dict, token: str) -> dict:
        """
        Internal member class to execute API commands against Authentic8
        Harvester.
        """
        data = [
            {
                self.KEY_COMMAND: self.SET_AUTH_COMMAND,
                self.KEY_DATA: token
            },
            command
        ]
        response = requests.post(url=self._api_url, json=data)
        # return the second object, as the first will be the auth result.
        data = response.json()
        if len(data) != 2:
            raise Exception(f'Did not receive two response objects for Harvester Task {data}')
        return data[1]

    def create_capture_task(self, url: str, proxy: CountryCode, image=True, html=True) -> str:
        """
        Attempt to run a Harvester Authentic8 capture task against the
        supplied URL, via the specified proxy location. Optionally specify if
        the caller wants just the image or just the HTML. Returns the task ID
        that was spawned.
        """
        cmd = {
            self.KEY_COMMAND: self.CREATE_TASK_COMMAND,
            self.KEY_DEST_PATH: self._dest_path,
            self.KEY_DEST_NAME: self.HARVEST_TASK_DEST_STR,
            self.KEY_DEST_AUTH: self._storage_token,
            self.KEY_DEST_BUCKET: self._s3_bucket,
            self.KEY_EGRESS: proxy.value,
            self.KEY_TASK_PARAMS: {
                self.KEY_URLS: [url],
                self.KEY_REQUEST_TYPE: self.VISUAL_REQUEST_TYPE,
                self.KEY_VIS_PARAMS: []
            }
        }
        if image:
            cmd[self.KEY_TASK_PARAMS][self.KEY_VIS_PARAMS].append({self.KEY_NAME: self.IMAGE_OUTPUT})
        if html:
            cmd[self.KEY_TASK_PARAMS][self.KEY_VIS_PARAMS].append({self.KEY_NAME: self.MIME_HTML_OUTPUT})
        result = self.__run_api_command(cmd, self._api_token)
        result_dict = result.get(self.KEY_RESULT)
        if not result_dict or not result_dict.get(self.KEY_TASK_ID):
            raise Exception('Task ID not returned from Harvester task')
        return result_dict.get(self.KEY_TASK_ID)

    def get_tasks(self, finished: bool = False) -> list:
        """
        Retrieve all Harvester tasks, filtered by finished status if supplied.
        """
        cmd = {
            self.KEY_COMMAND: self.FIND_TASK_COMMAND
        }
        if finished:
            cmd[self.KEY_FINISHED] = finished

        result = self.__run_api_command(cmd, self._api_token)
        result_dict = result.get(self.KEY_RESULT)
        if not isinstance(result_dict, list):
            raise Exception('Malformed Harvester response when fetching all tasks')
        return result_dict

    def delete_task(self, task_id: str) -> bool:
        """
        Delete Harvester Authentic8 task by ID.
        """
        cmd = {
            self.KEY_COMMAND: self.DELETE_TASK_COMMAND,
            self.KEY_TASK_ID: task_id
        }
        result = self.__run_api_command(cmd, self._api_token)
        result_dict = result.get(self.KEY_RESULT)
        if not result_dict or result_dict.get(self.KEY_DELETED) is None:
            raise Exception(f'Malformed Harvester response when deleting task {task_id}')
        return result_dict.get(self.KEY_DELETED) is True

    def download_file(self, file_id: str) -> bytes:
        """
        Requires the S3 file ID of the file stored in the Authentic8 permenant
        storage pool. Does not work with file path.
        """
        params = {
            self.KEY_ID: file_id,
            self.KEY_AUTH: self._storage_token
        }
        response = requests.post(url=self._getfile_url, data=params)
        response.raise_for_status()
        return response.content

    def delete_file(self, file_id: str) -> str:
        """
        Requires the S3 file ID of the file stored in the Authentic8 permenant
        storage pool. Does not work with file path.
        """
        cmd = {
            self.KEY_COMMAND: self.DELETE_FILE_COMMAND,
            self.KEY_FILE_ID: file_id
        }
        result = self.__run_api_command(cmd, self._storage_token)

        if result.get(self.KEY_ERROR, '') == self.ALREADY_DELETED_ERROR:
            return f'deleted file {file_id}'

        result_dict = result.get(self.KEY_RESULT)
        if not result_dict:
            raise Exception(f'Malformed Harvester response when deleting file {file_id}')
        return result_dict

    def image_from_zip(self, ziparchive: bytes) -> Optional[bytes]:
        """
        Expects a zip archive in the format created by Harvester. Will extract
        the captured screenshot.
        """
        with ZipFile(BytesIO(ziparchive), 'r') as zip:
            if self.PNG_ARCHIVE_PATH in zip.namelist():
                return zip.read(self.PNG_ARCHIVE_PATH)

    def html_from_zip(self, ziparchive: bytes) -> Optional[str]:
        """
        Expects a zip archive in the format created by Harvester. Will extract
        the captured mhtml archive and parse out the html file.
        """
        try:
            with ZipFile(BytesIO(ziparchive), 'r') as zip:
                if self.MHTML_ARCHIVE_PATH in zip.namelist():
                    mhtml = zip.read(self.MHTML_ARCHIVE_PATH).decode('utf-8')
                    # MHTML can be parsed like an email - see https://datatracker.ietf.org/doc/html/rfc2557
                    email = Parser().parsestr(mhtml)
                    original_source = email.get(self.MHTML_ORIGINAL_SOURCE_HEADER)
                    # Find the portion of the email which has a content type of HTML(ignoring CSS for example). The
                    # content location should match the one that triggered this capture in the first place.
                    for portion in email.get_payload():
                        if portion.get_content_type() == self.MHTML_HTML_CONTENT_TYPE:
                            if portion.get(self.MHTML_CONTENT_LOCATION) == original_source:
                                return portion.get_payload()
        except Exception:
            # Not a huge fan of surpression these, but we don't have a ton of options. The missing HTML will trigger
            # the needed investigation.
            pass
