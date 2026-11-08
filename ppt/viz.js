/* Python-generated event replay. No KD-tree query algorithm is reimplemented here. */
(() => {
  'use strict';
  const D = window.KD_DATA;
  if (!D) return;
  const allSlides = [...document.querySelectorAll('#deck>.slide')];
  const containers = [...document.querySelectorAll('#deck .viz')];
  const states = new Map();
  let active = null, timer = null, renderer = null, scene, camera, group, canvas;
  let dragging = null;
  const defaultCamera = {yaw:.76, pitch:.48, zoom:1};
  const flat = n => n ? [n,...flat(n.left),...flat(n.right)] : [];
  const nodes = flat(D.tree), nodeById = new Map(nodes.map(n=>[String(n.id),n]));
  const coords = p => p.coords || p.point;
  const minOf = b => b?.min || b?.lower;
  const maxOf = b => b?.max || b?.upper;
  const titleMap={visit:'访问节点',prune_disjoint:'不相交 · 跳过子树',accept_subtree:'完全包含 · 接收子树',point_hit:'单点命中',update_best:'更新最近候选',prune_distance:'距离下界过大 · 剪枝',build:'选取中位数并划分'};
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function getEvents(kind){
    if(kind==='build')return D.buildEvents||[];
    if(kind==='range')return D.range.events;
    if(kind==='nearest')return D.nearest.events;
    if(kind==='dynamic'||kind==='insertion')return D.dynamic.steps;
    return [];
  }
  function maxStep(s){return getEvents(s.kind).length;}
  function insertionPlot(s){
    const root=s.step?D.dynamic.steps[s.step-1].plainTree:null;
    const raw=flat(root),factor=16/(D.dynamic.steps.length+1);
    return {root,points:raw.map(n=>({id:n.id,coords:n.point.map(v=>v*factor)})),factor};
  }
  function stateFor(el){return states.get(el.closest('.slide').dataset.slideId);}
  function colors(){
    const dark=active?.el.closest('.slide').classList.contains('dark');
    return {paper:dark?0x0a0a0a:0xffffff, ink:dark?0xffffff:0x333333, grid:dark?0x444444:0xd4d4d2,blue:dark?0x96b0ff:0x002fa7,muted:dark?0x777777:0xaaaaaa};
  }
  function eventsState(s){
    const out={hits:new Set(),pruned:new Set(),visited:new Set(),built:new Set(),current:null,bestId:null,bestSquared:null,event:null};
    if(s.kind==='overview'){['B','C','F','H'].forEach(id=>out.hits.add(id));return out;}
    if(s.kind==='insertion'){
      const raw=flat(insertionPlot(s).root);
      out.current=raw.at(-1)?.id||null;
      raw.forEach(n=>out.built.add(String(n.id)));
      if(out.current)out.hits.add(out.current);
      return out;
    }
    for(const e of getEvents(s.kind).slice(0,s.step)){
      const id=String(e.nodeId??e.id??'');out.current=id;out.event=e;
      if(e.type==='visit')out.visited.add(id);
      if(s.kind==='build')out.built.add(id);
      if(e.type==='point_hit')out.hits.add(id);
      if(e.type==='accept_subtree')flat(nodeById.get(id)).forEach(n=>out.hits.add(String(n.id)));
      if(e.type==='prune_disjoint'||e.type==='prune_distance')flat(nodeById.get(id)).forEach(n=>out.pruned.add(String(n.id)));
      if(e.type==='update_best'){
        out.bestId=String(e.bestId??id);
        out.bestSquared=e.bestSquared??e.distanceSquared??e.distance_squared;
      }
    }
    if(s.kind==='nearest'&&s.step===maxStep(s)){
      out.bestId=String(D.nearest.result);out.bestSquared=D.nearest.distanceSquared;
    }
    if(out.bestId)out.hits.add(out.bestId);
    return out;
  }
  function makeUI(el){
    const slide=el.closest('.slide');
    const s={id:slide.dataset.slideId,kind:el.dataset.demo,el,step:0,camera:{...defaultCamera}};
    if(s.kind==='dynamic')s.step=D.dynamic.steps.length;
    if(s.kind==='build')s.step=1;
    if(s.kind==='overview')s.step=0;
    el.innerHTML=`<div class="viz-stage">${s.kind==='dynamic'?'<div class="dynamic-stage"><div class="viz-tree plain"><div class="tree-title">PLAIN · 无重建</div><div class="tree-map"></div></div><div class="viz-tree balanced"><div class="tree-title">REBUILD · α = 0.75</div><div class="tree-map"></div></div></div>':'<div class="viz-3d"><div class="viz-labels"></div></div><div class="viz-tree"><div class="tree-title">'+(s.kind==='insertion'?'PLAIN · 无重建':'TREE / AXIS')+'</div><div class="tree-map"></div></div>'}</div>
    <div class="viz-toolbar"><button type="button" data-action="prev" aria-label="上一步">上一步</button><button type="button" data-action="next" aria-label="下一步">下一步</button><button type="button" data-action="play">播放</button><button type="button" data-action="reset">重置</button><button type="button" data-action="camera">视角复位</button><span class="step-count"></span></div><div class="viz-status" aria-live="polite"></div>`;
    if(s.kind==='overview')el.querySelector('.viz-toolbar').style.display='none';
    el.addEventListener('click',e=>{const btn=e.target.closest('button[data-action]');if(!btn)return;action(s,btn.dataset.action);e.stopPropagation();});
    el.addEventListener('wheel',e=>e.stopPropagation(),{passive:true});
    el.addEventListener('touchstart',e=>e.stopPropagation(),{passive:true});
    el.addEventListener('touchend',e=>e.stopPropagation(),{passive:true});
    states.set(s.id,s);return s;
  }
  function drawTree(host,root,marks,dynamic=false){
    if(!host)return;
    if(!root){host.innerHTML='';return;}
    const list=[],lines=[];let rank=0,maxDepth=0;
    function visit(n,depth){if(!n)return null;const left=visit(n.left,depth+1);const p={n,rank:rank++,depth};list.push(p);maxDepth=Math.max(maxDepth,depth);const right=visit(n.right,depth+1);if(left)lines.push([p,left]);if(right)lines.push([p,right]);return p;}
    visit(root,0);
    const x=p=>4+(p.rank+.5)/rank*92;
    const y=p=>5+(p.depth+.5)/(maxDepth+1)*90;
    let html='<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">';
    for(const [a,b]of lines)html+=`<line x1="${x(a)}" y1="${y(a)}" x2="${x(b)}" y2="${y(b)}" stroke="currentColor" opacity=".25" stroke-width=".4" vector-effect="non-scaling-stroke"/>`;
    html+='</svg>';
    for(const p of list){const id=String(p.n.id);let cl='tree-node';if(marks.hits.has(id))cl+=' hit';if(marks.pruned.has(id))cl+=' pruned';if(marks.current===id)cl+=' current';html+=`<span class="${cl}" style="left:${x(p)}%;top:${y(p)}%" title="${esc(id)} · ${'xyz'[p.n.axis]||p.n.axis} · (${p.n.point})">${esc(dynamic?id.replace(/^[PT]0?/,''):id)}</span>`;}
    host.innerHTML=html;
  }
  function initializeRenderer(){
    if(canvas)return;
    if(window.THREE){
      try{
        renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});
        renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));canvas=renderer.domElement;
        scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(38,1,.1,300);group=new THREE.Group();scene.add(group);
      }catch(e){console.warn('WebGL unavailable; using static projection',e);}
    }
    if(!canvas){canvas=document.createElement('canvas');canvas.dataset.fallback='2d';}
    canvas.setAttribute('aria-label','三维点云，拖动调整视角');
    canvas.addEventListener('pointerdown',e=>{if(!active)return;dragging={x:e.clientX,y:e.clientY,yaw:active.camera.yaw,pitch:active.camera.pitch};canvas.setPointerCapture(e.pointerId);e.stopPropagation();});
    canvas.addEventListener('pointermove',e=>{if(!dragging||!active)return;active.camera.yaw=dragging.yaw+(e.clientX-dragging.x)*.008;active.camera.pitch=Math.max(-1.2,Math.min(1.2,dragging.pitch+(e.clientY-dragging.y)*.008));render3D(active,eventsState(active));broadcast(active);});
    canvas.addEventListener('pointerup',e=>{dragging=null;e.stopPropagation();});
    canvas.addEventListener('pointercancel',()=>dragging=null);
  }
  function box(min,max,color,opacity=.3,fill=false){
    const size=max.map((x,i)=>Math.max(.02,x-min[i]));
    const geo=new THREE.BoxGeometry(...size);
    let obj;
    if(fill)obj=new THREE.Mesh(geo,new THREE.MeshBasicMaterial({color,transparent:true,opacity,depthWrite:false,side:THREE.DoubleSide}));
    else {const edges=new THREE.EdgesGeometry(geo);geo.dispose();obj=new THREE.LineSegments(edges,new THREE.LineBasicMaterial({color,transparent:true,opacity}));}
    obj.position.set(...min.map((v,i)=>(v+max[i])/2-8));group.add(obj);return obj;
  }
  function line(a,b,color,opacity=1){
    const geo=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a.map(v=>v-8)),new THREE.Vector3(...b.map(v=>v-8))]);
    group.add(new THREE.Line(geo,new THREE.LineBasicMaterial({color,transparent:true,opacity})));
  }
  function clearScene(){
    while(group.children.length){const child=group.children[0];group.remove(child);child.traverse(o=>{o.geometry?.dispose();if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material?.dispose();});}
  }
  function render3D(s,marks){
    const host=s.el.querySelector('.viz-3d');if(!host)return;
    initializeRenderer();if(canvas.parentElement!==host){
      const oldHost=canvas.parentElement;
      if(oldHost){let poster=oldHost.querySelector('.viz-poster');if(!poster){poster=document.createElement('img');poster.className='viz-poster';poster.alt='三维场景静态帧';oldHost.prepend(poster);}try{poster.src=canvas.toDataURL('image/png');}catch(e){}}
      host.querySelector('.viz-poster')?.remove();host.prepend(canvas);
    }
    const width=host.clientWidth,height=host.clientHeight;if(!width||!height)return;
    const C=colors(),labels=host.querySelector('.viz-labels');labels.innerHTML='';
    if(!renderer){renderFallback(s,marks,width,height);return;}
    renderer.setSize(width,height,false);renderer.setClearColor(C.paper);camera.aspect=width/height;camera.updateProjectionMatrix();
    const r=36/s.camera.zoom;camera.position.set(r*Math.cos(s.camera.pitch)*Math.sin(s.camera.yaw),r*Math.sin(s.camera.pitch),r*Math.cos(s.camera.pitch)*Math.cos(s.camera.yaw));camera.lookAt(0,0,0);camera.updateMatrixWorld();
    // Logical coordinate z maps directly to WebGL z; axis labels remove ambiguity.
    clearScene();box([0,0,0],[16,16,16],C.grid,.5);
    line([0,0,0],[16,0,0],C.ink,.6);line([0,0,0],[0,16,0],C.ink,.6);line([0,0,0],[0,0,16],C.ink,.6);
    const addLabel=(text,p,cls='')=>{const v=new THREE.Vector3(...p.map(v=>v-8)).project(camera);if(v.z>1)return;const el=document.createElement('span');el.className='viz-label '+cls;el.textContent=text;el.style.left=((v.x+1)/2*width)+'px';el.style.top=((-v.y+1)/2*height)+'px';labels.append(el);};
    addLabel('x',[17,0,0],'axis');addLabel('y',[0,17,0],'axis');addLabel('z',[0,0,17],'axis');
    const insertion=s.kind==='insertion'?insertionPlot(s):null;
    if(insertion)addLabel('坐标范围 0–32',[0,16,0],'axis');
    for(const p of insertion?insertion.points:D.points){const id=String(p.id),point=coords(p),hit=marks.hits.has(id),pruned=marks.pruned.has(id),current=marks.current===id;
      const mesh=new THREE.Mesh(new THREE.SphereGeometry((hit||current) ? .31 : .19,12,8),new THREE.MeshBasicMaterial({color:hit||current?C.blue:C.ink,transparent:true,opacity:pruned ? .14 : (s.kind==='build'&&s.step>0&&!marks.built.has(id) ? .3 : .9)}));
      mesh.position.set(...point.map(v=>v-8));group.add(mesh);if(!insertion||current||Number(id.slice(1))%5===0||id==='T01')addLabel(id,point);
    }
    if(s.kind==='range'||s.kind==='overview'){
      box(D.range.lower,D.range.upper,C.blue,.07,true);box(D.range.lower,D.range.upper,C.blue,.9);
    }
    if(s.kind==='build'||insertion){
      function partition(n,min,max,depth=0){if(!n)return;const value=n.point[n.axis]*(insertion?.factor||1);if(marks.built.has(String(n.id))&&(depth<3||marks.current===String(n.id))){const a=[...min],b=[...max];a[n.axis]=value;b[n.axis]=value+.025;box(a,b,C.blue,depth===0?.14:.07,true);box(a,b,C.blue,.4);}
        const lm=[...max],rm=[...min];lm[n.axis]=value;rm[n.axis]=value;partition(n.left,min,lm,depth+1);partition(n.right,rm,max,depth+1);}
      partition(insertion?insertion.root:D.tree,[0,0,0],[16,16,16]);
      if(insertion?.points.length>1)line(insertion.points.at(-2).coords,insertion.points.at(-1).coords,C.blue);
    }
    const currentNode=nodeById.get(marks.current);
    if(currentNode?.bbox&&s.kind!=='build')box(minOf(currentNode.bbox),maxOf(currentNode.bbox),C.blue,.65);
    if(s.kind==='nearest'){
      const q=D.nearest.query;
      const query=new THREE.Mesh(new THREE.OctahedronGeometry(.4),new THREE.MeshBasicMaterial({color:C.blue}));query.position.set(...q.map(v=>v-8));group.add(query);addLabel('q',q);
      if(marks.bestSquared!=null&&Number.isFinite(marks.bestSquared)){
        const sphere=new THREE.Mesh(new THREE.SphereGeometry(Math.sqrt(marks.bestSquared),24,16),new THREE.MeshBasicMaterial({color:C.blue,wireframe:true,transparent:true,opacity:.16}));sphere.position.copy(query.position);group.add(sphere);
        const best=nodeById.get(marks.bestId);if(best)line(q,best.point,C.blue,.9);
      }
    }
    renderer.render(scene,camera);
  }
  function renderFallback(s,marks,w,h){
    canvas.width=w*devicePixelRatio;canvas.height=h*devicePixelRatio;
    const ctx=canvas.getContext('2d');ctx.scale(devicePixelRatio,devicePixelRatio);const C=colors();const css=n=>'#'+n.toString(16).padStart(6,'0');
    ctx.fillStyle=css(C.paper);ctx.fillRect(0,0,w,h);
    const project=p=>{let [x,y,z]=p.map(v=>v-8);const a=s.camera.yaw,b=s.camera.pitch;const xx=x*Math.cos(a)+z*Math.sin(a),zz=-x*Math.sin(a)+z*Math.cos(a);return [w/2+xx*w/30,h/2+(-y*Math.cos(b)+zz*Math.sin(b))*h/28];};
    const edge=(a,b,col)=>{ctx.strokeStyle=col;ctx.beginPath();ctx.moveTo(...project(a));ctx.lineTo(...project(b));ctx.stroke();};
    const drawBox=(lo,hi,col)=>{for(let a=0;a<3;a++)for(let b=0;b<2;b++)for(let c=0;c<2;c++){let p=[...lo],q=[...lo];const other=[0,1,2].filter(i=>i!==a);p[other[0]]=q[other[0]]=b?hi[other[0]]:lo[other[0]];p[other[1]]=q[other[1]]=c?hi[other[1]]:lo[other[1]];q[a]=hi[a];edge(p,q,col);}};
    drawBox([0,0,0],[16,16,16],css(C.grid));
    if(s.kind==='range'||s.kind==='overview')drawBox(D.range.lower,D.range.upper,css(C.blue));
    const points=s.kind==='insertion'?insertionPlot(s).points:D.points;
    for(const p of points){const id=String(p.id),[x,y]=project(coords(p));ctx.globalAlpha=marks.pruned.has(id)?.2:1;ctx.fillStyle=css(marks.hits.has(id)||marks.current===id?C.blue:C.ink);ctx.beginPath();ctx.arc(x,y,marks.hits.has(id)?5:3,0,Math.PI*2);ctx.fill();ctx.font='12px sans-serif';ctx.fillText(id,x+5,y-5);}ctx.globalAlpha=1;
    ctx.fillStyle=css(C.muted);ctx.font='12px sans-serif';ctx.fillText('兼容模式 · 静态投影',10,h-10);
  }
  function render(s){
    const total=maxStep(s);s.step=Math.max(0,Math.min(total,s.step));const marks=eventsState(s);
    s.el.querySelector('.step-count').textContent=s.kind==='overview'?'3D':`${s.step} / ${total}`;
    s.el.querySelector('[data-action="prev"]').disabled=s.step===0;
    s.el.querySelector('[data-action="next"]').disabled=s.step===total;
    let status='拖动旋转视角；按“下一步”回放 Python 执行事件。';
    if(s.kind==='overview'){status='三维点云 / 长方体范围查询 · 拖动旋转';drawTree(s.el.querySelector('.tree-map'),D.tree,marks);if(active===s)render3D(s,marks);}
    else if(s.kind==='dynamic'){
      const step=D.dynamic.steps[Math.max(0,s.step-1)];
      const plain=step?.plainTree||D.dynamic.plainTree,balanced=step?.balancedTree||D.dynamic.balancedTree;
      drawTree(s.el.querySelector('.plain .tree-map'),s.step?plain:null,marks,true);drawTree(s.el.querySelector('.balanced .tree-map'),s.step?balanced:null,marks,true);
      status=s.step?`已插入 ${step.n} 点 · 树高 ${step.heightPlain} → ${step.heightBalanced} · ${step.rebuilds} 次重建`:'同序列 (t,t,t) 插入：左侧不维护，右侧局部重建。';
    }else if(s.kind==='insertion'){
      drawTree(s.el.querySelector('.tree-map'),insertionPlot(s).root,marks,true);
      if(active===s)render3D(s,marks);
      const step=D.dynamic.steps[s.step-1];
      status=step?`无重建插入 ${step.n} 点 · h = ${step.heightPlain} · 最新点 (${step.n}, ${step.n}, ${step.n})`:'从空树开始：每步插入一个 (t,t,t)，观察空间划分和右链。';
    }else{
      drawTree(s.el.querySelector('.tree-map'),D.tree,marks);
      if(active===s)render3D(s,marks);
      const e=marks.event;
      if(e){status=`${titleMap[e.type]||e.type} · ${marks.current}`;
        if(s.kind==='build')status+=` · ${'xyz'[e.axis]||e.axis} 轴 · 深度 ${e.depth}`;
        if(s.kind==='range')status+=` · 访问 ${marks.visited.size} 节点 · 已命中 ${marks.hits.size} 点`;
        if(s.kind==='nearest')status+=` · 候选 ${marks.bestId||'—'} · 距离² ${marks.bestSquared==null?'—':Number(marks.bestSquared).toFixed(2)}`;
      }
    }
    s.el.querySelector('.viz-status').textContent=status;
    s.el.querySelector('[data-action="play"]').textContent=timer&&active===s?'暂停':'播放';
    return marks;
  }
  function stop(){if(timer)clearInterval(timer);timer=null;for(const s of states.values())s.el.querySelector('[data-action="play"]').textContent='播放';}
  function action(s,command){
    if(command==='play'){
      if(timer){stop();broadcast(s);return;}
      if(s.step===maxStep(s))s.step=0;
      timer=setInterval(()=>{if(document.hidden||active!==s){stop();return;}s.step=Math.min(maxStep(s),s.step+1);render(s);broadcast(s);if(s.step===maxStep(s))stop();},650);
    }else{
      stop();if(command==='prev')s.step--;if(command==='next')s.step++;if(command==='reset')s.step=0;if(command==='camera')s.camera={...defaultCamera};
    }
    render(s);broadcast(s);
  }
  function snapshot(){return [...states.values()].map(s=>({id:s.id,step:s.step,camera:{...s.camera}}));}
  function apply(incoming){
    if(!Array.isArray(incoming))return;
    for(const data of incoming){const s=states.get(data.id);if(!s)continue;s.step=Math.max(0,Math.min(maxStep(s),Number(data.step)||0));if(data.camera)s.camera={...defaultCamera,...data.camera};render(s);}
  }
  function broadcast(s){
    const kd=snapshot();
    if(document.body.classList.contains('ppt-preview')){parent.postMessage({kdReplay:1,id:s.id,kd},'*');return;}
    window.__pptPresenter?.emitDemo(kd);
    if(document.body.classList.contains('ppt-presenter'))document.querySelectorAll('#ppt-presenter iframe').forEach(f=>f.contentWindow?.postMessage({kdReplay:2,kd},'*'));
  }
  function activate(index){
    stop();active=containers.find(el=>el.closest('.slide')===allSlides[index]);active=active?stateFor(active):null;
    if(active)render(active);
    refreshConsole();
  }
  function refreshConsole(){
    const notes=document.querySelector('.ppt-notes-card');if(!notes)return;
    let panel=notes.querySelector('.kd-demo-console');
    if(!panel){panel=document.createElement('div');panel.className='kd-demo-console';notes.append(panel);panel.addEventListener('click',e=>{const command=e.target.closest('[data-action]')?.dataset.action;if(command&&active)action(active,command);});}
    panel.hidden=!active||active.kind==='overview';
    if(!panel.hidden)panel.innerHTML='<span>算法回放</span><button data-action="prev">上一步</button><button data-action="next">下一步</button><button data-action="reset">重置</button><button data-action="camera">视角复位</button>';
  }
  containers.forEach(makeUI);
  window.KDViz={activate,snapshot,receive:apply,action:(command)=>active&&action(active,command),debug:()=>({active:active?.id,renderer:renderer?'webgl':'2d',states:snapshot()})};
  addEventListener('message',e=>{
    if(e.data?.kdReplay===1&&document.body.classList.contains('ppt-presenter')){
      if(![...document.querySelectorAll('#ppt-presenter iframe')].some(f=>f.contentWindow===e.source))return;
      apply(e.data.kd);broadcast(active);
    }else if(e.data?.kdReplay===2&&e.source===parent)apply(e.data.kd);
  });
  addEventListener('resize',()=>active&&render(active));
  addEventListener('swiss-low-power-change',()=>{stop();if(active)render(active);refreshConsole();});
  addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  new MutationObserver(refreshConsole).observe(document.body,{attributes:true,attributeFilter:['class']});
  activate(window.__currentSlideIndex||0);
  function renderBenchmarks(){
    const host=document.getElementById('benchmark-chart');if(!host)return;
    const b=D.benchmarks;
    if(!b){host.textContent='请运行 demo/generate.py 生成实验数据。';return;}
    const rows=b.bySize||[];
    host.innerHTML=`<div class="bench-grid"><div class="bench-panel"><h3>范围查询 · d=3</h3><div class="bench-scale"></div></div><div class="bench-panel"><h3>维度变化 · N=${b.byDimension?.[0]?.n||'—'}</h3><div class="bench-dimension"></div></div></div>`;
    const table=host.querySelector('.bench-scale');
    if(rows.length){const sample=rows.slice(0,4);table.innerHTML='<table class="mini-table"><tr><th>N</th><th>KD/ms</th><th>暴力/ms</th><th>访问占比</th></tr>'+sample.map(r=>`<tr><td>${r.n}</td><td>${Number(r.range_kd_ms_per_query).toFixed(3)}</td><td>${Number(r.range_brute_ms_per_query).toFixed(3)}</td><td>${(r.range_visited_ratio*100).toFixed(1)}%</td></tr>`).join('')+'</table>';}
    else table.innerHTML='<p class="muted">请生成规模实验数据。</p>';
    host.querySelector('.bench-dimension').innerHTML=(b.byDimension||[]).map(r=>`<div class="bar-row"><span class="bar-label">d = ${r.d}</span><span class="bar-track"><span class="bar-fill" style="width:${r.range_visited_ratio*100}%"></span></span><span class="bar-value">${(r.range_visited_ratio*100).toFixed(1)}%</span></div>`).join('')+'<p class="muted">访问节点比例；查询盒体积比例固定为 8%，输出数量另见原始记录。</p>';
  }
  renderBenchmarks();
})();
