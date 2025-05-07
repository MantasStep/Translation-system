# Automatinis Vertimas

Vieno langelio Flask aplikacija teksto ir dokumentų (`.txt`, `.docx`) vertimui tarp lietuvių ir anglų kalbų. Naudoja tiek EasyNMT, tiek „Hugging Face“ modelius (Helsinki-NLP & Facebook M2M100).

---

## Funkcionalumas

- **Teksto vertimas** (LT → EN, EN → LT) per web UI.  
- **Dokumentų vertimas**: įkelti `.txt` arba `.docx` failai, išsaugoti su originalia struktūra ir paveikslėliais.  
- **Vertimų atmintis** (Translation Memory): saugo visus vertimus (tekstus ir dokumentus) su prisijungusio vartotojo ID.  
- **Vartotojų valdymas**: registracija, prisijungimas, administratoriaus rolės (kurti/keisti/trinti vartotojus, peržiūrėti Translation Memory).  
- **Failų parsisiuntimas**: išversto (ir originalaus) dokumento atsisiuntimas.

---

## Sistemos reikalavimai

- Python 3.9+  
- Git  
- Virtuali aplinka (pvz., `venv`)

---

## Diegimas

1. **Klonuokite repozitoriją**  
   ```bash
   git clone https://github.com/MantasStep/Translation-system.git
   cd Translation-system

2. **Sukurkite ir aktyvuokite virtualią aplinką**
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

3. **Įdiekite EasyNMT be jo priklausomybių**
py -m pip install --no-deps easynmt

4. **Įdiekite visus kitus paketus**
py -m pip install -r requirements.txt

5. **Sukurkite pradinius vartotojus**
python init_users.py

6. **Paleiskite aplikaciją**
flask run
# Aplikacija pasiekiama http://127.0.0.1:5000/login
