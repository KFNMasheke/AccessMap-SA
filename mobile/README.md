# AccessMap SA mobile concept

One React Native / Expo codebase targeting iOS, Android and web. This is a local concept, not a published native app. All facilities are fictional.

## Included

- Search and filter clinics/libraries.
- Sort by straight-line distance from a labelled fixed demo point.
- Open facility details with explicit unverified-hours status.
- Save facility IDs on the device and remove them later.
- Share clearly labelled demo details using the platform share sheet.
- Explore, Saved and About views, empty states and storage errors.

No GPS permission, account, map SDK, network data fetch, backend or analytics. A map is intentionally deferred until licensed, verified local context is available. The QGIS project remains the analysis/map-authoring tool.

## Run

Node 22.13+ and a compatible Expo environment are required. SDK 57 / React Native 0.86 / React 19.2.3 are declared; confirm the current compatible patch set with Expo's installer before a native build.

```sh
cd mobile
npm ci
npx expo install --check
npm start
```

Open the project with a compatible Expo Go or development build. iOS simulator builds require macOS/Xcode; Android emulators require the Android SDK. To run the browser target use `npm run web`. A standalone browser concept preview is included as `preview.html`; it needs no installation and mirrors the concept, but does not replace native verification.

```sh
npm test
npx expo export --platform web
```

The shared fictional data pack is `../data/mobile-pack.json`. Keep this relative path when extracting the repository. Bookmarks use AsyncStorage, which is unencrypted; only public demo facility IDs are stored. App IDs in `app.json` are placeholders to replace before publication.

## Readiness limits

Native signing, App Store/Play Store submission, on-device performance, screen-reader testing and offline cold starts have not been certified. SDK installation or browser checks do not prove native runtime behavior. No APK or IPA is included.

Before a real pilot: verify service records and rights, add correction governance, user-test language/accessibility, choose a maintained SDK patch set, run dependency review and measure actual bundle/device performance. No government functionality is implemented.
