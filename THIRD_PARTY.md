# Third-party components

本仓库仅分发自写脚本和说明，通过 pip 获取依赖，通过 Whisper 获取模型；以下不改变上游许可证。

| 组件 | 用途 | 上游许可证/说明 |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | B站元信息、字幕和媒体提取 | [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE)；独立可执行发行包可能包含其他许可组件，本项目使用 Python 包 |
| [OpenAI Whisper](https://github.com/openai/whisper) | 本地语音转写及模型下载 | [MIT](https://github.com/openai/whisper/blob/main/LICENSE) |
| [PyAV](https://github.com/PyAV-Org/PyAV) | 音视频解码和抽帧 | [上游许可证](https://github.com/PyAV-Org/PyAV/blob/main/LICENSE.txt)；使用的 FFmpeg 库和构建配置另受其许可证约束 |
| [Pillow](https://github.com/python-pillow/Pillow) | 画面联系图 | [上游许可证](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |

PyTorch、NumPy、Numba、tiktoken 等传递依赖遵循各自的上游许可证。视频和字幕的内容权利属于其权利人，不因工具采用 MIT 而改变。
