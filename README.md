# Claude Code 配置中文对照

把官方 Claude Code 配置字段翻成中文，方便在 iPhone Safari 上查阅。

**在线地址：** [https://alexcz-a11y.github.io/claude-code-settings-zh/](https://alexcz-a11y.github.io/claude-code-settings-zh/)

第一次打开前，仓库主人需要在 GitHub 打开 Pages（云端 token 没有仓库管理权限，无法代开）：

1. 打开 [Settings → Pages](https://github.com/alexcz-a11y/claude-code-settings-zh/settings/pages)
2. **最快：** Build and deployment → Source 选 **Deploy from a branch**，Branch 选 `main`，文件夹选 `/ (root)`
3. **或：** Source 选 **GitHub Actions**，然后重新跑 `.github/workflows/pages.yml`

静态文件已经在 `main` 根目录。iPhone Safari 打开上面的地址即可。

这不是配置生成器，也不收录任何人的真实配置。页面只对照官方文档里的键名、类型、默认值和允许值。

## 这页是什么

Claude Code 有两套容易混在一起的文件：

1. **`settings.json` 作用域**
   - 用户：`~/.claude/settings.json`
   - 项目共享：`.claude/settings.json`
   - 项目本地：`.claude/settings.local.json`
   - 托管：`managed-settings.json` / MDM / claude.ai 控制台
2. **`~/.claude.json`（全局配置）**  
   官方写明由 Claude Code 自己写：登录会话、MCP 服务器、每个项目的信任状态，以及 `/config` 写入的一小撮全局键。  
   **不要把密钥、OAuth token 或真实文件内容贴到这里。**

每个官方 All settings 索引中的键都有一张卡片：英文键名、中文名称与一句含义、类型、允许值 / 枚举（保持官方字符串）、默认值、作用范围、数字含义（若官方写了单位或上下限），以及指向官方章节的链接。

## 在 iPhone 上打开

1. 用 Safari 打开 [https://alexcz-a11y.github.io/claude-code-settings-zh/](https://alexcz-a11y.github.io/claude-code-settings-zh/)
2. 顶部搜索可按键名或中文过滤
3. 用分段控件切换 `settings.json`、`~/.claude.json`、优先级

页面按手机优先排版：系统字体、大字号、安全区、卡片布局。不会用宽表格把屏幕撑出横向滚动。

## 优先级（高 → 低）

托管设置 → `--settings` / 命令行 → `.claude/settings.local.json` → 项目 `.claude/settings.json` → 用户 `~/.claude/settings.json`。

列表键通常合并。官方点名 **`fallbackModel`** 和 **`modelPicker`** 不合并。

## 官方来源

抓取日期：2026-08-26。字段以当时的官方页面为准，不猜测未写明的枚举。

- [settings-reference](https://code.claude.com/docs/en/settings-reference)
- [settings](https://code.claude.com/docs/en/settings)
- [settings-example](https://code.claude.com/docs/en/settings-example)
- [claude-directory](https://code.claude.com/docs/en/claude-directory)
- [permissions](https://code.claude.com/docs/en/permissions)
- [permission-modes](https://code.claude.com/docs/en/permission-modes)
- [JSON Schema](https://json.schemastore.org/claude-code-settings.json)

相关：[data-usage](https://code.claude.com/docs/en/data-usage) · [context-window](https://code.claude.com/docs/en/context-window) · [prompt-caching](https://code.claude.com/docs/en/prompt-caching) · [sandboxing](https://code.claude.com/docs/en/sandboxing) · [model-config](https://code.claude.com/docs/en/model-config) · [managed-settings](https://code.claude.com/docs/en/managed-settings)

JSON Schema 可能落后于 CLI。Schema 里有、但官方 All settings 索引没有的键，页面会标成「未在官方文档写明」。

## 本地预览

这是静态站点。仓库根目录有 `index.html`。可用任意静态服务器打开，例如：

```bash
python3 -m http.server 8080
```

然后访问 `http://127.0.0.1:8080/`。

重新从已下载的官方文档生成数据：

```bash
python3 tools/build.py
```

## GitHub Pages

站点从 `main` 分支根目录发布。工作流见 `.github/workflows/pages.yml`。
