# app/translation/services/model_evaluator.py

from typing import Dict, Tuple, List

# Jūsų esami importai BLEU ir BERT funkcijoms:
from app.translation.services.evaluation.bleu import compute_sentence_bleu
from app.translation.services.evaluation.bert import compute_bert_f1

# Naujas importas ChrF:
from app.translation.services.evaluation.chrf import compute_sentence_chrf


def filter_models_by_direction(
    hf_models: Dict[str, dict],
    src_lang: str,
    tgt_lang: str
) -> Dict[str, dict]:
    """
    Gražina subset'ą hf_models, kurie palaiko tiksliai src_lang→tgt_lang kryptį.
    """
    from app.translation.constants import HF_MODELS

    active = {}
    print(f"🔍 [model_evaluator] Filtruojama reverse kryptis: {src_lang} → {tgt_lang}")
    for key, info in hf_models.items():
        ax = HF_MODELS.get(key, {})
        dirs = ax.get("directions", [])
        for static_src, static_tgt in dirs:
            if static_src.split("_")[0] == src_lang and static_tgt.split("_")[0] == tgt_lang:
                active[key] = info
                break
    print(f"🔍 [model_evaluator] Atrinkti reverse modeliai: {list(active.keys())}")
    return active


def compute_back_translations(
    fwd_translation: str,
    reverse_models: Dict[str, dict],
    source_lang: str,
    target_lang: str
) -> List[str]:
    """
    Atlieka vieną kartą atgalinį vertimą (back-translation) fwd_translation per visus reverse_models.
    Grąžina sąrašą atgalinių tekstų.
    """
    back_translations: List[str] = []
    print(f"🔄 [model_evaluator] Back-translation pradedama vieną kartą: '{fwd_translation[:30]}...'")

    for rev_name, rev_info in reverse_models.items():
        rev_tok = rev_info["tokenizer"]
        rev_model = rev_info["model"]
        print(f"🔄 [model_evaluator] Atgal verčiama per modelį: {rev_name}")

        try:
            if rev_name.startswith("m2m100"):
                rev_tok.src_lang = target_lang
                encoded_bt = rev_tok(fwd_translation, return_tensors="pt")
                bos_id_bt = rev_tok.get_lang_id(source_lang)
                outs_bt = rev_model.generate(**encoded_bt, forced_bos_token_id=bos_id_bt)

            elif rev_name.startswith("mbart"):
                src_code_bt = f"{target_lang}_XX" if target_lang != "lt" else "lt_LT"
                tgt_code_bt = f"{source_lang}_XX" if source_lang != "lt" else "lt_LT"
                rev_tok.src_lang = src_code_bt
                encoded_bt = rev_tok(fwd_translation, return_tensors="pt")
                try:
                    bos_id_bt = rev_tok.lang_code_to_id[tgt_code_bt]
                except KeyError:
                    print(f"⚠️ [model_evaluator] Modelis '{rev_name}' nepalaiko '{tgt_code_bt}', praleidžiu.")
                    continue
                outs_bt = rev_model.generate(**encoded_bt, forced_bos_token_id=bos_id_bt)

            else:
                encoded_bt = rev_tok(fwd_translation, return_tensors="pt", padding=True)
                outs_bt = rev_model.generate(**encoded_bt)

        except Exception as exc:
            print(f"⚠️ [model_evaluator] Klaida vertime '{rev_name}': {exc}. Praleidžiu šį modelį.")
            continue

        back_text = rev_tok.batch_decode(outs_bt, skip_special_tokens=True)[0]
        print(f"🔄 [model_evaluator] Back-text: '{back_text[:30]}...'")
        back_translations.append(back_text)

    if not back_translations:
        print("⚠️ [model_evaluator] Nėra reverse modelių arba nepavyko versti atgal, grąžinu tuščią sąrašą.")
    return back_translations


def round_trip_bleu_per_candidate(
    back_translations: List[str],
    source_text: str
) -> float:
    """
    Paimus jau apskaičiuotus atgalinius vertimus (back_translations), grąžina vidutinį BLEU.
    Jei back_translations sąrašas tuščias, gražina 0.0.
    """
    if not back_translations:
        print("⚠️ [model_evaluator][BLEU] Nėra atgalinių tekstų, grąžinu BLEU=0")
        return 0.0

    total_bleu = 0.0
    for bt in back_translations:
        bleu = compute_sentence_bleu(bt, source_text)
        print(f"📏 [model_evaluator] BLEU bt vs source: {bleu:.2f}")
        total_bleu += bleu

    avg_bleu = total_bleu / len(back_translations)
    print(f"📊 [model_evaluator] Vidutinis BLEU už kandidatą: {avg_bleu:.2f}")
    return avg_bleu


def round_trip_bert_per_candidate(
    back_translations: List[str],
    source_text: str,
    source_lang: str
) -> float:
    """
    Paimus jau apskaičiuotus back_translations, grąžina vidutinį BERTScore F1.
    Jei back_translations sąrašas tuščias arba BERTScore dalis meta klaidą, gražina 0.0.
    """
    if not back_translations:
        print("⚠️ [model_evaluator][BERT] Nėra atgalinių tekstų, grąžinu BERTScore=0")
        return 0.0

    try:
        hypotheses = back_translations
        references = [source_text] * len(back_translations)
        f1_scores = compute_bert_f1(hypotheses, references, lang=source_lang)
    except Exception as e:
        print(f"⚠️ [model_evaluator][BERT] BERTScore skaičiavimo klaida: {e}. Grąžinu 0.0")
        return 0.0

    for idx, f1 in enumerate(f1_scores):
        print(f"📏 [model_evaluator] BERTScore (F1) bt vs source (model {idx}): {f1:.4f}")

    avg_f1 = sum(f1_scores) / len(f1_scores)
    print(f"📊 [model_evaluator] Vidutinis BERT F1 už kandidatą: {avg_f1:.4f}")
    return avg_f1


def select_best_by_round_trip(
    candidates: Dict[str, str],
    hf_models: Dict[str, dict],
    source_text: str,
    source_lang: str,
    target_lang: str
) -> Tuple[str, str]:
    """
    (BLEU-vien tik pasirinkimas)
    Iš candidates pasirenka geriausią vertimą pagal round-trip BLEU,
    bet atgalinį vertimą atlieka tik vieną kartą per kandidatą.
    """
    print(f"🔍 [model_evaluator] Pradedama geriausio modelio paieška pagal BLEU...")
    reverse_models = filter_models_by_direction(hf_models, target_lang, source_lang)

    if not reverse_models:
        best_model_name = max(candidates, key=lambda m: len(candidates[m]))
        print(f"⚠️ [model_evaluator] Reverse modelių nėra, pasirenkamas ilgiausias: {best_model_name}")
        return candidates[best_model_name], best_model_name

    bleu_scores: Dict[str, float] = {}
    for fwd_model_name, fwd_translation in candidates.items():
        print(f"🔍 [model_evaluator] Skaičiuoju BLEU už kandidatą: {fwd_model_name}")

        back_texts = compute_back_translations(
            fwd_translation, reverse_models, source_lang, target_lang
        )

        avg_bleu = round_trip_bleu_per_candidate(back_texts, source_text)
        bleu_scores[fwd_model_name] = avg_bleu

    best_model_name = max(bleu_scores, key=bleu_scores.get)
    print(f"🏆 [model_evaluator] Geriausias BLEU modelis: {best_model_name} (BLEU={bleu_scores[best_model_name]:.2f})")
    return candidates[best_model_name], best_model_name


def select_best_by_hybrid(
    candidates: Dict[str, str],
    hf_models: Dict[str, dict],
    source_text: str,
    source_lang: str,
    target_lang: str,
    weight_bleu: float = 0.5
) -> Tuple[str, str]:
    """
    Iš candidates pasirenka geriausią vertimą,
    kombinuodama round-trip BLEU, BERTScore F1 ir ChrF.
    Atgalinį vertimą atlieka tik vieną kartą per kandidatą.
    """
    print(f"🔍 [model_evaluator] Pradedama hibridinio geriausio modelio paieška (BLEU+BERT+ChrF)...")
    reverse_models = filter_models_by_direction(hf_models, target_lang, source_lang)

    if not reverse_models:
        best_model_name = max(candidates, key=lambda m: len(candidates[m]))
        print(f"⚠️ [model_evaluator] Reverse modelių nėra, pasirenkamas ilgiausias: {best_model_name}")
        return candidates[best_model_name], best_model_name

    scores_hybrid: Dict[str, float] = {}
    bleu_scores: Dict[str, float] = {}
    bert_scores: Dict[str, float] = {}
    chrf_scores: Dict[str, float] = {}

    for mdl_name, fwd_translation in candidates.items():
        print(f"🔍 [model_evaluator] Skaičiuoju BLEU, BERT ir ChrF už kandidatą: {mdl_name}")

        # 1) Atlieku vieną back-translation visiems reverse modeliams:
        back_texts = compute_back_translations(
            fwd_translation, reverse_models, source_lang, target_lang
        )

        # 2) Vidutinis BLEU:
        avg_bleu = round_trip_bleu_per_candidate(back_texts, source_text)
        bleu_scores[mdl_name] = avg_bleu

        # 3) Vidutinis BERTScore F1:
        avg_f1 = round_trip_bert_per_candidate(back_texts, source_text, source_lang)
        bert_scores[mdl_name] = avg_f1

        # 4) Vidutinis ChrF:
        total_chrf = 0.0
        for bt in back_texts:
            chrf_val = compute_sentence_chrf(bt, source_text)
            print(f"📏 [model_evaluator] ChrF bt vs source: {chrf_val:.2f}")
            total_chrf += chrf_val
        avg_chrf = total_chrf / len(back_texts) if back_texts else 0.0
        print(f"📊 [model_evaluator] Vidutinis ChrF už kandidatą: {avg_chrf:.2f}")
        chrf_scores[mdl_name] = avg_chrf

        # 5) Hibridinis balas (pvz., BLEU 50%, BERT 30%, ChrF 20%):
        weight_bert = 0.3
        weight_chrf = 0.2
        hybrid_score = (
            weight_bleu * avg_bleu +
            weight_bert * (avg_f1 * 100) +
            weight_chrf * avg_chrf
        )
        scores_hybrid[mdl_name] = hybrid_score

        print(
            f"🔢 [model_evaluator] Modelis {mdl_name}: "
            f"BLEU={avg_bleu:.2f}, BERT_F1={avg_f1:.4f}, ChrF={avg_chrf:.2f}, "
            f"HIBRID={hybrid_score:.2f}"
        )

    best_model_name = max(scores_hybrid, key=scores_hybrid.get)
    print(
        f"🏆 [model_evaluator] Hibridinis geriausias modelis: {best_model_name} "
        f"(HIBRID={scores_hybrid[best_model_name]:.2f})"
    )
    return candidates[best_model_name], best_model_name
