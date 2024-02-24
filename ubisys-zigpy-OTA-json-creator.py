import os
import requests
import subprocess
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import datetime

# Basis-URL der Support-Firmware-Seite
base_url = 'https://www.ubisys.de'

# Ermittle den Pfad des aktuellen Skriptverzeichnisses
script_dir = os.path.dirname(os.path.abspath(__file__))

# Ermittle das heutige Datum und erstelle einen Unterordner
today = datetime.date.today()
date_folder = today.strftime("%Y-%m-%d")
date_folder_path = os.path.join(script_dir, date_folder)

# Erstelle den Unterordner, falls er nicht existiert
if not os.path.exists(date_folder_path):
    os.makedirs(date_folder_path)
    print(f"Unterordner {date_folder} wurde im Skriptverzeichnis erstellt.")

def download_ota_file(download_url):
    file_name = os.path.basename(urlparse(download_url).path)
    file_path = os.path.join(date_folder_path, file_name)
    response = requests.get(download_url)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    print(f"Datei {file_name} wurde heruntergeladen und im Unterordner {date_folder} gespeichert.")

def save_command_to_txt_and_execute(download_url, txt_filename='commands.txt', json_filename='ubisys.json'):
    txt_file_path = os.path.join(date_folder_path, txt_filename)
    print(f"Verarbeite Download-URL: {download_url}")
    zigpy_script_path = 'zigpy'  # Pfad zum Zigpy-Skript
    file_name = os.path.basename(urlparse(download_url).path)
    command = f"{zigpy_script_path} ota generate-index --ota-url-root=\"{download_url}\" {file_name}"

    with open(txt_file_path, 'a', encoding='utf-8') as txtfile:
        txtfile.write(command + "\n")

    print(f"Befehl zu {txt_filename} im Unterordner {date_folder} hinzugefügt.")
    command_output = execute_command(command)
    update_json_file(command_output, json_filename)

def execute_command(command):
    try:
        # Führe den Befehl aus und erfasse den Output
        result = subprocess.run(command, check=True, shell=True, cwd=date_folder_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        full_output = result.stdout.strip()  # Entferne mögliche Leerzeichen am Anfang und Ende

        # Extrahiere nur den JSON-Teil des Outputs
        json_start_index = full_output.find('[')
        if json_start_index != -1:
            json_output = full_output[json_start_index:]
            print("Befehl erfolgreich ausgeführt. JSON-Output:")
            print(json_output)  # Ausgabe des JSON-Outputs zur Überprüfung
            return json_output
        else:
            print("Kein JSON-Output gefunden.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Ausführen des Befehls: {e}")
        return None



def update_json_file(command_output, json_filename):
    json_file_path = os.path.join(date_folder_path, json_filename)
    if command_output:
        try:
            output_data = json.loads(command_output)  # Parsen des JSON-Outputs
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
            else:
                data = []
            data.extend(output_data)  # Füge den Output zum bestehenden Daten hinzu
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
            print(f"Output in {json_filename} aktualisiert.")
        except json.JSONDecodeError as e:
            print(f"Fehler beim Parsen des Befehlsoutputs: {e}")


def find_and_save_commands_to_txt(url, txt_filename='commands.txt', json_filename='ubisys.json'):
    txt_file_path = os.path.join(date_folder_path, txt_filename)
    open(txt_file_path, 'w').close()
    print(f"Neue Datei {txt_filename} im Unterordner {date_folder} erstellt.")

    try:
        print(f"Zugriff auf Seite: {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            if href.endswith('.ota.zigbee'):
                download_url = href if href.startswith('http') else base_url + href
                download_ota_file(download_url)
                save_command_to_txt_and_execute(download_url, txt_filename, json_filename)

    except requests.RequestException as e:
        print(f"Ein Fehler ist aufgetreten beim Zugriff auf: {url} - Fehler: {e}")

# Start-URL für das Skript
start_url = base_url + '/unterstuetzung/support-firmware/'
find_and_save_commands_to_txt(start_url)
