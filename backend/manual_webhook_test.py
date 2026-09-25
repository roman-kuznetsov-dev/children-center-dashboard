import requests
import json

url = 'http://127.0.0.1:8000/api/webhooks/ofd/'

payload = {
    "receipt_id": "TEST-001",
    "shop_name": "Космоклуб",
    "total": 1500,
    "payment_method": 2,
    "guests_count": 1,
    "items": [
        {"name": "Входной билет", "quantity": 3, "price": 500}
    ],
    "date": "2026-09-21T14:30:00"
}

response = requests.post(url, json=payload)
print(f'Статус: {response.status_code}')
print(f'Ответ: {response.json()}')