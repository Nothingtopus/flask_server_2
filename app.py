from flask import Flask, request, jsonify
import os
import time
from datetime import datetime
from collections import OrderedDict

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Sistema para duas plantas
PLANTS = {
    'rosa_deserto': {
        'last_hour': OrderedDict(),
        'daily': OrderedDict(), 
        'monthly': OrderedDict()
    },
    'cacto_estrela': {
        'last_hour': OrderedDict(),
        'daily': OrderedDict(),
        'monthly': OrderedDict()
    }
}

MAX_IMAGES = {'last_hour': 1, 'daily': 7, 'monthly': 12}

@app.route('/upload/<plant_type>', methods=['POST'])
def upload_file(plant_type):
    try:
        if plant_type not in PLANTS:
            return jsonify({"error": "Planta inválida. Use: rosa_deserto ou cacto_estrela"}), 400

        image_data = request.data
        if not image_data:
            return jsonify({"error": "Nenhum dado recebido"}), 400

        current_time = time.time()
        filename = f"{plant_type}_{int(current_time)}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Salva arquivo
        with open(filepath, "wb") as f:
            f.write(image_data)

        # Atualiza sistema de rotação
        update_image_collections(plant_type, filename, current_time)

        # Retorna URL sem 'https://'
        latest_url = f"flask-server-hj91.onrender.com/static/uploads/{filename}"
        return latest_url, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_image_collections(plant_type, filename, timestamp):
    dt = datetime.fromtimestamp(timestamp)
    plant_data = PLANTS[plant_type]

    plant_data['last_hour'].clear()
    plant_data['last_hour'][timestamp] = filename

    day_key = dt.strftime('%Y-%m-%d')
    plant_data['daily'][day_key] = filename
    while len(plant_data['daily']) > MAX_IMAGES['daily']:
        plant_data['daily'].popitem(last=False)

    month_key = dt.strftime('%Y-%m')
    plant_data['monthly'][month_key] = filename
    while len(plant_data['monthly']) > MAX_IMAGES['monthly']:
        plant_data['monthly'].popitem(last=False)

    cleanup_old_files()

def cleanup_old_files():
    try:
        current_files = set()
        for plant_data in PLANTS.values():
            for collection in plant_data.values():
                current_files.update(collection.values())

        all_files = set(os.listdir(UPLOAD_FOLDER))

        for filename in all_files:
            if filename not in current_files and filename.endswith('.jpg'):
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, filename))
                    print(f"Arquivo removido: {filename}")
                except:
                    pass
    except Exception as e:
        print(f"Erro na limpeza: {e}")

@app.route('/slideshow/<plant_type>')
def get_slideshow_images(plant_type):
    if plant_type not in PLANTS:
        return jsonify({"error": "Planta não encontrada"}), 404

    all_images = []

    if PLANTS[plant_type]['last_hour']:
        for timestamp, filename in PLANTS[plant_type]['last_hour'].items():
            all_images.append({
                'type': 'ultima_hora',
                'timestamp': timestamp,
                'url': f"flask-server-hj91.onrender.com/static/uploads/{filename}",
                'date': datetime.fromtimestamp(timestamp).strftime('%d/%m %H:%M')
            })

    for day, filename in PLANTS[plant_type]['daily'].items():
        all_images.append({
            'type': 'diaria',
            'timestamp': day,
            'url': f"flask-server-hj91.onrender.com/static/uploads/{filename}",
            'date': f"Diária: {day}"
        })

    for month, filename in PLANTS[plant_type]['monthly'].items():
        all_images.append({
            'type': 'mensal',
            'timestamp': month,
            'url': f"flask-server-hj91.onrender.com/static/uploads/{filename}",
            'date': f"Mensal: {month}"
        })

    return jsonify({
        'plant': plant_type,
        'total_images': len(all_images),
        'images': all_images
    })

@app.route('/images/status')
def get_status():
    status = {
        'total_physical_files': len(os.listdir(UPLOAD_FOLDER)),
        'plants': {
            'rosa_deserto': {
                'last_hour': len(PLANTS['rosa_deserto']['last_hour']),
                'daily': len(PLANTS['rosa_deserto']['daily']),
                'monthly': len(PLANTS['rosa_deserto']['monthly'])
            },
            'cacto_estrela': {
                'last_hour': len(PLANTS['cacto_estrela']['last_hour']),
                'daily': len(PLANTS['cacto_estrela']['daily']),
                'monthly': len(PLANTS['cacto_estrela']['monthly'])
            }
        },
        'max_allowed': MAX_IMAGES
    }
    return jsonify(status)

@app.route('/')
def home():
    return "<h1>Sistema Duas Plantas - ESP32-CAM</h1><p>Endpoints:</p><ul><li><strong>Upload Rosa:</strong> POST /upload/rosa_deserto</li><li><strong>Upload Cacto:</strong> POST /upload/cacto_estrela</li><li><strong>Slideshow Rosa:</strong> GET /slideshow/rosa_deserto</li><li><strong>Slideshow Cacto:</strong> GET /slideshow/cacto_estrela</li><li><a href='/images/status'>Status do Sistema</a></li></ul>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
