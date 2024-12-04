import requests
import yaml
from datetime import datetime
from database import licenses

def send_webhook(title, message, success=True):
    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)
    
    webhook_url = config['discord']['webhook_url']
    
    # Licensz adatok kinyerése az üzenetből
    lines = message.split('\n')
    license_key = None
    hwid = None
    ip = None
    
    for line in lines:
        if 'License' in line or 'License key' in line:
            license_key = line.split(': ')[1]
            break
    
    license_data = None
    if license_key:
        license_data = licenses.find_one({"key": license_key})
    
    if license_data:
        created_at = license_data.get('created_at')
        request_count = license_data.get('request_count', 0)
        
        time_diff = datetime.now() - created_at
        hours = int(time_diff.total_seconds() / 3600)
        time_str = f"{hours} órája"
        
        description = (
            "• License Information:\n"
            f"License Key: {license_key}\n"
            f"Product: {license_data.get('product', 'Minden termék')}\n"
            f"Total Requests: {request_count}\n"
            f"Created at: {time_str}"
        )
        
        if len(lines) > 2:  # Ha van HWID és IP információ
            hwid = lines[1].split(': ')[1]
            ip = lines[2].split(': ')[1]
            description += f"\nLatest IP: {ip}\nLatest HWID: {hwid}"
    else:
        description = message
    
    embed = {
        "title": f"{'🟢' if success else '🔴'} {title}",
        "description": description,
        "color": 65280 if success else 16711680
    }
    
    data = {"embeds": [embed]}
    requests.post(webhook_url, json=data) 