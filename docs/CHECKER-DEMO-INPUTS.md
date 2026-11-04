# Coverage checker demo inputs (live site)

Use https://divine16.github.io/sanctions-territory-reference/ after `make build` is deployed.

| Demo | Paste | Expected |
|------|-------|----------|
| Under-blocking | `CU, IR, UA-43, UA-14, UA-09` | **KP** missing |
| Over-blocking | `CU, IR, KP, UA-43, UA-14, UA-09, SY, SD` | **SY** and **SD** flagged (terminated) |
| Partial coverage | `CU, IR, KP, UA-43, UA-14` | **UA-09** missing |

Privacy: DevTools → Network → reload → run checker → no fetch/XHR beyond the page document.
