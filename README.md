# ZIT-ONLINE SYSTEM

Simple Flask-based online course system.

## Quickstart

1. Create and activate a virtual environment:

```powershell
python -m venv venv
& "venv/Scripts/Activate.ps1"
```

2. Install requirements:

```powershell
pip install -r requirements.txt
```

3. Run the app (from the project folder):

```powershell
cd "ZIT-ONLINE SYSTEM"
python app.py
```

4. Create a GitHub repository and push (see project README section below for details).

## Notes

- Application entry point: `app.py` (inside the `ZIT-ONLINE SYSTEM` folder).
- Static files and templates are under `templates/` and `static/` respectively.

## Adding to GitHub

To create a remote repository and push the local repo:

1. Create a repo on GitHub (via web UI) named `ZIT-ONLINE SYSTEM`.
2. In your project folder run:

```powershell
git remote add origin https://github.com/USER/REPO.git
git push -u origin main
```

Or, if you have the GitHub CLI (`gh`) authenticated:

```powershell
cd "ZIT-ONLINE SYSTEM"
gh repo create USER/REPO --public --source=. --remote=origin --push
```
