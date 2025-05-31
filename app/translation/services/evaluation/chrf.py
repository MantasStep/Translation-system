# app/translation/services/evaluation/chrf.py

from sacrebleu.metrics import CHRF

def compute_sentence_chrf(hypothesis: str, reference: str) -> float:
    """
    Apskaičiuoja ChrF (Character F-score) tarp vieno sakinio (hypothesis) ir vieno reference.
    Kadangi kai kuriose sacrebleu versijose CHRF neturi .score(), naudojame .corpus_score().

    - hypothesis: vienas išeities sakinys (anglų kalba, pvz.)
    - reference: vienas originalus sakinys (lietuvių kalba, pvz.)

    Grąžina ChrF balą (float) skalėje 0–100.
    """
    chrf_scorer = CHRF()

    # .corpus_score() laukia: (list_of_hypotheses, list_of_list_of_references)
    # kadangi turime vieną hipotezę ir vieną referenciją, suvyniojame juos į sąrašus:
    hyp_list = [hypothesis]
    ref_list = [[reference]]

    chrf_result = chrf_scorer.corpus_score(hyp_list, ref_list)
    # chrf_result.score yra float reikšmė 0–100
    return float(chrf_result.score)
