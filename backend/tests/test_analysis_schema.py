from app.models.analysis_result import AnalysisResult


def test_analysis_result_schema_accepts_standard_empty_result():
    result = AnalysisResult.model_validate(
        {
            "meta": {
                "demoFile": "example.dem",
                "game": "CS2",
                "map": "de_dust2",
                "targetSteam64": "7656119",
                "targetName": None,
                "windowSeconds": 30,
                "tickRate": 64,
                "parser": {"name": "demoinfocs-golang", "version": "v5"},
            },
            "summary": {
                "totalRounds": 0,
                "validRounds": 0,
                "tRounds": 0,
                "ctRounds": 0,
                "grenades": {
                    "smoke": 0,
                    "flash": 0,
                    "he": 0,
                    "molotov": 0,
                    "incendiary": 0,
                    "unknown": 0,
                },
            },
            "players": [],
            "rounds": [],
        }
    )

    assert result.meta.map == "de_dust2"

