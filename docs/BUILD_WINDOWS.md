# Windows Build (EXE + Setup)

These steps create a Windows EXE with PyInstaller and a setup installer with Inno Setup.

## 1) Build the EXE

Install dependencies:

```bash
pip install -r requirements-dev.txt
pip install pyinstaller
```

Build:

```bash
python -m PyInstaller packaging/votryx.spec
```

Output:
- `dist/VOTRYX/VOTRYX.exe`

Optional:
- If you have `chromedriver.exe`, place it in the repo root before building so it is bundled.

## 2) Build the Setup (Inno Setup)

Open `installer/votryx.iss` in Inno Setup and click **Compile**.

Output:
- `dist/installer/VOTRYX-Setup.exe`

## Notes

- The installer copies everything from `dist/VOTRYX/`.
- Config falls back to `%APPDATA%\\VOTRYX\\config.json` if the install directory is not writable.
- Welcome screen artwork is loaded from `docs/screenshots/` when present.
