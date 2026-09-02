---
name: project-layout
description: 多影片、多视频项目中的输入、工作文件和渲染输出边界。
---

# 多影片、多视频项目布局

## 核心概念

仓库同时管理源影片素材和多个视频交付项目，二者不是同一层级：

- film-slug：源影片身份，建议使用小写 kebab-case，例如 annual-meeting。
- project-slug：独立视频交付身份，建议使用“影片-类型-时长”或“影片-用途”命名，例如 annual-meeting-high-energy-90s。
- project_slug：项目清单中的独立视频交付身份，与项目目录名和 `id` 保持一致。
- workflow_id：调度层选择的主生产工作流身份，例如 generic-video 或 film-material；独立类型工作流由对应 Skill 自行维护。
- workflow_version：该生产工作流的版本标记，随工作流规则发生不兼容变化时递增。
- variant_id：同一项目批次中的候选、风格尝试或实验编号；它记录生产关系，不默认创建新的目录层级。

同一源影片的不同视频类型、平台、时长、旁白策略或剪辑目标，属于不同的 project-slug。只有同一交付目标的微调，才继续使用现有项目的 run/version。

## 目录职责

目录约定：

    assets/<film-slug>/       # 源影片输入素材、字幕、分析和 references
    projects/<project-slug>/  # 一个独立视频交付项目的 spec、工程和运行记录
    outputs/<project-slug>/   # 该视频项目的可观看渲染版本

共享源素材的示例：

    assets/annual-meeting/

    projects/annual-meeting/
    projects/annual-meeting-high-energy-90s/
    projects/annual-meeting-commentary/

    outputs/annual-meeting/
    outputs/annual-meeting-high-energy-90s/
    outputs/annual-meeting-commentary/

- assets/<film-slug>/ 承载用户提供的源视频、音频、字幕、图形、分析结果和 references/ 影片资料；不能写入 spec、项目工程、预览或渲染结果。
- projects/<project-slug>/ 是一个独立交付项目的工作真相，至少包含 video-spec.md，通常还包括 edit-plan.md、project.json、storyboard 和 HyperFrames 工程。
- outputs/<project-slug>/ 只放该视频项目的渲染版本：render-v001.mp4、render-v002.mp4……不覆盖历史版本。
- 项目通过 project.json.source_film_slug 关联 assets/<film-slug>/；不要复制源素材来制造新的影片输入边界。
- 新项目不能嵌套在另一个项目目录下。候选变体使用 variant_id、批次或 run 记录表达。

## 兼容说明

原先的 `projects/annual-meeting/high-energy-90s/` 已按本约定整理为顶层项目 `projects/annual-meeting-high-energy-90s/`；迁移保留原有文件，并同步修正项目 manifest、转录脚本源片路径、剪辑计划和 BGM 引用。

## 项目解析

1. 优先使用用户明确给出的 project-slug、项目路径、影片名和视频类型确定目标。
2. 如果用户只给出影片名，先确定 film-slug，再根据视频类型、平台、时长和用途解析已有 project-slug。
3. 如果已有项目的交付目标一致，进入迭代模式，修改该项目的 video-spec.md。
4. 如果同一影片的交付目标不同，创建新的顶层 projects/<project-slug>/，即使 assets/<film-slug>/ 已存在。
5. 不要递归扫描整个仓库寻找“最像”的 spec；只读取选定项目及其明确引用的源影片素材。
6. 根目录旧 video-spec.md 和 videos/<film-slug>/ 只作为 legacy 输入，除非用户明确指定，不作为新项目默认位置。

## 项目清单字段

新建项目的 project.json 至少应能表达：

    {
      "schema_version": 1,
      "id": "annual-meeting-high-energy-90s",
      "project_slug": "annual-meeting-high-energy-90s",
      "title": "年会不能停！年会真相高能片段",
      "source_film_slug": "annual-meeting",
      "workflow_id": "high-energy-clip",
      "workflow_version": "1",
      "video_type": "high-energy-clip",
      "production_mode": "asset-led",
      "variant_id": null
    }

source_film_slug 是素材来源关联；id/目录名是视频项目身份；variant_id 为空时表示这是独立交付项目而非候选记录。

## 版本规则

- 每次渲染都生成一个新版本，使用三位数字递增。
- 不覆盖既有版本，也不把某个版本标记为系统意义上的“最终版”。
- 内容发生修改时，从当前最大编号继续递增；仅重新运行同一版本不应覆盖原文件。
- 不建立 final 或 publish 子目录，用户自行选择要使用的版本。

## 主题与素材路径

- 主题文件属于 projects/<project-slug>/ 的工作目录；按 HyperFrames 契约处理 frame.md、design.md、DESIGN.md。
- 规格中的素材先写权威来源 assets/<film-slug>/...。
- 如果 HyperFrames 运行环境必须使用项目内路径，再把所需文件暂存到 projects/<project-slug>/assets/，并保持来源可追溯；暂存副本不是新的素材来源。
