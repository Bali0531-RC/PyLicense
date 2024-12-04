from flask import Flask, request, jsonify
import yaml
from database import licenses
from models import License
from utils import send_webhook
import secrets
import threading
import os
import time
from datetime import datetime
from discord_bot import run_bot

app = Flask(__name__)

with open('./config.yml', 'r') as file:
    config = yaml.safe_load(file)

def verify_api_key():
    api_key = request.headers.get('X-API-Key')
    if api_key != config['security']['api_key']:
        return False
    return True

@app.route('/api/client', methods=['POST'])
def check_license():
    if not verify_api_key():
        return jsonify({"success": False, "message": "Invalid API key"}), 401

    data = request.json
    license_key = data.get('license_key')
    hwid = data.get('hwid')
    ip = data.get('ip')
    product = data.get('product')

    if not all([license_key, hwid, ip, product]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    license_data = licenses.find_one({"key": license_key})
    
    if not license_data:
        send_webhook("Invalid License", f"License: {license_key}\nHWID: {hwid}\nIP: {ip}\nProduct: {product}", False)
        return jsonify({"success": False, "message": "Invalid license"}), 404

    if 'product' in license_data and license_data['product'] != product:
        send_webhook("Invalid Product", f"License: {license_key}\nHWID: {hwid}\nIP: {ip}\nProduct: {product}", False)
        return jsonify({"success": False, "message": "Invalid product for this license"}), 403

    if not license_data['is_active']:
        send_webhook("Inactive License", f"License: {license_key}\nHWID: {hwid}\nIP: {ip}", False)
        return jsonify({"success": False, "message": "License is inactive"}), 403

    if hwid not in license_data['hwids']:
        if len(license_data['hwids']) >= license_data['max_hwid']:
            send_webhook("HWID Lock", f"License: {license_key}\nHWID: {hwid}\nIP: {ip}", False)
            return jsonify({"success": False, "message": "HWID limit reached"}), 403
        licenses.update_one(
            {"key": license_key},
            {"$push": {"hwids": hwid}}
        )

    if ip not in license_data['ips']:
        licenses.update_one(
            {"key": license_key},
            {"$push": {"ips": ip}}
        )

    licenses.update_one(
        {"key": license_key},
        {"$inc": {"request_count": 1}}
    )

    send_webhook("Successful Validation", f"License: {license_key}\nHWID: {hwid}\nIP: {ip}", True)
    return jsonify({"success": True, "message": "License validated successfully"})

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_license_key():
    # 4 blokkos licensz kulcs generálása (pl: 53Y5-3IKB-5L40-SX7G)
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    blocks = []
    
    for _ in range(4):
        block = ''.join(secrets.choice(chars) for _ in range(4))
        blocks.append(block)
    
    return '-'.join(blocks)

def create_license():
    clear_screen()
    print("=== Új Licensz Létrehozása ===")
    
    license_key = input("Add meg a licensz kulcsot (vagy hagyd üresen a generáláshoz): ")
    if not license_key:
        license_key = generate_license_key()
    
    max_hwid = int(input("Add meg a maximum HWID számot: "))
    
    print("\nVálassz terméket:")
    print("1. PRODUCT1")
    print("2. PRODUCT2")
    print("3. PRODUCT3")
    print("4. Minden termék")
    
    while True:
        choice = input("Válassz (1-4): ")
        if choice == "1":
            product = "PRODUCT1"
            break
        elif choice == "2":
            product = "PRODUCT2"
            break
        elif choice == "3":
            product = "PRODUCT3"
            break
        elif choice == "4":
            product = None
            break
        else:
            print("Érvénytelen választás!")
    
    new_license = {
        "key": license_key,
        "max_hwid": max_hwid,
        "hwids": [],
        "ips": [],
        "request_count": 0,
        "created_at": datetime.now(),
        "is_active": True
    }

    if product:
        new_license["product"] = product
    
    licenses.insert_one(new_license)
    print(f"\nLicensz sikeresen létrehozva!")
    print(f"Licensz kulcs: {license_key}")
    print(f"Termék: {'Minden termék' if not product else product}")
    input("\nNyomj ENTER-t a folytatáshoz...")

def list_licenses():
    clear_screen()
    print("=== Licenszek Listája ===")
    
    all_licenses = list(licenses.find())
    if not all_licenses:
        print("Nincsenek licenszek az adatbázisban.")
    else:
        for license in all_licenses:
            print(f"\nLicensz kulcs: {license['key']}")
            print(f"Termék: {license.get('product', 'Minden termék')}")
            print(f"Maximum HWID: {license['max_hwid']}")
            print(f"Használt HWID-k száma: {len(license['hwids'])}")
            print(f"Kérések száma: {license['request_count']}")
            print(f"Aktív: {'Igen' if license['is_active'] else 'Nem'}")
            print("-" * 40)
    
    input("\nNyomj ENTER-t a folytatáshoz...")

def delete_license():
    clear_screen()
    print("=== Licensz Törlése ===")
    
    license_key = input("Add meg a törölni kívánt licensz kulcsot: ")
    result = licenses.delete_one({"key": license_key})
    
    if result.deleted_count > 0:
        print("\nLicensz sikeresen törölve!")
        send_webhook("License Deleted", f"License key: {license_key}", True)
    else:
        print("\nA licensz nem található!")
    
    input("\nNyomj ENTER-t a folytatáshoz...")

def reset_license():
    clear_screen()
    print("=== Licensz Resetelése ===")
    
    license_key = input("Add meg a resetelni kívánt licensz kulcsot: ")
    result = licenses.update_one(
        {"key": license_key},
        {"$set": {"hwids": [], "ips": []}}
    )
    
    if result.modified_count > 0:
        print("\nLicensz sikeresen resetelve!")
        send_webhook("License Reset", f"License key: {license_key}", True)
    else:
        print("\nA licensz nem található!")
    
    input("\nNyomj ENTER-t a folytatáshoz...")

def menu_thread():
    while True:
        clear_screen()
        print("=== Licensz Szerver Kezelő ===")
        print(f"Szerver fut: http://{config['server']['host']}:{config['server']['port']}")
        print("\n1. Új licensz létrehozása")
        print("2. Licenszek listázása")
        print("3. Licensz törlése")
        print("4. Licensz resetelése")
        print("0. Szerver leállítása")
        
        choice = input("\nVálassz egy menüpontot: ")
        
        if choice == "1":
            create_license()
        elif choice == "2":
            list_licenses()
        elif choice == "3":
            delete_license()
        elif choice == "4":
            reset_license()
        elif choice == "0":
            clear_screen()
            print("Szerver leállítása...")
            os._exit(0)
        else:
            print("\nÉrvénytelen választás!")
            input("Nyomj ENTER-t a folytatáshoz...")

if __name__ == "__main__":
    # Menü indítása külön szálban
    menu_thread = threading.Thread(target=menu_thread)
    menu_thread.daemon = True
    menu_thread.start()
    
    # Discord bot indítása külön szálban
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Szerver indítása
    print(f"Szerver indítása: http://{config['server']['host']}:{config['server']['port']}")
    app.run(
        host=config['server']['host'],
        port=config['server']['port']
    )
