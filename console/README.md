# Video Project Console

本地优先的视频工程控制台。项目状态使用 `assets/`、`projects/`、`outputs/` 下的文件保存，不使用数据库。

## 启动

```powershell
cd console
npm install
npm run build
$env:CODEX_RUNNER_MODE = "mock" # 可选：先用模拟任务验证界面
npm start
```

打开 <http://127.0.0.1:3040>。

真实 Codex 运行时，清除 `CODEX_RUNNER_MODE`，并确保 `codex`/`codex.cmd` 已在 PATH 中。可通过 `VIDEO_CONSOLE_WORKSPACE` 指定仓库根目录；默认使用当前仓库根目录。

## Electron 桌面壳

先构建前端，再安装 Electron 后运行：

```powershell
npm run build
npm install
npm run electron
```

Electron 只负责启动同一个本地 API 并加载同一个 `frontend/dist`，不会产生第二套业务逻辑。

## 开发

```powershell
cd console/frontend
npm run dev
```

开发服务默认在 `http://127.0.0.1:5173`，API 代理到 `127.0.0.1:3040`。后端可另开终端运行 `cd console; npm run start`。

## 验证

```powershell
cd console
npm test
npm run build
```

`CODEX_RUNNER_MODE=mock` 会生成分析、分镜、spec、构建和检查阶段事件，用于不调用模型的 UI 冒烟测试。
