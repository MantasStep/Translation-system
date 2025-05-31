# test_bleu.py

# 1. Importuojame compute_sentence_bleu iš mūsų BLEU modulio
try:
    from app.translation.services.evaluation.bleu import compute_sentence_bleu
except ModuleNotFoundError as e:
    print("❌ Negaliu importuoti compute_sentence_bleu: ", e)
    print("   Įsitikink, kad failas 'app/translation/services/evaluation/bleu.py' egzistuoja")
    exit(1)

# 2. Paruošiame testinius tekstus
reference = "Labas vakaras, kaip sekasi?"
hypothesis_good = "Labas vakaras, kaip sekasi?"
hypothesis_bad  = "Hello world"

# 3. Apskaičiuojame BLEU balus ir išvedame
try:
    bleu_good = compute_sentence_bleu(hypothesis_good, reference)
    bleu_bad  = compute_sentence_bleu(hypothesis_bad, reference)
    print(f"Reference  : {reference}")
    print(f"Hypothesis1: {hypothesis_good} -> BLEU = {bleu_good:.2f}")
    print(f"Hypothesis2: {hypothesis_bad}  -> BLEU = {bleu_bad:.2f}")
except Exception as e:
    print("❌ Klaida skaičiuojant BLEU:", e)
    exit(1)
