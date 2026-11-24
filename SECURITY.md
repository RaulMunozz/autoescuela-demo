# Security Policy

**Last reviewed:** 2026-11-24  
**Scope:** `RaulMunozz/autoescuela-demo` — Flask availability form with an admin view.

## Architecture

- Python 3.12, Flask 3.1.1, Flask-SQLAlchemy 3.1.1, SQLite, gunicorn.
- Routes: `/` (form), `/gracias`, `/login`, `/logout`, `/autoescuela`.
- Data: `Disponibilidad(id, nombre, telefono, disponibilidad_json)` in `instance/postbasey.db`.
- Session-based flag `logueado` for the admin view.
- Originally no external configuration, no CSRF protection, no password hashing and no security headers.

## Findings fixed in this revision

| Severity | Finding | Fix |
|---|---|---|
| Critical | Session signing key hardcoded in the public repository | `app.secret_key` now comes from `SECRET_KEY`. A random per-process fallback is used only for local development; production must set the variable. |
| Critical | Hardcoded plain-text admin credentials in source | Credentials removed from code. Login now requires `ADMIN_USER` and an `ADMIN_PASSWORD_HASH` generated with Werkzeug. Password comparison uses `check_password_hash`. |
| High | CSRF on all POST routes and state-changing logout via GET | CSRF token in every form, validated with `secrets.compare_digest` in `before_request`. `/logout` is POST-only. Session is cleared and rotated on login. |
| High | Cookies and browser protections not configured | `HttpOnly`, `SameSite=Lax`, optional `Secure` with `__Host-` prefix, plus `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, CSP and optional HSTS. |
| Medium | SQLite database files committed to the repository | Versioned `.db` files removed from the current tree and ignored. The app recreates the schema with `db.create_all()`. |
| Medium | Weak input validation and malformed JSON causing 500 errors | Length limits, allowlist of days/hours, and defensive JSON parsing with type checks. |
| Medium | No brute-force protection or login logging | In-memory per-IP rate limit (5 attempts / 5 minutes) and failed-login logging. |
| Low | Missing repository hygiene | Added `.gitignore` for databases, bytecode, IDE files and `.env`. |

## External configuration required for production

Set these in the hosting provider (Render or equivalent). Do **not** commit their values:

```text
SECRET_KEY=<random 32+ byte value>
ADMIN_USER=<admin username>
ADMIN_PASSWORD_HASH=<Werkzeug password hash>
COOKIE_SECURE=1
HSTS=1
DATABASE_URI=<persistent database URI>
```

Generate the password hash without placing the plaintext in shell history:

```powershell
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass()))"
```

`COOKIE_SECURE=1` enables `Secure` cookies and the `__Host-session` name; it requires HTTPS end-to-end. `HSTS=1` adds a one-year HSTS header.

## Known limitations / pending external work

- **High — history:** removing the database files from the current tree does not purge earlier commits. If any real personal data was ever committed, rotate/remove it and rewrite history in a coordinated maintenance window.
- **Medium — ephemeral storage:** with SQLite on a free ephemeral filesystem, data can be lost between deploys and multiple gunicorn workers may lock the file. Use a persistent disk or managed database via `DATABASE_URI`.
- **Medium — rate limit:** the in-memory limiter is per process and resets on restart. Use a provider-level WAF/rate limit for reliable protection.
- **Low — CSP:** the admin view contains an inline `<style>` block, so the CSP keeps `style-src 'unsafe-inline'`. Moving it to a static file would allow tightening this.
- **Low — dependencies:** versions are pinned but not hashed; no SBOM or automated dependency scanning is configured.

## Verification performed

- Syntax check of `app.py` and the three templates.
- Flask test client: unauthenticated `/autoescuela` redirects; POST without CSRF token returns 400; wrong credentials return 401; valid credentials require an externally supplied hash.
- Security headers present on responses.
- No secret values remain in the current source tree.

## Maintenance

- Rotate `SECRET_KEY` and the admin password if they were ever exposed.
- Re-run the checks after changing routes, templates or dependencies.
- If file uploads, JSON APIs or additional roles are added, perform a new audit.
