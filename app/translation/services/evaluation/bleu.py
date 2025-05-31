# app/translation/services/evaluation/bleu.py

import sacrebleu

def compute_sentence_bleu(hypothesis: str, reference: str) -> float:
    """
    Apskaičiuoja vieno sakinio BLEU balą (intervale 0–100) lokaliai, naudodamas sacrebleu.
    
    - hypothesis: atgal (back-translation) gautas tekstas (string)
    - reference: originalus tekstas (source_text)
    Grąžina balą (float) intervalo 0–100.
    """
    bleu = sacrebleu.sentence_bleu(hypothesis, [reference])
    return float(bleu.score)
