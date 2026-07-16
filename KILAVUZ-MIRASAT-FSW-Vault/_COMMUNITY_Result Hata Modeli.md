---
type: community
members: 18
---

# Result Hata Modeli

**Members:** 18 nodes

## Members
- [[.ok()]] - code - src/common/result.py
- [[.unwrap()]] - code - src/common/result.py
- [[.unwrap_or()]] - code - src/common/result.py
- [[Bir hata sonucu unwrap edilmeye çalışıldığında yükseltilir.]] - rationale - src/common/result.py
- [[Değeri döndürür; hata ise ResultError yükseltir (sessiz geçiş yok).]] - rationale - src/common/result.py
- [[Exception]] - code
- [[Görevi         Açık hatasonuç modeli (ResultT + ErrorCode). Sessizce başarıs]] - rationale - src/common/result.py
- [[ResultErrorCode birim testleri (REQ-SW-005).]] - rationale - tests/test_result.py
- [[ResultError]] - code - src/common/result.py
- [[T]] - code - src/common/result.py
- [[result.py]] - code - src/common/result.py
- [[test_err_cannot_be_ok_code()]] - code - tests/test_result.py
- [[test_err_carries_code_and_message()]] - code - tests/test_result.py
- [[test_ok_allows_none_value()]] - code - tests/test_result.py
- [[test_ok_carries_value()]] - code - tests/test_result.py
- [[test_result.py]] - code - tests/test_result.py
- [[test_unwrap_on_error_raises()]] - code - tests/test_result.py
- [[test_unwrap_or_default()]] - code - tests/test_result.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Result_Hata_Modeli
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_Mock Suruculer & Cekirdek]]
- 1 edge to [[_COMMUNITY_Ana Uygulama Dongusu]]

## Top bridge nodes
- [[result.py]] - degree 5, connects to 2 communities
- [[test_result.py]] - degree 10, connects to 1 community
- [[ResultError]] - degree 6, connects to 1 community
- [[.unwrap()]] - degree 4, connects to 1 community
- [[.ok()]] - degree 2, connects to 1 community