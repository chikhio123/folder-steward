import httpx
import time

res = httpx.post('http://localhost:8000/api/ai/organize-plans', json={'scope': 'others', 'min_confidence': 0.65})
task_id = res.json()['task_id']
print('Task ID:', task_id)

while True:
    task = httpx.get(f'http://localhost:8000/api/ai/tasks/{task_id}').json()
    print(task['status'], task['processed_items'], task['error_message'])
    if task['status'] in ('completed', 'failed'):
        break
    time.sleep(1)
