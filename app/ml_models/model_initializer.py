# app/ml_models/model_initializer.py

import os
from huggingface_hub import snapshot_download
from huggingface_hub.utils import RepositoryNotFoundError
from easynmt import EasyNMT
from typing import Optional
from transformers import (
    MarianTokenizer, MarianMTModel,
    M2M100Tokenizer, M2M100ForConditionalGeneration,
    MBart50TokenizerFast, MBartForConditionalGeneration,
)

HERE = os.path.dirname(__file__)
CACHE_DIR = os.path.abspath(os.path.join(HERE, '..', '..', 'models_cache'))

MODEL_CLASSES = {
    "lt_en":       (MarianTokenizer,             MarianMTModel),
    "en_lt":       (MarianTokenizer,             MarianMTModel),
    "m2m100_418M": (M2M100Tokenizer,             M2M100ForConditionalGeneration),
    "m2m100_1.2B": (M2M100Tokenizer,             M2M100ForConditionalGeneration),
    "mbart50_m2en":(MBart50TokenizerFast,        MBartForConditionalGeneration),
    "mbart50_en2m":(MBart50TokenizerFast,        MBartForConditionalGeneration),
}

ALLOWED_PAIRS = {("lt","en"), ("en","lt")}

from app.translation.constants import HF_MODELS
MODEL_REPOS = {k: v["model_name"] for k, v in HF_MODELS.items()}

def ensure_model(repo_id: str) -> Optional[str]:
    os.makedirs(CACHE_DIR, exist_ok=True)
    try:
        return snapshot_download(
            repo_id=repo_id,
            cache_dir=CACHE_DIR,
            resume_download=True,
            force_download=False,
            token=os.getenv("HF_HUB_TOKEN", None),
        )
    except RepositoryNotFoundError:
        print(f"!!! Repo `{repo_id}` not found on HF, skipping.")
        return None

def load_models():
    hf_models = {}

    for key, repo_id in MODEL_REPOS.items():
        print(f">>> Ensuring model '{key}' ({repo_id})...")
        path = ensure_model(repo_id)
        if not path:
            continue

        try:
            TokClass, ModelClass = MODEL_CLASSES[key]
            tok   = TokClass.from_pretrained(path, local_files_only=True)
            model = ModelClass.from_pretrained(path, local_files_only=True)

            if key.startswith("m2m100"):
                codes = set(tok.lang_code_to_id.keys())
                langs = {(s, t) for s, t in ALLOWED_PAIRS
                            if s in codes and t in codes}

            elif key.startswith("mbart50"):
                codes = set(tok.lang_code_to_id.keys())
                langs = {
                    (sc, tc)
                    for src, tgt in ALLOWED_PAIRS
                    for sc in codes if sc.startswith(f"{src}_")
                    for tc in codes if tc.startswith(f"{tgt}_")
                }

            else:
                src, tgt = key.split("_")
                langs = {(src, tgt)}

            if not langs:
                raise ValueError(
                    f"Model '{key}' ({path}) nepalaiko nė vienos ALLOWED_PAIRS poros: {ALLOWED_PAIRS}."
                )

            hf_models[key] = {"tokenizer": tok, "model": model, "langs": langs}
            print(f">>> HF '{key}' supports: {langs}")

        except Exception as e:
            print(f"!!! HF init failed for {key}: {e}")

    return hf_models