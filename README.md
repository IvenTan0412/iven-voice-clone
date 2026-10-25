# 男声 / 女声本地配音 Skill

同一个 Skill，按需求调用 **Iven 男声** 或 **已克隆的女声**，默认自动降噪。面向 macOS 14 或更新版本、原生运行的 M 系列 Mac，输出可用于剪辑的 24 kHz / 单声道 / PCM16 WAV。

## 在另一台 Mac 安装

登录有权访问此私有仓库的 GitHub 账号，选择 **Code → Download ZIP**，解压后在终端进入该目录，执行：

```bash
bash install.sh
```

也可以先克隆仓库，再运行同一条安装命令。首次安装会：

1. 准备 uv 和 Python 3.11.15（已安装 uv 时复用它）。
2. 在独立运行目录安装锁定版本的依赖，不复制旧电脑的虚拟环境。
3. 下载固定版本的 Qwen3-TTS 与 DeepFilterNet3 模型，检查每个文件的 SHA256。语音模型文件约 3.1 GB，需另留 Python 环境空间；下载时间取决于网络。
4. 校验两个音色，分别生成一段已经降噪的男声、女声测试音频。
5. 验证成功后安装 Skill。已有同名 Skill 会备份到运行目录，不丢弃旧版。

安装会打印 Skill 和测试音频的实际路径。回到 Codex 打开一个新对话，然后说：

> 使用 $iven-voice-clone，用女声朗读：“你好呀，很高兴见到你。”

> 使用 $iven-voice-clone，用男声读下面这段旁白，生成 WAV。

可以直接说“用女声配音”或“用 Iven 的声音朗读”；显式写出 Skill 名称更容易准确选择。

## 男声和女声分别是谁

| 选择 | 配置 | 参考素材 |
| --- | --- | --- |
| 男声 / Iven | `male` | 已使用的 Iven 男声参考片段 |
| 女声 | `female` | 本次“新录音 4”的女声参考片段 |

两个音色有独立参考 WAV、准确对应的参考文字和校验值，没有训练或下载两个专属大模型。它们共享一个通用合成模型。Skill 在无法确定音色时会询问，不默选。

## 不通过 Codex 也能调用

默认安装位置下：

```bash
bash "$HOME/.codex/skills/iven-voice-clone/scripts/run.sh" --voice female "你好呀，很高兴见到你。" -o "$HOME/Desktop/女声.wav"
bash "$HOME/.codex/skills/iven-voice-clone/scripts/run.sh" --voice male "今天想聊聊最近生活里的一些小事。" -o "$HOME/Desktop/男声.wav"
```

如果设置过 `CODEX_HOME`，请使用安装结果打印的实际 Skill 路径。

长文用 `--text-file 文案.txt` 代替直接输入文字。默认生成最终 `.wav`、原始 `.raw.wav` 和 `.json` 报告三个文件。已有文件不会覆盖。原始合成对照可使用 `--no-denoise`；另一采样版本可用 `--seed 43`。

## 本地文件与迁移

- Skill 默认安装到 `~/.codex/skills/iven-voice-clone`。
- 运行环境与模型默认放在 `~/.local/share/iven-voice-clone`。
- 仓库包含两个声音的参考资料，按私人音色资料管理，不公开仓库。
- 仓库不包含几 GB 的模型、虚拟环境、账号信息或历史输出。
- 安装完成后，生成和降噪离线运行，不需要 API Key，不上传录音。参考文字已经保存，日常配音不依赖转写模型。

如需省去另一台电脑重新下载模型，可把旧电脑的 `~/.local/share/iven-voice-clone/models` 文件夹复制到新电脑同一路径，然后执行安装。安装仍会校验模型并重建 Python 环境。

测试或自定义目录可在安装时设置 `VOICE_CLONE_HOME`（运行目录）和 `VOICE_CLONE_SKILL_DIR`（Skill 目录）；路径支持空格。安装后的 Skill 会记住对应运行目录。

## 检查与恢复

```bash
bash "$HOME/.codex/skills/iven-voice-clone/scripts/run.sh" --list-voices
bash "$HOME/.codex/skills/iven-voice-clone/scripts/run.sh" --check
```

模型或依赖缺失时重新运行 `install.sh`；下载可以恢复，完整模型不会重复下载。安装失败时不要把未完成状态视为可用。若 Metal GPU 被宿主沙箱阻止，需要允许该条本地命令访问 GPU。

若要回退，查看运行目录 `installation.json` 中的 `previous_skill_backup`。它指向上次安装的备份；不要直接删除当前目录中的新工作。

音色相似度与降噪听感以试听为准。输出报告证明音色选择、时长、格式和技术检查，不等于人工听审。旁白是否代表真实经历、是否发布，仍由使用者决定。

## 本版验证

2026-10-25，在 macOS 26.6.2 / Apple Silicon 上，用全新 Python 环境完成安装，37 个锁定依赖检查通过。验证目录包含空格，安装从其他工作目录启动；模型 SHA256 校验、缺失模型配置的下载恢复、男声与女声生成及默认降噪均通过。另验证了 28.8 秒女声长文，及不默选音色、不覆盖已有输出、损坏参考检测。尚未在第二台实体 Mac 上运行；首次安装会在目标电脑再次生成两种音色的测试音频。
