# Integrace ověřeného přebírání kontrol

Uživatel 9.11.2026 schválil integraci pevných Devex/Dantzig/DSE pro všech pět produkčních správců do mastera a push včetně již commitnuté opravy mod011. Přímé/normalizované FT/SS/BG a výsledky Devex obnovy patří na perf/basis-direct-lu. Auto pricing a ostatní neověřené podmínky zachovají původní plné kontroly. Samotná obnova Devex vah se neintegruje.

1. Cílený test nově povolených pricingů na starém gate (RED), poté minimální rozšíření odpovídající změřenému kandidátu.
2. Cílené regrese kontrol, DSE fallback, mod011 a malé celé LP; všechny numerické procesy pod společnými zámky. Celou tříhodinovou sadu neopakujeme v souladu s dřívějším uživatelským požadavkem na cílenou integraci.
3. Nezávislé review včetně práce/paměti, commit jen produkční změny/testů a jejich evidence, push master bez přepisování historie.
4. Fast-forward existující izolované větve perf/basis-direct-lu, rozšířit její přímé testy na všechny tři pricingy a ověřit šest skutečných režimů. Commit přímé validace a odděleně experimentu Devex s raw výsledky, piny a shrnutím. Push jen tuto větev.
5. Ověřit vzdálené HEAD, zahrnutí mod011, stav mastera i zachování původních rozpracovaných souborů. Žádné nové plné runtime/mod011 solve.
