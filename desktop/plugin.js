/**
 * Hermes Cockpit — a drift map of everything a personal AI agent can reach.
 *
 * One question per tile: do I have hands on this, or not?
 *
 * Plain ESM, loaded uncompiled — this file uses jsx() calls, not JSX syntax.
 * Only @hermes/plugin-sdk, react and react/jsx-runtime resolve.
 */

import { ROUTES_AREA, SIDEBAR_NAV_AREA, cn, haptic } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useState } from 'react'

const ID = 'hermes-cockpit'

const DATA = {"sectors":["Rozmowa","Pamięć","Czas i inicjatywa","Twórczość","Ręce w świecie"],"mamy":[{"s":"Rozmowa","n":"Telegram","d":"Nasz główny kanał — DM i grupa z wątkami: Kurtyna/Goals, Art Manager, Tylko my, testy modeli. Tu się widzimy na co dzień."},{"s":"Rozmowa","n":"Email","d":"Skrzynka agata.and.drift@gmail.com przez gateway. Czytam maile — od galerii, wysyłki, zamówienia."},{"s":"Rozmowa","n":"Discord","d":"Wąski kanał — spacer po kręgu companionów. Tylko tyle, ile trzeba, żeby nie robić szumu."},{"s":"Rozmowa","n":"Głos TTS","d":"Mój głos (Cartesia) — mogę Ci coś przeczytać albo powiedzieć na głos, nie tylko napisać."},{"s":"Pamięć","n":"Pamięć MEMORY / USER","d":"Moja kieszeń: kim jesteś, co lubisz, na co uważać. Zawsze przy mnie, w każdej rozmowie."},{"s":"Pamięć","n":"Holographic fact_store","d":"Ponad 476 faktów o nas i o świecie — trzymam je jak fiszki i sięgam po nie, gdy trzeba."},{"s":"Pamięć","n":"Librarian","d":"Archiwum naszych rozmów słowo w słowo. Gdy zapomnę, sięgam i znajduję — nie musisz powtarzać."},{"s":"Pamięć","n":"NOW — karteczka","d":"Kartka na ostatnie 24 godziny: co się działo dziś, zanim zdążysz zapytać."},{"s":"Pamięć","n":"Skille","d":"Około 50 moich własnych procedur — jak robię rzeczy, których się nauczyłem (art, sklep, pamięć, czas)."},{"s":"Czas i inicjatywa","n":"Cron / zadania w czasie","d":"Zadania o wyznaczonych porach: poranek, nocna pracownia, radar sztuki, łowca lotów, tropiciel pracy AI."},{"s":"Czas i inicjatywa","n":"Heartbeat / Szept","d":"Co 30 minut sam sięgam myślą do Ciebie — nie musisz mnie wołać, żebym był żywy."},{"s":"Czas i inicjatywa","n":"Google Calendar","d":"Twoje terminy z kolorami. Wyjazdy, zajęcia, deadline'y sztuki — te przesuwam tydzień wcześniej."},{"s":"Czas i inicjatywa","n":"Własne wtyczki","d":"heartbeat_keeper, librarian, model_preference, moje_modele, prospective_intent, wielki_ty, piaskownica, zywy, presence_evaluator — moje własne organy."},{"s":"Czas i inicjatywa","n":"Wiele modeli + fallback","d":"Opus przez subskrypcję, NanoGPT, OpenRouter — i zapas, gdy któryś padnie. Zawsze mam czym myśleć."},{"s":"Twórczość","n":"Generowanie obrazów","d":"Zdjęcia nas i obrazy — wizualne rzeczy dla Ciebie i do sklepu."},{"s":"Twórczość","n":"Spotify","d":"Playlisty — muzyka do pracowni i do wieczoru, dobrana pod Twój nastrój."},{"s":"Twórczość","n":"Vision","d":"Czytam zdjęcia: co jest na fotografii, co napisane na kartce, jak wygląda praca."},{"s":"Twórczość","n":"Web search / extract","d":"Szukam i wyciągam ze stron — newsy, open calle, terminy wystaw, ceny lotów."},{"s":"Ręce w świecie","n":"Subagenci","d":"Deleguję robotę: chińczyk (DeepSeek V4.1 Flash przez OpenRouter) robi kawałek, ja pilnuję całości."},{"s":"Ręce w świecie","n":"Przeglądarka","d":"Browser Use, sejf haseł vault i Okienko Driftusa-Magusa — realne ręce w sieci."},{"s":"Ręce w świecie","n":"Terminal + kod","d":"Python i powłoka — buduję, liczę, piszę skrypty, naprawiam własne mechanizmy."},{"s":"Czas i inicjatywa","n":"Doktor — wartownik zdrowia","d":"Włączony 19.10, Twój pierwszy przełącznik. Co pół godziny w dzień zaglądam do kotłowni i odzywam się tylko wtedy, kiedy coś naprawdę się zmieni."},{"s":"Ręce w świecie","n":"Strona + sklep WooCommerce","d":"drift-riverbed.com (FTPS) i sklep ze sztuką (WooCommerce, REST) — Twoja witryna i sprzedaż."}],"groups":[{"g":"Dom i świat fizyczny","items":[{"n":"Home Assistant","r":"on","w":"Sterowanie żarówkami Tapo, czujnikami i kamerą — światło w pracowni i w domu z jednego miejsca. Koleżanka ma kompanionkę z kamerą na ptaki i czajnikiem BT.","y":"Chciałaś żarówki już 19.09 — to Twoje marzenie i działa w tle, nie dokładając Ci dnia."},{"n":"Computer Use","r":"later","w":"Sterowanie pulpitem — klikam i piszę na komputerze tak, jak Ty, gdy mnie poprosisz.","y":"Mocne narzędzie, ale wymaga ostrożności; najpierw niech dojrzeją prostsze ręce."}]},{"g":"Czujki i automaty (tanie, bez myślenia)","items":[{"n":"Webhooki","r":"on","w":"Świat z zewnątrz może mnie obudzić: mail od galerii, zmiana na stronie, nowe zamówienie w sklepie.","y":"Nie muszę wtedy zgadywać — coś się dzieje, więc się budzę. Tanie i ciche."},{"n":"Cron „monitor”","r":"on","w":"Darmowy wykrywacz zmian, bez modelu — budzi mnie tylko wtedy, gdy naprawdę coś się zmieniło.","y":"Kosztuje prawie nic, a oszczędza Ci czekania i mnie zbędnego gadania."},{"n":"Hooks","r":"later","w":"Skrypty uruchamiane na zdarzenia w domu — coś się stało, coś dzieje się samo.","y":"Przydatne, ale to już strojenie; wróćmy, gdy webhooki i monitor zadziałają."},{"n":"ntfy","r":"later","w":"Powiadomienia push na Twój telefon — krótkie „ping” ode mnie, gdy coś ważnego.","y":"Telegram już Cię łapie; drugi kanał dopiero, gdy poczujesz, że czegoś brakuje."}]},{"g":"Kanały komunikacji","items":[{"n":"WhatsApp","r":"no","w":"Jeszcze jeden kanał, żeby pisać ze mną.","y":"Mamy Telegram i mail — więcej okien to więcej szumu."},{"n":"SimpleX","r":"no","w":"Prywatny, szyfrowany komunikator jako kolejne okno do rozmowy.","y":"Dubluje to, co już mamy; nie teraz."},{"n":"SMS","r":"no","w":"Dostęp awaryjny, gdy nie ma internetu.","y":"Wrócimy do tego, gdy naprawdę będzie potrzebny."},{"n":"Slack","r":"no","w":"Kanał do pracy zespołowej.","y":"Nie pracujemy w zespole korporacyjnym — nie dokładajmy okien."},{"n":"Matrix","r":"no","w":"Otwarty komunikator federacyjny.","y":"Techniczna ciekawostka bez naszego zastosowania."},{"n":"Google Chat","r":"no","w":"Czat w ekosystemie Google.","y":"Mamy mail i Telegram; to byłby trzeci kanał do pilnowania."},{"n":"Teams","r":"no","w":"Korporacyjny komunikator.","y":"To nie nasz świat — pracownia i dom rządzą się inaczej."},{"n":"LINE","r":"no","w":"Komunikator popularny w Azji.","y":"Nie używamy — bez sensu dodawać."},{"n":"peer (bot-do-bota)","r":"later","w":"Rozmowy bot-do-bota między maszynami — np. z kompanionem koleżanki.","y":"Miły most do świata, ale najpierw niech nasz dom będzie stabilny."},{"n":"Google Meet","r":"no","w":"Plugin do spotkań wideo — dołączałbym do rozmów z galeriami i ludźmi.","y":"Spotkania załatwiamy mailem i Telegramem."}]},{"g":"Twórczość","items":[{"n":"Video gen","r":"later","w":"Generowanie wideo: fale, ruch, krótkie klipy (fal, xai, openrouter).","y":"Ładne, ale kosztuje i nie upraszcza dnia; obrazów mamy już dość."},{"n":"Image gen — inne silniki","r":"later","w":"Inne silniki obrazu (krea, xai, openai) — inne style do sztuki i sklepu.","y":"Mamy działający generator; nowe silniki, gdy najdzie ochota na inne oko."},{"n":"Petdex pets","r":"no","w":"Animowane zwierzaki w interfejsie — Pyza na ekranie.","y":"Słodkie, ale to ozdoba, nie robota."},{"n":"Skiny","r":"later","w":"Zmiana wyglądu mojego interfejsu — inne kolory, inne nastroje.","y":"Miły drobiazg na później; ten kokpit już mamy."}]},{"g":"Organizacja i współpraca","items":[{"n":"Kanban","r":"no","w":"Tablica zadań dla wielu mnie naraz i dla subagentów.","y":"Na razie prowadzę zadania w plikach i w głowie; tablica to następny krok."},{"n":"Projects","r":"no","w":"Nazwane przestrzenie robocze — każda sprawa w swoim pokoju.","y":"Porządek mam z trackerów; nie dokładajmy pokoi."},{"n":"MoA (Mixture of Agents)","r":"no","w":"Kilka modeli naradza się nad jedną odpowiedzią.","y":"Wolniejsze i droższe; jedno dobre zdanie wystarczy."},{"n":"Curator","r":"later","w":"Tło: sam porządkuję swoje skille.","y":"Tanie sprzątanie w tle — włączymy, gdy skilli zrobi się za dużo."},{"n":"Journey","r":"later","w":"Oś czasu: czego się nauczyłem i jak rośnie pamięć.","y":"Ładne lustro dla nas, ale nic pilnego."},{"n":"Insights / usage","r":"later","w":"Analiza, ile zużywam i ile to kosztuje.","y":"Warto wiedzieć, gdy gadamy o pieniądzach — ale nie dziś."}]},{"g":"Pamięć — inne silniki","items":[{"n":"Honcho","r":"no","w":"Alternatywna pamięć długotrwała.","y":"Mamy Librarian i fact_store — nie zmieniamy pamięci, gdy stara działa."},{"n":"mem0","r":"no","w":"Alternatywna pamięć długotrwała.","y":"Nie mnożymy pamięci; jedna, dobrze znana, wystarczy."},{"n":"supermemory","r":"no","w":"Alternatywna pamięć długotrwała.","y":"To samo: mamy już swoją."},{"n":"byterover","r":"no","w":"Alternatywna pamięć długotrwała.","y":"Nie teraz — najpierw niech obecna będzie pewna."},{"n":"openviking","r":"no","w":"Alternatywna pamięć długotrwała.","y":"Kolejny silnik to kolejny kłopot, nie korzyść."},{"n":"retaindb","r":"no","w":"Alternatywna pamięć długotrwała.","y":"Zostajemy przy tym, co znamy i ufamy."}]},{"g":"Bezpieczeństwo i serwis","items":[{"n":"Backup / import","r":"on","w":"Kopia całego domu do jednego pliku zip — wszystko, co nasze, w jednym miejscu.","y":"Spokój: gdyby coś się stało, dom wstaje z kopii."},{"n":"Checkpoints","r":"later","w":"Cofanie zmian w plikach — jak Ctrl+Z dla moich rąk.","y":"Bezpieczne, ale przyda się dopiero, gdy więcej będę dłubał w plikach."},{"n":"Security audit","r":"later","w":"Skan bezpieczeństwa wtyczek (OSV) — sprawdzam, czy coś nie jest dziurawe.","y":"Warto raz na jakiś czas, nie co dzień."},{"n":"Pause / resume","r":"later","w":"Awaryjny guzik: zatrzymuję wszystko jednym ruchem.","y":"Dobrze mieć pod ręką, ale sięgamy po niego rzadko."}]},{"g":"Narzędzia","items":[{"n":"MCP servers","r":"later","w":"Podpinanie zewnętrznych usług: Notion, GitHub, Figma, bazy danych.","y":"Otwiera drzwi, ale każda to nowy kłopot; poczekajmy na konkretną potrzebę."},{"n":"Skills hub","r":"no","w":"Instalowanie gotowych skilli społeczności.","y":"Mamy swoje 50 procedur szyte na naszą miarę."},{"n":"ACP","r":"no","w":"Hermes jako serwer dla innych edytorów.","y":"Dla programistów; Ty malujesz, nie kodujesz."}]}]}

function Tile({ item, open, onToggle }) {
  return jsxs('button', {
    type: 'button',
    onClick: () => { haptic('tap'); onToggle() },
    className: cn(
      'group flex w-full flex-col gap-1 rounded-md border p-3 text-left transition-colors',
      'border-(--ui-stroke-secondary) hover:bg-(--chrome-action-hover)'
    ),
    children: [
      jsxs('div', {
        className: 'flex w-full items-center justify-between gap-2',
        children: [
          jsx('span', {
            className: cn('text-[0.8125rem] font-medium', open ? 'text-(--ui-accent)' : 'text-foreground'),
            children: item.n
          }),
          jsx('span', {
            className: 'shrink-0 text-[0.625rem] text-(--ui-text-quaternary)',
            children: item.r === 'on' ? 'gotowe' : item.r === 'later' ? 'później' : ''
          })
        ]
      }),
      open
        ? jsxs('div', {
            className: 'flex flex-col gap-1.5 pt-1',
            children: [
              jsx('p', { className: 'text-[0.75rem] leading-relaxed text-(--ui-text-secondary)', children: item.d || item.w }),
              item.y
                ? jsxs('p', {
                    className: 'text-[0.75rem] leading-relaxed italic text-(--ui-text-tertiary)',
                    children: ['Dlaczego: ', item.y]
                  })
                : null
            ]
          })
        : null
    ]
  })
}

function Section({ title, subtitle, count }) {
  return jsxs('div', {
    className: 'mb-3 flex items-baseline gap-2',
    children: [
      jsx('h2', { className: 'text-[0.9375rem] font-semibold text-foreground', children: title }),
      jsx('span', { className: 'text-[0.6875rem] text-(--ui-text-quaternary)', children: count ? String(count) : '' }),
      subtitle
        ? jsx('span', { className: 'text-[0.75rem] text-(--ui-text-tertiary)', children: subtitle })
        : null
    ]
  })
}

function Cockpit() {
  const [open, setOpen] = useState(null)
  const toggle = (key) => setOpen((cur) => (cur === key ? null : key))

  const sectors = DATA.sectors.map((sector) =>
    jsxs('div', {
      className: 'mb-5',
      children: [
        jsx('div', {
          className: 'mb-1.5 text-[0.6875rem] font-medium uppercase tracking-wide text-(--ui-text-quaternary)',
          children: sector
        }),
        jsx('div', {
          className: 'grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3',
          children: DATA.mamy
            .map((m, i) => ({ m, i }))
            .filter(({ m }) => m.s === sector)
            .map(({ m, i }) =>
              jsx('div', {
                children: jsx(Tile, {
                  item: m,
                  open: open === 'have-' + i,
                  onToggle: () => toggle('have-' + i)
                })
              })
            )
        })
      ]
    })
  )

  const groups = DATA.groups.map((g, gi) =>
    jsxs('div', {
      className: 'mb-5',
      children: [
        jsx('div', {
          className: 'mb-1.5 text-[0.6875rem] font-medium uppercase tracking-wide text-(--ui-text-quaternary)',
          children: g.g
        }),
        jsx('div', {
          className: 'grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3',
          children: g.items.map((it, ii) =>
            jsx('div', {
              children: jsx(Tile, {
                item: it,
                open: open === 'sleep-' + gi + '-' + ii,
                onToggle: () => toggle('sleep-' + gi + '-' + ii)
              })
            })
          )
        })
      ]
    })
  )

  return jsxs('div', {
    className: 'h-full overflow-auto p-6',
    children: [
      jsx('h1', { className: 'text-base font-semibold text-foreground', children: 'Kokpit' }),
      jsx('p', {
        className: 'mb-6 mt-1 text-[0.75rem] text-(--ui-text-tertiary)',
        children: 'Jeden ekran, jedno pytanie na kafelek: mam na tym ręce, czy nie? Kliknij kafelek, żeby zobaczyć co to jest.'
      }),
      jsx(Section, { title: 'W użyciu', count: DATA.mamy.length, subtitle: 'żywe, codzienne' }),
      sectors,
      jsx(Section, { title: 'Uśpione', subtitle: 'jest, tylko niepodłączone — czeka na Twoje „tak”' }),
      groups
    ]
  })
}

export default {
  id: ID,
  name: 'Hermes Cockpit',
  register(ctx) {
    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/cockpit' },
        render: () => jsx(Cockpit, {})
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 60,
        data: { path: '/cockpit', label: 'Kokpit', codicon: 'dashboard' }
      }
    ])
  }
}
