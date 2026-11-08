# KD-tree 课程汇报协作指南

这份指南面向第一次参与课程小组汇报的同学，也面向协助开发、测试和排版的 AI agent。目标是在尽量少的步骤内把仓库跑起来，并让源码、实验数据、HTML 和讲稿保持一致。

最终交付物是 `ppt/index.html`。它已把 Three.js、算法回放数据和全部样式内联，可以作为一个单文件离线打开。放映者不需要 Python、Node.js、guizang skill 或任何远程三维服务；Python 和 Node.js 只用于开发、测试与重新构建。

## 1. 快速开始

克隆课程小组仓库：

```powershell
git clone https://github.com/Iliyasfiel/algorithm-presentation.git
cd algorithm-presentation
```

最低环境要求：

| 工具 | 要求 | 用途 |
|---|---|---|
| Python | 推荐 3.12；源码必须兼容 3.10 及以上 | 算法、实验、测试和构建脚本 |
| Node.js | 推荐 22 或更高版本 | 读取逐页 JS 并生成单文件 HTML；直接放映不需要 |
| Git | 任意仍受支持的近期版本 | 分支、提交和 Pull Request |
| 桌面浏览器 | 推荐最新版 Edge、Chrome 或 Firefox | 离线放映；WebGL 兼容性最好 |

基础算法、HTML 构建和项目检查只使用 Python 标准库和 Node 内置模块，**不需要运行 `pip install` 或 `npm install`**。PDF 导出是独立的可选流程，需要浏览器渲染工具，具体配置见 [PDF 预览说明](ppt/qa/pdf-preview.md)。不要为基础流程安装导出专用依赖。

先核对版本：

```powershell
py -3.12 --version
node --version
git --version
```

如果本机只能使用 Python 3.10 或 3.11，代码仍应通过；新增语法和标准库用法不得突破 Python 3.10。

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

如果 PowerShell 阻止激活脚本，直接调用虚拟环境中的解释器即可，无需修改执行策略：

```powershell
.\.venv\Scripts\python.exe --version
```

后续命令中的 `python` 也可以替换为 `.\.venv\Scripts\python.exe`。

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
node --version
git --version
```

如果 `python3.12` 命令不存在，可以使用本机已有的其他 Python 3.10+ 解释器，例如 `python3 -m venv .venv`，并核对其版本。Node.js 只影响构建和自动检查；只负责放映的同学无需安装。

## 2. 先看哪里

进入仓库后按这个顺序阅读：

1. 根目录 `AGENTS.md`：AI agent 的最高优先级仓库说明。若具体目录还有 `AGENTS.md`，还须读取离目标文件最近的那一份。
2. [README.md](README.md)：项目交付物、演示快捷键和最短构建流程。
3. 本文件：环境、源码边界、验证与协作规则。
4. [demo/README.md](demo/README.md)：算法 API、事件格式、数据约定和实验方法。
5. [ppt/README.md](ppt/README.md)：PPT 使用、维护入口和现有验收记录。
6. [docs/kdtree-report.md](docs/kdtree-report.md) 与 [docs/kdtree-speaker-script.md](docs/kdtree-speaker-script.md)：18 页内容依据、公式和讲稿。

如果当前分支暂时没有根 `AGENTS.md`，先确认是否落后远端；不要用自己的临时规则替代仓库约定。

## 3. 目录与修改入口

| 要修改的内容 | 应改的源文件 | 说明 |
|---|---|---|
| 页面文案、备注、逐页时长 | `ppt/content.js` | 观众可见内容、结构化备注和时长的主要来源 |
| 完整提纲、公式与教学论证 | `docs/kdtree-report.md` | 18 页内容依据 |
| 口播稿和现场操作提示 | `docs/kdtree-speaker-script.md` | 与页面结论、时间和操作保持一致 |
| 核心算法 | `demo/kdtree.py` | 一般 `d` 维建树、范围查询、最近邻、插入与局部重建 |
| 可执行教学代码 | `demo/teaching.py` | 第 6、8、12 页直接提取；保留 `# PPT:<name>:start` / `end` 标记 |
| 算法单元测试 | `demo/test_kdtree.py`、`demo/test_teaching.py` | 核心实现与教学片段都要覆盖 |
| 数据生成、轨迹与实验 | `demo/generate.py` | 生成固定案例、动态快照、基准、CSV 和 SVG |
| 三维空间图、树图与回放控件 | `ppt/viz.js` | 只负责事件可视化和交互 |
| 页面排版与控件样式 | `ppt/deck.css` | 保持 18 页白色主题和蓝黑灰配色 |
| 单文件构建逻辑 | `ppt/build_deck.py` | 读取内容、代码、模板、数据和资源后生成 HTML |
| 最终演示 | `ppt/index.html` | 构建产物，直接复制即可离线打开 |

页面数量和构建映射目前硬编码在 `ppt/build_deck.py` 中，并配套 18 页讲稿。默认保持 18 页白色主题；若确实需要改变页数，必须同步修改内容、布局、讲稿、时长和构建映射，并完成全套验收。

`ppt/assets/template-swiss.source.html` 是本地模板快照。最终 HTML 不访问外部技能目录、CDN、远程字体或三维 API。

### AI 修改 PPT：必须使用 guizang-ppt-skill

修改 PPT 内容、版式、样式、动效、代码展示或演讲者/观众屏交互前，AI Agent 必须显式使用 **`guizang-ppt-skill`**，先读取其 `SKILL.md`，再按任务读取瑞士风版式、主题、演讲者模式及检查规范。这不是可选建议；仓库中已保存模板也不能替代技能工作流。

技能来源为 <https://github.com/op7418/guizang-ppt-skill>。按各自 Agent 的技能安装机制配置，确认它能找到该名称；不要把自己的安装绝对路径提交到项目。若不可用，应先如实说明并协助配置。用户已经确定的 18 页、全白主题、蓝黑灰配色和三维演示要求优先于模板默认设计。

放映成品、仅运行现有构建/测试或开发不涉及 PPT 设计的 Python 算法，不要求安装技能。该区别保证维护遵循设计流程，同时不让技能成为离线放映或基础检查的运行依赖。完整维护入口见 [ppt/README.md](ppt/README.md)。

## 4. 不要手改生成物

以下文件由命令生成，不应直接手工维护：

- `ppt/index.html`
- `ppt/slide-plan.json`
- `ppt/preview.pdf`（PDF 静态预览，导出方式见 [PDF 预览说明](ppt/qa/pdf-preview.md)）
- `demo/output/data.json`
- `demo/output/data.js`
- `demo/output/*.csv`
- `demo/output/*.svg`

应修改它们的上游源文件，然后重新运行生成命令。直接编辑 `index.html` 会在下一次构建时被覆盖；只改 `data.json` 或只改 `data.js` 还会破坏两者的一致性。

构建链路是：

```text
Python 算法与 trace
  -> demo/generate.py 导出严格 JSON（并生成 data.js 包装）
  -> ppt/build_deck.py 内联数据、Three.js、页面样式与回放脚本
  -> ppt/index.html 单文件离线放映
```

Python 是算法结果的唯一来源，JSON 是前后端之间的数据契约，`ppt/viz.js` 只回放 Python 已经产生的事件。不要在 JavaScript 里另写一套查询算法，也不要用前端临时计算“修正”导出结果。新增事件类型时，需要同时更新 Python trace、生成器、JSON 约定、回放代码和相关测试。

## 5. 内容与算法约定

- 图形用固定三维点集方便展示，定义与复杂度推导仍面向一般固定 `d` 维。
- 第 9、10、15 页的一般维度和摊还分析前提不能为了版面删减成只适用于三维的结论。
- 区分静态中位数建树、动态插入树高、单次最坏成本和纯插入摊还成本，不把树平衡直接等同于所有查询都是对数时间。
- 范围查询使用闭区间；重复坐标和等距最近邻使用确定 ID 平局规则。
- 保持 18 页的白色页面、白色三维画布和蓝黑灰配色，不添加远程图片、背景流体、在线字体或额外装饰动画。
- 第 13 页只展示无重建插入，第 14 页才进入局部重建对比。
- 页面代码直接来自 `demo/teaching.py`，不要复制一份到 `content.js` 后分别维护。

涉及公式、复杂度条件或实验解释的修改，应同步核对 `docs/kdtree-report.md`、`docs/kdtree-speaker-script.md`、页面内容和测试结果。

## 6. 测试与构建

所有命令均从仓库根目录运行。先跑针对性正确性测试，再生成需要的正式数据，构建 HTML，最后做只读聚合检查。

### 日常最小检查

```powershell
python -m unittest demo/test_kdtree.py demo/test_teaching.py -v
python scripts/check_project.py
```

`python scripts/check_project.py` 是只读验证入口。它会：

- 运行 11 项 `unittest`（核心算法 8 项，教学查询代码 3 项）；
- 检查 Node.js 源文件语法；
- 检查 HTML 与当前导出数据的一致性。

它不会重新构建 HTML，也不会重跑性能实验。若当前检出还没有这个脚本，先更新远端分支，不要另造一个同名但规则不同的检查器。

### 修改文案、样式或回放界面

测试后重建最终 HTML：

```powershell
python -m unittest demo/test_kdtree.py demo/test_teaching.py -v
python ppt/build_deck.py
python scripts/check_project.py
```

也可以使用带预构建的一体检查：

```powershell
python scripts/check_project.py --build
```

加 `--build` 会先重新构建 `ppt/index.html` 和 `ppt/slide-plan.json`，再执行检查。它**不会重新运行性能实验**。构建需要 Node.js 22+。

### 修改算法、事件或实验

只有当变更需要刷新演示快照、CSV、SVG 或正式性能数据时，才运行完整生成：

```powershell
python demo/generate.py
python ppt/build_deck.py
python scripts/check_project.py
```

`demo/generate.py` 会重新实测计时，所以数值可能随机器和运行批次变化。正式提交或现场演示前，应确认第 16 页所讲数值与当前导出数据一致。

开发中可以用小规模实验快速冒烟：

```powershell
python demo/generate.py --quick
```

注意：`--quick` **会直接覆盖正式导出数据**。它只用于临时检查；之后必须再运行不带参数的 `python demo/generate.py` 恢复完整数据，否则不要提交、构建正式版本或上台演示。

## 7. 给 AI agent 的可复制任务模板

把方括号内容替换为本次具体任务。这个模板已经写入了仓库边界、验证顺序和诚实汇报要求。

```text
你是本仓库的协作开发 agent。开始前依次阅读根 AGENTS.md（以及目标路径下更近的 AGENTS.md）、README.md、CONTRIBUTING.md，再按任务读取 demo/、ppt/ 和 docs/ 中的对应说明。

任务：
[描述要实现的用户可见结果、验收条件和明确不在本轮范围内的内容]

允许修改：
[列出允许编辑的源文件或目录]

约束：
- 若任务涉及 PPT 内容、版式、样式、动效、代码展示或演讲者/观众屏交互，必须显式使用 guizang-ppt-skill，先读 SKILL.md 及相关参考，再实施修改。
- 保持一般 d 维推导、18 页白色主题和 Python 轨迹 -> JSON -> Three.js 回放边界。
- 不手改 ppt/index.html、ppt/slide-plan.json、demo/output/data.json、demo/output/data.js、CSV 或 SVG；通过源文件和构建命令更新。
- 基础流程不运行 pip/npm 安装项目依赖；PDF 导出专用可选环境按其说明配置，不引入远程 CDN、字体或三维服务。
- 不改动或删除 ppt/assets/ 中的第三方许可证。
- 除非任务明确要求刷新正式实验，不运行 demo/generate.py，也不使用 --quick 生成提交数据。
- 按“先测试、再构建、最后只读检查”的顺序工作；例行测试和构建无需逐项请求人工审批。

工作流程：
1. 检查 git status，先保护用户已有改动。
2. 涉及 PPT 时先加载 guizang-ppt-skill；定位源文件和受影响的数据契约，作出最小修改。
3. 运行 python -m unittest demo/test_kdtree.py demo/test_teaching.py -v。
4. 若改了 PPT 文案、样式、教学代码或回放，运行 python scripts/check_project.py --build；若改了算法或正式实验数据，先确认是否需要运行 python demo/generate.py，再构建。
5. 运行 python scripts/check_project.py，并执行任务要求的离线浏览器验收。

交付报告：
- 列出改动文件和关键行为变化。
- 列出实际运行的命令及通过/失败结果。
- 明确哪些 UI 功能亲手验证过，哪些因环境限制尚未验证。
- 不把静态检查、历史记录或“应当可用”等同于完整双屏、WebGL、演讲者模式验收。
```

如果只做一个小改动，可以缩短模板，但必须保留“源文件与生成物边界、最小测试集、实际验收、未完成项”，以及涉及 PPT 时必须使用 guizang-ppt-skill 的要求。

## 8. 分支、提交与 Pull Request

每个主题使用独立分支，避免多人同时改默认分支：

```powershell
git status
git switch main
git pull --ff-only
git switch -c feat/short-description
```

修改并验证后，只暂存本任务相关文件：

```powershell
git diff --check
git status --short
git add <相关文件>
git diff --cached
git commit -m "docs: describe ..."
git push -u origin HEAD
```

然后在 GitHub 上创建指向 `main` 的 Pull Request。PR 描述应写清：

- 原先的问题和修改后的可见行为；
- 修改的源文件，以及由命令重新生成的产物；
- 实际运行的测试、构建和 UI 检查；
- 尚未验证的场景或已知限制。

页面文案变化通常需要一并提交 `ppt/content.js`、对应 Markdown 和重新生成的 `ppt/index.html`。实验轨迹变化通常还会涉及 `demo/output/` 中的正式数据与图表。生成的提交物应由命令产生，不能夹带 `--quick` 的临时数据。

第三方资源保持原样：不要删除或改写 `ppt/assets/GUIZANG-LICENSE.txt`、`ppt/assets/THREE-LICENSE.txt` 或其他许可证。若未来确需升级第三方依赖，应保留并核对完整许可证文本，不要悄悄替换。

## 9. 离线放映与诚实 UI 验收

### 放映方式

最终只需要 `ppt/index.html`。可以直接双击打开，也可以把该单文件复制到演示电脑。它不依赖开发服务器、网络、guizang skill 或远程三维服务。

现场建议使用最新版桌面 Edge 或 Chrome，并提前确认：

- 方向键和 PageUp/PageDown 能翻页，Home/End 能到首尾页；
- ESC 能打开总览；
- 第 4、7、11 页的三维图可拖动，并能单步、播放、暂停和重置；
- 第 13 页从空树播放无重建插入；
- 第 14 页展示重建对比，重置后可从空状态回放；
- P 能打开演讲者窗口，浏览器允许该单文件的弹窗；
- 备注区按钮与当前页预览都能控制观众屏，回放步数和相机视角同步；
- 观众屏冻结、恢复和窗口重开在目标设备上确实可用；
- 在关闭网络后逐页检查 18 页内容、公式、代码和三维图，不出现外部请求。

如果浏览器不能创建 WebGL 上下文，页面会使用兼容投影；正式演示前仍应确认三维模式正常工作。

### 验收标准

自动检查通过只证明 11 项算法测试、Node 语法和 HTML/导出数据一致性通过，不能替代真实浏览器交互。UI 验收必须同时做到：

1. 实际打开**本次构建**的 `ppt/index.html`，不是旧缓存或历史文件。
2. 目视检查 18 页的标题、公式、代码、数值、overflow、白色主题和三维画布。
3. 亲手操作关键回放、拖动视角、演讲者模式和观众屏同步。
4. 将结果如实写进 PR 或 [ppt/qa/verification.md](ppt/qa/verification.md)：写清浏览器版本、已验证项、未验证项和失败现象。

当前仓库的 [ppt/qa/verification.md](ppt/qa/verification.md) 已明确记录：最终逐页截图、完整双屏回放/相机同步、冻结恢复、计时和弹窗恢复尚未全部实测。除非本次确实完成并观察到这些行为，否则不要把它们改写成“已验收”。

## 10. 常见问题

**`python` 打开了应用商店或版本低于 3.10**

Windows 优先使用 `py -3.12` 创建虚拟环境；macOS/Linux 使用 `python3.12`。不要继续使用缺少 `venv` 或版本过旧的系统解释器。

**`Activate.ps1` 被执行策略阻止**

使用 `.\.venv\Scripts\python.exe` 直接运行命令，不需要修改执行策略。

**提示缺少包**

先确认虚拟环境已激活且 Python 版本正确。基础流程没有 `requirements.txt` 或 `package.json` 依赖，不要用安装包绕过源码问题。若是 PDF 导出报缺少渲染工具，则按独立的导出说明配置其可选环境。

**`node` 不存在，但只想放映**

直接复制并打开 `ppt/index.html`。只有重新构建或运行 Node 语法检查时才需要 Node.js 22+。

**改了 `ppt/index.html`，下次构建后消失**

编辑 `content.js`、`deck.css`、`viz.js` 或 `demo/teaching.py` 等源文件，再运行构建命令。`index.html` 是生成物。

**`check_project.py` 提示 HTML 或导出数据不一致**

先确认改动了哪一层：文案/样式/回放变化运行 `python scripts/check_project.py --build`；正式实验数据变化先按需运行 `python demo/generate.py`，再构建和检查。不要手改其中一个数据文件来消除差异。

**性能数字与讲稿不一致**

默认生成会重新实测。检查是否刚运行过 `demo/generate.py`，并同步第 16 页、讲稿和当前导出数据。不要承诺不同机器、不同运行批次会得到完全相同的耗时。

**运行过 `--quick` 后图或数值变小**

运行 `python demo/generate.py` 恢复正式规模，再重新构建。`--quick` 的产物只能用于临时冒烟。

**教学代码没有出现在 PPT 中**

检查 `demo/teaching.py` 中对应的 `# PPT:<name>:start` 与 `# PPT:<name>:end` 标记，以及 `ppt/build_deck.py` 使用的名称是否一致。不要直接把完整代码手贴进生成 HTML。

**演讲者窗口没有出现**

确认按的是 P，并检查浏览器是否拦截了本地文件弹窗。改用目标浏览器重新测试；仅看到静态脚本检查通过不算双屏验收。

**三维图为空白或显示兼容模式**

确认浏览器硬件加速和 WebGL 可用，重新打开本次构建的 HTML；离线放映不需要远程三维服务。若最终只能使用兼容投影，应在验收记录和现场说明中如实注明。

## 11. 协作底线

- 先读需求和相关源文件，再做最小改动；不要顺手重写无关模块。
- 默认保持 Python 3.10 兼容、一般 `d` 维推导和 18 页白色主题。
- 只提交与任务有关的源文件和由命令生成的相关产物。
- 算法正确性优先于视觉现象；测试通过不能代替浏览器验收，浏览器“看起来正常”也不能代替算法测试。
- 例行的读取、编辑、测试、构建、分支和 PR 准备应直接执行，不设置逐步人工审批关卡。
- 最终汇报要区分“已验证”“未验证”和“验证失败”，列出文件、命令和结果。
