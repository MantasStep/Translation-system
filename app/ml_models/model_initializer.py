import os
from huggingface_hub import snapshot_download
from huggingface_hub.utils import RepositoryNotFoundError
from easynmt import EasyNMT
from typing import Optional
from transformers import (
    MarianTokenizer, MarianMTModel,
    M2M100Tokenizer, M2M100ForConditionalGeneration,
    MBart50Tokenizer, MBartForConditionalGeneration,
)

# define here base directory for cache
HERE = os.path.dirname(__file__)
# absolute path to models_cache
CACHE_DIR = os.path.abspath(os.path.join(HERE, '..', '..', 'models_cache'))

# supported repos
MODEL_REPOS = {
    "lt_en":       "Helsinki-NLP/opus-mt-tc-big-lt-en",
    "en_lt":       "Helsinki-NLP/opus-mt-tc-big-en-lt",
    "m2m100_418M": "facebook/m2m100_418M",
    "m2m100_1.2B": "facebook/m2m100_1.2B",
    "mbart50_m2m": "facebook/mbart-large-50-many-to-many-mmt",
    "mbart50_m2en":"facebook/mbart-large-50-many-to-one-mmt",
    "mbart50_en2m":"facebook/mbart-large-50-one-to-many-mmt",
}

# allowed language pairs
ALLOWED_PAIRS = {("lt","en"), ("en","lt")}


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
    easy_models = {}
    hf_models   = {}

    for key, repo in MODEL_REPOS.items():
        print(f">>> Ensuring model '{key}' ({repo})…")
        path = ensure_model(repo)
        if not path:
            continue

        # try EasyNMT for m2m models
        if key in ("m2m100_418M", "m2m100_1.2B"):
            try:
                em = EasyNMT(path)
                easy_models[key] = {"model": em, "langs": ALLOWED_PAIRS}
                print(f">>> EasyNMT '{key}' loaded for LT<->EN")
                continue
            except Exception as e:
                print(f">>> EasyNMT init failed for {key}: {e}")

        # fallback to HF for other repos
        try:
            if key.startswith("m2m100"):
                tok   = M2M100Tokenizer.from_pretrained(path, local_files_only=True)
                model = M2M100ForConditionalGeneration.from_pretrained(path, local_files_only=True)
                all_langs = set(tok.lang_code_to_id.keys())
            elif key.startswith("mbart50"):
                tok   = MBart50Tokenizer.from_pretrained(path, local_files_only=True)
                model = MBartForConditionalGeneration.from_pretrained(path, local_files_only=True)
                all_langs = set(tok.lang_code_to_id.keys())
            else:
                tok   = MarianTokenizer.from_pretrained(path, local_files_only=True)
                model = MarianMTModel.from_pretrained(path, local_files_only=True)
                src, tgt = key.split("_")
                all_langs = {src, tgt}

            # filter language pairs
            langs = {(s, t) for s in all_langs for t in all_langs if (s, t) in ALLOWED_PAIRS}
            if langs:
                hf_models[key] = {"tokenizer": tok, "model": model, "langs": langs}
                print(f">>> HF '{key}' supports: {langs}")
            else:
                print(f"--- HF '{key}' loaded but no LT<->EN, skip")
        except Exception as e:
            print(f"!!! HF init failed for {key}: {e}")

    return easy_models, hf_models
