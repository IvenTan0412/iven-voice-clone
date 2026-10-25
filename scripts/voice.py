#!/usr/bin/env python3
"""Generate either saved voice and denoise locally by default."""
import argparse
import json
import os
import platform
import sys
from pathlib import Path

from common import ROOT, check_assets, profile, runtime_dir

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
ALIASES = {"male": "male", "男声": "male", "iven": "male", "female": "female", "女声": "female"}


def rms(x):
    import numpy as np
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64))))


def db(x):
    import math
    return 20 * math.log10(max(float(x), 1e-10))


def normalize(x):
    import numpy as np
    if not len(x) or not np.isfinite(x).all() or rms(x) < 1e-8:
        raise ValueError("模型没有生成有效音频")
    return x * min(10 ** (-22 / 20) / rms(x), 10 ** (-3 / 20) / max(abs(x)))


def denoise(x):
    import numpy as np
    from scipy.signal import resample_poly, correlate, correlation_lags
    from mlx_audio.sts.models.deepfilternet import DeepFilterNetModel
    model = DeepFilterNetModel.from_pretrained(str(runtime_dir() / "models/denoise"), subfolder=None)
    pad = 12000
    audio48 = np.pad(resample_poly(x, 2, 1), (pad, pad))
    enhanced = model.enhance_array(audio48)[pad:pad + len(x) * 2]
    y = resample_poly(enhanced, 1, 2)[:len(x)]
    # Match the filter's latency before comparing levels or saving.
    c = correlate(y, x, mode="full", method="fft")
    lags = correlation_lags(len(y), len(x))
    mask = abs(lags) <= 2400
    lag = int(lags[mask][np.argmax(c[mask])])
    if lag > 0:
        y = np.pad(y[lag:], (0, lag))
    elif lag < 0:
        y = np.pad(y, (-lag, 0))[:len(x)]
    n = len(x) // 480 * 480
    xf, yf = x[:n].reshape(-1, 480), y[:n].reshape(-1, 480)
    energy = np.sqrt(np.mean(xf ** 2, axis=1))
    active = energy > 10 ** (-32 / 20)
    if not active.any():
        raise ValueError("未检测到足够的人声，未交付降噪音频")
    y *= min(rms(xf[active]) / max(rms(yf[active]), 1e-10), 10 ** (-3 / 20) / max(float(abs(y).max()), 1e-10))
    yf = y[:n].reshape(-1, 480)
    quiet = (energy < 10 ** (-40 / 20)) & (energy > 10 ** (-65 / 20))
    return y.astype(np.float32), {
        "method": "DeepFilterNet3", "alignment_samples": lag,
        "active_level_change_db": db(rms(yf[active]) / rms(xf[active])),
        "low_energy_reduction_db": db(rms(xf[quiet]) / max(rms(yf[quiet]), 1e-10)) if quiet.any() else None,
        "note": "Low-energy reduction is a noise proxy, not a perceptual quality score.",
    }


def main():
    parser = argparse.ArgumentParser(description="男声 / 女声本地配音，默认自动降噪")
    parser.add_argument("text", nargs="?")
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--voice", choices=ALIASES)
    parser.add_argument("-o", "--out", type=Path)
    parser.add_argument("--no-denoise", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--list-voices", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.list_voices:
        for v in ("male", "female"):
            data, _ = profile(v)
            print(f"{v}: {data['label']}")
        return
    if args.check:
        check_assets(full=True)
        import mlx.core as mx
        mx.eval(mx.array([1.0]) * 2)
        print(json.dumps({"status": "ok", "platform": platform.platform(), "device": str(mx.default_device()), "voices": ["male", "female"], "models_verified": True}))
        return
    if not args.voice or not args.out:
        parser.error("请明确指定 --voice male/female 和 -o 输出.wav")
    if bool(args.text) == bool(args.text_file):
        parser.error("请提供文本或 --text-file，两者只能选择一个")
    text = args.text_file.read_text(encoding="utf-8").strip() if args.text_file else args.text.strip()
    if not text:
        parser.error("文本不能为空")
    out = args.out.expanduser().resolve()
    if out.suffix.lower() != ".wav":
        parser.error("输出文件须使用 .wav 扩展名")
    raw, meta = out.with_suffix(".raw.wav"), out.with_suffix(".json")
    for p in (out, raw, meta):
        if p.exists():
            parser.error(f"文件已存在，未覆盖：{p}")
    check_assets()
    voice = ALIASES[args.voice]
    data, ref = profile(voice)
    import numpy as np
    import soundfile as sf
    import mlx.core as mx
    from mlx_audio.tts.utils import load_model
    model = load_model(str(runtime_dir() / "models/tts"))
    mx.random.seed(args.seed)
    chunks = [np.asarray(r.audio).reshape(-1) for r in model.generate(
        text=text, ref_audio=str(ref), ref_text=data["reference_text"], lang_code="zh",
        temperature=data["temperature"], speed=1.0,
    )]
    if not chunks or model.sample_rate != 24000:
        raise ValueError("未生成预期的 24 kHz 音频")
    x = normalize(np.concatenate(chunks).astype(np.float32))
    out.parent.mkdir(parents=True, exist_ok=True)
    # Reserve names exclusively; raw output remains recoverable if enhancement fails.
    with raw.open("xb") as f:
        sf.write(f, x, 24000, format="WAV", subtype="PCM_16")
    del model
    mx.clear_cache()
    y, processing = (x.copy(), {"method": "none"}) if args.no_denoise else denoise(x)
    fade = min(120, len(y) // 4)
    y[:fade] *= np.linspace(0, 1, fade)
    y[-fade:] *= np.linspace(1, 0, fade)
    if len(y) != len(x) or not np.isfinite(y).all() or (abs(y) >= .999).any() or rms(y) < 1e-8:
        raise ValueError("输出音频检查未通过；原始合成保留在 .raw.wav")
    with out.open("xb") as f:
        sf.write(f, y, 24000, format="WAV", subtype="PCM_16")
    decoded, sr = sf.read(out)
    report = {
        "voice": voice, "label": data["label"], "text": text, "seed": args.seed,
        "temperature": data["temperature"], "denoised": not args.no_denoise,
        "sample_rate": sr, "channels": 1, "subtype": "PCM_16", "seconds": len(decoded) / sr,
        "clipped_samples": int((abs(decoded) >= .999).sum()), "peak_dbfs": db(abs(decoded).max()),
        "file": str(out), "raw_file": str(raw), "processing": processing,
        "subjective_quality": "pending_audition",
    }
    with meta.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"失败：{exc}", file=sys.stderr)
        sys.exit(1)
