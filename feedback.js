// ===== زر «ملاحظاتك» في كل صفحات «أول خطوة» =====
// عدّلي هنا بس، والتغيير يطلع في كل الصفحات.
const FEEDBACK = {
  email: "sara.alzhrani2004@gmail.com",
  formUrl: "https://forms.gle/PU69ckb1GRskeM6e8",   // رابط فورم الملاحظات: الزر يفتحه مباشرة
  linkedin: ""     // رابط بروفايلك في لينكدإن (اختياري)
};
// ===================================================

(function(){
  const css = `
  .fb-btn{position:fixed; inset-inline-start:16px; bottom:calc(16px + env(safe-area-inset-bottom,0px)); z-index:50; display:inline-flex; align-items:center; gap:6px; background:var(--accent,#0B7A5C); color:var(--accent-ink,#fff); border:0; border-radius:999px; padding:10px 16px; font:inherit; font-size:14px; font-weight:600; cursor:pointer; box-shadow:0 6px 18px rgb(0 0 0 / .18)}
  body{padding-bottom:72px}
  .fb-btn:focus-visible{outline:2px solid var(--ink,#0F201B); outline-offset:3px}
  .fb-back{position:fixed; inset:0; z-index:60; background:rgb(0 0 0 / .45); display:grid; place-items:center; padding:16px}
  .fb-back[hidden]{display:none!important}
  .fb-install[hidden]{display:none!important}
  .fb-card{width:min(460px,100%); background:var(--surface,#fff); color:var(--ink,#0F201B); border:1px solid var(--line,#D9E2DE); border-radius:14px; padding:20px; display:grid; gap:12px; font-family:inherit; direction:rtl; text-align:right; max-height:calc(100vh - 32px); overflow:auto}
  .fb-card h2{margin:0; font-size:18px}
  .fb-card p{margin:0; font-size:13.5px; color:var(--muted,#5A6B65)}
  .fb-types{display:flex; flex-wrap:wrap; gap:6px}
  .fb-types button{border:1px solid var(--line,#D9E2DE); background:var(--bg,#F2F5F3); color:inherit; border-radius:999px; padding:5px 12px; font:inherit; font-size:13.5px; cursor:pointer}
  .fb-types button[aria-pressed="true"]{background:var(--accent,#0B7A5C); color:var(--accent-ink,#fff); border-color:var(--accent,#0B7A5C)}
  .fb-card textarea{font:inherit; font-size:14px; color:inherit; background:var(--bg,#F2F5F3); border:1px solid var(--line,#D9E2DE); border-radius:8px; padding:10px; min-height:110px; resize:vertical; width:100%; box-sizing:border-box}
  .fb-row{display:flex; gap:8px; flex-wrap:wrap; align-items:center}
  .fb-send{background:var(--accent,#0B7A5C); color:var(--accent-ink,#fff); border:0; border-radius:8px; padding:10px 18px; font:inherit; font-weight:600; cursor:pointer}
  .fb-close{background:none; border:1px solid var(--line,#D9E2DE); color:inherit; border-radius:8px; padding:10px 14px; font:inherit; cursor:pointer}
  .fb-mail{font-size:13px; color:var(--muted,#5A6B65)}
  .fb-mail b{direction:ltr; unicode-bidi:isolate; color:var(--ink,#0F201B)}
  .fb-copy{background:none; border:0; color:var(--accent,#0B7A5C); text-decoration:underline; cursor:pointer; font:inherit; font-size:13px; padding:0}
  .fb-foot{margin-top:10px; font-size:12.5px; color:var(--muted,#5A6B65)}
  .fb-foot a{color:var(--ink,#0F201B); font-weight:500}
  @media (max-width:640px){
    .fb-btn{width:48px; height:48px; padding:0; justify-content:center; font-size:0; gap:0; bottom:calc(76px + env(safe-area-inset-bottom,0px)); inset-inline-start:auto; inset-inline-end:12px; opacity:.92}
    .fb-btn::before{content:"💬"; font-size:22px}
  }
  @media (max-width:640px){ .fb-hide-mobile .fb-btn{display:none} }
  /* مساحة فاضية تحت الصفحة عشان الزر ما يغطي آخر سطر */
  body.fb-pad{padding-bottom:76px}
  @media (max-width:640px){ body.fb-pad{padding-bottom:136px} body.fb-pad.fb-hide-mobile{padding-bottom:0} }
  @media (max-width:640px){ .fb-btn{transition:transform .2s ease, opacity .2s} .fb-btn.fb-away{transform:translateY(140px); opacity:0; pointer-events:none} }
  @media print{ .fb-btn,.fb-back{display:none!important} }`;
  const st = document.createElement("style"); st.textContent = css; document.head.append(st);
  document.body.classList.add("fb-pad");
  // في صفحة السيرة الزر يغطي الخانات في الجوال، فنكتفي برابط الملاحظات تحت الصفحة
  if(document.getElementById("cvForm")) document.body.classList.add("fb-hide-mobile");

  const track = (path, title) => { try{ window.goatcounter && window.goatcounter.count && window.goatcounter.count({path, title, event:true}); }catch(e){} };
  const page = document.title.split("|")[0].trim() || "الموقع";
  const EN = document.documentElement.lang === "en";
  const tr = (ar, en) => EN ? en : ar;

  const btn = document.createElement("button");
  btn.className = "fb-btn"; btn.type = "button"; btn.textContent = tr("💬 ملاحظاتك", "💬 Feedback");
  btn.setAttribute("aria-haspopup", "dialog");
  document.body.append(btn);

  if(FEEDBACK.formUrl){
    const a = document.createElement("a");
    a.className = btn.className; a.textContent = btn.textContent; a.href = FEEDBACK.formUrl; a.target = "_blank"; a.rel = "noopener";
    a.setAttribute("aria-label", tr("ملاحظاتك","Feedback")); a.title = tr("ملاحظاتك","Feedback");
    a.style.textDecoration = "none";
    a.addEventListener("click", ()=>track("feedback/form", page));
    btn.replaceWith(a);
  } else {
    const back = document.createElement("div"); back.className = "fb-back"; back.hidden = true;
    back.innerHTML = `
      <div class="fb-card" role="dialog" aria-modal="true" aria-labelledby="fb-title">
        <h2 id="fb-title">ملاحظاتك تهمنا</h2>
        <p>لقيت خطأ في إعلان؟ عندك اقتراح؟ أو تبي تنضاف شركتك؟ اكتب لنا.</p>
        <div class="fb-types" role="group" aria-label="نوع الملاحظة">
          <button type="button" aria-pressed="true" data-t="اقتراح">💡 اقتراح</button>
          <button type="button" aria-pressed="false" data-t="خطأ في إعلان">⚠️ خطأ في إعلان</button>
          <button type="button" aria-pressed="false" data-t="مشكلة في الموقع">🛠 مشكلة في الموقع</button>
          <button type="button" aria-pressed="false" data-t="إضافة شركة أو فرصة">🏢 إضافة شركة أو فرصة</button>
          <button type="button" aria-pressed="false" data-t="طلب إزالة إعلان">🗑 طلب إزالة</button>
        </div>
        <label for="fb-msg" class="fb-mail">اكتب ملاحظتك</label>
        <textarea id="fb-msg" placeholder="مثلًا: الإعلان الفلاني انتهى، أو ياليت تضيفون…"></textarea>
        <div class="fb-row">
          <button type="button" class="fb-send" id="fb-send">إرسال بالإيميل</button>
          <button type="button" class="fb-close" id="fb-close">إلغاء</button>
        </div>
        <p class="fb-mail">يفتح لك تطبيق الإيميل والرسالة جاهزة. لو ما فتح، راسلنا على: <b id="fb-addr"></b> <button type="button" class="fb-copy" id="fb-copy">نسخ</button></p>
      </div>`;
    document.body.append(back);
    const $ = s => back.querySelector(s);
    $("#fb-addr").textContent = FEEDBACK.email;
    let type = "اقتراح";
    back.querySelectorAll(".fb-types button").forEach(b=>b.addEventListener("click", ()=>{
      type = b.dataset.t; back.querySelectorAll(".fb-types button").forEach(x=>x.setAttribute("aria-pressed", String(x===b)));
    }));
    const open = ()=>{ back.hidden = false; $("#fb-msg").focus(); track("feedback/open", page); };
    const close = ()=>{ back.hidden = true; btn.focus(); };
    btn.addEventListener("click", open);
    $("#fb-close").addEventListener("click", close);
    back.addEventListener("click", e=>{ if(e.target === back) close(); });
    document.addEventListener("keydown", e=>{ if(e.key === "Escape" && !back.hidden) close(); });
    $("#fb-send").addEventListener("click", ()=>{
      const msg = $("#fb-msg").value.trim();
      if(msg.length < 3){ $("#fb-msg").focus(); return; }
      const subject = `أول خطوة: ${type}`;
      const body = `${msg}\n\n---\nالصفحة: ${page}\n${location.href}`;
      track("feedback/send", type);
      location.href = `mailto:${FEEDBACK.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    });
    $("#fb-copy").addEventListener("click", async e=>{
      try{ await navigator.clipboard.writeText(FEEDBACK.email); e.target.textContent = "انتسخ ✓"; }catch(err){ e.target.textContent = "انسخه يدويًا"; }
      setTimeout(()=>{ e.target.textContent = "نسخ"; }, 2000);
    });
  }

  // في الجوال: الزر يختفي وأنت تنزل في الصفحة، ويرجع أول ما تطلع لفوق أو توصل آخر الصفحة
  let lastY = scrollY;
  addEventListener("scroll", ()=>{
    const b = document.querySelector(".fb-btn"); if(!b) return;
    const y = scrollY, atEnd = innerHeight + y >= document.documentElement.scrollHeight - 40;
    if(y > lastY + 6 && y > 200 && !atEnd) b.classList.add("fb-away");
    else if(y < lastY - 6 || atEnd) b.classList.remove("fb-away");
    lastY = y;
  }, {passive:true});

  // ===== تطبيق على الجوال (PWA) =====
  if("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(()=>{});
  const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone;
  let installEvt = null;
  const installLine = document.createElement("div"); installLine.className = "fb-foot fb-install"; installLine.hidden = true;
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
  if(!standalone && ios){
    installLine.innerHTML = tr("📲 تبيه تطبيق على جوالك؟ من Safari اضغط زر المشاركة ثم «إضافة إلى الشاشة الرئيسية».", "📲 Want it as an app? In Safari, tap Share, then “Add to Home Screen”.");
    installLine.hidden = false;
  }
  addEventListener("beforeinstallprompt", e=>{
    e.preventDefault(); installEvt = e; if(standalone) return;
    installLine.innerHTML = ""; const b = document.createElement("button"); b.type = "button"; b.className = "fb-copy"; b.textContent = tr("📲 ثبّت «أول خطوة» كتطبيق على جوالك", "📲 Install Awal Khatwa as an app");
    b.onclick = async ()=>{ installEvt.prompt(); try{ const r = await installEvt.userChoice; track("pwa/"+r.outcome, "تثبيت التطبيق"); }catch(err){} installLine.hidden = true; };
    installLine.append(b); installLine.hidden = false;
  });

  // سطر التواصل تحت كل صفحة
  const wrap = document.querySelector(".wrap");
  if(wrap && !document.getElementById("contact")){
    const f = document.createElement("div"); f.className = "fb-foot";
    f.innerHTML = `${tr("للتواصل والملاحظات:","Contact & feedback:")} ${FEEDBACK.formUrl?`<a href="${FEEDBACK.formUrl}" target="_blank" rel="noopener">${tr("نموذج الملاحظات","Feedback form")}</a> · `:""}<a href="mailto:${FEEDBACK.email}" dir="ltr">${FEEDBACK.email}</a>${FEEDBACK.linkedin?` · <a href="${FEEDBACK.linkedin}" target="_blank" rel="noopener">LinkedIn</a>`:""}`;
    wrap.append(f);
  }
  if(wrap) wrap.append(installLine);
})();
