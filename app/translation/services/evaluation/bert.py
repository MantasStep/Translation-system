# app/translation/services/evaluation/bert.py

from bert_score import BERTScorer

def compute_bert_f1(hypotheses: list[str], references: list[str], lang: str) -> list[float]:
    """
    Atnaujintas variantas: naudojame xlm-roberta-base vietoje microsoft/infoxlm-base,
    nes xlm-roberta-base yra patikimai palaikomas BERTScorer klasėje.
    """
    scorer = BERTScorer(
        lang=lang,
        model_type="xlm-roberta-base",
        rescale_with_baseline=False
    )
    P, R, F1 = scorer.score(hypotheses, references)
    return F1.tolist()
