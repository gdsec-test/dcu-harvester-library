# dcu-harvester-library

Python library to allow different DCU applications to dispatch/monitor/and retrieve the results from Harvester.

## Example
```py
from harvester import CountryCode, HarvesterAsyncClient

auth = 'example'
file_auth = 'example'
bucket_id = 'example'
# The '/dev-downloads' here is just an example. This needs to match with a path that you have created in your
# Silo buckets.
client = HarvesterAsyncClient(auth, file_auth, bucket_id, '/dev-downloads', 'https://extapi.authentic8.com/')
taskId = client.create_capture_task('https://godaddy.com', CountryCode.US)

finished_tasks = client.get_tasks(finished=True)
for task in finished_tasks:
    try:
        taskId = task['task_id']
        if task['status'] == 'done':
            fileId = task['result_file_id']
            data = await client.download_file(fileId)
            image = client.image_from_zip(data)
            with open('test.png', 'wb') as f:
                f.write(image)
            html = client.html_from_zip(data)
            with open('test.html', 'w') as f:
                f.write(html)
    finally:
        if fileId:
            client.delete_file(fileId)
        client.delete_task(taskId)
```