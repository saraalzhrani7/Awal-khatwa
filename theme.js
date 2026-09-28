// ===== زر المظهر: لون الموقع + فاتح/داكن =====
// يتحمّل في <head> قبل ما تظهر الصفحة عشان ما يصير وميض ألوان.
// الاختيار يتحفظ في متصفح الزائر وينطبق على كل الصفحات.
(function(){
  const KEY = "awal-khatwa-theme";
  const PALETTES = [
    {id:"green", ar:"أخضر", en:"Green", sw:"linear-gradient(135deg,#E8F2EC 50%,#0B5A43 50%)"},
    {id:"navy",  ar:"كحلي", en:"Navy",  sw:"linear-gradient(135deg,#E6EDF5 50%,#1E3461 50%)"}
  ];
  const MODES = [
    {id:"auto",  ar:"تلقائي", en:"Auto"},
    {id:"light", ar:"فاتح",   en:"Light"},
    {id:"dark",  ar:"داكن",   en:"Dark"}
  ];
  // ألوان كل ثيم: فاتح (L) وداكن (D)
  const L = {
    green: "--bg:#EAF3EE; --surface:#F7FBF8; --ink:#0D3B2E; --muted:#4A6B5F; --line:#D2E3DA; --accent:#0B5A43; --accent-ink:#F7FBF8; --accent-soft:#D9EBE2; --saffron:#A8651A; --saffron-soft:#F6E6CC; --closed:#7F948C; --closed-soft:#E3ECE7; --focus:#0B5A43;",
    navy:  "--bg:#EAEFF6; --surface:#F7F9FC; --ink:#16274A; --muted:#4D5D7C; --line:#D5DDEA; --accent:#1E3461; --accent-ink:#F7F9FC; --accent-soft:#DCE4F0; --saffron:#A8651A; --saffron-soft:#F6E6CC; --closed:#858DA0; --closed-soft:#E4E9F1; --focus:#1E3461;"
  };
  const D = {
    green: "--bg:#0B1A15; --surface:#11241D; --ink:#DCEFE5; --muted:#93B3A6; --line:#1F3A31; --accent:#7ED3B0; --accent-ink:#0B1A15; --accent-soft:#18362B; --saffron:#E3A857; --saffron-soft:#3A2B17; --closed:#7C918A; --closed-soft:#16291F; --focus:#7ED3B0;",
    navy:  "--bg:#0E1526; --surface:#152037; --ink:#E1E8F3; --muted:#9DABC4; --line:#26334F; --accent:#A8C0E8; --accent-ink:#0E1526; --accent-soft:#223252; --saffron:#E3A857; --saffron-soft:#3A2B17; --closed:#7F8AA0; --closed-soft:#1A2540; --focus:#A8C0E8;"
  };
  const META = {green:["#EAF3EE","#0B1A15"], navy:["#EAEFF6","#0E1526"]};

  let css = "";
  for(const p in L){
    css += `:root[data-palette="${p}"]{${L[p]}}\n`;
    css += `@media (prefers-color-scheme: dark){ :root[data-palette="${p}"]:not([data-theme="light"]){color-scheme:dark; ${D[p]}} }\n`;
    css += `:root[data-palette="${p}"][data-theme="dark"]{color-scheme:dark; ${D[p]}}\n`;
  }
  css += `
  .th-wrap{position:relative; display:inline-flex}
  .sitenav .th-wrap{margin-inline-start:auto}
  .sitenav .th-wrap + .langbtn{margin-inline-start:6px}
  .th-btn{display:inline-flex; align-items:center; gap:6px; background:none; border:1px solid var(--line); border-radius:8px; padding:5px 10px; font:inherit; font-size:13px; color:var(--ink); cursor:pointer}
  .th-dot{width:12px; height:12px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 2px var(--surface), 0 0 0 3px var(--line)}
  .th-pop{position:absolute; top:calc(100% + 6px); inset-inline-end:0; z-index:70; width:200px; background:var(--surface); color:var(--ink); border:1px solid var(--line); border-radius:12px; padding:12px; box-shadow:0 10px 30px rgb(0 0 0 / .18); display:grid; gap:10px}
  .th-pop[hidden]{display:none!important}
  .th-pop h3{margin:0; font-size:12.5px; font-weight:600; color:var(--muted)}
  .th-sw{display:grid; grid-template-columns:repeat(2,1fr); gap:6px}
  .th-sw button{display:grid; justify-items:center; gap:4px; background:none; border:1px solid transparent; border-radius:8px; padding:6px 2px; font:inherit; font-size:12px; color:var(--ink); cursor:pointer}
  .th-sw button span{width:26px; height:26px; border-radius:50%; box-shadow:inset 0 0 0 1px rgb(0 0 0 / .15)}
  .th-sw button[aria-pressed="true"]{border-color:var(--accent); background:var(--accent-soft)}
  .th-md{display:flex; border:1px solid var(--line); border-radius:8px; overflow:hidden}
  .th-md button{flex:1; background:none; border:0; padding:6px 0; font:inherit; font-size:12.5px; color:var(--ink); cursor:pointer}
  .th-md button+button{border-inline-start:1px solid var(--line)}
  .th-md button[aria-pressed="true"]{background:var(--accent); color:var(--accent-ink)}
  @media (max-width:640px){ .th-btn .th-lbl{display:none} }
  @media print{ .th-wrap{display:none!important} }`;
  const st = document.createElement("style"); st.id = "theme-css"; st.textContent = css;
  document.head.append(st);

  const read = ()=>{ try{ return JSON.parse(localStorage.getItem(KEY)) || {}; }catch(e){ return {}; } };
  let cur = Object.assign({palette:"green", mode:"auto"}, read());
  // للتجربة: ?theme=navy&mode=dark
  const q = new URLSearchParams(location.search);
  if(q.get("theme")) cur.palette = q.get("theme");
  if(q.get("mode")) cur.mode = q.get("mode");

  const root = document.documentElement;
  function apply(){
    if(!L[cur.palette]) cur.palette = "green";
    root.dataset.palette = cur.palette;
    if(cur.mode === "auto") root.removeAttribute("data-theme"); else root.dataset.theme = cur.mode;
    const dark = cur.mode === "dark" || (cur.mode === "auto" && matchMedia("(prefers-color-scheme: dark)").matches);
    const m = document.querySelector('meta[name="theme-color"]');
    if(m) m.content = (META[cur.palette] || META.green)[dark ? 1 : 0];
  }
  apply();
  matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", apply);

  function save(){ try{ localStorage.setItem(KEY, JSON.stringify(cur)); }catch(e){} apply(); sync(); }
  let sync = ()=>{};

  function build(){
    const nav = document.querySelector(".sitenav"); if(!nav) return;
    const wrap = document.createElement("div"); wrap.className = "th-wrap";
    wrap.innerHTML = `<button type="button" class="th-btn" aria-haspopup="true" aria-expanded="false"><span class="th-dot"></span><span class="th-lbl"></span></button>
      <div class="th-pop" hidden role="dialog"><h3 class="th-h1"></h3><div class="th-sw"></div><h3 class="th-h2"></h3><div class="th-md"></div></div>`;
    const btn = wrap.querySelector(".th-btn"), pop = wrap.querySelector(".th-pop");
    const sw = wrap.querySelector(".th-sw"), md = wrap.querySelector(".th-md");
    PALETTES.forEach(p=>{ const b = document.createElement("button"); b.type = "button"; b.dataset.p = p.id; b.innerHTML = `<span style="background:${p.sw}"></span>`; b.append(document.createTextNode("")); sw.append(b); b.onclick = ()=>{ cur.palette = p.id; save(); }; });
    MODES.forEach(m=>{ const b = document.createElement("button"); b.type = "button"; b.dataset.m = m.id; md.append(b); b.onclick = ()=>{ cur.mode = m.id; save(); }; });
    const texts = ()=>{
      const E = root.lang === "en";
      wrap.querySelector(".th-lbl").textContent = E ? "Theme" : "المظهر";
      btn.setAttribute("aria-label", E ? "Theme" : "المظهر");
      wrap.querySelector(".th-h1").textContent = E ? "Color" : "اللون";
      wrap.querySelector(".th-h2").textContent = E ? "Mode" : "الوضع";
      sw.querySelectorAll("button").forEach((b,i)=>{ b.lastChild.textContent = E ? PALETTES[i].en : PALETTES[i].ar; });
      md.querySelectorAll("button").forEach((b,i)=>{ b.textContent = E ? MODES[i].en : MODES[i].ar; });
    };
    sync = ()=>{
      sw.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed", String(b.dataset.p === cur.palette)));
      md.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed", String(b.dataset.m === cur.mode)));
    };
    texts(); sync();
    // لما تتغير لغة الصفحة (زر English) تتغير نصوص الزر معها
    new MutationObserver(texts).observe(root, {attributes:true, attributeFilter:["lang"]});
    btn.onclick = e=>{ e.stopPropagation(); pop.hidden = !pop.hidden; btn.setAttribute("aria-expanded", String(!pop.hidden)); };
    document.addEventListener("click", e=>{ if(!wrap.contains(e.target)){ pop.hidden = true; btn.setAttribute("aria-expanded","false"); } });
    document.addEventListener("keydown", e=>{ if(e.key === "Escape" && !pop.hidden){ pop.hidden = true; btn.focus(); } });
    const lang = nav.querySelector(".langbtn");
    if(lang) lang.before(wrap); else nav.append(wrap);
  }
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();
})();
