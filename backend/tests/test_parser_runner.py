import json
import stat

import pytest

from app.services.parser_runner import ParserRunError, run_parser


def test_run_parser_parses_structured_stderr(tmp_path):
    parser = tmp_path / "parser.cmd"
    parser.write_text(
        "@echo off\n"
        "echo {\"code\":\"TARGET_PLAYER_NOT_FOUND\",\"message\":\"missing\",\"players\":[]} 1>&2\n"
        "exit /b 2\n",
        encoding="utf-8",
    )
    parser.chmod(parser.stat().st_mode | stat.S_IEXEC)

    with pytest.raises(ParserRunError) as exc:
        run_parser(
            parser_bin=parser,
            demo_path=tmp_path / "demo.dem",
            steam64="7656119",
            map_name="de_dust2",
            map_config_path=tmp_path / "map.json",
            output_path=tmp_path / "out.json",
        )

    assert exc.value.detail["code"] == "TARGET_PLAYER_NOT_FOUND"


def test_run_parser_reports_missing_binary(tmp_path):
    with pytest.raises(ParserRunError) as exc:
        run_parser(
            parser_bin=tmp_path / "missing.exe",
            demo_path=tmp_path / "demo.dem",
            steam64="7656119",
            map_name="de_dust2",
            map_config_path=tmp_path / "map.json",
            output_path=tmp_path / "out.json",
        )

    assert exc.value.detail["code"] == "DEMO_PARSE_FAILED"

