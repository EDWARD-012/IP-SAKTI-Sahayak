# Locale catalogs

- `hi/LC_MESSAGES/django.po` — Hindi strings for critical chrome (nav + Ask).
- `hi/LC_MESSAGES/django.mo` — compiled binary (shipped).

## Compile notes (Windows)

System `msgfmt` / GNU gettext is often missing on Windows PATH.
This repo compiled `.mo` with:

```powershell
.\.venv\Scripts\pip.exe install polib
.\.venv\Scripts\python.exe -c "import polib; po=polib.pofile('locale/hi/LC_MESSAGES/django.po'); po.save_as_mofile('locale/hi/LC_MESSAGES/django.mo')"
```

If gettext is installed:

```powershell
.\.venv\Scripts\python.exe manage.py compilemessages -l hi
```
