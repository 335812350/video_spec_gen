# 《年会不能停！》年会真相高能片段剪辑计划

## 交付定位

- 源影片 slug：`annual-meeting`
- 项目 slug：`annual-meeting-high-energy-90s`
- 用途：本地观看的年会高潮高能片段
- 成片：90.0s，16:9，24fps，有声
- 核心信息：年会现场，真相不能停
- 叙事承诺：年会表演失控，贪腐证据上屏，胡建林公开错调真相，并把话题落到“不要先裁掉诚实努力的人”。
- 处理边界：纯正片混剪，不加旁白、不使用外部 B-roll、不改变源片时间顺序。

## 素材依据

- 源视频：`assets/annual-meeting/media/年会不能停！.mp4`
- 剧情分析：`assets/annual-meeting/analysis/plot-segmentation.json`
- 镜头分析：`assets/annual-meeting/analysis/shot-refine.json`
- 选择记录：`assets/annual-meeting/analysis/high-energy-selection.json`
- BGM：`projects/annual-meeting-high-energy-90s/hyperframes/assets/office-groove-90s.wav`
- 字幕：沿用源视频内嵌字幕；不重新生成 SRT，不额外叠加重复字幕。

## 能量曲线

`舞台开唱（hook） → 职场 Rap 升级 → 贪腐视频上屏（爆点） → 庄正直失控 → Rap 释放 → 错调真相 → 反裁员发言（回收）`

全片保持源片顺序。BGM 只在对白和 Rap 的空隙托底：对白、证据视频、Rap 和胡建林发言时优先级最高，BGM duck 到不可抢词的音量。

## 选择记录

| 成片 | 源区间 | 时长 | 能量职责 | 组件 |
|---|---:|---:|---|---|
| 0.0–6.0 | 6015–6021 | 6s | 舞台开唱，3 秒内建立现场 | `aroll.subtitle-highlight` + `aroll.keyword-sticker` |
| 6.0–18.0 | 6056–6068 | 12s | “裁员/加班/五险一金”进入歌词 | `aroll.subtitle-highlight` |
| 18.0–38.0 | 6140–6160 | 20s | 贪腐供述上屏，核心爆点 | `broll-hero.pull-quote` + `aroll.subtitle-highlight` |
| 38.0–46.0 | 6180–6188 | 8s | 被曝光者失控，现场后果 | `aroll.subtitle-highlight` + `aroll.keyword-sticker` |
| 46.0–64.0 | 6241–6259 | 18s | 三人 Rap，情绪释放 | `aroll.subtitle-highlight` + `aroll.keyword-sticker` |
| 64.0–80.0 | 6387–6403 | 16s | 胡建林说出错调与沉默真相 | `aroll.subtitle-highlight` + `broll-hero.big-type` |
| 80.0–90.0 | 6486–6496 | 10s | 反对先裁人，价值回收 | `aroll.subtitle-highlight` + `broll-hero.pull-quote` |

## 声音与字幕

- 原片对白：完整保留，按源区间同步裁切。
- 原片环境声：完整保留；不做降噪式重塑，只在必要时做整体增益平衡。
- BGM：使用 `office-groove.wav`，循环或延长至 90 秒；无对白间隙目标音量约 0.16，人物说话/唱 Rap 时 duck 至约 0.04–0.06。
- 字幕：整句字幕常驻，关键词用 Maximalist Type 的大字号、重字重或 accent 色强调；每屏最多两行，避免盖住脸和大屏证据。
- 字幕处理：不把分析 JSON 或临时转录文件当作正式字幕；源视频内嵌字幕已经满足要求，直接沿用。
- 额外音效：不新增爆炸音效；仅允许极轻的转场低频或现场灯光切换声，不能盖原片。

## 画幅与视觉

- 画布：`1920×1080`，`24fps`，MP4，立体声。
- 源片：`1920×800`；使用上下黑边 letterbox，禁止 `object-fit: cover` 裁掉左右信息。
- 主题：`Maximalist Type`。
- accent：使用主题默认 accent；关键词可在“真相上屏 / 错调进来 / 诚实努力”处加重。
- 装饰密度：中等；仅使用大字、关键词贴纸、细线和一次短促文字撞击，不叠加图表、插画或 3D。
- 转场：以硬切为主；证据视频开始可用一次 2–3 帧白闪，结尾硬收在“说实话/谢谢”的原片停顿。

## 被舍弃候选

- `5951–6000`：高管《学猫叫》混乱，虽有能量但会分散“真相揭露”主线。
- `6508–6542`：董事长表态彻查，属于事后回收；90 秒版本优先保留胡建林完整价值发言。
- 片前错调、裁员计划和“优化涨薪”段：与本项目的年会现场单场景承诺不一致。

## 验收

- 选择文件通过 `high_energy_analyzer.py validate`，总时长 90.0s，所有区间在源片 7024.872s 内。
- 前 3 秒出现舞台人物和原片演唱 hook。
- 18–38s 的贪腐视频是可定位的主爆点；64–90s 完成真相与价值回收。
- 画面与独立原声音频的 `data-media-start`、时长和播放速率完全一致。
- 字幕逐句可读，关键词强调不遮脸；BGM 不盖对白、Rap 或发言。
