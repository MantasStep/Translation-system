# app/translation/constants.py

HF_MODELS = {
    "lt_en": {
        "model_name": "Helsinki-NLP/opus-mt-tc-big-lt-en",
        "directions": [("lt", "en")]
    },
    "en_lt": {
        "model_name": "Helsinki-NLP/opus-mt-tc-big-en-lt",
        "directions": [("en", "lt")]
    },
    "m2m100_418M": {
        "model_name": "facebook/m2m100_418M",
        "directions": [("en", "lt"), ("lt", "en")]
    },
    "m2m100_1.2B": {
        "model_name": "facebook/m2m100_1.2B",
        "directions": [("en", "lt"), ("lt", "en")]
    },
    "mbart_one_to_many": {
        "model_name": "facebook/mbart-large-50-one-to-many-mmt",
        "directions": [("en", "lt")]
    },
    "mbart_many_to_one": {
        "model_name": "facebook/mbart-large-50-many-to-one-mmt",
        "directions": [("lt", "en")]
    },
    "mbart_many_to_many": {
        "model_name": "facebook/mbart-large-50-many-to-many-mmt",
        "directions": [("lt", "en"), ("en", "lt")]
    }
}
