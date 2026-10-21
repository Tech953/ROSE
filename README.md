# Rose

Complete saved **Rose 0.19.0** game project, including all source files, bundled assets, rules, tests, launchers and documentation.

## Play locally

Install Python 3.10 or newer. On Windows, open `rose` and double-click `Start-Windows.bat`. On Linux or macOS:

```sh
cd rose
python3 server.py
```

Open `http://localhost:8778` and keep the server running. See the [original project instructions](rose/README.md) for platform and multiplayer details.

## Included files

- [rose/](rose/): every file from `Rose-Engine.zip`, preserved byte for byte.
- [docs/README.md](docs/README.md): indexed guides, audits and retained validation records.
- [docs/shared/](docs/shared/): printable character sheet, creature/stat guide and encounter toolkit.
- [upload-manifest.json](upload-manifest.json): source versions, coverage and file checksums.

Historical audits retain their original dates and verification limits. This upload preserves the saved implementation.

Series: [Thorns](https://github.com/Tech953/Thorns) → [Stem](https://github.com/Tech953/STEM) → [Rose](https://github.com/Tech953/ROSE).

## Rose.ENGINE physics lab

The [physics-lab/](physics-lab/) folder also includes the complete tracked source of the separately developed browser physics lab, including its tests and original hosting manifest. Run the canonical workbench with:

```sh
cd physics-lab/dist
python3 -m http.server 8780
```

Open `http://localhost:8780`. Run its validation with `node tests/validate.mjs` from `physics-lab/` using the Canvas dependency described in its README. The previously uploaded flat browser files are retained for compatibility.

The main game and browser lab are separate saved implementations; inclusion does not claim completed Rose 0.20 integration. The hosted lab retains its existing private access settings.

The earlier Rose 0.18 import record is retained in [docs/provenance/](docs/provenance/); the current root manifest describes the complete 0.19 package. Existing standalone references and the physics reference pointer remain available.
