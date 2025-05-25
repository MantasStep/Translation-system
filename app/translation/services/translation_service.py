# app/translation/services/translation_service.py

import time
import os
from flask import current_app
from flask_login import current_user
from app.ml_models.model_initializer import load_models
from app.database.models import TranslationMemory
from app import db
from app.translation.constants import HF_MODELS
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Hardcoded path locations
UPLOAD_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\uploads"
TRANSLATED_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations"


class TranslationService:
    def __init__(self):
        self.hf_models = load_models()

    def translate_text(self, text: str, source_lang: str, target_lang: str):
        active_hf_models = self.filter_models_by_direction(source_lang, target_lang)

        if not active_hf_models:
            raise ValueError(f"Nėra modelių palaikančių {source_lang}→{target_lang}")

        candidates = {}

        for key, info in active_hf_models.items():
            tok   = info["tokenizer"]
            model = info["model"]
            current_app.logger.debug(f"[HF:{key}] translating…")
            start = time.time()

            if key.startswith("m2m100"):
                tok.src_lang = source_lang
                encoded     = tok(text, return_tensors="pt")
                bos_id      = tok.get_lang_id(target_lang)
                outs        = model.generate(**encoded, forced_bos_token_id=bos_id)
            elif key.startswith("mbart"):
                src_lang_code = f"{source_lang}_XX"
                tgt_lang_code = f"{target_lang}_XX"
                tok.src_lang = src_lang_code
                encoded     = tok(text, return_tensors="pt")
                bos_id      = tok.lang_code_to_id[tgt_lang_code]
                outs        = model.generate(**encoded, forced_bos_token_id=bos_id)
            else:
                encoded = tok(text, return_tensors="pt", padding=True)
                outs    = model.generate(**encoded)

            translation = tok.batch_decode(outs, skip_special_tokens=True)[0]
            current_app.logger.debug(f"[HF:{key}] done in {time.time()-start:.2f}s")
            candidates[key] = translation

        best = max(candidates.values(), key=len)
        return best, candidates

    def save_translation(
        self,
        original: str,
        best: str,
        all_outs: dict,
        src: str,
        tgt: str,
        is_doc: bool = False,
        file_path: str = None,
        translated_path: str = None
    ):
        print(f"🛠️ Saugojamas vertimas į DB:\n  Originalus tekstas: {original}\n  Vertimas: {best}")

        if not current_user or not hasattr(current_user, 'id'):
            raise RuntimeError("Nepavyko nustatyti prisijungusio vartotojo.")

        # Pilni keliai išsaugojimui
        print(f"🛠️ Saugojamas failas: {file_path}, Išverstas failas: {translated_path}")
        
        file_path = os.path.join(UPLOAD_FOLDER, file_path) if file_path else None
        translated_path = os.path.join(TRANSLATED_FOLDER, translated_path) if translated_path else None

        print(f"⚡ Pilnas originalaus failo kelias: {file_path}")
        print(f"⚡ Pilnas išversto failo kelias: {translated_path}")

        try:
            rec = TranslationMemory(
                source_text=original if not is_doc else None,
                translated_text=best if not is_doc else None,
                source_lang=src,
                target_lang=tgt,
                is_document=is_doc,
                file_path=file_path,
                translated_path=translated_path,
                user_id=current_user.id
            )

            db.session.add(rec)
            db.session.commit()
            print("✅ Įrašas sėkmingai išsaugotas!")
        except Exception as e:
            print(f"❌ Klaida išsaugant įrašą į DB: {e}")


    def filter_models_by_direction(self, src: str, tgt: str):
        print(f"🛠️ Filtruojama kryptis: {src} → {tgt}")
        active_hf_models = {
            k: v for k, v in self.hf_models.items()
            if (src, tgt) in HF_MODELS[k]["directions"]
        }
        print(f"🎯 Atrinkti HF modeliai: {list(active_hf_models.keys())}")
        return active_hf_models
