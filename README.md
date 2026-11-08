# KD-tree：多维空间查询与动态维护

课程小组汇报项目，包含 **18 页白色主题 HTML PPT、Python 演示代码和逐页演讲稿**。三维图形回放 Python 导出的真实执行轨迹；定义与复杂度分析面向一般 d 维。

仓库：[Iliyasfiel/algorithm-presentation](https://github.com/Iliyasfiel/algorithm-presentation)。

## 我该从哪里开始？

| 你的任务 | 入口 |
|---|---|
| 直接看 PPT、上台演示 | [ppt/index.html](ppt/index.html)，下载到本地后用浏览器打开 |
| 静态预览全部页面 | [PDF 预览](ppt/preview.pdf)，不包含交互操作 |
| 准备演讲、排练与答问 | [逐页讲稿](docs/kdtree-speaker-script.md) |
| 理解内容、公式、证明与案例 | [汇报内容文档](docs/kdtree-report.md) |
| 请 AI Agent 配环境或改项目 | 先让它读 [AGENTS.md](AGENTS.md)，再按 [CONTRIBUTING.md](CONTRIBUTING.md) 操作 |
| 查看算法 API、数据与实验方法 | [Python 演示说明](demo/README.md) |
| 修改 HTML PPT 与回放 | [PPT 维护说明](ppt/README.md) |

## 只使用成品：无需开发环境

从 GitHub 的 **Code → Download ZIP** 下载并解压，或用 Git 克隆仓库，然后用支持 WebGL 的桌面浏览器打开 `ppt/index.html`。

该 HTML 已内置 Three.js、教学代码高亮和回放数据，能够单文件离线使用；不需要 Python 服务、Node.js、联网或 CDN。GitHub 文件页面只展示源文件，不会自动运行 PPT；要下载到本地后打开。本仓库尚未配置 GitHub Pages 托管。

- 方向键、PageUp/PageDown 翻页，Home/End 到首尾页，ESC 打开总览。
- 三维图内拖动旋转视角，用“上一步 / 下一步 / 播放 / 重置”回放算法。
- 第 13 页从空树开始，只展示无重建插入；第 14 页引入 α 与重建对比。
- P 打开演讲者模式和独立观众窗口；需允许浏览器弹窗。通过当前页预览或备注下方按钮操作算法回放。
- 普通模式的 B 切换静态模式；演讲者模式的 B 控制观众屏黑屏。

当前逐页计划 **19 分 45 秒**，答问另留 5～10 分钟。正式汇报前应在投影环境排练，确认双屏同步、公式和代码可读。

## 用 AI Agent 快速开始

先克隆项目并在 AI 编程工具中打开目录：

```text
git clone https://github.com/Iliyasfiel/algorithm-presentation.git
cd algorithm-presentation
```

可以把下面这段发给 Agent：

> 请先阅读 AGENTS.md、CONTRIBUTING.md 和 README.md，检查本机 Python、Node.js 与 Git。使用本项目的实际依赖配置环境，不新增不必要的包。运行 python scripts/check_project.py，解释检查结果与尚需人工验证的部分。随后完成我的具体任务：[在这里填写要修改的页面、算法或演示效果]。

详细环境步骤、虚拟环境、分支与 PR 流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。只放映、运行现有测试或构建不需要安装技能；**用 AI 修改 PPT 时必须显式使用 `guizang-ppt-skill`**，按 [PPT 维护规范](ppt/README.md) 先读取技能及相关参考。技能来源为 <https://github.com/op7418/guizang-ppt-skill>，通过所用 Agent 的技能机制配置，不将个人安装路径写入项目。

## 开发环境与一键检查

| 工具 | 用途 |
|---|---|
| Python 3.12+，语法最低支持 3.10 | 算法、数据导出、测试与构建脚本 |
| Node.js 22+ | 读取 PPT 内容数据、JavaScript 语法检查；不承担后端服务 |
| Git | 克隆和协作 |
| 支持 WebGL 的桌面浏览器 | 三维回放与现场演示 |

已在 Python 3.12.7、Node.js 24.18.0 下验证。**基础算法、HTML 构建和项目检查没有需要安装的第三方 Python/npm 包**，无需执行 `pip install` 或 `npm install`。PDF 导出另外使用可选的浏览器渲染环境，见 [PDF 预览说明](ppt/qa/pdf-preview.md)，不影响上述基础流程。

在仓库根目录运行：

```text
python --version
node --version
python scripts/check_project.py
```

检查内容包括核心与教学代码测试、JavaScript 语法、18 页及备注对应关系、白色主题、代码提取保真、完整实验数据与 HTML 内嵌数据一致性。检查本身不重测性能；失败会以非零退出码和具体原因报告。

需要先重新构建 PPT 再检查时：

```text
python scripts/check_project.py --build
```

自动检查不等于浏览器视觉或双屏验收。历史检查及未完成项见 [验证记录](ppt/qa/verification.md)。

## 修改后的生成顺序

**只改 PPT 文案、样式、交互或教学代码：**

```text
python ppt/build_deck.py
python scripts/check_project.py
```

**改了算法、案例或实验数据：**

```text
python -m unittest demo/test_kdtree.py demo/test_teaching.py -v
python demo/generate.py
python ppt/build_deck.py
python scripts/check_project.py
```

`generate.py` 会重新实测，耗时数值会随机器与运行变化。`--quick` 仅用于临时快速运行，会覆盖输出；提交前必须默认完整生成并重新打包。一键检查会拒绝仍处于 quick 模式的数据。

## 项目结构与维护入口

```text
AGENTS.md                       给 AI Agent 的项目规则与操作入口
CONTRIBUTING.md                 环境配置、开发与协作指南
scripts/check_project.py        无第三方包的一键检查
docs/
  kdtree-report.md              18 页完整内容、推导和演示约定
  kdtree-speaker-script.md      逐页口播、操作节点、时间与答问
demo/
  kdtree.py                     一般 d 维完整算法与轨迹
  teaching.py                   PPT 直接引用的三种查询教学代码
  generate.py                   固定案例、动态快照与实测数据生成
  test_kdtree.py                核心算法测试
  test_teaching.py              教学代码与完整实现对照测试
  output/                       JSON、JavaScript 数据、CSV、实验 SVG
ppt/
  content.js                    页面文案、讲稿备注与逐页时长
  deck.css                      排版与代码高亮
  viz.js                        Three.js / SVG 回放与交互
  build_deck.py                 单 HTML 打包脚本
  index.html                    离线成品（由脚本生成）
  preview.pdf                   PDF 静态预览（导出产物）
  slide-plan.json               页面 ID、版式与时间计划（生成）
  assets/                       本地模板、Three.js 与许可证
  qa/verification.md            验证记录
```

`demo/output/`、`ppt/index.html` 和 `ppt/slide-plan.json` 随源码提交，便于直接演示。应修改源码并重新生成，不要手改输出文件。教学代码从 `demo/teaching.py` 提取，文案改动要同步内容文档与讲稿。

PDF 为静态预览，三维演示使用选定步骤的画面；播放、旋转和演讲者模式仍需 HTML。导出方法、可选导出环境与本次检查见 [PDF 预览说明](ppt/qa/pdf-preview.md)。修改 PPT 后应同步重新导出预览，不直接编辑 PDF。

## 内容与实现约定

- N 为点数，d 为维度，r 为范围输出点数；三维可视化不替代一般维度分析。
- 涵盖中位数建树、轴对齐范围报告与计数、精确最近邻、无重建插入和 α 局部重建。
- 最近邻使用距离平方及确定的 ID 平局规则；范围使用闭区间，报告不在查询内部排序。
- 静态范围界、动态树高、单次重建成本与纯插入摊还界分别声明前提，不把平衡直接等同于所有查询对数时间。
- JavaScript 负责重放 Python 的事件，不重复实现核心查询。

## 第三方资源

网页模板源自 guizang-ppt-skill，本地副本及许可证见 [GUIZANG-LICENSE.txt](ppt/assets/GUIZANG-LICENSE.txt)。Three.js 固定使用 0.160.1 的本地 UMD 构建以支持单 HTML 离线内联，许可证见 [THREE-LICENSE.txt](ppt/assets/THREE-LICENSE.txt)。保留第三方许可与来源信息；仓库未另行声明原创部分的开源许可证。
