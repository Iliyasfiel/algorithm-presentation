window.KD_SLIDES = [
  {
    id: 's01',
    title: 'KD-tree：多维空间查询',
    kicker: 'INTRODUCTION',
    purpose: '用三维点云建立空间索引直觉，并交代本次汇报的算法主线。',
    duration: 30,
    notes: [
      'KD-tree 是一种空间索引结构；本次覆盖建树、轴对齐范围查询、精确最近邻，以及持续插入后的动态维护。',
      '汇报主线是“组织点、减少访问、维持结构”：先用三维点云直观理解，再用一般 d 维给出定义、正确性和复杂度条件。',
      '三维只负责可视化，算法结论不依赖三维；第 9 页会完整给出一般维度推导，第 10 页再落到二维和三维特例。',
      '开场可以先指出查询盒和查询点，让听众先有“哪些区域可以跳过”的问题意识，再进入后续页面。'
    ],
    transition: '先看暴力查询为什么不够。',
    body: `
      <p class='lead'>把 <span class='mono'>N</span> 个点组织成层次，让查询只进入仍可能产生答案的空间。</p>
      <div class='two-col'>
        <div>
          <div class='formula'>划分空间<br>减少访问</div>
          <p class='muted'>三维点云负责建立直觉；定义、正确性与复杂度面向一般 <i>d</i> 维。</p>
        </div>
        <div class='viz' data-demo='overview'></div>
      </div>
      <div class='tag'>固定维度 d · 点数 N · 输出 r</div>
    `
  },
  {
    id: 's02',
    title: '为什么不能逐点扫描？',
    kicker: 'MOTIVATION',
    purpose: '说明重复范围查询和最近邻查询的访问瓶颈，以及预处理换访问量的目标。',
    duration: 60,
    notes: [
      '三维采样场景需要反复做两类操作：取回给定长方体内的点，或找到离当前位置最近的采样点；它们分别对应范围查询与最近邻查询。',
      '暴力方法逐点检查，最坏成本为 O(dN)，固定维度时写作 O(N)。预处理不能消除所有最坏情况，目标是用额外存储换更少访问。',
      '这个结论适用于任何固定维度，不是三维专属技巧；高维或数据分布不利时，空间结构带来的剪枝可能明显变弱。',
      '这里不预设 KD-tree 总能胜过向量化扫描；后续结论都带着建树方式、查询形状和维度条件。'
    ],
    transition: '关键是让一次扫描只负责一小块空间。',
    body: `
      <div class='two-col'>
        <div>
          <div class='tag'>WITHOUT INDEX</div>
          <div class='big-number'>N</div>
          <p class='lead'>每次查询都检查全部点。</p>
        </div>
        <div>
          <div class='tag'>WITH SPATIAL STRUCTURE</div>
          <div class='big-number'>V ≤ N</div>
          <p class='lead'>预处理后，只访问仍可能相关的区域。</p>
        </div>
      </div>
      <div class='callout'>比较访问的节点数：扫描 N 个，索引访问 V 个。逐维判断需 O(d)，范围报告还需输出成本；最坏 V 仍可达到 N。</div>
    `
  },
  {
    id: 's03',
    title: '一层切分，一类约束',
    kicker: 'CONSTRUCTION',
    purpose: '解释循环选轴和中位数划分如何把多维点递归组织成空间层次。',
    duration: 60,
    notes: [
      '深度为 depth 的节点使用 axis = depth mod d，因此三维的选轴顺序是 x、y、z、x，依次循环。',
      '在选中维度排序后，以中位数点作为节点，其余点分入左右子树；中位数保证节点数量平衡，并不保证几何体积被平均切开。',
      '某棵子树的空间来自祖先切分形成的划分区域，代码还可以维护点集实际的紧包围盒；后者通常更紧，可用于更早剪枝。',
      '完整划分约束会沿路径累积成轴对齐区域；后面做复杂度证明使用经典划分区域，实际查询则可利用紧包围盒。'
    ],
    transition: '把规则套到同一组 15 个点上。',
    body: `
      <div class='formula'>axis = depth mod <i>d</i></div>
      <div class='formula small'>排序选中维 → 取中位数 → 左右递归</div>
      <div class='viz' data-demo='build'></div>
      <div class='two-col'>
        <div class='callout'><strong>划分区域</strong><br>祖先切分约束累积出的空间。</div>
        <div class='callout'><strong>紧包围盒</strong><br>子树实际点的逐维最小/最大值。</div>
      </div>
    `
  },
  {
    id: 's04',
    title: '三维点集建树',
    kicker: 'CASE STUDY',
    purpose: '用统一点集展示中位数选择、三层选轴和平衡建树过程。',
    duration: 85,
    notes: [
      '统一案例是 A 到 O 共 15 个三维点。先按 x 坐标排序，取下标 len(points) // 2，偶长度规则取偏右中位数；本案例根节点为 E=(8,1,5)。',
      '根节点左侧 7 个点、右侧 7 个点。左右子树的根按 y 坐标选择，分别为 H=(3,5,1) 与 L=(14,12,10)；随后进入 z 轴，继续循环。',
      '实现用唯一 ID 为相同坐标打破排序平局；重复坐标可能被分到两侧，所以空间约束要使用非严格不等式，不能断言左子树所有坐标都严格更小。',
      '动画只展开前三层，避免大量半透明平面互相遮挡；更深层通过高亮当前子树继续表达递归结构。'
    ],
    transition: '从演示规则进入可运行实现。',
    body: `
      <div class='two-col'>
        <div>
          <div class='big-number'>15</div>
          <p class='lead'>个唯一编号点，循环执行 <span class='mono'>x → y → z → …</span></p>
          <div class='mini-table'>
            <table>
              <thead><tr><th>层</th><th>节点</th><th>轴</th></tr></thead>
              <tbody>
                <tr><td>0</td><td>E (8, 1, 5)</td><td>x</td></tr>
                <tr><td>1</td><td>H · L</td><td>y</td></tr>
                <tr><td>2</td><td>继续递归</td><td>z</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class='viz' data-demo='build'></div>
      </div>
      <p class='ref'>中位数取 <span class='mono'>len(points) // 2</span>；本案例根节点左右各 7 点。</p>
    `
  },
  {
    id: 's05',
    title: '实现与构建代价',
    kicker: 'IMPLEMENTATION',
    purpose: '给出节点接口和递归建树片段，并区分排序建树与线性选择建树的复杂度。',
    duration: 75,
    notes: [
      '代码示意中的 d 由外层传入或封装保存；节点保存 id、坐标、划分轴、左右孩子、子树大小和紧包围盒，后两项会同时服务于范围计数、最近邻下界和动态重建。',
      '递归排序版本每层用 O(N log N) 排序，递推 B(N)=2B(N/2)+O(N log N)，得到 O(N log² N)；固定 d 时这是建树界。',
      '线性时间中位数选择把每层工作降为 O(N)，对应 O(N log N)。理论结论需要最坏线性选择算法；不能把 Python sorted 当成线性选择。',
      '显式保留维度成本时，两项分别加上 O(dN)；节点与包围盒持久存储为 O(dN)，固定 d 时就是 O(N)，临时列表不计入持久结构。'
    ],
    transition: '树建好后，查询需要判断三种空间关系。',
    body: `
      <div class='analysis-grid'>
      <div><pre class='code'>def build(points, depth=0):
    if not points:
        return None
    axis = depth % d
    ordered = sorted(points,
        key=lambda p: (p.coords[axis], p.id))
    mid = len(ordered) // 2
    left = build(ordered[:mid], depth + 1)
    right = build(ordered[mid + 1:], depth + 1)
    return make_node(ordered[mid], axis, left, right)</pre></div>
      <div class='analysis-copy'>
        <div class='proof-step'><span class='tag'>01 / 每层排序工作量</span>
          第 ℓ 层约有 2<sup>ℓ</sup> 个子问题，每个规模 N/2<sup>ℓ</sup>。
          <div class='formula'>2<sup>ℓ</sup> · O((N/2<sup>ℓ</sup>) log(N/2<sup>ℓ</sup>))<br>= O(N(log N − ℓ))</div>
        </div>
        <div class='proof-step'><span class='tag'>02 / 累加 L = ⌈log₂ N⌉ 层</span>
          <div class='formula'>B(N) = O(N ∑<sub>ℓ=0</sub><sup>L−1</sup>(L−ℓ))<br>= O(N · L(L+1)/2)<br>= O(N log<sup>2</sup>N)</div>
        </div>
        <div><span class='tag'>03 / 若改用线性中位数选择</span>
          每层合计 O(N)，共 O(log N) 层，得到 O(N log N)。
        </div>
      </div>
      </div>
      <p class='ref'>上述排序/选择按单坐标比较计费；自底向上合并 d 维包围盒另需 O(dN)。空间 O(dN)。</p>
    `
  },
  {
    id: 's06',
    title: '范围查询的三种关系',
    kicker: 'RANGE QUERY',
    purpose: '用包围盒与查询盒的相交关系组织跳过、整棵接收和继续递归。',
    duration: 70,
    notes: [
      '一般 d 维查询盒 Q 是 d 个闭区间的笛卡尔积。对当前子树包围盒 B，只需区分不相交、完全包含和部分相交三种关系。',
      '不相交时可以安全跳过；完全包含时范围报告要输出整棵子树，而范围计数可以直接读取子树 size，这里体现了报告与计数的区别。',
      '部分相交时检查当前节点，再递归两个子树；闭区间意味着落在边界上的点要计入，轴对齐盒公式不能直接套到球形半径查询。',
      '每条判断都在 d 个维度上执行；固定 d 时每次包围盒比较是常数时间，但高维时隐藏常数会随 d 增长。'
    ],
    transition: '让真实三维查询走完每一种事件。',
    body: `
      <div class='analysis-grid query-code'>
        <div data-code="report"></div>
        <div class='analysis-copy'>
          <div class='formula'>Q = ∏<sub>i=1</sub><sup>d</sup>[a<sub>i</sub>, b<sub>i</sub>]</div>
          <div class='proof-step'><span class='tag'>不相交 / disjoint</span>整棵子树跳过，不检查其内部点。</div>
          <div class='proof-step'><span class='tag'>完全包含 / contained</span>直接收集子树全部点。报告必须支付 O(r) 输出成本。</div>
          <div class='proof-step'><span class='tag'>部分相交 / partial</span>判断当前点，再递归左右孩子。</div>
          <p>调用：<span class='mono'>out = []; report(root, lo, hi, out)</span></p>
          <p class='ref'>relation 做 d 维包围盒比较；inside 按闭区间判断。subtree_points 以 O(m) 前序收集，不排序。</p>
        </div>
      </div>
    `
  },
  {
    id: 's07',
    title: '三维范围查询回放',
    kicker: 'RANGE DEMO',
    purpose: '通过统一点集展示跳过、部分相交、点数命中和整棵接收的完整过程。',
    duration: 60,
    notes: [
      '采用统一点集和第 04 页的树，查询 Q=[3,9]×[2,7]×[1,8]。逐维检查坐标后，答案是 B、C、F、H，共 4 个点。',
      '回放事件包括 visit、prune_disjoint、accept_subtree 和 point_hit；整棵接收与单点命中使用不同文字标记，不能只靠颜色区分。',
      '颜色只辅助识别：灰色尚未处理，橙色部分相交，蓝色完全包含，淡灰表示被剪枝；查询盒保持固定视角，避免遮挡变化影响理解。',
      '正确性验证时把范围报告得到的 ID 集合与暴力方法比较，同时要求范围计数等于报告结果长度。'
    ],
    transition: '为什么三个分支合起来不会漏点？',
    body: `
      <div class='two-col'>
        <div>
          <div class='formula small'>Q = [3, 9] × [2, 7] × [1, 8]</div>
          <div class='big-number'>4</div>
          <p class='lead'>命中 B、C、F、H</p>
          <div class='tag'>visit · prune · accept · hit</div>
        </div>
        <div class='viz' data-demo='range'></div>
      </div>
      <p class='muted'>回放同时显示树上节点与累计访问数；“接收子树”和“单点命中”用文字标签区分。</p>
    `
  },
  {
    id: 's08',
    title: '范围计数与正确性',
    kicker: 'CORRECTNESS',
    purpose: '利用包围盒不变式对三种查询分支做正确性归纳。',
    duration: 55,
    notes: [
      '核心不变式是：每棵子树维护的包围盒必须包含该子树全部点。对根节点和递归合并都保持这一性质，才能安全剪枝。',
      '不相交分支不会漏解；完全包含分支整棵接收不会引入多余点；部分相交分支检查当前节点并递归两侧，覆盖全部剩余可能。',
      '按树结构归纳可得范围报告既不漏也不重，每个节点数据只输出一次。计数正确性还额外依赖 size 的维护。',
      '插入或局部重建后必须重新合并 bbox 并更新 size；查询逻辑正确并不能弥补索引元数据错误。'
    ],
    transition: '把三个分支变成固定 d 维的访问量递推。',
    body: `
      <div class='analysis-grid query-code'>
        <div data-code="count"></div>
        <div class='analysis-copy'>
          <h3>与范围报告唯一关键差别</h3>
          <div class='formula'>完全包含 → 返回 node.size</div>
          <p>不用收集每个点，因此计数没有 O(r) 输出项。</p>
          <div class='callout'><strong>不变式</strong><br>子树点全部在 B 中，size 等于子树点数。</div>
          <p>不相交分支不漏解；包含分支不增错；其余分支由当前点和两棵子树完整覆盖。按树归纳得正确性。</p>
          <p class='ref'>调用 count(root, lo, hi) 返回整数。计数与报告共用相同包围盒、闭区间与点包含判定。</p>
        </div>
      </div>
    `
  },
  {
    id: 's09',
    title: '一般 d 维复杂度推导',
    kicker: 'DERIVATION',
    purpose: '完整说明经典条件下范围查询为何达到 O_d(N^(1−1/d)+r)。',
    duration: 135,
    notes: [
      '前提是固定 d≥2 的静态中位数平衡 KD-tree，循环选轴，并回答轴对齐盒查询；证明使用经典划分区域，采用一般位置假设，避开查询边界与切分面重合。',
      '沿一个边界超平面看访问：完整一轮 d 层后规模缩至约 N/2^d；法向轴只进入一侧，其余 d−1 轴每层最多进入两侧，故最多 2^(d−1) 个子问题。固定 d 层内的工作计为 O_d(1)，得到递推。',
      '令 a=2^(d−1)、b=2^d。展开 j 轮，T_d(N)≤a^j T_d(N/b^j)+C_d∑_{i=0}^{j−1}a^i；每一轮产生 a 倍边界子问题，每个规模缩小 b 倍。',
      '取 L≈log_b N，使叶子规模为常数。由于 d≥2，所以 a>1，几何级数和为 O_d(a^L)，叶子数也是 O_d(a^L)。代入 a^L=N^(log_b a)=N^((d−1)/d)，得到边界访问上界。',
      '查询盒有 2d 个面，固定 d 只乘依赖 d 的常数。紧包围盒可加强剪枝；但任意选轴、动态非中位数树或未处理退化几何时，不能直接引用这一证明。'
    ],
    transition: '再把边界访问与输出点数合在一起。',
    body: `
      <div class='tag'>固定 d ≥ 2 · 静态中位数平衡 · 循环选轴 · 轴对齐查询盒 · 一般位置</div>
      <div class='analysis-grid'>
        <div class='analysis-copy'>
          <div class='proof-step'><span class='tag'>01 / 数边界穿过的区域</span>
            取查询盒的一张边界超平面。完整 d 层中，法向轴只进入一侧，其余 d−1 轴最多各进入两侧。
            <div class='formula'>子问题数 a = 1 · 2<sup>d−1</sup><br>规模缩小倍数 b = 2<sup>d</sup></div>
          </div>
          <div class='proof-step'><span class='tag'>02 / 写出递推</span>
            <div class='formula'>T<sub>d</sub>(N) ≤ a T<sub>d</sub>(N/b) + C<sub>d</sub></div>
            C<sub>d</sub> 是固定 d 层内的工作，可依赖维度；T<sub>d</sub>(O(1)) = O<sub>d</sub>(1)。
          </div>
          <div class='callout'>d=3：a=4、b=8。每轮最多 4 个子问题，规模各缩至约 1/8。</div>
        </div>
        <div class='analysis-copy'>
          <div class='proof-step'><span class='tag'>03 / 展开 j 轮，不直接跳到结果</span>
            <div class='formula'>T<sub>d</sub>(N) ≤ a<sup>j</sup>T<sub>d</sub>(N/b<sup>j</sup>)<br>＋ C<sub>d</sub> ∑<sub>i=0</sub><sup>j−1</sup>a<sup>i</sup></div>
          </div>
          <div class='proof-step'><span class='tag'>04 / 展开到常数规模</span>
            取 L ≈ log<sub>b</sub>N。因 a &gt; 1，几何级数与叶子项均为 O<sub>d</sub>(a<sup>L</sup>)。
            <div class='formula'>a<sup>L</sup> = N<sup>log<sub>b</sub>a</sup><br>log<sub>2<sup>d</sup></sub>2<sup>d−1</sup> = (d−1)/d</div>
          </div>
          <div class='derivation-result'>T<sub>d</sub>(N) = O<sub>d</sub>(N<sup>1−1/d</sup>)</div>
        </div>
      </div>
      <p class='ref'>先分析一张边界；查询盒有 2d 个面，固定 d 时只增加常数因子。下一页再计入输出成本。</p>
    `
  },
  {
    id: 's10',
    title: '报告、计数与维度',
    kicker: 'COMPLEXITY',
    purpose: '区分范围报告与范围计数，并说明二维、三维及一般维度的结论边界。',
    duration: 60,
    notes: [
      '范围报告必须支付输出成本 Ω(r)，在经典静态条件与 d≥2 下为 O_d(N^(1−1/d)+r)；完全包含时也仍需遍历并输出 r 个点。Python 实现按树遍历顺序返回，仅在展示导出与验证时排序 ID；核心查询不增加 r log r 排序开销。',
      '范围计数在完全包含时直接读 size，不需要逐点输出，因此为 O_d(N^(1−1/d))；这是结论差异来自输出要求，不是计数遗漏了数据。',
      '二维报告为 O(√N+r)，三维为 O(N^(2/3)+r)。随着 d 增长，指数趋近 1，隐藏常数和逐维成本也变化，不能宣称高维仍高效。',
      'd=1 要单独处理：平衡有序树配合子树大小可做 O(log N+r) 报告、O(log N) 计数，不能把退化递推直接代入。'
    ],
    transition: '范围查询之后，转向只需要最近一点的查询。',
    body: `
      <div class='two-col'>
        <div class='formula'>报告：<i>O</i><sub>d</sub>(<i>N</i><sup>1−1/d</sup> + <i>r</i>)</div>
        <div class='formula'>计数：<i>O</i><sub>d</sub>(<i>N</i><sup>1−1/d</sup>)</div>
      </div>
      <table class='mini-table'>
        <thead><tr><th>维度</th><th>报告</th><th>计数</th></tr></thead>
        <tbody>
          <tr><td>d = 2</td><td>O(√N + r)</td><td>O(√N)</td></tr>
          <tr><td>d = 3</td><td>O(N<sup>2/3</sup> + r)</td><td>O(N<sup>2/3</sup>)</td></tr>
          <tr><td>固定 d ≥ 2</td><td>O<sub>d</sub>(N<sup>1−1/d</sup> + r)</td><td>O<sub>d</sub>(N<sup>1−1/d</sup>)</td></tr>
        </tbody>
      </table>
      <div class='analysis-grid'>
        <div class='callout'><strong>为何加 r？</strong><br>边界区域继续展开；完整包含的子树停止几何判断。报告仍需逐点输出，共 O(r)；计数直接加 size，无输出项。</div>
        <div class='callout'><strong>为何单独处理 d=1？</strong><br>此时 a=1，展开式的和为 L 而非几何增长，恢复 O(log N)；高维时指数趋近 1，剪枝可能减弱。</div>
      </div>
    `
  },
  {
    id: 's11',
    title: '最近邻的距离下界',
    kicker: 'NEAREST NEIGHBOR',
    purpose: '用查询点到包围盒的最小距离决定优先顺序和子树剪枝。',
    duration: 85,
    notes: [
      '对查询点 q 与包围盒 B，逐维计算 q 到闭区间的距离 δ_i；若 q_i 已在区间内则 δ_i=0，否则是到最近端点之差。',
      '平方和得到点 q 到整个包围盒的最小距离下界。B 中任何点都不可能比这个下界更近，因此当下界严格大于当前 best² 时可以整棵剪枝。',
      '优先访问距离下界较小的子树，通常更早得到好候选，从而扩大后续剪枝；但精确最近邻最坏仍可能访问全部点，固定 d 时为 O(N)。',
      '统一采用“严格大于 best² 才剪枝”，这样等距点仍有机会按最小 ID 更新。比较平方距离避免重复开方，树高 O(log N) 不等于最近邻最坏 O(log N)。',
      '三维例子 q=(6,3,3) 的最近点为 B=(5,4,2)，距离平方 (−1)²+1²+1²=3；三维搜索球只用于说明，公式对一般 d 维成立。'
    ],
    transition: '回放优先访问、候选更新和距离剪枝。',
    body: `
      <div class='two-col'>
        <div>
          <div class='formula small'>δ<sub>i</sub> = max(l<sub>i</sub> − q<sub>i</sub>, 0, q<sub>i</sub> − u<sub>i</sub>)</div>
          <div class='formula'>dist<sub>min</sub><sup>2</sup>(q, B) = ∑<sub>i=1</sub><sup>d</sup> δ<sub>i</sub><sup>2</sup></div>
          <div class='callout'><strong>剪枝</strong>　dist<sub>min</sub><sup>2</sup>(q, B) &gt; best<sup>2</sup></div>
          <p class='lead'>先访问下界更小的子树。</p>
        </div>
        <div class='viz' data-demo='nearest'></div>
      </div>
      <p class='ref'>3D 实例：q=(6,3,3) → B=(5,4,2)，距离平方 3。比较平方距离，不用开方。</p>
    `
  },
  {
    id: 's12',
    title: '最近邻代码与查询成本',
    kicker: 'TRADEOFFS',
    purpose: '汇总静态构建、存储和各查询的最坏结论，避免把不同前提混为一谈。',
    duration: 55,
    notes: [
      '本页代码从 demo/teaching.py 原样提取。best 是距离平方、ID、点组成的元组；唯一 ID 保证等距时比较到 ID 即可确定答案。空树返回 None 与无穷大。',
      'lower_bound 复用完整实现的 d 维点到包围盒距离公式；distance2 复用 d 维欧氏距离平方。只有下界严格大于候选距离才剪枝，因此保留等距更小 ID 的可能。',
      '每节点至多两个孩子，排序项数固定；距离及包围盒操作每次 O(d)，访问 V 个节点为 O(dV)，最坏 V=N。树高不能限制全部回溯的总访问量。',
      '代码片段省略输入校验和事件记录，但可执行且已与完整实现随机对照。建树与范围查询的一般维度结论沿用前面各页的前提，不能由最近邻实验反推最坏对数界。'
    ],
    transition: '持续插入后，前面的静态平衡前提还成立吗？',
    body: `
      <div class='analysis-grid query-code'>
        <div data-code="nearest"></div>
        <div class='analysis-copy'>
          <div class='proof-step'><span class='tag'>候选与等距规则</span>best 保存（距离平方、ID、点）。先比较距离，再以 ID 打破平局。</div>
          <div class='proof-step'><span class='tag'>严格大于才剪枝</span>下界等于 best[0] 时继续搜索，以免遗漏更小 ID 的等距点。</div>
          <div class='proof-step'><span class='tag'>先搜索下界小的子树</span>至多两个孩子，排序项数固定，不引入 log N 因子。</div>
          <div class='formula'>访问 V 个节点 → O(dV)<br>V ≤ N ⇒ 最坏 O(dN)</div>
          <p>树高限制单条路径，不能限制所有回溯路径的总访问量。</p>
          <p class='ref'>lower_bound 是上一页的包围盒距离下界；distance2 是 d 维欧氏距离平方。空树返回 (None, inf)。</p>
        </div>
      </div>
    `
  },
  {
    id: 's13',
    title: '插入如何破坏平衡',
    kicker: 'DYNAMIC INSERT',
    purpose: '展示普通 KD-tree 插入路径，并用单调序列说明平衡可能退化为链。',
    duration: 55,
    notes: [
      '新点从根开始，按当前节点的划分轴比较并递归进入一侧；到达空位置后建立叶子，再沿路径回溯更新 size 和 bbox。',
      '若插入顺序持续偏向同一侧，静态建树时获得的平衡会消失；最坏树高 h=Θ(N)，插入路径和部分查询都可能退化。',
      '一般 d 维链例是 p_t=(t,t,…,t)：无论当前轴是哪一维，新点都进入右侧，因此形成单链，这与随机点云的平均形态不同。',
      '这类极端序列用于说明结构风险，不代表所有持续插入都会退化；下一页才对相同序列启用局部重建进行对照。'
    ],
    transition: '用局部重建把偏离平衡的子树拉回来。',
    body: `
      <div class='two-col'>
        <div>
          <div class='formula small'>比较当前轴 → 递归一侧 → 回溯维护</div>
          <div class='formula'>p<sub>t</sub> = (t, t, …, t)</div>
          <div class='formula'>h = Θ(N)</div>
          <p class='lead'>每一轴都向右，形成单链。</p>
        </div>
        <div class='viz' data-demo='insertion'></div>
      </div>
      <div class='callout'>回溯必须同步更新 <span class='mono'>size</span> 与 <span class='mono'>bbox</span>；单调序列只说明退化风险。</div>
    `
  },
  {
    id: 's14',
    title: '局部重建恢复树高',
    kicker: 'REBUILDING',
    purpose: '借鉴替罪羊树的局部重建思想，在插入路径上修复最靠近根的失衡子树。',
    duration: 85,
    notes: [
      'α 是允许的最大孩子占比：max(size(L),size(R))/size(u) 不超过 α 时满足大小平衡约束。分母是以 u 为根的整棵子树，包含 u 自身，不是左右孩子点数之和；这个比例衡量节点数量，不衡量三维空间体积。',
      '本例 α=0.75，表示任一孩子最多占整棵子树的 75%。例如 size(u)=12，左右孩子为 9 和 2，9/12=0.75，不触发；再向大孩子插入一点，比例变为 10/13≈0.769，严格超过阈值，触发重建。',
      '取 1/2<α<1：高于 1/2 为中位数平衡后的插入留出余量，低于 1 才能保证沿路径规模按固定比例缩小。α 越小，约束越严格，通常重建更积极、树更矮；越接近 1，容忍偏斜越大，重建可能更少但路径更长。固定 α 不随 N 改变，复杂度常数依赖它。',
      '一次插入后，在路径上选最靠近根的失衡节点，只重建这一棵子树一次。收集全部点，从该子树根的原有深度重新循环选轴、按中位数递归建树。',
      '重建完成后接回原树，更新祖先 size 与 bbox，点数不变、内部树高降低。这借鉴替罪羊树的局部重建思想；KD-tree 各层承担不同维度的划分约束，不能直接套用普通搜索树旋转。'
    ],
    transition: '重建能把树高压下来，但代价和保证到哪里？',
    body: `
      <div class='formula small'>max(size(L), size(R)) &gt; α · size(u),　α ∈ (1/2, 1)</div>
      <div class='two-col'>
        <div class='analysis-copy'>
          <div class='proof-step'><span class='tag'>α / 最大孩子占比阈值</span>
            <p>允许任一孩子占整棵子树的比例上限。分母 size(u) 包含当前节点自身。</p>
          </div>
          <div class='proof-step'><span class='tag'>本例 α = 0.75</span>
            <p>9/12 = 75%：不触发。<br>向大孩子再插一点：10/13 ≈ 76.9%，触发。</p>
          </div>
          <div class='proof-step'><span class='tag'>小 α 更严格，大 α 更宽松</span>
            <p>α ↓：通常更频繁重建、树更矮。<br>α ↑：容忍更偏的树，路径可能更长。</p>
          </div>
          <p class='ref'>触发后：收集点 → 中位数重建 → 接回并维护。</p>
        </div>
        <div class='viz' data-demo='dynamic'></div>
      </div>
      <p class='ref'>固定 1/2 &lt; α &lt; 1：为插入留出余量，同时保证沿路径规模收缩；α 衡量点数比例，不是空间体积。</p>
    `
  },
  {
    id: 's15',
    title: '重建成本与摊还分析',
    kicker: 'COST MODEL',
    purpose: '区分单次最坏、树高与插入序列摊还成本，并推导当前重建实现的上界。',
    duration: 90,
    notes: [
      '前提为从空树开始只插入唯一 ID 的点，固定 α∈(1/2,1)，选最高失衡子树重建，重建使用中位数循环选轴，关闭 trace 和快照；N 为整个插入序列的最大规模。ID 哈希操作按平均/摊还平均 O(1) 计。',
      '一次规模 m 的重建包括 O(m) 收集和排序建树，合计 C(m)=O(m log²m+dm)。正常路径 O(d log N)；根级重建时单次最坏达到 O(N log²N+dN) 上界。每次更新结束后全部节点满足 α 约束，所以树高至多 1+log_(1/α)N。',
      '重建后的节点初始子树规模 s，任一孩子至多 s/2。该节点生命周期内又插入 t 个点，现规模 m=s+t，大孩子至多 s/2+t。触发时 αm<s/2+t=m/2+t/2，故 t>(2α−1)m=Ω_α(m)。祖先重建会结束这个生命周期，并产生新的中位数子树。',
      '每次插入给路径上每个节点分别存 O_α(log²N+d) 信用，包括未来的候选节点自身。信用绑定 Node 实例而非点 ID；后代重建不清空祖先账户。重建只花候选账户，旧子树所有节点及未用账户作废，新节点从零开始。候选已有 Ω_α(m) 次存款足以支付 C(m)，每条路径 O_α(log N) 个分别计费的账户，故摊还 O_α(log³N+d log N)。',
      '若改用有最坏线性保证的中位数选择，C(m)=O(m log m+dm)，同法得到 O_α(log²N+d log N)。这些是本实现策略的保守摊还上界，不是紧界、单次保证或动态范围查询界；删除、trace 和完整快照不在本分析中。'
    ],
    transition: '最后用实验验证实现，再讨论适用场景。',
    body: `
      <div class='analysis-grid'>
        <div class='analysis-copy'>
          <div class='proof-step'><span class='tag'>01 / 单次成本</span>
            <p>收集 O(m)；递归排序加包围盒合并：</p>
            <div class='formula'>C(m) = O(m log<sup>2</sup>m + dm)</div>
            <p>正常路径 O(d log N)；根级重建时，单次最坏上界为 O(N log<sup>2</sup>N+dN)。</p>
          </div>
          <div class='proof-step'><span class='tag'>02 / 树高保证</span>
            <div class='formula'>1 ≤ α<sup>k</sup>N ⇒ h ≤ 1+log<sub>1/α</sub>N</div>
            <p>候选以上已平衡且点数不变；以下整体重建，路径外不变，故恢复全树 α 约束。</p>
          </div>
          <div><span class='tag'>理论优化版本</span>若 C(m)=O(m log m+dm)，同法得到摊还 O<sub>α</sub>(log<sup>2</sup>N+d log N)。</div>
        </div>
        <div class='analysis-copy'>
          <div class='proof-step'><span class='tag'>03 / 重建之间至少多少插入？</span>
            <p>初始规模 s，中位数划分后孩子 ≤ s/2；新增 t 点，m=s+t。</p>
            <div class='formula'>αm &lt; s/2+t = m/2+t/2<br>⇒ t &gt; (2α−1)m = Ω<sub>α</sub>(m)</div>
          </div>
          <div class='proof-step'><span class='tag'>04 / 分摊给路径上的更新</span>
            <p>每个祖先每次存 O<sub>α</sub>(log<sup>2</sup>N+d) 信用，足够支付下一次 C(m)。每条路径有 O<sub>α</sub>(log N) 个祖先。</p>
            <div class='formula'>摊还插入：O<sub>α</sub>(log<sup>3</sup>N+d log N)</div>
          </div>
            <p class='ref'>信用绑定节点实例，重建后旧账户作废。仅从空树纯插入、固定 α、关闭追踪；N 为序列最大规模。</p>
        </div>
      </div>
      <p class='ref'>单次最坏 ≠ 摊还上界 ≠ 动态查询界。上述摊还界按本次重建策略推导，不直接套用普通替罪羊树的 O(log N)。</p>
    `
  },
  {
    id: 's16',
    title: '用实验验证什么',
    kicker: 'EXPERIMENTS',
    purpose: '把正确性验证、规模效应、维度效应与重建效果拆成可控制的实验。',
    duration: 55,
    notes: [
      '先做正确性实验：同一数据、同一查询分别运行 KD-tree 与暴力方法，比较范围报告 ID 集合、计数、最近距离和约定 ID。',
      '规模实验固定 d=3 增加 N；维度实验固定 N 改变 d。范围盒每维边长可取 ρ^(1/d) 以近似固定体积比例，并同时报告实际 r；这只能控制变量，不能单独证明维度效应。',
      '性能数据与手工演示点集分开，建议随机种子 42。建树和查询分开计时，多轮报告中位数；关闭动画和事件记录，访问量计数需保持各方法开销可比。',
      '重建实验使用同一单调插入序列，对照启用与关闭重建，报告树高、累计插入时间、重建次数和重建规模。所有数值都来自实际运行，不在幻灯里预填倍数。'
    ],
    transition: '这些操作最终落到哪些实际任务？',
    body: `
      <div id='benchmark-chart'></div>
      <div class='two-col'>
        <div>
          <div class='tag'>CORRECTNESS</div>
          <div class='tag'>SCALE · d = 3</div>
          <div class='tag'>DIMENSION · fixed N</div>
          <div class='tag'>REBUILD on / off</div>
        </div>
        <div class='mini-table'>
          <table>
            <thead><tr><th>指标</th><th>记录</th></tr></thead>
            <tbody>
              <tr><td>时间</td><td>建树 / 查询分开，多轮中位数</td></tr>
              <tr><td>访问与输出</td><td>访问节点数 / 访问比例 / 输出点数 r</td></tr>
              <tr><td>动态</td><td>树高 / 重建次数 / 重建规模</td></tr>
            </tbody>
          </table>
        </div>
      </div>
      <p class='ref'>Python 实测 · 固定随机种子 · 每批查询运行 3 轮取中位数 · 动画与事件追踪不计入耗时。</p>
    `
  },
  {
    id: 's17',
    title: '应用与结构选择',
    kicker: 'APPLICATION',
    purpose: '把范围与最近邻操作对应到实际任务，并给出选择 KD-tree 前的判断维度。',
    duration: 40,
    notes: [
      '三维点云中的区域裁剪对应范围报告，邻域检索常需要最近点候选；空间检索需让坐标与度量匹配查询形状，例如地理距离不能直接当作普通欧氏盒。',
      '适合的低维机器学习数据可以用 KD-tree 加速近邻候选；高维时剪枝可能失效，可比较其他空间树、网格或近似索引。',
      '选型前检查维度、数据分布、查询形状、更新频率、输出规模与存储预算。相同算法在不同条件下是可取舍的方案。',
      '应用页只对应本次已分析的操作；其他索引的复杂度和优势需要单独前提，不能在这里直接比较成统一排名。'
    ],
    transition: '回到结构与查询，用四个判断收束。',
    body: `
      <div class='two-col'>
        <div>
          <ul class='bullets'>
            <li><strong>点云</strong>　区域裁剪与邻域候选</li>
            <li><strong>空间检索</strong>　轴对齐区域筛选</li>
            <li><strong>机器学习</strong>　适合低维的近邻搜索</li>
          </ul>
        </div>
        <div>
          <div class='tag'>选择前核对</div>
          <p class='lead'>维度 × 分布 × 查询形状 × 更新频率 × 输出规模 × 存储预算</p>
        </div>
      </div>
      <div class='callout'>开头场景可以闭环：范围查询取工作区域，最近邻找最近采样点，持续采样时局部重建维持树高。</div>
    `
  },
  {
    id: 's18',
    title: '总结：结构与查询',
    kicker: 'SUMMARY',
    purpose: '用结构、查询、分析和维护四条主线收束全部结论并进入答问。',
    duration: 30,
    notes: [
      '结构上，KD-tree 用循环选轴和中位数划分组织多维点；查询上，范围查询利用包含关系，最近邻利用包围盒距离下界。',
      '分析上，在固定 d≥2、静态中位数平衡与经典一般位置条件下，范围报告为 O_d(N^(1−1/d)+r)，范围计数去掉输出项 r。',
      '维护上，固定 α 的局部重建可以恢复 O(log N) 树高；对从空树开始的纯插入序列，递归排序版本已推导 O_α(log³N+d log N) 保守摊还上界，动态查询界仍需另外分析。',
      '答问时可强调：树高不等于查询总访问量；报告与计数不同；一般维度公式与三维示意图是同一算法在不同表达层。'
    ],
    transition: '进入提问与讨论。',
    body: `
      <div class='two-col'>
        <div>
          <div class='tag'>01 STRUCTURE</div>
          <p class='lead'>循环选轴 × 中位数划分</p>
          <div class='tag'>02 QUERY</div>
          <p class='lead'>包含关系 × 距离下界</p>
        </div>
        <div>
          <div class='formula small'>R(N, r) = O<sub>d</sub>(N<sup>1−1/d</sup> + r)</div>
          <div class='formula small'>C(N) = O<sub>d</sub>(N<sup>1−1/d</sup>)</div>
          <p class='muted'>固定 d≥2 · 经典静态条件</p>
        </div>
      </div>
      <div class='callout'><strong>动态维护</strong>　局部重建保证树高，不自动保证查询或摊还更新界。</div>
      <p class='ref'>[1] <a href='https://algs4.cs.princeton.edu/92search/' target='_blank' rel='noreferrer'>Sedgewick &amp; Wayne · Geometric Search</a>　　[2] <a href='https://opendatastructures.org/ods-python/8_1_ScapegoatTree_Binary_Se.html' target='_blank' rel='noreferrer'>Morin · ScapegoatTree / partial rebuilding</a></p>
    `
  }
];
