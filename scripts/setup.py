"""Download pinned models, verify both voices, then install the skill."""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from common import ROOT, digest, read_json

FILES = ("SKILL.md", "README.md", "THIRD_PARTY.md", "install.sh", "requirements.in", "requirements.lock", "models.json")
DIRECTORIES = ("agents", "scripts", "voices")


def install(runtime, target):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("需要原生 arm64 的 M 系列 Mac")
    os.environ["VOICE_CLONE_HOME"] = str(runtime)
    from huggingface_hub import hf_hub_download
    for name, model in read_json(ROOT / "models.json").items():
        model_dir = runtime / "models" / name
        for entry in model["files"]:
            dest = model_dir / entry["local_path"]
            if dest.is_file() and dest.stat().st_size == entry["size"] and digest(dest) == entry["sha256"]:
                continue
            print(f"下载 / 校验：{name}/{entry['local_path']}", flush=True)
            downloaded = Path(hf_hub_download(
                repo_id=model["repo"], revision=model["revision"], filename=entry["remote_path"],
                local_dir=str(model_dir), force_download=dest.exists(),
            ))
            if downloaded.stat().st_size != entry["size"] or digest(downloaded) != entry["sha256"]:
                raise RuntimeError(f"模型校验失败：{downloaded}")
            if downloaded != dest:
                dest.parent.mkdir(parents=True, exist_ok=True)
                downloaded.replace(dest)
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    stage = Path(tempfile.mkdtemp(prefix=".voice-skill-stage-", dir=runtime))
    try:
        for name in FILES:
            shutil.copy2(ROOT / name, stage / name)
        for name in DIRECTORIES:
            shutil.copytree(ROOT / name, stage / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (stage / ".runtime-path").write_text(str(runtime) + "\n")
        python = runtime / ".venv/bin/python"
        subprocess.run([str(python), str(stage / "scripts/voice.py"), "--check"], check=True)
        samples = runtime / "checks" / stamp
        samples.mkdir(parents=True)
        for voice in ("male", "female"):
            subprocess.run([
                str(python), str(stage / "scripts/voice.py"), "--voice", voice,
                "你好，这是一段安装测试。今天的生活，简单又开心。", "-o", str(samples / f"{voice}.wav"),
            ], check=True)
            report = read_json(samples / f"{voice}.json")
            if report["voice"] != voice or not report["denoised"] or report["seconds"] <= 1 or report["clipped_samples"]:
                raise RuntimeError(f"{voice} 安装样音检查失败")
        # Keep previous installations outside the skill discovery directory.
        backup = None
        if target.exists() or target.is_symlink():
            old_skill = target / "SKILL.md"
            if target.is_symlink() or not old_skill.is_file() or "name: iven-voice-clone" not in old_skill.read_text():
                raise RuntimeError(f"目标已有不明内容，未覆盖：{target}")
            backup = runtime / "backups" / stamp
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(backup))
        try:
            shutil.move(str(stage), str(target))
        except Exception:
            if backup is not None and not target.exists():
                shutil.move(str(backup), str(target))
            raise
        result = {"status": "installed", "skill_dir": str(target), "runtime_dir": str(runtime), "sample_dir": str(samples), "previous_skill_backup": str(backup) if backup else None}
        (runtime / "installation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("安装成功。回到 Codex 后打开新对话即可使用 $iven-voice-clone。")
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--skill-dir", type=Path, required=True)
    args = ap.parse_args()
    install(args.runtime.expanduser().resolve(), args.skill_dir.expanduser().resolve())
