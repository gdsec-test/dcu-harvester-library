import zipfile
from io import BytesIO
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
from requests import Response
from harvester import CountryCode, HarvesterAsyncClient


class TestHarvesterAsyncClient(TestCase):
    BASE_URL = 'http://test'
    GODADDY_URL = 'https://godaddy.com'
    HTML_TEST_STR = 'test html'
    IMAGE_TEST_STR = 'test image'
    TEST_AUTH_STR = 'test auth'
    TEST_FILE_STR = 'test file'
    TEST_FILE_AUTH = 'test file auth'
    TEST_TASK = 'test task'
    KEY_URL = 'url'
    KEY_JSON = 'json'
    TEST_DICT = [{'test': '1'}]

    def setUp(self):
        self.client = HarvesterAsyncClient(
            self.TEST_AUTH_STR, self.TEST_FILE_AUTH, 'test bucket', '/test-path', self.BASE_URL
        )
        self.bytes_zip = BytesIO()

    @patch('requests.post')
    def test_create_capture_task_success(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: {self.client.KEY_TASK_ID: self.TEST_TASK}}]
        ])
        taskId = self.client.create_capture_task(self.GODADDY_URL, CountryCode.US)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][0], {
            self.client.KEY_COMMAND: self.client.SET_AUTH_COMMAND,
            self.client.KEY_DATA: self.TEST_AUTH_STR
        })
        self.assertEqual(taskId, self.TEST_TASK)

    @patch('requests.post')
    def test_create_capture_task_one_response(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}]
        ])
        with self.assertRaises(Exception):
            self.client.create_capture_task(self.GODADDY_URL, CountryCode.US)

    @patch('requests.post')
    def test_create_capture_task_missing_field(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: {}}]
        ])
        with self.assertRaises(Exception):
            self.client.create_capture_task(self.GODADDY_URL, CountryCode.US)

    @patch('requests.post')
    def test_get_tasks_success(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: self.TEST_DICT}]
        ])
        result = self.client.get_tasks()
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][1], {
            self.client.KEY_COMMAND: self.client.FIND_TASK_COMMAND
        })
        self.assertEqual(result, self.TEST_DICT)

    @patch('requests.post')
    def test_get_tasks_success_finished_false(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: self.TEST_DICT}]
        ])
        result = self.client.get_tasks(False)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][1], {
            self.client.KEY_COMMAND: self.client.FIND_TASK_COMMAND,
            self.client.KEY_FINISHED: False
        })
        self.assertEqual(result, self.TEST_DICT)

    @patch('requests.post')
    def test_get_tasks_success_finished_true(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: self.TEST_DICT}]
        ])
        result = self.client.get_tasks(True)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][1], {
            self.client.KEY_COMMAND: self.client.FIND_TASK_COMMAND,
            self.client.KEY_FINISHED: True
        })
        self.assertEqual(result, self.TEST_DICT)

    @patch('requests.post')
    def test_get_tasks_malformed(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {}]
        ])
        with self.assertRaises(Exception):
            self.client.get_tasks()

    @patch('requests.post')
    def test_delete_task_success(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {
                self.client.KEY_RESULT: {self.client.KEY_DELETED: True}
            }]
        ])
        result = self.client.delete_task(self.TEST_TASK)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][1], {
            self.client.KEY_COMMAND: self.client.DELETE_TASK_COMMAND,
            self.client.KEY_TASK_ID: self.TEST_TASK
        })
        self.assertTrue(result)

    @patch('requests.post')
    def test_delete_task_failed(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: {self.client.KEY_DELETED: False}}]
        ])
        result = self.client.delete_task(self.TEST_TASK)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][1], {
            self.client.KEY_COMMAND: self.client.DELETE_TASK_COMMAND,
            self.client.KEY_TASK_ID: self.TEST_TASK
        })
        self.assertFalse(result)

    @patch('requests.post')
    def test_delete_task_malformed(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: {}}]
        ])
        with self.assertRaises(Exception):
            self.client.delete_task(self.TEST_TASK)

    @patch('requests.post')
    def test_delete_file_success(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {self.client.KEY_RESULT: 'success'}]
        ])
        result = self.client.delete_file(self.TEST_FILE_STR)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/api/')
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][0], {
            self.client.KEY_COMMAND: self.client.SET_AUTH_COMMAND,
            self.client.KEY_DATA: self.TEST_FILE_AUTH
        })
        self.assertEqual(mock_post.call_args[1][self.KEY_JSON][1], {
            self.client.KEY_COMMAND: self.client.DELETE_FILE_COMMAND,
            self.client.KEY_FILE_ID: self.TEST_FILE_STR
        })
        self.assertTrue(result)

    @patch('requests.post')
    def test_delete_file_malformed(self, mock_post):
        mock_post.return_value.json = Mock(side_effect=[
            [{}, {}]
        ])
        with self.assertRaises(Exception):
            self.client.delete_file(self.TEST_FILE_STR)

    @patch('requests.post')
    def test_download_file_success(self, mock_post):
        mock_post.return_value = MagicMock(spec=Response(), side_effect=[self.client.KEY_DATA])
        mock_post.return_value.content = self.client.KEY_DATA
        result = self.client.download_file(self.TEST_FILE_STR)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1][self.KEY_URL], f'{self.BASE_URL}/getfile/')
        self.assertEqual(mock_post.call_args[1][self.client.KEY_DATA], {
            self.client.KEY_ID: self.TEST_FILE_STR,
            self.client.KEY_AUTH: self.TEST_FILE_AUTH
        })
        self.assertEqual(result, self.client.KEY_DATA)

    def test_image_from_zip(self):
        with zipfile.ZipFile(self.bytes_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.client.PNG_ARCHIVE_PATH, self.IMAGE_TEST_STR)
        ret_data = self.client.image_from_zip(self.bytes_zip.getvalue())
        self.assertEqual(self.IMAGE_TEST_STR, ret_data.decode())

    def test_image_from_zip_missing_file(self):
        with zipfile.ZipFile(self.bytes_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('contents/test.txt', self.IMAGE_TEST_STR)
        ret_data = self.client.image_from_zip(self.bytes_zip.getvalue())
        self.assertIsNone(ret_data)

    def test_html_from_zip(self):
        data = f'{self.client.MHTML_CHUNK_BOUNDARY}{self.client.HTML_CHUNK_BOUNDARY}{self.HTML_TEST_STR}'
        with zipfile.ZipFile(self.bytes_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.client.MHTML_ARCHIVE_PATH, data)
        ret_data = self.client.html_from_zip(self.bytes_zip.getvalue())
        self.assertEqual(ret_data, self.HTML_TEST_STR)

    def test_html_from_zip_malformed(self):
        with zipfile.ZipFile(self.bytes_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.client.MHTML_ARCHIVE_PATH, self.HTML_TEST_STR)
        ret_data = self.client.html_from_zip(self.bytes_zip.getvalue())
        self.assertIsNone(ret_data)
