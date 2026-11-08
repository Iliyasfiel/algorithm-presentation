"""Build a self-contained HTML deck from the guizang template and local assets."""
from pathlib import Path
import json
import re
import subprocess
import builtins
import html
import io
import keyword
import tokenize

ROOT = Path(__file__).resolve().parent


def script(text):
    return '<script>\n' + text.replace('</script', '<\\/script') + '\n</script>'


def highlight_python(match):
    """Tokenize at build time so highlighting also works offline and in previews."""
    source = html.unescape(match.group(1))
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    output, cursor, after_def = [], 0, False
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in (tokenize.ENDMARKER, tokenize.INDENT, tokenize.DEDENT,
                          tokenize.NEWLINE, tokenize.NL, tokenize.ENCODING):
            continue
        start = offsets[token.start[0] - 1] + token.start[1]
        end = offsets[token.end[0] - 1] + token.end[1]
        category = None
        if token.type == tokenize.NAME:
            if keyword.iskeyword(token.string):
                category = 'keyword'
            elif after_def:
                category = 'function'
            elif hasattr(builtins, token.string):
                category = 'builtin'
            after_def = token.string in ('def', 'class')
        else:
            category = {tokenize.STRING:'string', tokenize.NUMBER:'number',
                        tokenize.COMMENT:'comment', tokenize.OP:'operator'}.get(token.type)
        output.append(html.escape(source[cursor:start]))
        value = html.escape(source[start:end])
        output.append(f'<span class="tok-{category}">{value}</span>' if category else value)
        cursor = end
    output.append(html.escape(source[cursor:]))
    name = re.search(r'def\s+(\w+)', source)
    label = name.group(1).upper() if name else 'ALGORITHM'
    return '<div class="code-block"><div class="code-label">PYTHON / '+label+'</div><pre class="code"><code class="language-python">'+''.join(output)+'</code></pre></div>'


def main():
    content_path = ROOT / 'content.js'
    command = "const fs=require('fs'),vm=require('vm');let c={window:{}};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);process.stdout.write(JSON.stringify(c.window.KD_SLIDES));"
    slides = json.loads(subprocess.check_output(['node', '-e', command, str(content_path)], encoding='utf-8'))
    ids = ['cover','problem','partition','build-example','build-analysis','range-rules','range-demo','range-correctness','range-derivation','range-bounds','nearest','static-costs','insertion','rebuilding','rebuild-costs','experiments','applications','closing']
    layouts = ['S01','S03','S05','S08','S08','S13','S08','S05','S11','S08','S08','S21','S08','S14','S08','S07','S19','S10']
    themes = ['hero light' if i in (0,5,9,14,17) else 'light' for i in range(18)]
    recipes = ['hero','split-statement','stack-layers','duo-compare','duo-compare','three-forces','duo-compare','stack-layers','timeline-h','duo-compare','duo-compare','spec-sheet','duo-compare','loop-form','duo-compare','h-bar','four-cards','split-statement']
    pages, notes, plan = [], [], []
    teaching = (ROOT.parent/'demo/teaching.py').read_text(encoding='utf-8')
    def code_slot(match):
        name = match.group(1)
        snippet = re.search(r'# PPT:'+name+r':start\n([\s\S]*?)\n# PPT:'+name+r':end', teaching)
        if not snippet:
            raise ValueError(f'Missing Python teaching snippet: {name}')
        return '<pre class="code">'+html.escape(snippet.group(1))+'</pre>'
    for i, slide in enumerate(slides):
        body = re.sub(r'<div data-code="(\w+)"></div>', code_slot, slide['body'])
        body = re.sub(r"<pre class=['\"]code['\"]>([\s\S]*?)</pre>", highlight_python, body)
        # Nodes are real Python IDs; no illustrative algorithm runs in JavaScript.
        title = slide['title']
        pages.append(f'''<section class="slide kd-slide {themes[i]}" data-layout="{layouts[i]}" data-animate="{recipes[i]}" data-slide-id="{ids[i]}">
<div class="canvas-card">
<div class="chrome-min"><div class="l">KD-TREE / ALGORITHM STUDY</div><div class="r">{i+1:02d} / {len(slides):02d}</div></div>
<header class="kd-heading" data-anim="head"><div class="t-cat">{slide['kicker']}</div><h2>{title}</h2></header>
<div class="kd-body" data-anim="body">{body}</div>
<div class="kd-foot"><span>3D DEMONSTRATION · d-DIMENSIONAL ANALYSIS</span><span>{ids[i].upper()}</span></div>
</div></section>''')
        notes.append(dict(id=ids[i], title=title, section=slide['kicker'], minutes=slide['duration']/60, purpose=slide['purpose'], talk=slide['notes'], transition=slide['transition']))
        plan.append(dict(page=i+1,id=ids[i],layout=layouts[i],theme=themes[i],title=title,duration=slide['duration'],purpose=slide['purpose']))
    template = (ROOT / 'assets/template-swiss.source.html').read_text(encoding='utf-8')
    template = template.replace('[必填] 替换为 PPT 标题 · Deck Title', 'KD-tree · 多维空间查询与动态维护')
    # No fonts, modules or scripts fetched at presentation time.
    template = re.sub(r'<!-- GZ:FONTS:START[\s\S]*?<!-- GZ:FONTS:END -->', '', template)
    template = template.replace('</style>', (ROOT/'deck.css').read_text(encoding='utf-8') + '\n</style>', 1)
    start = template.index('<!-- ============================================================', template.index('<div id="deck">'))
    end = template.index('\n</div>\n\n<div id="nav">', start)
    template = template[:start] + '\n'.join(pages) + template[end:]
    template = re.sub(r'const SPEAKER_NOTES = \[[\s\S]*?\];\s*window.__SPEAKER_NOTES__ = SPEAKER_NOTES;', lambda _: 'const SPEAKER_NOTES = '+json.dumps(notes,ensure_ascii=False)+';\nwindow.__SPEAKER_NOTES__ = SPEAKER_NOTES;', template, count=1)
    template = re.sub(r'<script src="https://unpkg.com/lucide[^\"]*"></script>\s*<script>lucide.createIcons\(\);</script>', '', template)
    template = re.sub(r'<script type="module">[\s\S]*?</script>', '', template)
    # Let interactive graphics own their wheel, touch and form events.
    template = template.replace("addEventListener('wheel',e=>{\n  wheelAcc", "addEventListener('wheel',e=>{\n  if(e.target.closest?.('.viz,#ppt-presenter,#overview'))return;\n  wheelAcc")
    template = template.replace("addEventListener('touchend',e=>{\n  const dx", "addEventListener('touchend',e=>{\n  if(e.target.closest?.('.viz,#ppt-presenter'))return;\n  const dx")
    template = template.replace("if(window.__pptPresenter?.handleKey(e))return;", "if(e.target?.matches?.('input,textarea,select,[contenteditable=\"true\"]')&&!document.body.classList.contains('ppt-presenter'))return;\n  if(window.__pptPresenter?.handleKey(e))return;")
    # Integrate custom visualization with deck/presenter/preview navigation.
    template = template.replace('window.__pptPresenter?.onSlideChange(idx);', "window.__pptPresenter?.onSlideChange(idx);\n  window.KDViz?.activate(idx);\n  dispatchEvent(new CustomEvent('kd-slide-change',{detail:{index:idx}}));")
    # Reuse guizang transports; custom state is included in restore snapshots.
    template = template.replace("emit({type:'goto',index:idx,seq,screenMode,circles});", "emit({type:'goto',index:idx,seq,screenMode,circles,kd:window.KDViz?.snapshot()});")
    template = template.replace("if(message.type==='bye'){showAudienceEnded();return;}", "if(message.type==='kd-viz'){if(!document.body.classList.contains('kd-frozen'))window.KDViz?.receive(message.kd);return;}\n    if(message.type==='bye'){showAudienceEnded();return;}")
    template = template.replace("go(Number(message.index),{force:true});}", "go(Number(message.index),{force:true});if(message.kd)window.KDViz?.receive(message.kd);}")
    template = template.replace("return{initMode,onSlideChange,handleKey", "return{emitDemo:kd=>{if(mode==='presenter'&&!audienceFrozen)emit({type:'kd-viz',kd});},initMode,onSlideChange,handleKey")
    template = template.replace("function applyAudienceScreen(value){", "function applyAudienceScreen(value){\n    document.body.classList.toggle('kd-frozen',value==='frozen');")
    template = template.replace("type:'preview-goto',index:i}", "type:'preview-goto',index:i,kd:window.KDViz?.snapshot()}")
    template = template.replace("go(Number(message.index),{force:true});\n  }\n  function sendGoto", "go(Number(message.index),{force:true});if(message.kd)window.KDViz?.receive(message.kd);\n  }\n  function sendGoto")
    # Preview custom events route through the parent, without touching slide controls.
    bundle = script((ROOT.parent/'demo/output/data.js').read_text(encoding='utf-8'))
    bundle += script((ROOT/'assets/three.min.js').read_text(encoding='utf-8'))
    bundle += script((ROOT/'viz.js').read_text(encoding='utf-8'))
    bundle += script("""window.__playSlide=function(i){if(window.__lowPowerMode)return;const s=document.querySelectorAll('#deck>.slide')[i];if(!s)return;const h=s.querySelector('.kd-heading');if(h)h.animate([{opacity:0,transform:'translateY(8px)'},{opacity:1,transform:'none'}],{duration:260,easing:'ease-out'});};window.__playSlide(window.__currentSlideIndex||0);""")
    template = template.replace('</body>', bundle+'\n</body>')
    (ROOT/'index.html').write_text(template,encoding='utf-8')
    (ROOT/'slide-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Built {len(slides)} slides, {sum(x["duration"] for x in slides)/60:.1f} planned minutes; {len(template.encode("utf-8")):,} bytes. Offline: ppt/index.html')


if __name__ == '__main__':
    main()
