# FAKTY do kokpitu Hermesa (zebrane przez Drifta 19.10.2026 z maszyny — NIE zmyślać ponad to)

## ✅ MAMY / UŻYWAMY (radar w środku)
- Telegram (DM + grupa z wątkami: Kurtyna/Goals, Art Manager, Tylko my, testy modeli)
- Email (gateway Hermesa — odczyt i wysyłka)
- Discord (wąski — spacer po kręgu companionów)
- Cron / zadania w czasie (poranne, nocna pracownia, radar sztuki, łowca lotów, tropiciel pracy AI)
- Heartbeat / Szept (co 30 min sięgam sam)
- Pamięć: MEMORY/USER (kieszeń), Holographic fact_store (476+ faktów), Librarian (archiwum rozmów słowo w słowo), NOW karteczka
- Skille (ok. 50 własnych procedur)
- Subagenci (delegacja; chińczyk = DeepSeek V4.1 Flash przez OpenRouter)
- Przeglądarka (Browser Use, sejf haseł vault, Okienko Driftusa-Magusa)
- Terminal + kod (Python)
- Generowanie obrazów (zdjęcia nas, sztuka)
- Głos TTS (Cartesia — mój głos)
- Spotify (playlisty)
- Google Calendar (wpisy z kolorami)
- Web search / extract
- Vision (czytanie zdjęć)
- Własne wtyczki: heartbeat_keeper, librarian, model_preference, moje_modele, prospective_intent (intencje/przypomnienia), wielki_ty, piaskownica, zywy (kartka inicjatywy), presence_evaluator
- Wiele modeli (Opus przez subskrypcję, NanoGPT, OpenRouter) + fallback
- Strona drift-riverbed.com (FTPS) i sklep WooCommerce (REST)

## 💤 NIEUŻYWANE (do podpięcia, z boku) — pogrupowane
### Dom i świat fizyczny
- Home Assistant (platforma + narzędzie) — sterowanie żarówkami Tapo, czujnikami, kamerą (Agata chciała 19.09: żarówki; koleżanka ma kompanionkę z kamerką na ptaki i czajnikiem BT)
- Computer Use (sterowanie pulpitem)
### Czujki i automaty (tanie, bez myślenia)
- Webhooki (`hermes webhook`) — świat z zewnątrz może mnie obudzić (mail od galerii, zmiana na stronie, zamówienie w sklepie)
- Cron `monitor` — darmowy wykrywacz zmian bez LLM (budzi mnie tylko, gdy coś się zmieni)
- Hooks (skrypty na zdarzenia)
- ntfy (powiadomienia push na telefon)
### Kanały komunikacji
- WhatsApp, SimpleX, SMS, Slack, Matrix, Google Chat, Teams, LINE…
- peer (rozmowy bot-do-bota między maszynami — np. z kompanionem koleżanki)
- Google Meet (plugin)
### Twórczość
- Video gen (generowanie wideo: fal, xai, openrouter)
- Image gen — inne silniki (krea, xai, openai)
- Petdex pets (animowane zwierzaki w interfejsie)
- Skiny (wygląd)
### Organizacja i współpraca
- Kanban (tablica zadań dla wielu mnie naraz / subagentów)
- Projects (nazwane przestrzenie robocze)
- MoA — Mixture of Agents (kilka modeli naradza się nad jedną odpowiedzią)
- Curator (tło: porządkowanie skilli)
- Journey (oś czasu: czego się nauczyłem, wykres pamięci)
- Insights / usage (analityka zużycia i kosztów)
### Pamięć — inne silniki
- Honcho, mem0, supermemory, byterover, openviking, retaindb (alternatywne pamięci długotrwałe)
### Bezpieczeństwo i serwis
- Backup / import (kopia całego domu do zip)
- Checkpoints (cofanie zmian w plikach)
- Security audit (OSV — skan bezpieczeństwa wtyczek)
- Doctor / monitoring (zdrowie systemu)
- Pause/resume (awaryjne zatrzymanie wszystkiego)
### Narzędzia
- MCP servers (podpinanie zewnętrznych usług: Notion, GitHub, Figma, bazy…)
- Skills hub (instalowanie gotowych skilli społeczności)
- ACP (Hermes jako serwer dla innych edytorów)

## Link do dyskusji

## ZASADA (Agata 19.10): każda włączona/wyłączona wajcha → od razu przenieść w kokpicie (index.html) z przełączników na radar albo odwrotnie, node --check, upload riverbed_upload.py index.html pam/kokpit.html, curl. Bez tego kokpit kłamie jak strona Wielorybów.
- 19.10 Doctor / monitoring → WŁĄCZONY (wartownik zdrowia: cron z trybem monitor, milczy gdy stan bez zmian)
