# Python KD-tree 演示

本目录实现一般 \(d\) 维 KD-tree，并以报告中的 15 个三维点作为固定演示案例。代码只使用 Python 标准库，不需要安装 NumPy 或 Matplotlib。

## 运行

在仓库根目录执行：

```powershell
python demo/generate.py
python -m unittest demo/test_kdtree.py -v
python -m unittest demo/test_teaching.py -v
```

第一次生成完整数据。开发时可以缩小实验规模做快速检查：

```powershell
python demo/generate.py --quick
```

`--quick` 会写入较小的实测结果；正式展示前应再运行默认命令，恢复完整规模数据。

## 文件

- `kdtree.py`：建树、范围报告/计数、最近邻、插入与 \(\alpha\) 局部重建。
- `generate.py`：生成固定案例、动态插入快照、实测基准、CSV 和 SVG。
- `test_kdtree.py`：随机暴力对照、重复坐标、闭区间、等距 ID 平局、插入和元数据测试。
- `teaching.py`：可执行教学片段（范围报告、范围计数、最近邻），PPT 第 6、8、12 页直接提取其源码并生成语法高亮。
- `test_teaching.py`：验证教学片段与完整实现对一般维度、重复坐标、边界和空树保持一致。
- `output/data.json`：完整数据，使用严格 JSON 数字。
- `output/data.js`：`window.KD_DATA = ...`，可直接由静态页面加载。
- `output/benchmarks_by_size.csv`：3D 不同点数的实测结果。
- `output/benchmarks_by_dimension.csv`：固定点数下 2、3、5、10、20 维的实测结果。
- `output/dynamic_steps.csv`：31 次单调插入的树高、重建次数与累计耗时。
- `output/*.svg`：由实测 CSV/JSON 数值生成的自包含 SVG 图。

## 核心 API

```python
from demo.kdtree import (
    Point,
    build,
    insert,
    nearest,
    range_count,
    range_report,
    validate_tree,
)

points = [
    Point("A", (2, 3, 4)),
    Point("B", (5, 4, 2)),
    Point("C", (9, 6, 7)),
]

root = build(points, dimension=3)
hits = range_report(root, (3, 2, 1), (9, 7, 8))
count = range_count(root, (3, 2, 1), (9, 7, 8))
point, distance_squared = nearest(root, (6, 3, 3))

root = insert(root, Point("D", (4, 7, 9)), rebalance=True, alpha=0.75)
metadata = validate_tree(root)
```

主要规则如下：

- 第 `depth` 层使用 `axis = depth % d`。
- 排序键为 `(coords[axis], id)`；偶数点取偏右中位数。
- 范围查询与计数均使用闭区间。
- `range_report` 按树遍历产生的顺序返回点，不保证点 ID 有序；需要稳定展示时由调用方在验证或输出阶段排序。
- 最近邻按 `(距离平方, id)` 选最小；只在子树距离下界严格大于当前最优值时剪枝。
- 空树最近邻返回 `(None, math.inf)`。
- `insert` 会修改插入路径上的节点，始终使用返回值作为新根。
- `rebalance=True` 时，一次插入最多重建一个子树，并选择插入路径上最靠近根的失衡节点。

`build`、`range_report`、`range_count`、`nearest` 和 `insert` 都可传入列表作为 `trace`。事件包括：

- 建树：`build`
- 范围查询：`visit`、`prune_disjoint`、`accept_subtree`、`point_hit`
- 最近邻：`visit`、`update_best`、`prune_distance`
- 动态插入：`insert_visit`、`insert_attach`、`rebalance_select`、`insert_rebuild`

`subtree_points` 保持根→左→右的前序遍历，不按 ID 排序。`subtree_ids` 在追踪事件中使用，并按字典序返回，因此 `prune_disjoint` 和 `accept_subtree` 的 `ids` 与 `subtreeIds` 都是稳定排序后的子树 ID。

## JSON 约定

- `points` 的坐标和树节点的 `point` 均为数组。
- `tree.id` 是点 ID，`tree.point` 是坐标数组。
- `buildEvents` 使用根→左→右前序，每个事件含 `nodeId`、`depth`、`axis` 和子树信息。
- `range.result` 是生成阶段的展示结果，按 ID 排序后写入；这不改变核心 `range_report` 不承诺 ID 顺序的接口约定。
- `dynamic.steps` 有 31 项，每项均含 `plainTree` 和 `balancedTree` 完整快照，便于前端逐帧播放。
- `meta` 记录排序、平局、闭区间和实验方法；`validation` 记录生成时的自动校验结果。

## 基准方法

基准数据使用固定随机种子，与 15 点演示集分开。规模实验固定 \(d=3\)，N 为 250、500、1000、2000；维度实验固定 N=512，\(d\) 为 2、3、5、10、20。范围盒每维边长为 `volume_fraction ** (1/d)`，避免高维固定边长导致输出比例指数下降。

计时使用 `time.perf_counter()`，对若干批查询取中位数后换算为单次查询毫秒。KD-tree 与暴力范围计时都包含结果列表物化，但两者都不对结果 ID 排序；排序只发生在事后正确性校验和固定 JSON 输出阶段。访问节点数在独立的事件记录过程中统计，不计入计时批次。动态插入的平衡版计时也在 `trace=None` 的影子树上单独完成，避免把事件记录成本混入普通版对照。CSV、JSON 和 SVG 中的数值都来自当前机器上的实际生成过程；不同机器和不同运行之间会有波动。
