# app/translation/services/evaluation/bleu.py

import sacrebleu

def compute_sentence_bleu(hypothesis: str, reference: str) -> float:
    bleu = sacrebleu.sentence_bleu(hypothesis, [reference])
    return float(bleu.score)
