import os
import tempfile
from pathlib import Path
from astpack.packer import pack_repository


def test_pack_repository():
    sample_dir = Path(__file__).parent / "sample_code"

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        out_path = tmp.name

    try:
        res = pack_repository(
            target_dir=str(sample_dir),
            output_path=out_path,
            prune_mode="stubs",
        )

        assert res["files_count"] >= 1
        assert res["saved_tokens"] >= 0
        assert os.path.exists(out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# Repository Context Pack" in content
        assert "Semantic Compression Report" in content
        assert "Project Structure" in content
        assert "```python" in content
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)
