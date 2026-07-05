from datetime import datetime

from app.services.perfectworld_demo_importer import (
    PerfectWorldClient,
    PerfectWorldCredentials,
    PerfectWorldCredentialsError,
    PerfectWorldSignerError,
    cup_id_from_url,
    decode_wmpvp_log_line,
    decrypt_perfectworld_data,
    first_match_id,
    import_recent_dust2_demos,
    parse_log_candidate,
    parse_signer_bridge_output,
    read_local_login_bridge_credentials,
    resolve_perfectworld_credentials,
    sign_perfectworld_request,
    split_local_login_token,
)


def encode_wmpvp_log_line(line: str) -> str:
    encoded = []
    for idx, byte in enumerate(line.encode("utf-8")):
        encoded.append(f"{byte ^ ((42 + 3 * idx) % 255):02x}")
    return f"^{''.join(encoded)}$"


def test_decode_wmpvp_log_line_reverses_client_encoding():
    line = '[2026-07-02T22:59:46.246] download demo: {"signedDemo":{"matchId":"9207998683795397900"}}'

    assert decode_wmpvp_log_line(encode_wmpvp_log_line(line)) == line


def test_decode_wmpvp_log_line_reverses_embedded_client_encoding():
    line = '[2026-07-02T22:59:46.246] download demo: {"signedDemo":{"matchId":"9207998683795397900"}}'

    assert decode_wmpvp_log_line(f"info {encode_wmpvp_log_line(line)}") == f"info {line}"


def test_parse_download_demo_log_candidate_redacts_nothing_but_returns_metadata_only():
    line = (
        '[2026-07-02T22:59:46.246] download demo: '
        '{"dir":"C:\\\\Users\\\\demo\\\\9207998683795397900_0.zip",'
        '"signedDemo":{"matchId":"9207998683795397900","cup_id":0},'
        '"src":"https://pwaweblogin.wmpvp.com/csgo/demo/9207998683795397900_0.dem?access_token=secret"}'
    )

    candidate = parse_log_candidate(line)

    assert candidate is not None
    assert candidate.match_id == "9207998683795397900"
    assert candidate.cup_id == 0
    assert candidate.local_path is not None
    assert candidate.seen_at == datetime.fromisoformat("2026-07-02T22:59:46")


def test_oss_demo_url_match_and_cup_id_are_detected():
    url = "https://pvp-demo-hz.oss-cn-hangzhou.aliyuncs.com/demo/normal/9207998683795397900_1.dem?Expires=x"

    assert first_match_id(url) == "9207998683795397900"
    assert cup_id_from_url(url) == 1


def test_client_requires_access_token_for_live_match_requests():
    client = PerfectWorldClient(access_token=None, pwa_jt=None, login_steam64=None)

    assert client.can_request_live_matches is False


def test_import_requires_credentials_and_does_not_fallback_to_local_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "empty-appdata"))
    monkeypatch.delenv("PERFECTWORLD_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(
        "app.services.perfectworld_demo_importer.read_local_login_bridge_credentials",
        lambda: PerfectWorldCredentials(source="local_client_login_bridge"),
    )

    try:
        import_recent_dust2_demos(
            perfect_uid="123",
            steam64=None,
            access_token=None,
            pwa_jt=None,
            login_steam64=None,
            limit=5,
            window_seconds=30,
            uploads_dir=tmp_path / "uploads",
            results_dir=tmp_path / "results",
            download_dir=tmp_path / "perfectworld",
            parser_bin=tmp_path / "parser.exe",
            map_config_path=tmp_path / "map.json",
        )
    except PerfectWorldCredentialsError:
        return

    raise AssertionError("import should require Perfect World credentials")


def test_credentials_can_be_read_from_local_client_logs(tmp_path, monkeypatch):
    appdata = tmp_path / "AppData" / "Roaming"
    log_dir = appdata / "Wmpvp" / "Log"
    log_dir.mkdir(parents=True)
    line = (
        '[2026-07-05T12:00:00.000] download demo: '
        '{"src":"https://pwaweblogin.wmpvp.com/csgo/demo/1_0.dem?access_token=auto-token&match_id=1",'
        '"PwaSteamId":"76561199177996326"}'
    )
    (log_dir / "pvpClient.2026-07-05.log").write_text(f"info {encode_wmpvp_log_line(line)}\n", encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.delenv("PERFECTWORLD_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(
        "app.services.perfectworld_demo_importer.read_local_login_bridge_credentials",
        lambda: PerfectWorldCredentials(source="local_client_login_bridge"),
    )

    credentials = resolve_perfectworld_credentials(access_token=None, pwa_jt=None, login_steam64=None)

    assert credentials.access_token == "auto-token"
    assert credentials.login_steam64 == "76561199177996326"
    assert credentials.source == "local_client_logs"


def test_split_local_login_token_reads_access_token_and_login_id():
    token, server_time, login_id = split_local_login_token("access-token_1783270143_76561199177996326")

    assert token == "access-token"
    assert server_time == "1783270143"
    assert login_id == "76561199177996326"


def test_credentials_can_be_read_from_local_login_bridge(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            token = encode_wmpvp_log_line("bridge-token_1783270143_76561199177996326")
            return f'{{"token":"{token}"}}'.encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == 2
        assert request.headers["Origin"] == "https://match.wmpvp.com"
        return FakeResponse()

    monkeypatch.setattr("app.services.perfectworld_demo_importer.urllib.request.urlopen", fake_urlopen)

    credentials = read_local_login_bridge_credentials()

    assert credentials.access_token == "bridge-token"
    assert credentials.login_steam64 == "76561199177996326"
    assert credentials.source == "local_client_login_bridge"


def test_decrypt_perfectworld_encoded_data():
    assert decrypt_perfectworld_data("123456", "FZG6ZGNA3gUOF9cYRsaTzg==") == "hello"


def test_sign_perfectworld_request_uses_bridge_payload(tmp_path, monkeypatch):
    bridge = tmp_path / "signer_bridge.js"
    bridge.write_text("// test bridge", encoding="utf-8")
    calls = []

    def fake_run(command, input, text, capture_output, check, timeout):
        calls.append(
            {
                "command": command,
                "input": input,
                "text": text,
                "capture_output": capture_output,
                "check": check,
                "timeout": timeout,
            }
        )

        class Completed:
            stdout = '{"signature":"signed-value"}'

        return Completed()

    monkeypatch.setattr("app.services.perfectworld_demo_importer.subprocess.run", fake_run)

    signature = sign_perfectworld_request(
        randnum="123456",
        timestamp="1783233171",
        data="access_token=a&cup_id=0&match_id=1",
        signer_bridge_path=bridge,
    )

    assert signature == "signed-value"
    assert calls[0]["command"] == ["node", str(bridge)]
    assert calls[0]["timeout"] == 3
    assert '"randnum": "123456"' in calls[0]["input"]
    assert '"data": "access_token=a&cup_id=0&match_id=1"' in calls[0]["input"]


def test_parse_signer_bridge_output_ignores_native_logs():
    output = 'game proxy started\n{"signature":"signed-value"}'

    assert parse_signer_bridge_output(output) == {"signature": "signed-value"}


def test_sign_perfectworld_request_requires_configured_bridge(tmp_path):
    try:
        sign_perfectworld_request(
            randnum="123456",
            timestamp="1783233171",
            data="match_id=1",
            signer_bridge_path=tmp_path / "missing.js",
        )
    except PerfectWorldSignerError:
        return

    raise AssertionError("missing signer bridge should fail")


def test_signed_url_uses_swap_data_signature(monkeypatch, tmp_path):
    bridge = tmp_path / "signer_bridge.js"
    bridge.write_text("// test bridge", encoding="utf-8")
    monkeypatch.setattr("app.services.perfectworld_demo_importer.random.randint", lambda _start, _end: 855385)
    monkeypatch.setattr("app.services.perfectworld_demo_importer.time.time", lambda: 1783233171)
    monkeypatch.setattr("app.services.perfectworld_demo_importer.sign_perfectworld_request", lambda **_: "sig")
    client = PerfectWorldClient(
        access_token="token",
        pwa_jt=None,
        login_steam64=None,
        signer_bridge_path=bridge,
    )

    url = client.signed_url(path="/match-api/demo", method="POST", data='{"access_token":"token","match_id":"1"}', query_params=None)

    assert url == "https://pwaweblogin.wmpvp.com/match-api/demo?a=20000&r=855385&s=sig&t=1783233171"
