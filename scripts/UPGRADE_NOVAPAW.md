# NovaPaw 升级流程

每次 QwenPaw 发布新版本时执行。

> **本文件保护**：升级时请先把本文件复制到临时位置（如 `/tmp/UPGRADE_NOVAPAW.md`），
> 或从 git main 分支恢复（`git checkout main -- scripts/UPGRADE_NOVAPAW.md`）。
> NovaPaw 目录在升级中会被整体替换，目录内的文件会丢失。

## Phase 1: QwenPaw & 归档

```bash
# 1. 更新 QwenPaw
git -C C:\LingLong\Dev\Development\QwenPaw fetch --tags
git -C C:\LingLong\Dev\Development\QwenPaw checkout <version>

# 2. 归档 NovaPaw → git old 分支
git -C C:\LingLong\Dev\Development\NovaPaw add -A
git -C C:\LingLong\Dev\Development\NovaPaw commit -m "NovaPaw archive before <version>"
git -C C:\LingLong\Dev\Development\NovaPaw push origin master:old --force

# 3. 停服 + 改名（如 mv 失败用 cmd.exe ren）
```

## Phase 2: 基础 NovaPaw

```bash
mkdir -p NovaPaw
cp -r QwenPaw/src NovaPaw/
cp -r QwenPaw/console NovaPaw/
cp -r QwenPaw/packages NovaPaw/          # v2.2.0+ 新增：内联包
cp QwenPaw/{pyproject.toml,setup.py,LICENSE} NovaPaw/
cp QwenPaw/README*.md NovaPaw/ 2>/dev/null

# 改名脚本（注意：先确认 python 可用；用旧 env 的 python.exe）
cp rename_qwenpaw_to_novapaw.py NovaPaw/
printf "a\ne\nyes\ny\ny\ny\n" | python NovaPaw/rename_qwenpaw_to_novapaw.py
rm NovaPaw/rename_novapaw_to_novapaw.py

# packages/ 内的包也要改名（v2.2.0+）
# qwenpawmail-mcp → novapawmail-mcp：目录名、pyproject.toml、src/ 下模块目录、所有源码内 qwenpaw→novapaw 引用

# Git 初始化
git -C NovaPaw init && git -C NovaPaw config user.email "..." && git -C NovaPaw config user.name "NovaPaw"
git -C NovaPaw add -A && git -C NovaPaw commit -m "NovaPaw <version> base"
git -C NovaPaw push -f origin master:main
```

## Phase 3: 从 old 分支恢复定制文件

```bash
mkdir /tmp/r && cd /tmp/r
git init -q && git remote add origin https://github.com/llldxpt/NovaPaw.git
git fetch origin old --depth 1 -q
git checkout FETCH_HEAD -- \
  src/novapaw/agents/tools/search_web.py \
  src/novapaw/agents/tools/text_to_speech.py \
  src/novapaw/app/routers/embeddings.py \
  console/src/api/modules/embedding.ts \
  "console/src/pages/Settings/Embeddings/" \
  console/public/logo-dark.png console/public/logo-light.png \
  start.py init_project.py \
  scripts/UPGRADE_NOVAPAW.md
```

**注意**：`builtinRoutes.tsx` / `builtinMenu.ts` / `Header.tsx` **不要**整体从 old 复制！
（v2.2.0 有结构变化，如 `/workspace`→`/files`、新增 marketplace/checkpoints 等）
应在新版文件上**精确添加** Embeddings 路由/菜单项 + 修改 Header 的 logo 引用。

## Phase 4: 新版文件的精确修改

### 4.1 start.py / init_project.py
`"env" / "Scripts"` → `"env"`（嵌入式 Python）

### 4.2 tools（v2.2.0+ 自动注册）
- 工具加 `@tool_descriptor(...)` 装饰器（含 ui_description/ui_icon）
- **必须**带 governance 参数，否则 startup 报 "Governance gap"：
  ```python
  @tool_descriptor(
      tool_type="network", target_param="query",
      policy_name="SearxngSearch", default_policy="allow",
      policy_reason="...", ui_description="...", ui_icon="🔎",
  )
  ```
- `tools/__init__.py` 加 import 即可（`__all__` 自动生成）；config.py 的
  `_default_builtin_tools()` 也从 descriptor 自动收集，无需手动加条目

### 4.3 config.py / routers/__init__.py
- `from .embeddings import router as embeddings_router` + `router.include_router(...)`

### 4.4 provider_catalog.py（v2.2.0+ providers 移到这里）
- 删除 `PROVIDER_NOVAPAW`（novapaw-local）
- 添加 4 个 Nova AI 供应商：`nova-ai`(本地,1234)、`nova-ai-cluster`(集群,15050)、
  `nova-ai-api`(API)、`nova-ai-token-plan`(Token Plan)——后两个 base_url 均为
  `https://api.firstarpc.com/v1`，`require_api_key=True`
- 更新 `BUILTIN_PROVIDERS` 元组和 `__all__`
- `provider_discovery_policy.py` 同步加 policy（否则 KeyError）
- `provider_manager.py`：`get_provider("novapaw-local")` 加 None 检查

### 4.5 Frontend
| 文件 | 操作 |
|------|------|
| `i18n.ts` | `"en"` → `"zh"` |
| `pyproject.toml` | 删除重复的 novapaw script 入口 |
| `vite.config.ts` | 删除 markdown-vendor 分块（Object.defineProperty 错误根因）|
| `api/index.ts` | 添加 embeddingApi import + spread |
| `tsconfig.app.json` | `"strict": true` → `false`（移除 noUnusedLocals/Parameters）|
| `package.json` | build 简化为 `vite build && npm run precompress` |
| `Login/index.tsx` | logo `.svg` → `.png` |
| `Header.tsx` | logo 引用改 .png；禁用 web PyPI 更新检查 |
| `locales/*.json` | nav.embeddings + embeddings 完整翻译（28键），**用 Python json 库修改** |
| `builtinRoutes.tsx` | 精确加 `core.embeddings` 路由 |
| `builtinMenu.ts` | 精确加 embeddings 菜单项（order 85）|

## Phase 5: 构建 & 部署 env

```bash
cd console && npm install && npm run build && cd ..

# 部署到 env（直接复制，不用 pip install -e！）
rm -rf env/Lib/site-packages/novapaw
cp -r src/novapaw env/Lib/site-packages/novapaw
mkdir -p env/Lib/site-packages/novapaw/console
cp -r console/dist/* env/Lib/site-packages/novapaw/console/

# qwenpaw 兼容别名（__getattr__ 懒重定向）
# env/Lib/site-packages/qwenpaw/__init__.py

# novapawmail_mcp（v2.2.0+）：**必须直接复制，不要 pip install -e！**
rm -f env/Lib/site-packages/_editable_impl_*.pth
cp -r packages/novapawmail-mcp/src/novapawmail_mcp env/Lib/site-packages/

# 关键依赖对齐（对照 pyproject.toml 主依赖列表逐一核对 == 精确约束）
# 常见必须检查：agentscope、reme-ai、reme-auto-fin、reme-daily-paper
env/python.exe -m pip check   # 应输出 "No broken requirements found."
```

## Phase 6: 验证 & 发行版

```bash
env/python.exe start.py --host 127.0.0.1 --port 8088
curl http://127.0.0.1:8088/api/version   # 确认版本号
curl http://127.0.0.1:8088/              # 前端 200
```

发行版 = 复制 NovaPaw 的 src/console/packages/pyproject/setup/LICENSE/start/init + env，
修复 env（同上），删除 node_modules。

## 关键教训

1. **绝不 `pip install -e` 进要分发的 env**——editable 的 .pth 写死开发机绝对路径，
   用户复制到别的电脑后 `ModuleNotFoundError`。novapaw、novapawmail_mcp 都踩过这个坑。
   统一做法：直接复制包到 site-packages。
2. **不从 old 复制源码覆盖新版**——在**新版**上精确编辑（v2.2.0 的 routes/Header 结构变化大）。
3. **JSON 用 Python 改**，不用 sed。
4. **git 用 `git -C <绝对路径>`**，避免 CWD 漂移；git init 前确认在项目根目录。
5. **升级后必须逐项核对 pyproject.toml 依赖版本**（== 约束的），本次 agentscope 2.0.4→2.0.7.post1、
   reme-ai 0.4.1.0→0.4.1.10、reme 插件缺失都是这么发现的。
6. **v2.2.0 工具须带 governance 参数**，否则启动报 Governance gap。
7. **`Object.defineProperty` 前端错误** = vite markdown-vendor 分块未删。
8. **嵌入式 Python** 用 `env/python.exe`（非 Scripts/）；本文件自身在升级中会丢，
   记得从 git 恢复。
