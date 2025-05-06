# app/translation/services/translation_service.py

import time
from flask import current_app
from flask_login import current_user
from app.ml_models.model_initializer import load_models
from app.database.models import TranslationMemory
from app import db

class TranslationService:
    def __init__(self):
        # Modeliai užkraunami tik vieną kartą, kai sukuriama šio serviso instancija
        self.easy_models, self.hf_models = load_models()

    def translate_text(self, text: str, source_lang: str, target_lang: str):
        """
        Išverčia tekstą per visus modelius, kurie palaiko source_lang→target_lang.
        Grąžina tuple(best_translation, all_candidates).
        """
        # Atrenkame tik tuos EasyNMT ir HF modelius, kurie palaiko šią kryptį
        easy_active = {
            k: info for k, info in self.easy_models.items()
            if (source_lang, target_lang) in info["langs"]
        }
        hf_active = {
            k: info for k, info in self.hf_models.items()
            if (source_lang, target_lang) in info["langs"]
        }

        candidates = {}

        # 1) EasyNMT modeliai
        for key, info in easy_active.items():
            em = info["model"]
            current_app.logger.debug(f"[EasyNMT:{key}] translating…")
            start = time.time()
            out = em.translate(
                text,
                source_lang=source_lang,
                target_lang=target_lang
            )
            current_app.logger.debug(f"[EasyNMT:{key}] done in {time.time()-start:.2f}s")
            candidates[key] = out

        # 2) Hugging Face modeliai
        #    (Marian ir M2M100 pagal raktus)
        from transformers import (
            MarianTokenizer, MarianMTModel,
            M2M100Tokenizer, M2M100ForConditionalGeneration
        )

        for key, info in hf_active.items():
            tok   = info["tokenizer"]
            model = info["model"]
            current_app.logger.debug(f"[HF:{key}] translating…")
            start = time.time()

            if key.startswith("m2m100"):
                # M2M100: nustatome src_lang ir bos_token
                tok.src_lang = source_lang
                encoded     = tok(text, return_tensors="pt")
                bos_id      = tok.get_lang_id(target_lang)
                outs        = model.generate(**encoded, forced_bos_token_id=bos_id)

            else:
                # Marian: vienam poros repo
                encoded = tok(text, return_tensors="pt", padding=True)
                outs    = model.generate(**encoded)

            translation = tok.batch_decode(outs, skip_special_tokens=True)[0]
            current_app.logger.debug(f"[HF:{key}] done in {time.time()-start:.2f}s")
            candidates[key] = translation

        if not candidates:
            raise ValueError(f"Nėra modelių palaikančių {source_lang}→{target_lang}")

        # Pasirenkame „geriausią“ (čia – ilgiausią) vertimą
        best = max(candidates.values(), key=len)
        return best, candidates

    def save_translation(
        self,
        original: str,
        best: str,
        all_outs: dict,
        src: str,
        tgt: str,
        is_doc: bool=False,
        file_path: str=None
    ):
        """
        Įrašo vertimą į TranslationMemory su prisijungusio vartotojo ID.
        """
        if not current_user or not hasattr(current_user, 'id'):
            raise RuntimeError("Nepavyko nustatyti prisijungusio vartotojo.")

        rec = TranslationMemory(
            source_text     = original     if not is_doc else None,
            translated_text = best,
            source_lang     = src,
            target_lang     = tgt,
            is_document     = is_doc,
            file_path       = file_path,
            user_id         = current_user.id
        )
        db.session.add(rec)
        db.session.commit()

    def translate_api(self, data: dict):
        """
        Flask view kviečia su JSON {text, src, tgt}.
        Atlieka vertimą, įrašo jį į DB ir grąžina rezultatus.
        """
        txt = data['text']
        src = data['src']
        tgt = data['tgt']
        best, all_outs = self.translate_text(txt, src, tgt)
        self.save_translation(txt, best, all_outs, src, tgt, is_doc=False)
        return {'best': best, 'candidates': all_outs}
