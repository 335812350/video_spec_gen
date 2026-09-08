# 使用说明

## 初始化

在空文件夹中用 Codex 打开后，说：

```text
把当前文件夹初始化成视频创作工作区
```

初始化后的目录：

```text
assets/       源影片输入边界，按 assets/<film-slug>/ 组织
projects/     独立交付项目，按 projects/<project-slug>/ 组织
outputs/      渲染输出，按 outputs/<project-slug>/ 组织并递增版本
.codex-tmp/   当前任务的临时文件，按 project-slug 分目录，任务结束后清理
video-spec.md 视频规格
setup.*       初始化脚本
doctor.*      环境检查脚本
```

## 环境检查

Windows：

```powershell
.\doctor.ps1
```

macOS/Linux：

```bash
./doctor.sh
```

## 素材

把源视频、音频、图片放入 `assets/<film-slug>/`；研究资料写入其 `references/` 子目录。

## 临时文件

临时文件写入 `.codex-tmp/<project-slug>/`，例如转写结果、音频分析、字幕缓存和下载缓存。

不要把用户原始素材、`video-spec.md`、HyperFrames 工程或最终视频写入这里。任务结束后清理该目录。

## 下一步

素材准备好后，对 Codex 说：

```text
根据 assets 里的素材生成 video-spec.md
```
