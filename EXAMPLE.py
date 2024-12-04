import requests
import uuid

API_URL = "http://ip:port/api/client"
API_KEY = "API_KEY"
LICENSE_KEY = "LICENSE_KEY"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "license_key": LICENSE_KEY,
    "hwid": "HWID",
    "ip": "127.0.0.1",
    "product": "GPT"
}

try:
    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("Licensz érvényes!")
        else:
            print(f"Licensz érvénytelen! Ok: {result.get('message')}")
    else:
        print(f"Szerver hiba: {response.status_code} - {response.text}")
        
except requests.exceptions.ConnectionError:
    print("Kapcsolódási hiba: Nem sikerült csatlakozni a szerverhez")
except requests.exceptions.RequestException as e:
    print(f"Hiba történt a kérés során: {str(e)}")
except ValueError as e:
    print(f"Hiba történt a válasz feldolgozása során: {str(e)}")
except Exception as e:
    print(f"Váratlan hiba történt: {str(e)}") 