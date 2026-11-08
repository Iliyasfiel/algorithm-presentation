# PDF 预览导出与验证

## 本次结论

2026-11-08 在 Windows 上完成最终静态导出。`ppt/preview.pdf` 共 18 页，中文、代码高亮、公式、表格和三维静态帧均可读；PDF 保留可选中文字，不是全页截图拼装。

- 源 HTML：`ppt/index.html`
- 源 HTML SHA256：`619EAF8C871AC11F25BB5E7264399D9F0720A4976AE9CD6AC759FBC63E47D6C5`
- 最终 PDF：`ppt/preview.pdf`
- PDF SHA256：`1748093541CDCB3F3F0017FEA3B66AAED5DA015ADAB28D2B94651E8002792480`
- PDF 大小：3,270,143 字节
- PDF 技能要求的一次性 artifact create marker 已在首次导出生效命令前成功执行。

## 可复现导出

本次最终复现使用普通 `node` 和显式环境变量：

```powershell
$runtime = "C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt\dependencies"
$env:CODEX_NODE_MODULES = Join-Path $runtime "node\node_modules"
$env:EDGE_PATH = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$env:POPPLER_BIN = Join-Path $runtime "native\poppler\Library\bin"
node ppt/export_pdf.mjs --render
```

环境变量作用如下：

- `CODEX_NODE_MODULES`：指向包含 Playwright 与 pdf-lib 的 `node_modules`；可绕过 WindowsApps 目录不可列举的问题。
- `EDGE_PATH`：指定独立无头 Edge/Chrome 可执行文件。
- `POPPLER_BIN`：指向含 `pdftoppm.exe` 的目录，只在 `--render` 时使用。

脚本会先读取显式环境变量，再尝试自动发现随附运行时和常见 Edge/Chrome 路径。`--render` 是可选 QA 开关，使用 Poppler 从最终 PDF 回渲 18 张 PNG；省略时仍会导出并检查 PDF 的页数和比例。

这次验证环境：

| 运行项 | 版本/用途 |
|---|---|
| Windows | 本次唯一验证环境 |
| Node.js | v24.18.0，本次最终复现使用普通 `node` |
| Microsoft Edge | 157.0.4341.42，独立无头进程 |
| Playwright | 1.62.1，页面渲染、激活与静态捕获 |
| pdf-lib | 1.17.1，合并 18 个单页 PDF |
| Poppler `pdftoppm` | 仅用于 `--render` 的视觉回渲 |
| pypdf / Pillow | 仅用于本次文本层、尺寸与接触表 QA |

Playwright、pdf-lib 和 Edge 仅是可选 PDF 导出流程的运行时依赖。项目普通构建与 HTML 放映没有新增依赖，仓库也没有新增 `package.json`、`package-lock.json` 或 Python 依赖清单。

导出脚本没有修改 `content.js`、`viz.js`、`deck.css`、`index.html` 或根文档。它先逐页设置静态步骤，在打印媒体下只显示一个 slide，分别输出一页 16:9 PDF，再用 pdf-lib 按原顺序合并。

普通全页 print 会把共享 WebGL canvas 在多个幻灯片之间移动，并受原 `page-break-after` 影响。脚本因此注入了临时打印 CSS、覆盖分页规则，并对每页断言 `display/visibility/opacity` 与画布尺寸。页面源码保持不变。

## 静态回放步骤

三维槽采用两阶段处理：先逐个激活、强制重绘并保存包含 canvas 与 HTML 标签的完整槽位截图，全部捕获结束后再统一替换为 poster；避免隐藏共享 canvas 后污染下一槽，也避免切页时自动 poster 覆盖带标签截图。

| 页 | 页面 ID | 回放类型 | 定格步骤 | 渲染证据 |
|---:|---|---|---:|---|
| 1 | `cover` | 总览点云 | `0` | WebGL，非白 canvas 像素 22,804 |
| 3 | `partition` | 建树 | `15 / 15`，建树完成 | WebGL，非白 canvas 像素 73,399 |
| 4 | `build-example` | 建树 | `15 / 15`，建树完成 | WebGL，非白 canvas 像素 73,399 |
| 7 | `range-demo` | 范围查询 | `21 / 21`，查询完成 | WebGL，非白 canvas 像素 18,626 |
| 11 | `nearest` | 最近邻 | `12 / 12`，查询完成 | WebGL，非白 canvas 像素 8,569 |
| 13 | `insertion` | 无重建插入 | `16 / 31`，插入过程 | WebGL，非白 canvas 像素 93,985 |
| 14 | `rebuilding` | α 重建对比 | `31 / 31`，重建完成 | 双 SVG 树，最终树高 31 → 6 |

第 13 页的点都在 `(t,t,t)` 对角线上，默认镜头沿对角线看时投影会重叠。导出脚本仅为该静态帧使用侧向镜头 `yaw=2.25, pitch=0.28, zoom=1`，使三维点列、立方体线框和切分面可辨认；页面算法和交互源码未改。

## 尺寸与文字层

18 页全部为 960 × 540 pt，即 13.333 × 7.5 in，严格 16:9。Poppler 以 120 dpi 回渲的 18 张 QA PNG 全部为 1600 × 900。

| 页 | PDF 尺寸 | 提取字符数 |
|---:|---:|---:|
| 1 | 960 × 540 pt | 309 |
| 2 | 960 × 540 pt | 284 |
| 3 | 960 × 540 pt | 303 |
| 4 | 960 × 540 pt | 333 |
| 5 | 960 × 540 pt | 744 |
| 6 | 960 × 540 pt | 703 |
| 7 | 960 × 540 pt | 342 |
| 8 | 960 × 540 pt | 627 |
| 9 | 960 × 540 pt | 613 |
| 10 | 960 × 540 pt | 412 |
| 11 | 960 × 540 pt | 378 |
| 12 | 960 × 540 pt | 811 |
| 13 | 960 × 540 pt | 342 |
| 14 | 960 × 540 pt | 670 |
| 15 | 960 × 540 pt | 678 |
| 16 | 960 × 540 pt | 582 |
| 17 | 960 × 540 pt | 286 |
| 18 | 960 × 540 pt | 367 |

pypdf 从 18 页共提取 8,784 个非空字符，证明文字层存在。提取结果中的部分兼容汉字码位与页面 Unicode 写法不同，因此逐页判断以最终 PDF 回渲图为准；18 页都显示正常中文标题与正文。

## 视觉核对

已生成并目视检查 `tmp/pdfs/contact-sheet.png` 中的全部 18 页，并放大检查封面、代码、复杂度、范围和三维页。重点检查范围包括第 1、4、6–15 页。

- 第 6、8、12 页 Python 代码完整，语法高亮、缩进和调用文字均未裁切。
- 第 9、10、15 页推导链、上下标、条件说明和复杂度结论完整；白色背景与蓝色强调保持原设计。
- 第 1、3、4、7、11、13 页均可见真实三维点云、范围盒或切分面以及树形图。
- 第 13 页最终版本同时显示 16 个插入点、T01/T05/T10/T16 标签、立方体线框、切分面和右侧 16 节点右链；仅导出槽隐藏 T15 标签，末段节点同时使用导出时缩小样式，避免标签相互遮挡。
- 第 14 页完整显示无重建右链与 α=0.75 重建树；第 13、14 页内容分工未混用。
- 18 页均为白底 16:9，没有重复页、空白页、横向溢出或文字压到页脚。

脚本中的 6 个 WebGL 槽全部通过非白 canvas 像素断言；浏览器控制台错误、页面异常和失败请求均为 0。

`python scripts/check_project.py` 本次通过：算法与教学测试、18 页结构与白色主题、Python 代码块、内联脚本和数据一致性均正常。

本次验证针对 PDF 静态预览。演讲者双屏、实时回放、拖动相机和冻结/恢复交互属于 HTML 演示验收，不由静态 PDF 证明。
