# norint pasileist koda:
# venv\Scripts\activate
# python -m flask run

from flask import Flask, request, jsonify, render_template
from easynmt import EasyNMT
import torch
import time

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

# Sukuriame Flask aplikaciją
app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)
