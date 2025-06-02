# app/translation/services/evaluation/bert.py

from bert_score import BERTScorer

def compute_bert_f1(hypotheses: list[str], references: list[str], lang: str) -> list[float]:
    scorer = BERTScorer(
        lang=lang,
        model_type="xlm-roberta-base",
        rescale_with_baseline=False
    )
    P, R, F1 = scorer.score(hypotheses, references)
    return F1.tolist()
