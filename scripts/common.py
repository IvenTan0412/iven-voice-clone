"""Small shared paths and integrity checks for this skill."""
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def runtime_dir():
    value = os.environ.get("VOICE_CLONE_HOME")
    if not value and (ROOT / ".runtime-path").exists():
        value = (ROOT / ".runtime-path").read_text().strip()
    return Path(value or Path.home() / ".local/share/iven-voice-clone").expanduser().resolve()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def profile(voice):
    data = read_json(ROOT / "voices" / voice / "profile.json")
    ref = ROOT / "voices" / voice / "reference.wav"
    if not ref.is_file() or digest(ref) != data["reference_sha256"]:
        raise ValueError(f"音色参考缺失或已改变：{ref}")
    return data, ref


def check_assets(full=False):
    for voice in ("male", "female"):
        profile(voice)
    for name, model in read_json(ROOT / "models.json").items():
        for entry in model["files"]:
            p = runtime_dir() / "models" / name / entry["local_path"]
            if not p.is_file() or p.stat().st_size != entry["size"]:
                raise ValueError(f"模型文件缺失或不完整：{p}；请重新运行 install.sh")
            if full and digest(p) != entry["sha256"]:
                raise ValueError(f"模型校验失败：{p}；请移走损坏文件后重新安装")
