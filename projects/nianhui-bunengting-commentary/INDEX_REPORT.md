# 《年会不能停！》素材索引报告

## 索引结论

新项目只消费用户指定的正片与两份普通剧情分析，不使用旧项目 annual-meeting-commentary，也不使用任何 high-energy 开头的 JSON。索引覆盖足以进入第三人称解说草案阶段；关键反转、贪腐链和结局仍以带声音的连续原片复核。

## 可用输入

| 类型 | 路径 | 覆盖/状态 |
| --- | --- | --- |
| 权威正片 | assets/annual-meeting/media/年会不能停！.mp4 | 7024.872472 秒；1920×800；24fps |
| 剧情分段 | assets/annual-meeting/analysis/plot-segmentation.json | 155 条剧情段，113–6960 秒 |
| 镜头细化 | assets/annual-meeting/analysis/shot-refine.json | 154 条剧情段，1881 个嵌套镜头，174–7024 秒 |
| 影片资料 | assets/annual-meeting/references/ | 本地事实卡、故事上下文和媒体清单 |

明确排除：assets/annual-meeting/analysis/high-energy-candidates-exploration.json、high-energy-selection.json、high-energy-selection-rap-full.json，以及 projects/annual-meeting-commentary/ 的全部项目文件。

## 技术与字幕

- 源片时长由 ffprobe 测得为 7024.872472 秒，约 117 分 04.9 秒。
- 源片画面为 1920×800、24fps，输出建议 1920×1080、30fps，使用 contain 保留原始宽银幕画面。
- 当前未发现独立 SRT/ASS/VTT；JSON 中 dialogue 仅为对白摘录，不能直接作为正式字幕。
- 旁白字幕应在用户确认音色并生成阿里云旁白后，再从旁白音频转录或由句级时间轴生成。

## 主要剧情覆盖

1. 共同记忆与工厂年会：113–240 秒。
2. 错调源头：392–812 秒，重点是庄正直运作调职、皮特误读报名材料。
3. 裁员计划与总部错位：813–3440 秒，含广进计划、胡建林入职、员工恐慌和连升三级。
4. 工厂危机与真相调查：3537–5367 秒，含工厂关闭、假零件、行贿链、马杰坦白和证据准备。
5. 年会高潮与公开发声：5521–6507 秒，含赶场、检举视频、Rap、错调真相和反裁员发言。
6. 处理与人物结局：6508–6960 秒，含董事长承诺、马杰升职、胡建林回厂、潘怡然追梦及片尾集体舞蹈。

## 下一阶段

索引阶段完成，可进入新项目的文稿确认。正式镜头计划应以本报告和草案为入口，不读取旧项目的 edit-plan、旁白、音乐或 HyperFrames 工程。
