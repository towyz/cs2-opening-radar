import json
import os
import random
import re
import shutil
import subprocess
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse

from app.models.analysis_result import AnalysisResult
from app.services.local_demo_store import extract_dem_from_zip
from app.services.parser_runner import ParserRunError, run_parser
from app.services.result_store import read_result


DEMO_FILE_RE = re.compile(r"(?P<match_id>\d{12,})_(?P<cup_id>\d+)\.(?:zip|dem)$", re.IGNORECASE)
MATCH_ID_RE = re.compile(
    r'"match_id"\s*:\s*"?(\d{12,})"?|match_id=(\d{12,})|/demo/(?:[^/]+/)?(\d{12,})_'
)
DEMO_URL_RE = re.compile(r"https?://[^\s\"'}]+(?:\.dem|\.dem\.zip|/csgo/demo/)[^\s\"'}]*", re.IGNORECASE)
MAP_RE = re.compile(r"\b(de_[a-z0-9_]+|dust[_-]?2|dust2)\b", re.IGNORECASE)
ENCODED_LOG_RE = re.compile(r"\^([0-9a-fA-F]{20,})\$")
ACCESS_TOKEN_RE = re.compile(
    r"(?:[?&]access_token=|[\"']access_token[\"']\s*:\s*[\"']|[\"']accessToken[\"']\s*:\s*[\"'])([^&\s\"'}]+)",
    re.IGNORECASE,
)
PWA_JT_RE = re.compile(
    r"(?:[\"'](?:pwa_jt|Pwa-Jt|jt)[\"']\s*:\s*[\"']|(?:pwa_jt|Pwa-Jt|jt)=)([^&\s\"'}]+)",
    re.IGNORECASE,
)
STEAM64_RE = re.compile(
    r"(?:PwaSteamId|steamid|steam_id|steam64)[^0-9]{0,30}(7656119\d{10})",
    re.IGNORECASE,
)
PERFECTWORLD_AES_KEY_PREFIX = "G#r%*VCDYj6P5$mny0838MhH8d"
PERFECTWORLD_WEB_API_APP_ID = "20000"


@dataclass(frozen=True)
class PerfectWorldCandidate:
    match_id: str
    cup_id: int
    url: str | None
    local_path: Path | None
    seen_at: datetime
    map_name: str | None = None


@dataclass(frozen=True)
class ImportedDemo:
    match_id: str
    source_path: Path
    result: AnalysisResult | None


@dataclass(frozen=True)
class PerfectWorldImportReport:
    imported: list[ImportedDemo]
    scanned: int
    downloaded: int
    skipped: list[str]
    source: str
    notice: str | None = None


class PerfectWorldCredentialsError(ValueError):
    pass


@dataclass(frozen=True)
class PerfectWorldCredentials:
    access_token: str | None = None
    pwa_jt: str | None = None
    login_steam64: str | None = None
    source: str = "none"


def import_recent_dust2_demos(
    *,
    perfect_uid: str,
    steam64: str | None,
    access_token: str | None,
    pwa_jt: str | None,
    login_steam64: str | None,
    limit: int,
    window_seconds: int,
    uploads_dir: Path,
    results_dir: Path,
    download_dir: Path,
    parser_bin: Path,
    map_config_path: Path,
    signer_bridge_path: Path | None = None,
) -> PerfectWorldImportReport:
    credentials = resolve_perfectworld_credentials(
        access_token=access_token,
        pwa_jt=pwa_jt,
        login_steam64=login_steam64,
    )
    client = PerfectWorldClient(
        access_token=credentials.access_token,
        pwa_jt=credentials.pwa_jt,
        login_steam64=credentials.login_steam64,
        signer_bridge_path=signer_bridge_path,
    )
    source = "perfectworld_api"
    if not client.can_request_live_matches:
        raise PerfectWorldCredentialsError(
            "Perfect World access token is required to actively request recent demos, and none was found in request, environment, or local client logs."
        )
    candidates = client.recent_dust2_candidates(perfect_uid=perfect_uid, limit=limit)
    imported: list[ImportedDemo] = []
    skipped: list[str] = []
    downloaded = 0

    for candidate in candidates:
        if len(imported) >= limit:
            break
        if candidate.map_name and candidate.map_name != "de_dust2":
            skipped.append(f"{candidate.match_id}: map is {candidate.map_name}")
            continue
        try:
            source_path, did_download = materialize_candidate(candidate, download_dir)
            if did_download:
                downloaded += 1
            upload_path = uploads_dir / f"perfectworld-{candidate.match_id}-{candidate.cup_id}.dem"
            result_path = results_dir / f"perfectworld-{candidate.match_id}-{candidate.cup_id}.json"
            result = None
            if steam64:
                prepare_candidate_demo(source_path, upload_path)
                run_parser(
                    parser_bin=parser_bin,
                    demo_path=upload_path,
                    steam64=steam64,
                    map_name="de_dust2",
                    map_config_path=map_config_path,
                    output_path=result_path,
                    window_seconds=window_seconds,
                )
                result = AnalysisResult.model_validate(read_result(result_path))
            imported.append(ImportedDemo(candidate.match_id, source_path, result))
        except ParserRunError as exc:
            code = str(exc.detail.get("code", "DEMO_PARSE_FAILED"))
            skipped.append(f"{candidate.match_id}: {code}")
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            skipped.append(f"{candidate.match_id}: {exc}")

    return PerfectWorldImportReport(
        imported=imported,
        scanned=len(candidates),
        downloaded=downloaded,
        skipped=skipped[:20],
        source=source,
        notice=None,
    )


class PerfectWorldSignerError(ValueError):
    pass


class PerfectWorldClient:
    match_api = "https://pwaweblogin.wmpvp.com"
    app_api = "https://appactivity.wmpvp.com"

    def __init__(
        self,
        *,
        access_token: str | None,
        pwa_jt: str | None,
        login_steam64: str | None,
        signer_bridge_path: Path | None = None,
    ) -> None:
        self.access_token = (access_token or "").strip()
        self.pwa_jt = (pwa_jt or "").strip()
        self.login_steam64 = (login_steam64 or "").strip()
        self.signer_bridge_path = signer_bridge_path or default_signer_bridge_path()

    @property
    def can_request_live_matches(self) -> bool:
        return bool(self.access_token)

    def recent_dust2_candidates(self, *, perfect_uid: str, limit: int) -> list[PerfectWorldCandidate]:
        candidates: list[PerfectWorldCandidate] = []
        page = 1
        while len(candidates) < limit and page <= 5:
            payload = self.get_json(
                self.match_api,
                "/user-info/match-list",
                {
                    "uid": perfect_uid,
                    "page": page,
                    "page_size": 15,
                    "game_types": "10,12,14,16,27,20",
                    "access_token": self.access_token,
                },
            )
            for item in extract_match_items(payload):
                if not is_dust2_match(item):
                    continue
                match_id = extract_match_id(item)
                if not match_id:
                    continue
                try:
                    url = self.demo_url(match_id)
                except ValueError:
                    url = None
                candidates.append(
                    PerfectWorldCandidate(
                        match_id=match_id,
                        cup_id=0,
                        url=url,
                        local_path=None,
                        seen_at=datetime.now(),
                        map_name="de_dust2",
                    )
                )
                if len(candidates) >= limit:
                    break
            page += 1
        return candidates

    def demo_url(self, match_id: str) -> str:
        try:
            return self.demo_url_from_signed_match_api(match_id)
        except PerfectWorldSignerError:
            raise
        except ValueError:
            pass
        payload = self.get_json(
            self.app_api,
            "/steamcn/app/csgo/match/demo",
            {"match_id": match_id, "access_token": self.access_token},
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict) and data.get("demo_url"):
            return str(data["demo_url"])
        raise ValueError(f"{match_id}: demo_url was not returned")

    def demo_url_from_signed_match_api(self, match_id: str) -> str:
        payload = self.post_signed_json(
            "/match-api/demo",
            {
                "access_token": self.access_token,
                "match_id": match_id,
            },
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict) and data.get("demo_url"):
            return str(data["demo_url"])
        raise ValueError(f"{match_id}: signed demo_url was not returned")

    def post_signed_json(self, path: str, body: dict[str, object]) -> dict[str, object]:
        body_json = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        signed_url = self.signed_url(path=path, method="POST", data=body_json, query_params=None)
        request = urllib.request.Request(
            signed_url,
            data=body_json.encode("utf-8"),
            headers={**self.client_headers(), "Content-Type": "application/json;charset=UTF-8"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: unexpected response")
        code = payload.get("code")
        if code not in (0, "0", None):
            message = payload.get("msg") or payload.get("message") or "Perfect World API request failed"
            raise ValueError(f"{path}: {message}")
        return decode_encoded_payload(payload)

    def signed_url(
        self,
        *,
        path: str,
        method: str,
        data: str,
        query_params: dict[str, object] | None,
    ) -> str:
        randnum = str(random.randint(100000, 999999))
        timestamp = str(int(time.time()))
        signature = sign_perfectworld_request(
            randnum=randnum,
            timestamp=timestamp,
            data=data,
            signer_bridge_path=self.signer_bridge_path,
        )
        url = (
            f"{self.match_api}{path}?{urlencode({'a': PERFECTWORLD_WEB_API_APP_ID, 'r': randnum, 's': signature, 't': timestamp})}"
        )
        if method.upper() == "GET" and query_params:
            url = f"{url}&{urlencode(query_params)}"
        return url

    def get_json(self, base_url: str, path: str, params: dict[str, object]) -> dict[str, object]:
        headers = self.client_headers()
        url = f"{base_url}{path}?{urlencode(params)}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}: unexpected response")
        code = payload.get("code")
        if code not in (0, "0", None):
            message = payload.get("msg") or payload.get("message") or "Perfect World API request failed"
            raise ValueError(f"{path}: {message}")
        payload = decode_encoded_payload(payload)
        return payload

    def client_headers(self) -> dict[str, str]:
        headers = {"Referer": "https://client.wmpvp.com", "User-Agent": "Mozilla/5.0"}
        if self.login_steam64:
            headers["PwaSteamId"] = self.login_steam64
        if self.pwa_jt:
            headers["Pwa-Jt"] = self.pwa_jt
        return headers


def sign_perfectworld_request(
    *,
    randnum: str,
    timestamp: str,
    data: str,
    signer_bridge_path: Path | None = None,
) -> str:
    bridge_path = signer_bridge_path or default_signer_bridge_path()
    if bridge_path is None or not bridge_path.exists():
        raise PerfectWorldSignerError("Perfect World SWAP_DATA signer bridge is not configured")
    payload = {
        "randnum": randnum,
        "ts": timestamp,
        "data": data,
        "version": 1,
    }
    try:
        completed = subprocess.run(
            [signer_node_runtime(), str(bridge_path)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=True,
            timeout=3,
        )
    except subprocess.TimeoutExpired as exc:
        raise PerfectWorldSignerError("Perfect World SWAP_DATA signer bridge timed out") from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise PerfectWorldSignerError("Perfect World SWAP_DATA signer bridge failed") from exc
    try:
        response = parse_signer_bridge_output(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PerfectWorldSignerError("Perfect World SWAP_DATA signer bridge returned invalid JSON") from exc
    signature = response.get("signature") if isinstance(response, dict) else None
    if not isinstance(signature, str) or not signature:
        raise PerfectWorldSignerError("Perfect World SWAP_DATA signer bridge did not return a signature")
    return signature


def parse_signer_bridge_output(stdout: str) -> dict[str, object]:
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
    parsed = json.loads(stdout)
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("signer bridge response is not an object", stdout, 0)
    return parsed


def signer_node_runtime() -> str:
    return (os.environ.get("PERFECTWORLD_SIGNER_NODE") or "node").strip() or "node"


def decode_encoded_payload(payload: dict[str, object]) -> dict[str, object]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return payload
    token = data.get("t")
    encrypted = data.get("e")
    if not isinstance(token, (str, int)) or not isinstance(encrypted, str):
        return payload
    decrypted = decrypt_perfectworld_data(str(token), encrypted)
    try:
        payload["data"] = json.loads(decrypted)
    except json.JSONDecodeError as exc:
        raise ValueError("Perfect World encoded response could not be decoded") from exc
    return payload


def decrypt_perfectworld_data(token: str, encrypted: str) -> str:
    key = f"{PERFECTWORLD_AES_KEY_PREFIX}{token}"
    script = """
const crypto = require("crypto");
const fs = require("fs");
const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const decipher = crypto.createDecipheriv("aes-256-ecb", Buffer.from(payload.key, "utf8"), null);
decipher.setAutoPadding(true);
process.stdout.write(decipher.update(payload.encrypted, "base64", "utf8") + decipher.final("utf8"));
"""
    try:
        completed = subprocess.run(
            ["node", "-e", script],
            input=json.dumps({"key": key, "encrypted": encrypted}),
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Perfect World encoded response requires local Node.js crypto support") from exc
    return completed.stdout


def extract_match_items(payload: dict[str, object]) -> list[dict[str, object]]:
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("list", "records", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def extract_match_id(item: dict[str, object]) -> str | None:
    for key in ("match", "match_id", "matchId", "pvp_match_id", "pvpMatchId"):
        value = item.get(key)
        if value:
            return str(value)
    match_result = item.get("match_result")
    if isinstance(match_result, dict):
        for key in ("match", "match_id", "matchId", "pvp_match_id", "pvpMatchId"):
            value = match_result.get(key)
            if value:
                return str(value)
    return None


def is_dust2_match(item: dict[str, object]) -> bool:
    candidates: list[object] = [item.get("map"), item.get("map_name"), item.get("mapName"), item.get("match_name")]
    match_result = item.get("match_result")
    if isinstance(match_result, dict):
        candidates.extend(
            [
                match_result.get("map"),
                match_result.get("map_name"),
                match_result.get("mapName"),
                match_result.get("game_map_name"),
            ]
        )
    for candidate in candidates:
        if isinstance(candidate, dict):
            if any(is_dust2_text(str(value)) for value in candidate.values()):
                return True
        elif candidate is not None and is_dust2_text(str(candidate)):
            return True
    return False


def is_dust2_text(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return "dust2" in normalized or "dust_2" in normalized or "de_dust2" in normalized or "炙热沙城" in value


def discover_perfectworld_candidates() -> list[PerfectWorldCandidate]:
    candidates: dict[tuple[str, int], PerfectWorldCandidate] = {}
    for candidate in local_demo_candidates():
        candidates[(candidate.match_id, candidate.cup_id)] = candidate
    for candidate in log_candidates():
        key = (candidate.match_id, candidate.cup_id)
        existing = candidates.get(key)
        if existing is None or candidate.seen_at > existing.seen_at:
            candidates[key] = merge_candidate(existing, candidate)
    return sorted(candidates.values(), key=lambda item: item.seen_at, reverse=True)


def local_demo_candidates() -> list[PerfectWorldCandidate]:
    candidates: list[PerfectWorldCandidate] = []
    for demo_dir in default_demo_search_dirs():
        if not demo_dir.exists():
            continue
        for path in demo_dir.glob("*"):
            if not path.is_file():
                continue
            match = DEMO_FILE_RE.search(path.name)
            if match is None:
                continue
            candidates.append(
                PerfectWorldCandidate(
                    match_id=match.group("match_id"),
                    cup_id=int(match.group("cup_id")),
                    url=None,
                    local_path=path,
                    seen_at=datetime.fromtimestamp(path.stat().st_mtime),
                    map_name=None,
                )
            )
    return candidates


def log_candidates() -> list[PerfectWorldCandidate]:
    log_dir = default_wmpvp_log_dir()
    if log_dir is None or not log_dir.exists():
        return []
    candidates: list[PerfectWorldCandidate] = []
    for log_path in sorted(log_dir.glob("pvpClient*.log"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            decoded = decode_wmpvp_log_line(line)
            candidate = parse_log_candidate(decoded)
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def parse_log_candidate(line: str) -> PerfectWorldCandidate | None:
    if "demo" not in line.lower():
        return None
    payload = parse_download_payload(line)
    seen_at = parse_log_time(line)
    if isinstance(payload, dict):
        signed_demo = payload.get("signedDemo") if isinstance(payload.get("signedDemo"), dict) else {}
        match_id = str(signed_demo.get("matchId") or signed_demo.get("match_id") or "")
        cup_id = int(signed_demo.get("cup_id") or 0)
        url = str(payload.get("src") or "")
        local_path = Path(str(payload["dir"])) if payload.get("dir") else None
        if match_id:
            return PerfectWorldCandidate(match_id, cup_id, url or None, local_path, seen_at, map_from_text(line))

    match_id = first_match_id(line)
    url = first_demo_url(line)
    if match_id is None or url is None:
        return None
    cup_id = cup_id_from_url(url)
    return PerfectWorldCandidate(match_id, cup_id, url, None, seen_at, map_from_text(line))


def parse_download_payload(line: str) -> dict[str, object] | None:
    marker = "download demo:"
    idx = line.lower().find(marker)
    if idx < 0:
        return None
    raw = line[idx + len(marker) :].strip()
    try:
        payload, _ = json.JSONDecoder().raw_decode(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def decode_wmpvp_log_line(line: str) -> str:
    marker = ENCODED_LOG_RE.search(line)
    if marker is None:
        return line
    payload = marker.group(1)
    if len(payload) % 2 != 0:
        return line
    decoded = bytearray()
    try:
        for idx in range(0, len(payload), 2):
            byte = int(payload[idx : idx + 2], 16)
            decoded.append(byte ^ ((42 + 3 * (idx // 2)) % 255))
    except ValueError:
        return line
    decoded_text = decoded.decode("utf-8", errors="replace")
    return f"{line[: marker.start()]}{decoded_text}{line[marker.end():]}"


def resolve_perfectworld_credentials(
    *,
    access_token: str | None,
    pwa_jt: str | None,
    login_steam64: str | None,
) -> PerfectWorldCredentials:
    explicit = PerfectWorldCredentials(
        access_token=(access_token or "").strip() or None,
        pwa_jt=(pwa_jt or "").strip() or None,
        login_steam64=(login_steam64 or "").strip() or None,
        source="request",
    )
    if explicit.access_token:
        return explicit

    env_credentials = PerfectWorldCredentials(
        access_token=(os.environ.get("PERFECTWORLD_ACCESS_TOKEN") or "").strip() or None,
        pwa_jt=(os.environ.get("PERFECTWORLD_PWA_JT") or "").strip() or None,
        login_steam64=(os.environ.get("PERFECTWORLD_LOGIN_STEAM64") or "").strip() or None,
        source="environment",
    )
    if env_credentials.access_token:
        return env_credentials

    local_login_credentials = read_local_login_bridge_credentials()
    if local_login_credentials.access_token:
        return local_login_credentials

    return read_credentials_from_wmpvp_logs()


def read_local_login_bridge_credentials() -> PerfectWorldCredentials:
    request = urllib.request.Request(
        "http://127.0.0.1:55555/",
        headers={
            "Host": "localhost.pwaweblogin.wmpvp.com:55555",
            "Origin": "https://match.wmpvp.com",
            "Referer": "https://match.wmpvp.com/",
            "User-Agent": "Mozilla/5.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            raw = response.read().decode("utf-8")
    except OSError:
        return PerfectWorldCredentials(source="local_client_login_bridge")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return PerfectWorldCredentials(source="local_client_login_bridge")
    if not isinstance(payload, dict):
        return PerfectWorldCredentials(source="local_client_login_bridge")
    encoded_token = payload.get("token")
    if not isinstance(encoded_token, str) or not encoded_token:
        return PerfectWorldCredentials(source="local_client_login_bridge")
    token, _server_time, login_id = split_local_login_token(decode_wmpvp_log_line(encoded_token))
    return PerfectWorldCredentials(
        access_token=token,
        pwa_jt=None,
        login_steam64=login_id if login_id and login_id.startswith("7656119") else None,
        source="local_client_login_bridge",
    )


def split_local_login_token(decoded: str) -> tuple[str | None, str | None, str | None]:
    parts = decoded.rsplit("_", 2)
    if len(parts) != 3:
        return None, None, None
    token, server_time, login_id = (part.strip() for part in parts)
    return token or None, server_time or None, login_id or None


def read_credentials_from_wmpvp_logs() -> PerfectWorldCredentials:
    log_dir = default_wmpvp_log_dir()
    if log_dir is None:
        return PerfectWorldCredentials(source="local_client_logs")
    try:
        log_dir_exists = log_dir.exists()
    except OSError:
        return PerfectWorldCredentials(source="local_client_logs")
    if not log_dir_exists:
        return PerfectWorldCredentials(source="local_client_logs")

    access_token: str | None = None
    pwa_jt: str | None = None
    login_steam64: str | None = None
    try:
        log_paths = sorted(log_dir.glob("pvpClient*.log"), key=lambda item: item.stat().st_mtime, reverse=True)
    except OSError:
        return PerfectWorldCredentials(source="local_client_logs")

    for log_path in log_paths[:10]:
        try:
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            decoded = decode_wmpvp_log_line(line)
            access_token = access_token or extract_first(ACCESS_TOKEN_RE, decoded)
            pwa_jt = pwa_jt or extract_first(PWA_JT_RE, decoded)
            login_steam64 = login_steam64 or extract_first(STEAM64_RE, decoded)
            if access_token and pwa_jt and login_steam64:
                return PerfectWorldCredentials(access_token, pwa_jt, login_steam64, "local_client_logs")
        if access_token:
            return PerfectWorldCredentials(access_token, pwa_jt, login_steam64, "local_client_logs")

    return PerfectWorldCredentials(access_token, pwa_jt, login_steam64, "local_client_logs")


def extract_first(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if match is None:
        return None
    return match.group(1)


def materialize_candidate(candidate: PerfectWorldCandidate, download_dir: Path) -> tuple[Path, bool]:
    if candidate.local_path and candidate.local_path.exists():
        return candidate.local_path, False
    existing = find_downloaded_candidate(download_dir, candidate)
    if existing is not None:
        return existing, False
    if not candidate.url:
        raise ValueError("demo download URL requires Perfect World client SWAP_DATA signature")
    download_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".zip" if ".zip" in candidate.url.lower() else ".dem"
    target_path = download_dir / f"{candidate.match_id}_{candidate.cup_id}{suffix}"
    request = urllib.request.Request(candidate.url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response, target_path.open("wb") as out:
        shutil.copyfileobj(response, out)
    return target_path, True


def find_downloaded_candidate(download_dir: Path, candidate: PerfectWorldCandidate) -> Path | None:
    for suffix in (".zip", ".dem"):
        path = download_dir / f"{candidate.match_id}_{candidate.cup_id}{suffix}"
        if path.exists():
            return path
    return None


def prepare_candidate_demo(source_path: Path, upload_path: Path) -> None:
    suffix = source_path.suffix.lower()
    if suffix == ".dem":
        shutil.copyfile(source_path, upload_path)
        return
    if suffix == ".zip":
        extract_dem_from_zip(source_path, upload_path)
        return
    raise ValueError("candidate is not a .dem or .zip file")


def merge_candidate(
    existing: PerfectWorldCandidate | None,
    candidate: PerfectWorldCandidate,
) -> PerfectWorldCandidate:
    if existing is None:
        return candidate
    return PerfectWorldCandidate(
        match_id=candidate.match_id,
        cup_id=candidate.cup_id,
        url=candidate.url or existing.url,
        local_path=candidate.local_path or existing.local_path,
        seen_at=max(candidate.seen_at, existing.seen_at),
        map_name=candidate.map_name or existing.map_name,
    )


def default_wmpvp_log_dir() -> Path | None:
    appdata = os.environ.get("APPDATA")
    return Path(appdata) / "Wmpvp" / "Log" if appdata else None


def default_wmpvp_demo_dir() -> Path | None:
    appdata = os.environ.get("APPDATA")
    return Path(appdata) / "Wmpvp" / "demo" if appdata else None


def default_demo_search_dirs() -> list[Path]:
    candidates = [Path("D:/csgodemocache")]
    wmpvp_demo_dir = default_wmpvp_demo_dir()
    if wmpvp_demo_dir is not None:
        candidates.insert(0, wmpvp_demo_dir)
    return candidates


def default_signer_bridge_path() -> Path | None:
    configured = (os.environ.get("PERFECTWORLD_SIGNER_BRIDGE") or "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[3] / "tools" / "perfectworld_signer_bridge" / "signer_bridge.js"


def parse_log_time(line: str) -> datetime:
    match = re.search(r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
    if match is None:
        return datetime.fromtimestamp(0)
    try:
        return datetime.fromisoformat(match.group(1))
    except ValueError:
        return datetime.fromtimestamp(0)


def first_match_id(line: str) -> str | None:
    match = MATCH_ID_RE.search(line)
    if match is None:
        return None
    return next((group for group in match.groups() if group), None)


def first_demo_url(line: str) -> str | None:
    match = DEMO_URL_RE.search(line)
    return match.group(0) if match else None


def cup_id_from_url(url: str) -> int:
    match = re.search(r"_(\d+)\.dem", urlparse(url).path, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def map_from_text(text: str) -> str | None:
    match = MAP_RE.search(text)
    if match is None:
        return None
    value = match.group(1).lower().replace("-", "_")
    if value in {"dust2", "dust_2"}:
        return "de_dust2"
    return value
