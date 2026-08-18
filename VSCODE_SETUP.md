# VS Code Setup

1. Extract the project.
2. Open the project folder in VS Code.
3. Install the Python extension.
4. Select the `.venv` interpreter.
5. Open Terminal.
6. Run:

```bash
python -m venv .venv
```

Activate it — Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Then, with the venv active:

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env: set a real JWT_SECRET at minimum
python scripts/seed.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. API docs are at `http://127.0.0.1:8000/docs`.

Development login: `admin` / `ChangeMe!12345`. Change this before treating
the system as anything other than local development — and note the app
will refuse to start at all with `APP_ENV` set to anything other than
`development` unless `JWT_SECRET` (and `BACKUP_KEY`, if backups are in
use) have been changed from their placeholder values.

## GitHub

```bash
git init -b main
git add .
git commit -m "Build offline pharmaceutical distribution system"
git remote add origin https://github.com/leviupendo/offline-pharma-distribution-system.git
git push -u origin main
```

Never commit `.env`, private keys, passwords, live databases or production backups.
