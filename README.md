# Automatinis Vertimas

Vieno langelio Flask aplikacija teksto ir dokumentų (​.txt, ​.docx) vertimui tarp lietuvių ir anglų kalbų. Naudoja tiek EasyNMT, tiek „Hugging Face“ modelius (Helsinki-NLP & Facebook M2M100).

---

## Funkcionalumas

- **Teksto vertimas** (LT→EN, EN→LT) per web UI.
- **Dokumentų vertimas**: įkelti ​.txt arba ​.docx failai, išsaugoti su originalia struktūra ir paveikslėliais.
- **Vertimų atmintis** (Translation Memory): įrašomi visi vertimai (tekstai ir dokumentai) su prisijungusio vartotojo ID.
- **Vartotojų valdymas**: registracija, prisijungimas, administratoriaus rolės (kurti/keisti/trinti vartotojus, peržiūrėti Translation Memory).
- **Failų parsisiuntimas**: išversto (ir originalaus) dokumento atsisiuntimas.

---

## Sistemos reikalavimai

- Python 3.9+
- Git
- Virtuali aplinka (pvz. venv)

---

## Diegimas

1. **Klonuokite repozitoriją**  
   ```bash
   git clone https://github.com/<jūsų-vardas>/automatinis-vertimas.git
   cd automatinis-vertimas

## Sukurkite ir aktyvuokite virtualią aplinką

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

## Sukurkite pradinius vartotojus

python init_users.py

## Paleiskite aplikaciją

flask run

# Paprastai bus pasiekiama http://127.0.0.1:5000//login