# bilibili-summary
输入B站BV号，自动提取字幕或转写音频，辅助 Codex 生成视频概括。

这是作者全力依靠codex plus作出的skill 环境是MBA m5 16g macOSTahoe 26.4 如有报错希望大家在拜托自己的ai老师解决的同时也能与作者通信便于维护项目/笑

以下为codex老师自己撰写的readme请大家欣赏（）：
# bilibili-summary

给 Codex 一个 BV 号，获取视频信息、字幕或本地语音转写，再由助手生成概括、核心观点和时间线。演示类视频可下载画面并生成联系图，帮助助手理解无旁白部分。

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 和 [OpenAI Whisper](https://github.com/openai/whisper)。无需额外付费 API Key；Codex 本身的使用仍按所用账户或服务计费。

## 安装

需要 Python 3.10+、网络访问以及足够存放 PyTorch、Whisper 模型和临时媒体的磁盘空间。建议预留数 GB。以下为 macOS/Linux 示例：

```bash
# 下载本仓库后，进入包含 SKILL.md 的目录
python3 scripts/install.py
```

Windows 使用 `py -3 scripts/install.py`，安装后的解释器为 `.venv\Scripts\python.exe`。PyAV 负责音频解码，本脚本不要求系统安装 ffmpeg 命令；部分平台若没有匹配的 PyAV 预编译包，可能需要额外构建依赖。

如需 Codex 自动发现，将整个仓库放到 `$CODEX_HOME/skills/bilibili-summary`（未设置时使用 `~/.codex/skills/bilibili-summary`），再创建上述虚拟环境。重新加载技能或重启应用后，发送 BV 号和总结请求。脚本路径由技能目录确定，不依赖任何作者电脑路径。

## 使用

```bash
.venv/bin/python scripts/extract.py BV1fZUGYaEHx --output-dir ./work
# 适用于软件演示、地图、图表等依赖画面的内容
.venv/bin/python scripts/extract.py BV1fZUGYaEHx --output-dir ./work --frames
# 指定分P和自动语言识别
.venv/bin/python scripts/extract.py 'https://www.bilibili.com/video/BV1fZUGYaEHx/?p=1' --output-dir ./work --language auto
# 更高精度模型：首次下载更大，运行更慢
.venv/bin/python scripts/extract.py BV1fZUGYaEHx --output-dir ./work --model small --refresh
```

Windows 将 `.venv/bin/python` 替换为 `.venv\Scripts\python.exe`。

结果位于 `work/<BV号>/p<分P>/`：

- `evidence.json`：标题、作者、时长、简介、内容来源和逐段时间戳。
- `transcript.txt`：带时间戳的字幕或语音转写。
- `audio.*`：需要转写时下载的音频。
- `video.*`、`frames/`：启用 `--frames` 时生成的视频及抽样画面。

**命令行工具输出证据，不会单独生成 AI 总结。** Codex 技能会让助手阅读证据，再在聊天中总结。画面默认均匀抽取24个时间点，短暂画面可能漏过，细节需进一步检查。

## 模型与缓存

Whisper 默认使用 `base` 模型，首次调用时从上游下载，之后本地运行。默认模型缓存为 `~/.cache/bilibili-summary/models`。可设置 `BILIBILI_SUMMARY_CACHE`，或传入 `--model-dir`。`--model /path/to/base.pt` 可使用已下载的模型。Numba 的编译缓存也保存在工具缓存目录。

已成功生成的转写会复用；切换模型或语言会重建，`--refresh` 可主动重建。输出目录区分BV号和分P，避免误用其他视频音频。下载的文件和转写保存在本地，清理时可删除输出目录；删除模型缓存后，下次会重新下载。

## 限制与排错

- 字幕接口可能要求登录，脚本会转为音频识别；不自动读取登录状态。会员、地区或其他访问限制可能导致音频同样不可用。
- 下载失败时，先确认视频在当前网络可访问，并更新 yt-dlp：`.venv/bin/python -m pip install -U yt-dlp`。
- 模型下载失败时，可在可访问网络中预先下载，再用 `--model` 指定本地模型。
- `base` 中文转写可能错认专名、数字，也可能对音乐或静音产生误识别。应结合画面核对；可选更大模型改善质量。
- 长视频需要更多内存与处理时间；当前实现将完整音频解码到内存。
- 默认只处理指定的一P，未指定则第一P，不会自动总结整个合集。
- 仅处理有权访问的内容，遵守平台规则和内容使用权限。

## 验证

```bash
.venv/bin/python -m unittest discover -s tests -v
```

验证记录：在 macOS、Python 3.12 环境下，通用版使用 BV1fZUGYaEHx 和预先下载的 base 模型、音频，验证了在线元信息提取、字幕不可用时的本地转写、视频下载与24个时间点的画面抽样。单元测试验证了字幕读取、缓存复用、BV号与分P隔离、无效输入处理。首次模型下载与全新虚拟环境安装未在本次重复测试；Windows/Linux 尚未实际验证。

## 许可证

自写代码与技能说明采用 [MIT](LICENSE)。依赖和模型遵循各自的上游许可证，见 [THIRD_PARTY.md](THIRD_PARTY.md)。本仓库不分发视频、模型权重、账号凭据或依赖包。
