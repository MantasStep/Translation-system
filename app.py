# norint pasileist koda:
# venv\Scripts\activate
# python -m flask run

# i gita koda pushint:
# git add .
# git commit -m "pavadinimas"
# git push

from flask import Flask, request, jsonify, render_template, send_file
from easynmt import EasyNMT
from docx import Document
from DataBase import db, TranslationMemory
import torch
import time
import os
import shutil
import uuid

# Modelių konfigūracija (tik `m2m` modeliai)
model_configs = {
    'm2m_100_418M': ('m2m_100_418M', None),
    'm2m_100_1.2B': ('m2m_100_1.2B', None)
}

# Modelių saugojimo kelias
base_model_path = r"E:\univerui\4_kursas\bakalauras\kodas\modeliai"

# Aptinkame, ar GPU prieinamas
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Naudojamas įrenginys: {device.upper()}")

# Inicializuojame modelius
models_dict = {}

for model_name, (model_path, lang_map) in model_configs.items():
    print(f"Įkeliame modelį: {model_name}")
    start_time = time.time()
    
    models_dict[model_name] = EasyNMT(model_path, device=device, use_fp16=True)
    
    elapsed_time = time.time() - start_time
    print(f"Modelis '{model_name}' įkeltas per {elapsed_time:.2f} sekundžių.\n")


def translate_text(text, source_lang, target_lang):
    translations = {}
    for model_name, model_instance in models_dict.items():
        translations[model_name] = model_instance.translate(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
            batch_size=16
        )
    return max(translations.values(), key=len)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Sukuriame Flask aplikaciją
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///translations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Sukuriame DB, jei dar nėra
with app.app_context():
    db_path = os.path.join(os.getcwd(), 'translations.db')
    if not os.path.exists(db_path):
        print("Duomenų bazės failas nerastas. Kuriama nauja DB...")
        db.create_all()
        print("Duomenų bazė sukurta.")
    else:
        print("Duomenų bazė jau egzistuoja.")


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
TRANSLATED_FOLDER = os.path.join(os.getcwd(), 'translated')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSLATED_FOLDER'] = TRANSLATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maksimalus failo dydis 16MB
app.config['ALLOWED_EXTENSIONS'] = {'docx', 'txt'}

@app.route('/')
def index():
    return render_template('index.html')

# Funkcija geriausiam vertimui pasirinkti (jei bus naudojama daugiau nei vienas modelis)
def determine_best_translation(translations):
    return max(translations.values(), key=len)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    original_text = data.get('text')
    direction = data.get('direction')
    target_lang = 'en' if direction == 'lt-en' else 'lt'
    source_lang = 'lt' if direction == 'lt-en' else 'en'

    translations = {}

    print(f"Pradedamas vertimas: '{original_text}'")

    # Pasirenkame modelius pagal kryptį (naudosime abu `m2m` modelius)
    for model_name, model_instance in models_dict.items():
        print(f"Modelis '{model_name}' pradeda vertimą...")
        start_time = time.time()

        translations[model_name] = model_instance.translate(
            original_text,
            source_lang=source_lang,
            target_lang=target_lang,
            batch_size=16
        )

        elapsed_time = time.time() - start_time
        print(f"Modelis '{model_name}' užbaigė vertimą per {elapsed_time:.2f} sekundžių.")

    # Pasirenkame geriausią vertimą
    best_translation = determine_best_translation(translations)
    print("Vertimas baigtas. Geriausias vertimas pasirinktas.\n")

    return jsonify({'translations': translations, 'best_translation': best_translation})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        print("Nerastas failas užklausoje.")
        return 'Nėra failo formoje', 400

    file = request.files['file']
    direction = request.form.get('direction', 'lt-en')
    source_lang = 'lt' if direction == 'lt-en' else 'en'
    target_lang = 'en' if direction == 'lt-en' else 'lt'

    if file.filename == '':
        print("Failo vardas tuščias.")
        return 'Failas nepasirinktas', 400

    if not allowed_file(file.filename):
        print(f"Nepalaikomas failo formatas: {file.filename}")
        return 'Nepalaikomas failo formatas. Galimi: .docx, .doc, .txt', 400


    original_filename = file.filename
    file_id = str(uuid.uuid4())
    saved_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_original.docx")
    file.save(saved_path)
    print(f"Failas išsaugotas: {saved_path}")

    translated_path = os.path.join(app.config['TRANSLATED_FOLDER'], f"{file_id}_translated.docx")
    shutil.copy(saved_path, translated_path)
    print("Pradėtas vertimas...")

    paragraph_count = 0

    if saved_path.endswith('.txt'):
        with open(saved_path, 'r', encoding='utf-8') as f:
            content = f.read()

        translated_text = translate_text(content, source_lang, target_lang)

        with open(translated_path.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
            f.write(translated_text)

        print("TXT failas išverstas.")

        # Įrašom į DB
        entry = TranslationMemory(
            text=content,
            translation=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            confirmed=True,
            is_document=False,
            file_path=translated_path.replace('.docx', '.txt')
        )
        db.session.add(entry)
        db.session.commit()

        return send_file(translated_path.replace('.docx', '.txt'), as_attachment=True, download_name='isverstas.txt')

    else:
        doc = Document(translated_path)
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                try:
                    print(f"Verčiamas paragrafas {paragraph_count + 1}: {paragraph.text[:50]}...")
                    paragraph.text = translate_text(paragraph.text, source_lang, target_lang)
                    print(f"Paragrafas {paragraph_count + 1} išverstas.")
                except Exception as e:
                    print(f"Klaida verčiant paragrafą {paragraph_count + 1}: {str(e)}")
                    paragraph.text = f"[KLAIDA VERČIANT: {str(e)}]"
                paragraph_count += 1

        doc.save(translated_path)
        print(f"Vertimas baigtas. Išsaugotas: {translated_path}\n")

        # Įrašom į DB
        entry = TranslationMemory(
            text=None,
            translation=None,
            source_lang=source_lang,
            target_lang=target_lang,
            confirmed=True,
            is_document=True,
            file_path=translated_path
        )
        db.session.add(entry)
        db.session.commit()

        return send_file(translated_path, as_attachment=True, download_name='isverstas.docx')

@app.errorhandler(400)
def bad_request(e):
    return 'Netinkama užklausa.', 400

@app.errorhandler(500)
def server_error(e):
    return 'Įvyko serverio klaida.', 500

if __name__ == '__main__':
    app.run(debug=True)
