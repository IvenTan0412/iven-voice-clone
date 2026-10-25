# 上游组件与模型

本仓库只携带运行脚本和经用户要求同步到私有仓库的两段参考录音；模型由安装程序从公开上游下载。

- Qwen3-TTS：[官方项目](https://github.com/QwenLM/Qwen3-TTS)，Apache-2.0。
- MLX 8-bit 模型：[mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit)，模型卡标注 Apache-2.0。
- MLX Audio：[项目](https://github.com/Blaizzy/mlx-audio)，依赖锁文件固定本次验证的版本。
- DeepFilterNet：[原项目](https://github.com/Rikorose/DeepFilterNet)；下载 [MLX 权重的 v3 子目录](https://huggingface.co/mlx-community/DeepFilterNet-mlx/tree/main/v3)。
- uv：[安装说明](https://docs.astral.sh/uv/getting-started/installation/)。

下载版本、实际文件大小及 SHA256 均记录在 `models.json`。参考录音仅供本私有套件调用，不因代码上传而转为公开素材。
