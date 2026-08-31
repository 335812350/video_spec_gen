---
name: project-layout
description: 多影片项目中的输入、工作文件和渲染输出边界。
---

# 多影片项目布局

## 目录职责

仓库根目录是影片集合，不是一部影片的工作目录。每部影片使用稳定的
`<film-slug>`，建议使用小写 kebab-case。

```text
assets/<film-slug>/       # 用户输入素材 + references/影片资料
projects/<film-slug>/     # 可编辑的计划、spec、HyperFrames 工程
outputs/<film-slug>/      # 可观看的视频版本
```

- `assets` 承载用户提供的输入素材，以及本 skill 在 `references/` 下生成的影片资料、来源记录和内容语境；
  agent 可以写入这些 reference 文档，但不生成或覆盖 spec、HTML 或渲染视频，也不覆盖用户原始素材。
- `assets/<film-slug>/analysis/` 可存放用户已有或由本地片源推导的分析结果；分析文件必须标明时间码依据和不完整覆盖，不能把外部剧情资料伪装成镜头事实。
- `projects` 是工作真相。`video-spec.md` 和后续的 `edit-plan.md` 都放这里；若渲染器要求工程内媒体路径，可以在这里暂存素材副本，但源文件仍以 `assets/<film-slug>/` 为准。
- `outputs` 只放渲染得到的视频：`render-v001.mp4`、`render-v002.mp4`……
- 每个版本都是可观看的视频；不再区分“预览文件”和“最终文件”，也不建立额外的 final/publish 层。
- 不建立 `final` 或 `publish` 子目录。用户自行选择要使用的版本。

## 影片解析

1. 优先使用用户给出的片名、slug 或路径确定影片。
2. 没有明确指向时，只列出 `projects/` 下的候选 slug 并询问。
3. 确定影片后，只读取对应的 `assets/<film-slug>/` 和
   `projects/<film-slug>/`，不能递归扫描整个仓库寻找“最像”的 spec。
4. 根目录已有的 `video-spec.md` 是 legacy 文件：可以读取，但不能作为新片默认输出位置。
5. 现有 `videos/<film-slug>/` 是 legacy HyperFrames 工程；只有用户明确给出其路径时才读取。

## 版本规则

- 每次渲染都生成一个新版本，使用三位数字递增。
- 不覆盖既有版本，也不把某个版本标记为系统意义上的“最终版”。
- 影片内容发生修改时，从当前最大编号继续递增；仅重新运行同一版本不应覆盖原文件。

## 主题文件

主题文件属于目标影片的工作目录。根据当前 HyperFrames 契约，按其实际解析顺序处理
`frame.md`、`design.md`、`DESIGN.md`；不要在仓库根目录创建共享主题文件。

## 素材路径

规格中的素材先写权威来源 `assets/<film-slug>/...`。进入 HyperFrames 工程时，若运行环境不能读取仓库外层路径，再把所需文件暂存到
`projects/<film-slug>/assets/`，并保持文件名和来源可追溯；暂存副本不是新的素材来源。
