# v0.1 validation

Validated 2026-10-19. This describes the local release checks; it is not a claim that native apps or real community data are production-ready.

| Check | Result |
|---|---|
| Python engine + CLI suite | 9 tests passed |
| Mobile model suite | 2 tests passed |
| QGIS 3.34.4 integration | Portable project reopened after relocation; six valid layers and two layouts |
| QGIS calculations | All 320 demo points matched the reference engine |
| QGIS edge cases | Missing category produces unknown; geographic calculation CRS and reversed thresholds rejected; lon/lat input reprojection exercised |
| Map exports | Clinic and library layouts rendered and visually checked |
| Expo SDK dependency check | Declared versions matched installed SDK recommendations using its offline metadata |
| React Native web export | Export completed; generated JS bundle approximately 391 KB before compression |
| Browser concept | Search, categories, detail sheet, bookmark persistence, empty states, tabs and platform appearance checked |
| Browser responsive layout | No document overflow at 320, 390, 768 and 1280 px |
| React Native web runtime | Search, categories, details, bookmarks across reload and About view checked; no JavaScript runtime errors |

## Still to verify

- Physical iOS and Android behavior, native builds, signing, screen readers, startup time, battery and binary size.
- A currently supported QGIS LTR and QGIS 4 compatibility before a real deployment.
- Real service data, licences, community usefulness, facility capacity and practical accessibility.
- Hosted features and government workflows: neither exists in this release.

GitHub Actions configuration is included for repeatable engine, QGIS and mobile build checks. Remote workflow status must be checked independently after publication.
