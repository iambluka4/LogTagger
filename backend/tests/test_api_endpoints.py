import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

def test_get_events():
    """Тестує GET /api/events"""
    response = requests.get(f"{BASE_URL}/events")
    print(f"GET /api/events: Status {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total events: {data.get('total_count', 'N/A')}")
        print(f"Page: {data.get('page', 'N/A')} of {data.get('total_pages', 'N/A')}")
        print(f"Events on page: {len(data.get('events', []))} \n")
    else:
        print(f"Error: {response.text}")

def test_get_event(event_id=1):
    """Тестує GET /api/events/{id}"""
    response = requests.get(f"{BASE_URL}/events/{event_id}")
    print(f"GET /api/events/{event_id}: Status {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Event ID: {data.get('id')}")
        print(f"Event source: {data.get('siem_source')}")
        print(f"Event severity: {data.get('severity')}")
        print(f"Has labels: {'Yes' if data.get('labels') else 'No'}")
        print(f"Has raw_log: {'Yes' if data.get('raw_log') else 'No'} \n")
    else:
        print(f"Error: {response.text} \n")

def test_label_event(event_id=1):
    """Тестує POST /api/events/{id}/label"""
    data = {
        "true_positive": True,
        "attack_type": "bruteforce",
        "mitre_tactic": "TA0001",
        "mitre_technique": "T1110",
        "manual_tags": ["test", "api"]
    }
    response = requests.post(f"{BASE_URL}/events/{event_id}/label", json=data)
    print(f"POST /api/events/{event_id}/label: Status {response.status_code}")
    print(f"Response: {response.text} \n")

def test_fetch_events(siem_type="wazuh"):
    """Тестує POST /api/events/fetch"""
    data = {
        "siem_type": siem_type
    }
    response = requests.post(f"{BASE_URL}/events/fetch", json=data)
    print(f"POST /api/events/fetch ({siem_type}): Status {response.status_code}")
    print(f"Response: {response.text} \n")

def test_export_events():
    """Тестує POST /api/events/export"""
    # Використовуємо останній тиждень для фільтра
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")
    
    data = {
        "format": "csv",
        "filters": {
            "date_from": date_from,
            "date_to": date_to
        },
        "include_raw_logs": False
    }
    response = requests.post(f"{BASE_URL}/events/export", json=data)
    print(f"POST /api/events/export: Status {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Export completed: {result.get('message')}")
        print(f"Filename: {result.get('filename')}")
        print(f"Records exported: {result.get('record_count')} \n")
    else:
        print(f"Error: {response.text} \n")

def test_get_alerts():
    """Тестує GET /api/alerts"""
    response = requests.get(f"{BASE_URL}/alerts")
    print(f"GET /api/alerts: Status {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total alerts: {data.get('meta', {}).get('total', 'N/A')}")
        print(f"Page: {data.get('meta', {}).get('page', 'N/A')} of {data.get('meta', {}).get('pages', 'N/A')}")
        print(f"Alerts on page: {len(data.get('data', []))} \n")
    else:
        print(f"Error: {response.text} \n")

def test_auto_tag_alerts():
    """Тестує POST /api/alerts/auto-tag"""
    response = requests.post(f"{BASE_URL}/alerts/auto-tag")
    print(f"POST /api/alerts/auto-tag: Status {response.status_code}")
    print(f"Response: {response.text} \n")

def main():
    """Виконує всі тести"""
    print("Starting API endpoint tests...\n")
    
    # Тестування events endpoints
    test_get_events()
    
    # Спробуємо отримати деталі першої події
    test_get_event(1)
    
    # Спробуємо додати мітку до події
    test_label_event(1)
    
    # Спробуємо отримати події з SIEM
    test_fetch_events()
    
    # Спробуємо експортувати події
    test_export_events()
    
    # Тестування alerts endpoints
    test_get_alerts()
    
    # Спробуємо автоматичне маркування
    test_auto_tag_alerts()
    
    print("API endpoint tests completed!")

if __name__ == "__main__":
    main()
