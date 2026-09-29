#!/usr/bin/env python3
# 由 index.html 派生「精读版」reading.html：
#  - 工具栏 = 5 个纯色高亮（hl_orange/cyan/pink/green/gray），点击即上色、不弹取色盘/编辑器
#  - 去掉批注层（编辑器弹层、总评、清样版、视角切换等）——保留渲染/点选/触屏/导出
import re, io, sys

SRC='index.html'; OUT='reading.html'
html=open(SRC,encoding='utf-8').read()

# ---------- 1. SHAPES/PALETTES/DEF_COLOR 换成五色高亮 ----------
old_cfg = re.search(r"const SHAPES = \[.*?const DEF_COLOR=\{[^}]*\};", html, re.S)
assert old_cfg, "config block not found"
new_cfg = """const SHAPES = [
  {key:'hl_orange', ic:'●', lb:'橙·学术写作参考', cls:'mk-highlight-span', color:'#FFB86CA6'},
  {key:'hl_cyan',   ic:'●', lb:'青·日常听说读写', cls:'mk-highlight-span', color:'#ABF7F7A6'},
  {key:'hl_pink',   ic:'●', lb:'粉·完全生词',     cls:'mk-highlight-span', color:'#FFB8EBA6'},
  {key:'hl_green',  ic:'●', lb:'绿·眼熟未必准',   cls:'mk-highlight-span', color:'#BBFABBA6'},
  {key:'hl_gray',   ic:'●', lb:'灰·借鉴意义不大', cls:'mk-highlight-span', color:'#CACFD9A6'},
];
const PALETTES = {};
const DEF_COLOR={hl_orange:'#FFB86CA6',hl_cyan:'#ABF7F7A6',hl_pink:'#FFB8EBA6',hl_green:'#BBFABBA6',hl_gray:'#CACFD9A6'};
const SHAPE_COLOR={hl_orange:'#FFB86CA6',hl_cyan:'#ABF7F7A6',hl_pink:'#FFB8EBA6',hl_green:'#BBFABBA6',hl_gray:'#CACFD9A6'};"""
html=html[:old_cfg.start()]+new_cfg+html[old_cfg.end():]

# ---------- 2. 高亮渲染：所有 hl_* 都用背景色 ----------
html=html.replace(
  "    if(shape==='circle'||shape==='box'){}\n"
  "    else if(shape==='highlight'){\n"
  "      spans.filter(sp=>sp.s>=mk.start&&sp.e<=mk.end).forEach(sp=>{sp.el.classList.add('mk-highlight-span');sp.el.style.background=hexA(mk.color,.55);sp.el.dataset.mk=(sp.el.dataset.mk||'')+mk.id+',';});\n"
  "    } else {\n"
  "      spans.filter(sp=>sp.s>=mk.start&&sp.e<=mk.end).forEach(sp=>{sp.el.classList.add(cls);sp.el.style.textDecorationColor=mk.color;sp.el.dataset.mk=(sp.el.dataset.mk||'')+mk.id+',';});\n"
  "    }",
  "    // 精读版：只有纯色高亮\n"
  "    spans.filter(sp=>sp.s>=mk.start&&sp.e<=mk.end).forEach(sp=>{sp.el.classList.add('mk-hl');sp.el.style.background=mk.color;sp.el.dataset.mk=(sp.el.dataset.mk||'')+mk.id+',';});"
)

# ---------- 3. 去掉圆圈/方框 overlay 队列（精读版没有） ----------
html=html.replace(
  "circleBoxQueue=circleBoxQueue.concat(marks.filter(m=>m.shape==='circle'||m.shape==='box').map(m=>({pid,m})));",
  "/* 精读版无圆圈/方框 */"
)
# drawOverlays 空转
html=re.sub(
  r"function drawOverlays\(\)\{.*?\n\}\n",
  "function drawOverlays(){ /* 精读版：无圆圈/方框 overlay */ }\n",
  html, count=1, flags=re.S
)

# ---------- 4. buildTools 换成 5 色按钮 + 撤销/导出/导入 ----------
old_tools = re.search(r"function buildTools\(\)\{.*?\n\}\n", html, re.S)
assert old_tools, "buildTools not found"
new_tools = """function buildTools(){
  const t=document.getElementById('tools'); t.innerHTML='';
  SHAPES.forEach(s=>{
    const d=document.createElement('div'); d.className='tool'+(activeShape===s.key?' active':''); d.dataset.shape=s.key;
    d.title=s.lb;
    d.innerHTML=`<span class="ic" style="color:${s.color}">●</span><span class="dot" style="background:${s.color}"></span>`;
    // 精读版：点色块直接选中该色（不弹取色盘）
    d.onclick=(e)=>{e.stopPropagation();activeShape=s.key;activeColor[s.key]=s.color;clearPendStart();hint(s.lb+'：点首词再点尾词定范围，或直接划选');buildTools();};
    t.appendChild(d);
  });
  const sep=document.createElement('div'); sep.className='tsep'; t.appendChild(sep);
  const bUndo=document.createElement('div'); bUndo.className='tool mini'; bUndo.title='撤销';
  bUndo.innerHTML=`<span class="ic">↩</span>`; bUndo.onclick=(e)=>{e.stopPropagation();undo();}; t.appendChild(bUndo);
  const bWipe=document.createElement('div'); bWipe.className='tool mini'; bWipe.title='清空全部标记';
  bWipe.innerHTML=`<span class="ic">🧹</span>`; bWipe.onclick=(e)=>{e.stopPropagation();if(confirm('清空本文所有标记？')){history.length=0;Object.keys(paraMarks).forEach(k=>paraMarks[k]=[]);rerenderAndDraw();hint('已清空全部标记');}}; t.appendChild(bWipe);
  const sep2=document.createElement('div'); sep2.className='tsep'; t.appendChild(sep2);
  const bSave=document.createElement('div'); bSave.className='tool mini'; bSave.title='导出标记 JSON';
  bSave.innerHTML=`<span class="ic">💾</span>`; bSave.onclick=(e)=>{e.stopPropagation();downloadJSON();}; t.appendChild(bSave);
  const bImp=document.createElement('div'); bImp.className='tool mini'; bImp.title='导入标记 JSON';
  bImp.innerHTML=`<span class="ic">📥</span>`; bImp.onclick=(e)=>{e.stopPropagation();document.getElementById('fileInput').click();}; t.appendChild(bImp);
  if(restoredFromLocal){
    const bClr=document.createElement('div'); bClr.className='tool mini'; bClr.title='清空本地暂存';
    bClr.innerHTML=`<span class="ic">🗑</span>`; bClr.onclick=(e)=>{e.stopPropagation();clearLocal();}; t.appendChild(bClr);
  }
}
"""
html=html[:old_tools.start()]+new_tools+html[old_tools.end():]

# ---------- 5. 点词行为：精读版 = 上色/取消色（不弹编辑器） ----------
old_he = re.search(r"function handleEditClick\(pid, span, ev\)\{.*?\n\}\n\n// 用绝对定位", html, re.S)
assert old_he, "handleEditClick not found"
new_he = """function handleEditClick(pid, span, ev){
  let s=+span.dataset.start, e=+span.dataset.end;
  const tok=plainOf(pid).slice(s,e);
  const isBlank=/^\\s*$/.test(tok);
  if(!activeShape){ hint('先在右侧选一个颜色'); return; }

  // 无起点：第一次点击设起点
  if(isBlank && !pendStart) return;
  if(!pendStart){
    pendStart={pid,s,e}; paintPend(pid,s,e);
    hint('已设起点「'+plainOf(pid).slice(s,e)+'」，再点一个词确定范围（同词再点=只标这个词）'); return;
  }
  if(pendStart.pid!==pid){
    clearPendStart(); pendStart={pid,s,e}; paintPend(pid,s,e);
    hint('已设起点「'+plainOf(pid).slice(s,e)+'」，再点一个词确定范围（同词再点=只标这个词）'); return;
  }
  // 同词再点 → 只标这一个词
  if(pendStart.s===s && pendStart.e===e){
    clearPendStart(); applyRange(pid,s,e); return;
  }
  // 不同词 → 首尾包裹成范围
  const a=Math.min(pendStart.s,s), b=Math.max(pendStart.e,e);
  clearPendStart(); applyRange(pid,a,b);
}

// 用绝对定位的高亮块标出"起点词\""""
html=html[:old_he.start()]+new_he+html[old_he.end():]

# ---------- 6. applyRange/createMark：直接上色，不弹编辑器 ----------
html=html.replace(
  "  history.push({type:'add', pid, ids:[mk.id]});\n  rerenderAndDraw();\n  openEditor(pid, mk, true);\n}",
  "  history.push({type:'add', pid, ids:[mk.id]});\n  rerenderAndDraw();\n}"
)
html=html.replace(
  "  history.push({type:'add', pid, ids:[newMk.id]});\n  rerenderAndDraw();\n  openEditor(pid, newMk, true);\n}",
  "  history.push({type:'add', pid, ids:[newMk.id]});\n  rerenderAndDraw();\n}"
)

# ---------- 7. 注入精读版 CSS ----------
css_inject = """
  .mk-hl{border-radius:2px}
  /* 精读版：隐藏批注/总评/视角切换等批阅专属 UI */
  #editModal,#sumModal,#pickModal,#viewToggle,#swatch{display:none!important}
"""
html=html.replace("</style>", css_inject+"</style>", 1)

# ---------- 8. 精读版：不加载内联标记（纯文本起步） ----------
# render() 里：if(!paraMarks[pid]) paraMarks[pid]=marks;  →  改为精读版不套用 marks
html=html.replace(
  "    const {plain, marks}=parsePara(b.text, pid);\n    if(!paraMarks[pid]) paraMarks[pid]=marks;",
  "    const parsed=parsePara(b.text, pid);\n    const plain=parsed.plain, marks=[];\n    if(!paraMarks[pid]) paraMarks[pid]=marks;"
)

# ---------- 8. 标题/标签改精读语义 ----------
html=html.replace("<title>", "<title>")

# ---------- 8b. 精读版：空标记段落也要切成词级 span ----------
html=html.replace(
  "  if(!marks.length){frag.appendChild(document.createTextNode(plain));return frag;}",
  "  if(!marks.length){\n    tokenize(plain).forEach(tk=>{\n      const span=document.createElement('span'); span.className='run'; span.textContent=tk.text;\n      span.dataset.pid=pid; span.dataset.start=tk.s; span.dataset.end=tk.e;\n      frag.appendChild(span);\n    });\n    return frag;\n  }"
)

# ---------- 8c. 精读版：加「导入文本」按钮 ----------
html=html.replace(
  "}; t.appendChild(bImp);\n  if(restoredFromLocal){",
  "}; t.appendChild(bImp);\n"
  "  const bTxt=document.createElement('div'); bTxt.className='tool mini'; bTxt.title='导入文本（粘贴纯文本，一行一段）';\n"
  "  bTxt.innerHTML=`<span class=\"ic\">📝</span>`; bTxt.onclick=(e)=>{e.stopPropagation();openTextImport();}; t.appendChild(bTxt);\n"
  "  if(restoredFromLocal){"
)

# ---------- 8d. 精读版：openTextImport 函数 + texts 快照 ----------
extra_js = r"""
/* ===== 精读版扩展：导入文本（一行一段） ===== */
function openTextImport(){
  const cur=DATA.blocks.map(b=>b.text).join('\n');
  const raw=prompt('粘贴纯文本（一行一段，空行会忽略；标点请自备）：',cur);
  if(raw===null) return;
  const lines=raw.split('\n').map(l=>l.replace(/\r$/,'')).filter(l=>l.trim()!=='');
  if(!lines.length){ hint('没有有效文本'); return; }
  DATA.blocks=lines.map((line,i)=>{
    let type='para';
    if(i===0 && /^[A-Z][a-z]+[ ,]/.test(line)) type='salutation';
    return {type, id:'p'+i, text:line};
  });
  Object.keys(paraMarks).forEach(k=>delete paraMarks[k]);
  history.length=0;
  try{ localStorage.removeItem(paperKey()); }catch(e){}
  rerenderAndDraw();
  hint('已导入 '+lines.length+' 段');
}

/* ===== 精读版扩展：导出附带正文快照 texts ===== */"""
html=html.replace("/* ==================== 视角切换 ==================== */", extra_js+"\n/* ==================== 视角切换 ==================== */", 1)

# exportData 里加 texts 快照
html=html.replace(
  "  return {\n    tool:'writing-optimizer',\n    version:3,\n    paper:DATA.meta.title,\n    savedAt:new Date().toISOString(),\n    marks\n  };",
  "  const texts={};\n  DATA.blocks.forEach((b,idx)=>{ texts['p'+idx]=parsePara(b.text,'p'+idx).plain; });\n  return {\n    tool:'writing-optimizer',\n    version:3,\n    paper:DATA.meta.title,\n    savedAt:new Date().toISOString(),\n    texts,\n    marks\n  };"
)

open(OUT,'w',encoding='utf-8').write(html)
print("written", OUT, len(html), "bytes")