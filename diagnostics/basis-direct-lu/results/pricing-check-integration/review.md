# Review přímé integrace

Read-only reviewer /root/review_pricing_integration: 0 Critical,0 Important,0 Minor. Společný gate je identický s ověřeným masterem3dc0bcda a automaticky se používá přes existující direct-factor hook pro přímé i normalizované FT/SS/BG. Implementace nepřidává práci do faktorizačních kernelů ani per-factor stav.

Regrese check-reuse.jl nyní pokrývá všechny tři pevné pricingy a obě reprezentace. Zachovává test skutečného backendu, publikované normalizace, fallbacku, nepovedené refaktorizace a opětovné způsobilosti. Dantzig ignoruje váhy, proto jeho observer po pivotu poškozuje costs; vážené pricingy nadále testují nulovou váhu. Společný regresní modul skutečně používá instalovaný direct factory pro FT/SS/BG, HH/PFI jsou další produkční kontroly.

Nová změna v této větvi je testovací; nepřidává zbytečné produkční skeny, alokace nebo retained memory. Testy jsou řízeny pod všemi zámky: root run-locked.py předává FD python launcheru a ten je prostřednictvím close_fds=False zachovává pro Julia potomky. Žádný nový plný runtime/mod011 solve.
