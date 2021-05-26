# dcu-harvester-library

Python library to allow different DCU applications to dispatch/monitor/and retrieve the results from Harvester.

## Example
```py
import asyncio
from harvester import CountryCode, HarvesterAsyncClient

auth = 'example'
file_auth = 'example'
bucket_id = 'example'
client = HarvesterAsyncClient(auth, file_auth, bucket_id, 'https://extapi.authentic8.com/')
taskId = await client.create_capture_task('https://godaddy.com', CountryCode.US)

await asyncio.sleep(45) # Tasks are async, so give it some time to finish.

finished_tasks = await client.get_tasks(finished=True)
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
            await client.delete_file(fileId)
        await client.delete_task(taskId)
```