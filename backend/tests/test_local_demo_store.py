import json
import zipfile

from app.services.local_demo_store import list_local_demos, prepare_local_demo


def test_list_local_demos_reads_configured_directories(tmp_path):
    demo_dir = tmp_path / "demos"
    demo_dir.mkdir()
    demo_path = demo_dir / "match.dem"
    demo_path.write_bytes(b"demo")
    ignored = demo_dir / "notes.txt"
    ignored.write_text("ignore", encoding="utf-8")
    config = tmp_path / "local_demo_config.json"
    config.write_text(json.dumps({"demoDirectories": [str(demo_dir)]}), encoding="utf-8")

    demos = list_local_demos(config)

    assert [demo.name for demo in demos] == ["match.dem"]
    assert demos[0].kind == "dem"


def test_prepare_local_demo_extracts_dem_from_zip(tmp_path):
    demo_dir = tmp_path / "demos"
    demo_dir.mkdir()
    source_zip = demo_dir / "match.zip"
    with zipfile.ZipFile(source_zip, "w") as archive:
        archive.writestr("match.dem", b"demo-bytes")
    config = tmp_path / "local_demo_config.json"
    config.write_text(json.dumps({"demoDirectories": [str(demo_dir)]}), encoding="utf-8")
    upload_path = tmp_path / "upload.dem"

    prepare_local_demo(source_zip, config, upload_path)

    assert upload_path.read_bytes() == b"demo-bytes"
