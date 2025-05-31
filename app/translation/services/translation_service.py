import time
import os
from flask import current_app
from flask_login import current_user

from bert_score import BERTScorer
from huggingface_hub import snapshot_download

# Importuojame vietinį HF modelių pakrovimą (snapshot + local_files_only)
from app.ml_models.model_initializer import load_models

from app.database.models import TranslationMemory
from app import db
from app.translation.constants import HF_MODELS
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Importuojame hibridinę atranką (BLEU + BERTScore)
from app.translation.services.model_evaluator import select_best_by_hybrid

# mBART kalbų žemėlapis
MBART_LANG_CODE = {
    "en": "en_XX",
    "lt": "lt_LT",
    # Galite pridėti ir kitas, jei prireiks
}

# Kietai užkoduoti folderiai dokumentams
UPLOAD_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\uploads"
TRANSLATED_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations"


def ensure_bert_model(
    lang: str = "lt",
    model_type: str = "xlm-roberta-base"
):
    """
    1) Pirmiausia bandome BERTScorer(lang, model_type) tiesiogiai.
       Jei svoriai jau yra lokaliai HF cache, konstrukcija praeis be klaidos (ir be interneto).
       (Dabar 'model_type' = "xlm-roberta-base" – patikimai palaikomas raktas BERTScorer).
    2) Jei konstrukcija meta klaidą (pvz., svoriai dar neparsisiųsti), todėl:
       - snapshot_download(repo_id=model_type, cache_dir=...) – vienkartinis parsisiuntimas lokaliai.
    3) Po parsisiuntimo dar kartą bandome BERTScorer(lang, model_type).
       Dabar svoriai turėtų būti lokaliai, todėl veiks be interneto. Jeigu ir vėl meta klaidą –
       reiškia talpykla sugadinta, ir mes metame RuntimeError su instrukcija ištrinti cache dir.
    """

    print(f"🔄 Bandome įkrauti BERTScorer (model_type='{model_type}') lokaliai (be interneto)...")
    try:
        # 1) Bandome tiesiogiai – jeigu svoriai jau yra talpykloje (~/.cache/torch/transformers…), tai veiks.
        scorer = BERTScorer(
            lang=lang,
            model_type=model_type,
            rescale_with_baseline=True
        )
        print(f"✅ BERTScorer '{model_type}' pakrautas iš lokalaus cache.")
        return

    except Exception as first_err:
        # Jeigu failų nėra (ar kitokia klaida), tęsiame su parsisiuntimu
        print(f"⚠️ Nepavyko įkrauti BERTScorer lokaliai: {first_err}")
        print("   Pradedame vienkartinį parsisiuntimą / atnaujinimą per Hugging Face...")

    # 2) Vienkartinis parsisiuntimas (arba atnaujinimas) į lokalią talpyklą:
    cache_dir = os.path.join(
        os.path.expanduser("~"),
        ".cache",
        "huggingface",
        "models",
        model_type.replace("/", "_")
    )

    try:
        local_path = snapshot_download(
            repo_id=model_type,
            cache_dir=cache_dir,
            resume_download=True,
            force_download=False,
            token=os.getenv("HF_HUB_TOKEN", None),
        )
        print(f"🔽 BERTScorer svoriai parsiųsti/atnaujinti: {local_path}")
    except Exception as exc:
        err = (
            f"❌ BERTScorer modelio '{model_type}' svorių parsisiuntimas nepavyko:\n"
            f"   {exc}\n"
            f"   Patikrinkite interneto ryšį ir katalogą '{cache_dir}'.\n"
            "Vienkartiniam parsisiuntimui galite paleisti:\n"
            f"    from bert_score import BERTScorer\n"
            f"    BERTScorer(lang='{lang}', model_type='{model_type}')\n"
            "Tada paleiskite programą be interneto.\n"
        )
        print(err)
        raise RuntimeError(err)

    # 3) Po parsisiuntimo dar kartą bandome BERTScorer(lang, model_type)
    try:
        scorer = BERTScorer(
            lang=lang,
            model_type=model_type,
            rescale_with_baseline=True
        )
        print(f"✅ BERTScorer '{model_type}' sėkmingai pakrautas lokaliai po parsisiuntimo.")
        return
    except Exception as second_err:
        err = (
            f"❌ Nepavyko inicializuoti BERTScorer net ir po parsisiuntimo:\n"
            f"   {second_err}\n"
            f"   Gali būti, kad HF cache pažeistas arba trūksta failų.\n"
            f"   Ištrinkite katalogą '{cache_dir}' ir paleiskite programą su internetu dar kartą.\n"
        )
        print(err)
        raise RuntimeError(err)

class TranslationService:
    def __init__(self):
        # 1. Užtikriname, kad BERTScorer modelis būtų pasiekiamas lokaliai
        try:
            ensure_bert_model(
                lang="lt",
                model_type="xlm-roberta-base"
            )
        except RuntimeError as e:
            # Jei nepavyksta, mes toliau tęsiame be BERTScore (tik BLEU režimu)
            print(f"⚠️ BERT modelio tikrinimas nepavyko: {e}")
            print("   Tęsiu be BERTScore – hibridinis vertinimas remsis vien BLEU")

        # 2. Įkrauname HF modelius (kiti vertimai)
        try:
            self.hf_models = load_models()
        except RuntimeError as e:
            print(f"❌ HF modelių pakrovimo klaida: {e}")
            raise

        print("✅ HF modeliai sėkmingai įkrauti:", list(self.hf_models.keys()))

        # 3. Inicializuojame DocumentService, jei reikia dokumentų vertimo
        from app.upload.services.document_service import DocumentService
        self.doc_service = DocumentService()

    def translate_text(self, text: str, source_lang: str, target_lang: str):
        """
        Atlieka vertimą per visus HF modelius (forward),
        po to pasirenka geriausią vertimą pagal hibridinį BLEU + BERTScore.
        Grąžina (best_translation, all_candidates_dict).
        """

        print(f"🔄 Pradedamas vertimas: '{text}' ({source_lang} → {target_lang})")

        # 1. Filtruojame HF modelius pagal source_lang→target_lang
        active_hf_models = self.filter_models_by_direction(source_lang, target_lang)
        if not active_hf_models:
            raise ValueError(
                f"Nėra HF modelių palaikančių kryptį: {source_lang}→{target_lang}"
            )
        print("🔎 Atrinkti forward‐vertimo modeliai:", list(active_hf_models.keys()))

        # 2. Atlikti forward vertimą per kiekvieną modelį
        candidates: dict[str, str] = {}
        for key, info in active_hf_models.items():
            tok = info["tokenizer"]
            model = info["model"]
            print(f"📝 [HF:{key}] Pradedamas vertimas...")
            start = time.time()

            if key.startswith("m2m100"):
                tok.src_lang = source_lang
                encoded = tok(text, return_tensors="pt")
                bos_id = tok.get_lang_id(target_lang)
                outs = model.generate(
                    **encoded,
                    forced_bos_token_id=bos_id
                )

            elif key.startswith("mbart"):
                if source_lang not in MBART_LANG_CODE or target_lang not in MBART_LANG_CODE:
                    raise ValueError(
                        f"mBART kodas nerastas kalbai: {source_lang} arba {target_lang}"
                    )

                src_code = MBART_LANG_CODE[source_lang]
                tgt_code = MBART_LANG_CODE[target_lang]
                tok.src_lang = src_code
                encoded = tok(text, return_tensors="pt")
                bos_id = tok.lang_code_to_id[tgt_code]
                outs = model.generate(
                    **encoded,
                    forced_bos_token_id=bos_id
                )

            else:
                encoded = tok(text, return_tensors="pt", padding=True)
                outs = model.generate(**encoded)

            translation = tok.batch_decode(outs, skip_special_tokens=True)[0]
            duration = time.time() - start
            print(
                f"⌛ [HF:{key}] Vertimas baigtas per {duration:.2f} s → "
                f"'{translation}'"
            )
            candidates[key] = translation

        print("📦 Visi forward‐vertimo kandidatai:", candidates)

        # 3. Pasirenkame geriausią vertimą pagal hibridinį BLEU + BERTScore
        try:
            best_translation, best_model_key = select_best_by_hybrid(
                candidates,
                self.hf_models,
                text,
                source_lang,
                target_lang,
                weight_bleu=0.5  # 50% BLEU, 50% BERTScore
            )
            print(f"🎖️ [Hibridinis] Pasirinktas modelis: {best_model_key}")
            print(f"🎯 [Hibridinis] Geriausias vertimas: '{best_translation}'")
        except Exception as e:
            # Jeigu BERT dalyje įvyko klaida, grąžiname ilgiausią vertimą (tik BLEU)
            print(f"❌ Klaida renkantis geriausią hibridinį modelį: {e}")
            best_translation = max(candidates.values(), key=len)
            print("⚠️ Pasirinktas atsarginis (ilgiausias) vertimas:", best_translation)

        return best_translation, candidates

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
        """
        Išsaugoti vertimo įrašą į duomenų bazę.
        Atspausdina pranešimą, ar pavyko išsaugoti.
        """
        print("💾 Pradedamas įrašas į DB...")
        print(
            f"🛠️ Saugojamas vertimas:\n"
            f"  Originalus tekstas: {original}\n"
            f"  Vertimas: {best}"
        )
        print(
            f"🛠️ Papildoma informacija:\n"
            f"  source_lang={src}, target_lang={tgt}, is_doc={is_doc}"
        )
        print(
            f"🛠️ Saugojamas failas: {file_path}, Išverstas failas: {translated_path}"
        )

        if not current_user or not hasattr(current_user, "id"):
            raise RuntimeError("Nepavyko nustatyti prisijungusio vartotojo.")

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
            print("✅ Įrašas sėkmingai išsaugotas į DB!")
        except Exception as e:
            print(f"❌ Klaida saugant įrašą į DB: {e}")
            current_app.logger.error(f"❌ Klaida saugant įrašą į DB: {e}")

    def filter_models_by_direction(self, src: str, tgt: str) -> dict:
        """
        Filtruoja self.hf_models pagal src→tgt porą, naudodamas HF_MODELS metaduomenis.
        Gražina {model_key: model_info, ...}.
        """
        current_app.logger.debug(f"🛠️ Filtruojama kryptis: {src} → {tgt}")
        active_hf_models = {}
        for model_key, model_info in self.hf_models.items():
            static_dirs = HF_MODELS.get(model_key, {}).get("directions", [])
            for static_src, static_tgt in static_dirs:
                if static_src.split("_")[0] == src and static_tgt.split("_")[0] == tgt:
                    active_hf_models[model_key] = model_info
                    break

        print("🔍 Atrinkti modeliai dėl krypties:", list(active_hf_models.keys()))
        return active_hf_models
