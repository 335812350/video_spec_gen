---
name: movie-voice-tts
description: Use when a film commentary project needs Alibaba Cloud voice auditions, locked narration synthesis, or caption timing for an approved script.
---

# 影视解说配音

影视解说旁白统一使用仓库的阿里云 TTS 能力。音色选择服务于已确认的叙述视角，不能替代用户的声音与创意决定。

## 规则

1. 先读取 `../aliyun-tts/SKILL.md`，再读取项目状态和用户确认的文稿。
2. 使用 `python .agents/skills/aliyun-tts/scripts/aliyun_tts.py models` 和 `voices` 查询当前 Workspace 可用模型、音色和授权；不得猜测 voice ID。
3. 用户需要比较时，用相同文稿生成 8--15 秒试音，保存到新的 `projects/<project-slug>/generated/voiceover/auditions/` 路径。
4. 用户明确选定模型和音色后，才生成整篇旁白。输出写入新的版本目录，不覆盖历史音频或 manifest。
5. 文稿、专名读音或情绪要求变化时，回到文稿或用户确认，不静默修改采用稿。

## 时间戳与字幕

- 阿里云输出未提供可用时间信息时，优先复用 `npx hyperframes transcribe` 生成旁白的时间戳。中文转录必须显式指定语言或模型，完成后抽查专名、首尾边界和关键句。
- 旁白音频、转录结果和字幕属于项目产物，写入 `projects/<project-slug>/generated/voiceover/`。
- 片源对白字幕与旁白字幕分开处理；分析 JSON 中的对白摘录不能直接作为正式字幕。

## 交付

记录实际模型、voice、文稿路径、输出文件、转录或字幕路径与已知问题，但不得记录 API Key。用户确认后，总导演将 `VOICE_CONFIRMED` 或 `NARRATION_READY` 写入项目状态。
