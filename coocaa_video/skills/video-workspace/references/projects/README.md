# Projects

每个独立视频交付项目使用一个顶层 `project-slug` 目录，不要嵌套项目。

```text
projects/
├─ annual-meeting-high-energy-90s/
│  ├─ project.json
│  ├─ video-spec.md
│  ├─ edit-plan.md
│  └─ hyperframes/
└─ annual-meeting-commentary/
   └─ video-spec.md
```

## 规则

- `projects/<project-slug>/` 是项目工作目录，保存 spec、编辑计划和 HyperFrames 工程。
- `project.json` 使用 `source_film_slug` 关联 `assets/<film-slug>/`。
- 同一影片的不同视频类型、平台、时长或音频策略，使用新的 `project-slug`。
- 不要把用户源素材复制成新的输入边界。
