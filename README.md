# 💪 FitApp - Science Based Hypertrophy

**FitApp** je moderná a vizuálne prepracovaná webová aplikácia navrhnutá pre nadšencov fitness, ktorí chcú systematicky budovať svalovú hmotu na základe vedeckých princípov hypertrofie. Aplikácia umožňuje spravovať tréningové plány, zaznamenávať výživu, sledovať progres a monitorovať preťaženie (progressive overload).

---

## 🚀 Hlavné Funkcie

### 1. 📅 Kalendár a Prehľad (Dashboard)
- Vizualizácia naplánovaných a dokončených tréningových dní v interaktívnom kalendári.
- Sledovanie tréningovej konzistentnosti pomocou aktívneho streak-u.
- Rýchly prehľad o dnešnom pláne priamo na domovskej obrazovke.

### 2. ⚡ Aktívny Tréning a Asynchrónne Sledovanie
- **Rozrobený tréning**: Ak počas cvičenia prejdete na inú podstránku (napr. Výživa), v navigačnom bare sa zobrazí zvýraznený odkaz `⚡ Rozrobený tréning`, ktorý vás vráti presne tam, kde ste prestali.
- **Ukladanie na pozadí**: Automatické zálohovanie rozpísaných sérií a hodnôt do `localStorage` každých 5 sekúnd.
- **Bežiaci časovač**: Časovač tréningu beží na pozadí pomocou ukladania časovej pečiatky (`timestamp`). Čas beží aj vtedy, ak zatvoríte prehliadač alebo vypnete kartu.
- **Progresívne preťaženie**: Pri každom cviku vidíte váš predošlý výkon (váha × opakovania) pre jednoduché prekonávanie limitov.

### 3. 🛠️ Tréningový Plánovač
- Možnosť plne prispôsobiť tréningové dni, svalové partie, série a opakovania.
- **Rýchle ukladanie**: Integrácia asynchrónnych AJAX požiadaviek (Fetch API) – ukladanie jednotlivých cvikov a dní prebieha okamžite bez otravného znovunačítania celej stránky.
- **Rýchla REGENERÁCIA**: Funkcia automaticky pregeneruje tréningový plán náhodným výberom cvikov z kategorizovaných onboardingových zoznamov.

### 4. 🍎 Výživa a Sledovanie Makroživín
- Zaznamenávanie denného príjmu (Kalórie, Bielkoviny, Sacharidy, Tuky).
- Interaktívne progress bary s farebným odlíšením jednotlivých živín (bielkoviny = azúrová, sacharidy = žltá, tuky = ružová).
- Prehľadný denný log s možnosťou mazania jedál.
- Interaktívny graf s trendom vývoja príjmu za zvolené obdobie pomocou `Chart.js`.

---

## 🛠️ Technologický Stack

- **Backend**: Python (Flask)
- **Databáza & Auth**: Supabase (PostgreSQL)
- **Frontend**: HTML5, Vanilla CSS (Premium Cyber-Hypertrophy glassmorphic design), Vanilla JavaScript
- **Grafy**: Chart.js
- **Ikony**: Bootstrap Icons

---

## ⚙️ Spustenie Aplikácie Lokálne

### 1. Požiadavky
Uistite sa, že máte nainštalovaný Python (verzia 3.8 a novšia) a správcu balíčkov `pip`.

### 2. Klonovanie a Inštalácia
Nainštalujte potrebné knižnice a závislosti zo súboru `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Nastavenie Premenných Prostredia
Vytvorte súbor `.env` v koreňovom adresári projektu a pridajte prístupové údaje k vašej databáze Supabase:
```env
SUPABASE_URL=tvoja_supabase_url
SUPABASE_KEY=tvoj_supabase_anon_key
SUPABASE_SERVICE_KEY=tvoj_supabase_service_role_key
SECRET_KEY=tvoj_flask_secret_key
```

### 4. Spustenie Servera
Pre spustenie aplikácie môžete použiť pripravené dávkové súbory:
- Kliknite na `run_fitapp.bat` alebo `start_app.bat` na systéme Windows.
- Alebo ručne v termináli zadajte:
```bash
python app.py
```
Aplikácia bude dostupná na lokalnej adrese: **`http://127.0.0.1:8080`**.
