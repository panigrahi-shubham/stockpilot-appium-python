# StockPilot Appium Python

Android UI test automation for [StockPilot](https://github.com/panigrahi-shubham/stockpilot-android) using Appium, UiAutomator2, Python, and pytest. The suite runs against an existing APK.

## Run the tests

Use Python 3.14, Node.js 24, Java, Android SDK and ADB. Start an Android API 35 test emulator. Each scenario clears StockPilot app data on the selected device.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install --global appium@3.9.0
appium driver install uiautomator2@7.6.2
appium --address 127.0.0.1 --port 4723
```

In a second terminal, download the [StockPilot 2.5.0 QA APK](https://github.com/panigrahi-shubham/stockpilot-android/releases/tag/stockpilot-v2.5.0-vortex) into this folder. Replace the serial placeholder with the Android emulator shown by ADB.

```powershell
adb devices -l
$serial = 'YOUR_ADB_SERIAL'
.\.venv\Scripts\python.exe -m pytest --device $serial --apk ./StockPilot-2.5.0-Vortex-QA.apk -m smoke -v --junitxml=artifacts/smoke.xml
```

Omit `--apk` if StockPilot is installed. Remove `-m smoke` to run all 36 scenarios. Use `-m "not live"` to omit the two external-service cases. Demo sign-in requires an internet-validated emulator network.

## Structure and design decisions

- `tests/` contains 36 scenarios across login, catalog, cart and checkout, gestures, Android system features, WebViews and marketplace flows.
- `stockpilot/` contains page objects and shared Android commands. Tests keep their assertions close to the scenario. Explicit waits follow app state and React Native test IDs.
- `conftest.py` starts one Appium session and resets the app between tests. The suite uses the APK's seeded demo accounts and reads the generated OTP from the in-app SMS preview.
- The WebView tests interact with Android accessibility nodes and use touch scrolling. The failure hook captures screenshots and UI hierarchies under `artifacts/`.

## CI and results

The GitHub Actions workflow verifies the published APK's SHA-256, starts an Android API 35 emulator and runs four smoke tests on pull requests and pushes to main. A manual run can select regression. CI uploads JUnit XML and diagnostics. The runner passed all four smoke tests locally with the published APK. [Sample HTML report](docs/sample-smoke-report.html)

The suite targets Android. In a prior StockPilot 2.5.0 run, saving a seller draft opened a discard confirmation. The regression test reports that behavior as a failure if it recurs. The live market rate and practice portal cases depend on external services.
