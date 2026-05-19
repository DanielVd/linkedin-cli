#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import os
import secrets
import shutil
import sys
import threading
import time
import datetime
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".config" / "linkedin-cli" / "config.json"
QUEUE_PATH = Path.home() / ".config" / "linkedin-cli" / "queue.json"
LOG_PATH = Path.home() / ".config" / "linkedin-cli" / "linkedin-cli.log"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
REST_IMAGES_INIT_URL = "https://api.linkedin.com/rest/images?action=initializeUpload"
REST_POSTS_URL = "https://api.linkedin.com/rest/posts"
DEFAULT_SCOPES = ["openid", "profile", "email", "w_member_social"]


class CliError(RuntimeError):
    pass


def step_start(msg: str) -> None:
    print(f"[step] {msg}...")


def step_done(msg: str) -> None:
    print(f"[done] {msg}")
    log_line(f"DONE {msg}")


def ensure_config_dir() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_line(msg: str) -> None:
    ensure_config_dir()
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{ts} {msg}\\n")


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise CliError("Config non trovato. Esegui: linkedin-cli init-config")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(data: dict[str, Any]) -> None:
    ensure_config_dir()
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def b64url_sha256(value: str) -> str:
    dig = hashlib.sha256(value.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(dig).decode("utf-8").rstrip("=")


def http_post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_form_basic_auth(url: str, client_id: str, client_secret: str, data: dict[str, str]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Authorization", f"Basic {creds}")
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_json(url: str, token: str) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def http_post_json_with_headers(url: str, token: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    hdrs.update(headers)
    req = urllib.request.Request(url, method="POST", data=json.dumps(payload).encode("utf-8"), headers=hdrs)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def http_put_binary(url: str, data: bytes, content_type: str) -> None:
    req = urllib.request.Request(url, method="PUT", data=data, headers={"Content-Type": content_type})
    with urllib.request.urlopen(req, timeout=120):
        return


def ensure_token(cfg: dict[str, Any]) -> str:
    token_data = cfg.get("token", {})
    access_token = token_data.get("access_token")
    if not access_token:
        raise CliError("Token mancante. Esegui: linkedin-cli login")
    return access_token


def cmd_init_config(args: argparse.Namespace) -> None:
    step_start("inizio config")
    cfg = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "redirect_uri": args.redirect_uri,
        "linkedin_version": args.linkedin_version,
        "scopes": [x.strip() for x in args.scopes.split(",") if x.strip()] if args.scopes else DEFAULT_SCOPES,
    }
    save_config(cfg)
    step_done("config salvata")
    print(f"OK: {CONFIG_PATH}")


def cmd_show_config(_: argparse.Namespace) -> None:
    step_start("carico config")
    cfg = load_config()
    sanitized = dict(cfg)
    if "client_secret" in sanitized:
        sanitized["client_secret"] = "***"
    if "token" in sanitized:
        sanitized["token"] = {"access_token": "***", **{k: v for k, v in sanitized["token"].items() if k != "access_token"}}
    print(json.dumps(sanitized, indent=2))
    step_done("config mostrata")


def build_auth_url(cfg: dict[str, Any], state: str, code_challenge: str | None = None) -> str:
    params = {
        "response_type": "code",
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "scope": " ".join(cfg.get("scopes", DEFAULT_SCOPES)),
        "state": state,
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def cmd_auth_url(args: argparse.Namespace) -> None:
    step_start("carico config")
    cfg = load_config()
    state = args.state or secrets.token_urlsafe(24)
    code_verifier = None
    code_challenge = None
    if args.pkce:
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = b64url_sha256(code_verifier)
    url = build_auth_url(cfg, state, code_challenge)
    print(url)
    if code_verifier:
        print(f"\nstate={state}\ncode_verifier={code_verifier}")
    else:
        print(f"\nstate={state}\nmode=no-pkce")
    step_done("authorization url pronta")


def exchange_code(cfg: dict[str, Any], code: str, code_verifier: str | None) -> dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }
    if code_verifier:
        data["code_verifier"] = code_verifier
    return http_post_form(TOKEN_URL, data)


def cmd_exchange_token(args: argparse.Namespace) -> None:
    step_start("carico config")
    cfg = load_config()
    token_data = exchange_code(cfg, args.code, args.code_verifier)
    cfg["token"] = token_data
    cfg["token_saved_at"] = int(time.time())
    save_config(cfg)
    print(json.dumps(token_data, indent=2))
    step_done("token salvato")


def cmd_login(args: argparse.Namespace) -> None:
    step_start("carico config")
    cfg = load_config()

    parsed = urllib.parse.urlparse(cfg["redirect_uri"])
    if parsed.scheme != "http" or not parsed.hostname or not parsed.port:
        raise CliError("redirect_uri deve essere tipo: http://localhost:8080/callback")

    state = secrets.token_urlsafe(24)
    code_verifier = None
    code_challenge = None
    if args.pkce:
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = b64url_sha256(code_verifier)
    auth_url = build_auth_url(cfg, state, code_challenge)

    result: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            code = qs.get("code", [None])[0]
            st = qs.get("state", [None])[0]
            err = qs.get("error", [None])[0]
            if err:
                result["error"] = err
            elif code and st == state:
                result["code"] = code
            else:
                result["error"] = "missing_code_or_bad_state"

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>OK, puoi tornare al terminale.</h1>")

        def log_message(self, format, *args):
            return

    server = HTTPServer((parsed.hostname, parsed.port), CallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)

    step_start("apri url login nel browser")
    print(auth_url)
    if shutil.which("xdg-open"):
        subprocess.Popen(["xdg-open", auth_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    step_start("attendo callback oauth")
    thread.start()
    thread.join(timeout=180)
    server.server_close()

    if "code" not in result:
        raise CliError(f"Login fallito: {result.get('error', 'timeout')}" )

    step_start("scambio code con token")
    token_data = exchange_code(cfg, result["code"], code_verifier)
    cfg["token"] = token_data
    cfg["token_saved_at"] = int(time.time())
    save_config(cfg)
    step_done("login completato")
    print("OK login")


def cmd_me(_: argparse.Namespace) -> None:
    step_start("carico token")
    cfg = load_config()
    token = ensure_token(cfg)
    step_start("chiamo userinfo")
    data = http_get_json(USERINFO_URL, token)
    print(json.dumps(data, indent=2))
    step_done("profilo ricevuto")


def cmd_whoami(_: argparse.Namespace) -> None:
    step_start("carico token")
    cfg = load_config()
    token = ensure_token(cfg)
    step_start("chiamo userinfo")
    data = http_get_json(USERINFO_URL, token)

    linkedin_id = data.get("sub", "")
    name = data.get("name") or " ".join(filter(None, [data.get("given_name", ""), data.get("family_name", "")])).strip()
    email = data.get("email", "")

    print(f"id: {linkedin_id}")
    print(f"name: {name}")
    print(f"email: {email}")
    step_done("whoami completato")


def cmd_post_text(args: argparse.Namespace) -> None:
    step_start("carico token")
    cfg = load_config()
    token = ensure_token(cfg)

    step_start("prendo profilo autore")
    me = http_get_json(USERINFO_URL, token)
    sub = me.get("sub")
    if not sub:
        raise CliError("Campo 'sub' mancante in userinfo")

    payload = {
        "author": f"urn:li:person:{sub}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": args.text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": args.visibility,
        },
    }

    if args.preview:
        print(json.dumps(payload, indent=2))
        step_done("preview payload pronto")
        return

    step_start("pubblico post")
    resp = http_post_json(POSTS_URL, token, payload)
    print(json.dumps(resp, indent=2))
    step_done("post pubblicato")


def build_share_payload(author_sub: str, text: str, visibility: str, link: str | None = None) -> dict[str, Any]:
    media_category = "ARTICLE" if link else "NONE"
    media = [{"status": "READY", "originalUrl": link}] if link else []
    return {
        "author": f"urn:li:person:{author_sub}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": media_category,
                **({"media": media} if media else {}),
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility,
        },
    }


def cmd_post_link(args: argparse.Namespace) -> None:
    step_start("carico token")
    cfg = load_config()
    token = ensure_token(cfg)
    step_start("prendo profilo autore")
    me = http_get_json(USERINFO_URL, token)
    sub = me.get("sub")
    if not sub:
        raise CliError("Campo 'sub' mancante in userinfo")

    payload = build_share_payload(sub, args.text, args.visibility, link=args.url)
    if args.preview:
        print(json.dumps(payload, indent=2))
        step_done("preview payload pronto")
        return

    step_start("pubblico post link")
    resp = http_post_json(POSTS_URL, token, payload)
    print(json.dumps(resp, indent=2))
    step_done("post link pubblicato")


def cmd_post_file(args: argparse.Namespace) -> None:
    step_start("carico file testo")
    text = Path(args.path).read_text(encoding="utf-8").strip()
    if not text:
        raise CliError("File vuoto")

    fake_args = argparse.Namespace(text=text, visibility=args.visibility, preview=args.preview)
    cmd_post_text(fake_args)


def cmd_doctor(_: argparse.Namespace) -> None:
    step_start("controllo ambiente")

    print("== linkedin-cli doctor ==")

    print(f"python: {sys.version.split()[0]}")
    print(f"config_path: {CONFIG_PATH}")
    if CONFIG_PATH.exists():
        try:
            cfg = load_config()
            print("config_exists: true")
            print(f"client_id_set: {bool(cfg.get('client_id'))}")
            print(f"client_secret_set: {bool(cfg.get('client_secret'))}")
            print(f"redirect_uri: {cfg.get('redirect_uri', '')}")
            print(f"scopes: {','.join(cfg.get('scopes', []))}")
            print(f"linkedin_version: {cfg.get('linkedin_version', '202605')}")

            token = (cfg.get("token") or {}).get("access_token")
            print(f"token_present: {bool(token)}")
        except Exception as exc:
            print(f"config_parse_error: {exc}")
    else:
        print("config_exists: false")

    print("health: OK")
    step_done("doctor completato")


def cmd_post_image(args: argparse.Namespace) -> None:
    step_start("carico token")
    cfg = load_config()
    token = ensure_token(cfg)
    version = cfg.get("linkedin_version", "202605")

    step_start("prendo profilo autore")
    me = http_get_json(USERINFO_URL, token)
    sub = me.get("sub")
    if not sub:
        raise CliError("Campo 'sub' mancante in userinfo")
    owner = f"urn:li:person:{sub}"

    img_path = Path(args.path)
    if not img_path.exists():
        raise CliError(f"File immagine non trovato: {img_path}")
    image_bytes = img_path.read_bytes()

    suffix = img_path.suffix.lower()
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
    }.get(suffix)
    if not content_type:
        raise CliError("Formato non supportato. Usa jpg/jpeg/png/gif")

    step_start("inizializzo upload immagine")
    init_payload = {
        "initializeUploadRequest": {
            "owner": owner,
        }
    }
    init_resp = http_post_json_with_headers(
        REST_IMAGES_INIT_URL,
        token,
        init_payload,
        {"Linkedin-Version": version, "X-Restli-Protocol-Version": "2.0.0"},
    )

    value = init_resp.get("value", {})
    upload_url = value.get("uploadUrl")
    image_urn = value.get("image")
    if not upload_url or not image_urn:
        raise CliError(f"initializeUpload risposta inattesa: {init_resp}")

    step_start("carico bytes immagine")
    http_put_binary(upload_url, image_bytes, content_type)

    post_payload = {
        "author": owner,
        "commentary": args.text,
        "visibility": args.visibility,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {
            "media": {
                "id": image_urn,
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    if args.preview:
        print(json.dumps({"image_init": init_resp, "post_payload": post_payload}, indent=2))
        step_done("preview payload pronto")
        return

    step_start("creo post con immagine")
    resp = http_post_json_with_headers(
        REST_POSTS_URL,
        token,
        post_payload,
        {"Linkedin-Version": version, "X-Restli-Protocol-Version": "2.0.0"},
    )
    print(json.dumps(resp, indent=2))
    step_done("post immagine pubblicato")


def cmd_post_carousel(args: argparse.Namespace) -> None:
    step_start("carico token")
    cfg = load_config()
    token = ensure_token(cfg)
    version = cfg.get("linkedin_version", "202605")
    me = http_get_json(USERINFO_URL, token)
    sub = me.get("sub")
    if not sub:
        raise CliError("Campo 'sub' mancante in userinfo")
    owner = f"urn:li:person:{sub}"

    images = []
    for path_str in args.paths:
        img_path = Path(path_str)
        if not img_path.exists():
            raise CliError(f"File immagine non trovato: {img_path}")
        content_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif"}.get(img_path.suffix.lower())
        if not content_type:
            raise CliError("Formato non supportato. Usa jpg/jpeg/png/gif")
        step_start(f"upload {img_path.name}")
        init_resp = http_post_json_with_headers(
            REST_IMAGES_INIT_URL,
            token,
            {"initializeUploadRequest": {"owner": owner}},
            {"Linkedin-Version": version, "X-Restli-Protocol-Version": "2.0.0"},
        )
        value = init_resp.get("value", {})
        upload_url = value.get("uploadUrl")
        image_urn = value.get("image")
        if not upload_url or not image_urn:
            raise CliError(f"initializeUpload risposta inattesa: {init_resp}")
        http_put_binary(upload_url, img_path.read_bytes(), content_type)
        images.append({"id": image_urn, "altText": img_path.stem})

    post_payload = {
        "author": owner,
        "commentary": args.text,
        "visibility": args.visibility,
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"multiImage": {"images": images}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if args.preview:
        print(json.dumps(post_payload, indent=2))
        step_done("preview carousel pronto")
        return
    resp = http_post_json_with_headers(
        REST_POSTS_URL, token, post_payload,
        {"Linkedin-Version": version, "X-Restli-Protocol-Version": "2.0.0"},
    )
    print(json.dumps(resp, indent=2))
    step_done("post carousel pubblicato")


def load_queue() -> list[dict[str, Any]]:
    if not QUEUE_PATH.exists():
        return []
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(items: list[dict[str, Any]]) -> None:
    ensure_config_dir()
    QUEUE_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


def cmd_queue_add(args: argparse.Namespace) -> None:
    items = load_queue()
    job = {
        "id": secrets.token_hex(6),
        "run_at": args.run_at,
        "type": args.type,
        "payload": json.loads(Path(args.payload).read_text(encoding="utf-8")),
        "status": "pending",
        "retries": 0,
    }
    items.append(job)
    save_queue(items)
    print(json.dumps(job, indent=2))
    step_done("job aggiunto")


def cmd_queue_list(_: argparse.Namespace) -> None:
    print(json.dumps(load_queue(), indent=2))
    step_done("queue mostrata")


def cmd_queue_run(args: argparse.Namespace) -> None:
    items = load_queue()
    now = datetime.datetime.now(datetime.timezone.utc)
    changed = False
    for job in items:
        if job.get("status") not in {"pending", "failed"}:
            continue
        run_at = datetime.datetime.fromisoformat(job["run_at"])
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=datetime.timezone.utc)
        if run_at > now and not args.force:
            continue
        try:
            payload_file = Path("/tmp/_inline_payload.json")
            payload_file.write_text(json.dumps(job["payload"]), encoding="utf-8")
            if job["type"] == "post_text":
                cmd_post_text(argparse.Namespace(text=job["payload"]["text"], visibility=job["payload"].get("visibility", "PUBLIC"), preview=False))
            elif job["type"] == "post_link":
                cmd_post_link(argparse.Namespace(text=job["payload"]["text"], url=job["payload"]["url"], visibility=job["payload"].get("visibility", "PUBLIC"), preview=False))
            elif job["type"] == "post_image":
                cmd_post_image(argparse.Namespace(path=job["payload"]["path"], text=job["payload"]["text"], visibility=job["payload"].get("visibility", "PUBLIC"), preview=False))
            else:
                raise CliError(f"job type non supportato: {job['type']}")
            job["status"] = "done"
            changed = True
        except Exception as exc:
            job["status"] = "failed"
            job["last_error"] = str(exc)
            job["retries"] = int(job.get("retries", 0)) + 1
            changed = True
            if job["retries"] <= args.max_retries:
                job["status"] = "pending"
    if changed:
        save_queue(items)
    print(json.dumps(items, indent=2))
    step_done("queue run completato")


def cmd_oauth_debug(args: argparse.Namespace) -> None:
    step_start("carico config")
    cfg = load_config()
    print(f"token_url: {TOKEN_URL}")
    print(f"client_id: {cfg.get('client_id')}")
    print(f"redirect_uri: {cfg.get('redirect_uri')}")
    print(f"code_len: {len(args.code)}")
    print(f"code_verifier_len: {len(args.code_verifier) if args.code_verifier else 0}")

    body_method_payload = {
        "grant_type": "authorization_code",
        "code": args.code,
        "redirect_uri": cfg["redirect_uri"],
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }
    if args.code_verifier:
        body_method_payload["code_verifier"] = args.code_verifier

    basic_method_payload = {
        "grant_type": "authorization_code",
        "code": args.code,
        "redirect_uri": cfg["redirect_uri"],
    }
    if args.code_verifier:
        basic_method_payload["code_verifier"] = args.code_verifier

    print("\n== method: client_secret_post ==")
    try:
        resp = http_post_form(TOKEN_URL, body_method_payload)
        print(json.dumps(resp, indent=2))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        print(f"HTTP {err.code}: {body}")

    print("\n== method: client_secret_basic ==")
    try:
        resp = http_post_form_basic_auth(TOKEN_URL, cfg["client_id"], cfg["client_secret"], basic_method_payload)
        print(json.dumps(resp, indent=2))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        print(f"HTTP {err.code}: {body}")

    step_done("oauth debug completato")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="linkedin-cli", description="LinkedIn Consumer CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-config", help="salva credenziali OAuth")
    p_init.add_argument("--client-id", required=True)
    p_init.add_argument("--client-secret", required=True)
    p_init.add_argument("--redirect-uri", required=True)
    p_init.add_argument("--scopes", help="csv scopes")
    p_init.add_argument("--linkedin-version", default="202605", help="header Linkedin-Version, formato YYYYMM")
    p_init.set_defaults(func=cmd_init_config)

    p_cfg = sub.add_parser("show-config", help="mostra config mascherata")
    p_cfg.set_defaults(func=cmd_show_config)

    p_auth = sub.add_parser("auth-url", help="genera url auth manuale")
    p_auth.add_argument("--state", help="state custom")
    p_auth.add_argument("--pkce", action="store_true", help="abilita PKCE (default: off)")
    p_auth.set_defaults(func=cmd_auth_url)

    p_exchange = sub.add_parser("exchange-token", help="code -> token")
    p_exchange.add_argument("--code", required=True)
    p_exchange.add_argument("--code-verifier", help="necessario se usi PKCE")
    p_exchange.set_defaults(func=cmd_exchange_token)

    p_login = sub.add_parser("login", help="flow automatico browser + callback localhost")
    p_login.add_argument("--pkce", action="store_true", help="abilita PKCE (default: off)")
    p_login.set_defaults(func=cmd_login)

    p_me = sub.add_parser("me", help="mostra userinfo")
    p_me.set_defaults(func=cmd_me)

    p_who = sub.add_parser("whoami", help="profilo compatto")
    p_who.set_defaults(func=cmd_whoami)

    p_post = sub.add_parser("post-text", help="pubblica testo")
    p_post.add_argument("--text", required=True)
    p_post.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p_post.add_argument("--preview", action="store_true", help="stampa payload senza pubblicare")
    p_post.set_defaults(func=cmd_post_text)

    p_post_link = sub.add_parser("post-link", help="pubblica testo + link")
    p_post_link.add_argument("--text", required=True)
    p_post_link.add_argument("--url", required=True)
    p_post_link.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p_post_link.add_argument("--preview", action="store_true", help="stampa payload senza pubblicare")
    p_post_link.set_defaults(func=cmd_post_link)

    p_post_file = sub.add_parser("post-file", help="pubblica testo da file")
    p_post_file.add_argument("--path", required=True)
    p_post_file.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p_post_file.add_argument("--preview", action="store_true", help="stampa payload senza pubblicare")
    p_post_file.set_defaults(func=cmd_post_file)

    p_post_img = sub.add_parser("post-image", help="pubblica post con immagine")
    p_post_img.add_argument("--path", required=True, help="path immagine jpg/png/gif")
    p_post_img.add_argument("--text", required=True)
    p_post_img.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p_post_img.add_argument("--preview", action="store_true", help="stampa payload senza pubblicare")
    p_post_img.set_defaults(func=cmd_post_image)

    p_post_car = sub.add_parser("post-carousel", help="pubblica post multi-immagine")
    p_post_car.add_argument("--paths", nargs="+", required=True)
    p_post_car.add_argument("--text", required=True)
    p_post_car.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    p_post_car.add_argument("--preview", action="store_true")
    p_post_car.set_defaults(func=cmd_post_carousel)

    p_q_add = sub.add_parser("queue-add", help="aggiunge job in coda")
    p_q_add.add_argument("--type", required=True, choices=["post_text", "post_link", "post_image"])
    p_q_add.add_argument("--run-at", required=True, help="ISO datetime")
    p_q_add.add_argument("--payload", required=True, help="file json payload")
    p_q_add.set_defaults(func=cmd_queue_add)

    p_q_list = sub.add_parser("queue-list", help="mostra queue")
    p_q_list.set_defaults(func=cmd_queue_list)

    p_q_run = sub.add_parser("queue-run", help="esegue queue")
    p_q_run.add_argument("--force", action="store_true")
    p_q_run.add_argument("--max-retries", type=int, default=2)
    p_q_run.set_defaults(func=cmd_queue_run)

    p_odebug = sub.add_parser("oauth-debug", help="debug token exchange con due metodi client auth")
    p_odebug.add_argument("--code", required=True)
    p_odebug.add_argument("--code-verifier")
    p_odebug.set_defaults(func=cmd_oauth_debug)

    p_doc = sub.add_parser("doctor", help="diagnostica setup locale")
    p_doc.set_defaults(func=cmd_doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except CliError as err:
        print(f"Errore: {err}", file=sys.stderr)
        return 2
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        print(f"HTTP {err.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as err:
        print(f"Errore rete: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
