# app/translation/services/evaluation/chrf.py

from sacrebleu.metrics import CHRF

def compute_sentence_chrf(hypothesis: str, reference: str) -> float:
    chrf_scorer = CHRF()

    hyp_list = [hypothesis]
    ref_list = [[reference]]

    chrf_result = chrf_scorer.corpus_score(hyp_list, ref_list)
    return float(chrf_result.score)
