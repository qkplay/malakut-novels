(()=>{'use strict';
if(document.getElementById('malakut-tools'))return;
const $=(q,root=document)=>root.querySelector(q);
const settingsKey='malakut:reader:v2',bookmarkKey='malakut:'+location.pathname;
const candidates=[...document.querySelectorAll('article,main,.chapter,.content,.novel,.story')].filter(e=>(e.innerText||'').trim().length>500);
const content=candidates.sort((a,b)=>b.innerText.length-a.innerText.length)[0]||$('main')||document.body;
if(content!==document.body)content.id='malakut-content';else document.body.classList.add('malakut-body-content');
const defaults={mode:'original',font:'original',size:22,line:2,width:780,brightness:100,speed:30,focus:false,layout:'scroll'};
let state;try{state={...defaults,...JSON.parse(localStorage.getItem(settingsKey)||'{}')}}catch{state={...defaults}}
const clamp=(v,min,max,fallback)=>Number.isFinite(+v)?Math.max(min,Math.min(max,+v)):fallback;
state.size=clamp(state.size,14,40,22);state.line=clamp(state.line,1.4,2.8,2);state.width=clamp(state.width,560,1100,780);state.brightness=clamp(state.brightness,45,100,100);state.speed=clamp(state.speed,5,120,30);
if(!['scroll','single','spread'].includes(state.layout))state.layout='scroll';
const bar=document.createElement('div');bar.id='malakut-tools';bar.innerHTML=`<div class="ml-top"><a class="ml-home" href="/malakut-novels/" aria-label="الصفحة الرئيسية لمكتبة الملكوت" title="العودة للمكتبة">⌂ الرئيسية</a><button data-act="panel" aria-expanded="false">☷ إعدادات القراءة</button><button data-act="play">▶ تمرير</button><button data-act="prev" class="ml-page-control" hidden>→ السابقة</button><button data-act="next" class="ml-page-control" hidden>التالية ←</button><button data-act="smaller">أ−</button><button data-act="bigger">أ+</button><button data-act="save">🔖 حفظ</button><button data-act="resume">↩ استكمال</button><button data-act="focus">◫ تركيز</button><button data-act="print">طباعة PDF</button><span class="malakut-info"></span><button data-act="hide">إخفاء</button></div><div class="ml-panel" hidden><div class="ml-panel-head"><strong>✦ قارئ الملكوت</strong><span>مساحتك الخاصة للقراءة</span></div><label>طريقة العرض<select data-setting="layout"><option value="scroll">تمرير مستمر</option><option value="single">صفحة واحدة</option><option value="spread">صفحتان متقابلتان</option></select></label><label>نمط الصفحة<select data-setting="mode"><option value="original">التصميم الأصلي</option><option value="paper">ورقي دافئ</option><option value="white">أبيض وأسود</option><option value="eink">حبر إلكتروني · E-Ink</option><option value="night">ليلي</option><option value="clean">قراءة نقية</option></select></label><label>الخط العربي<select data-setting="font"><option value="original">خط الرواية الأصلي</option><option value="amiri">أميري</option><option value="naskh">نسخ عربي</option><option value="ruqaa">رقعة</option><option value="traditional">Traditional Arabic</option><option value="sans">عربي واضح</option></select></label><label>حجم الخط <output data-out="size"></output><input type="range" data-setting="size" min="14" max="40" step="1"></label><label>تباعد السطور <output data-out="line"></output><input type="range" data-setting="line" min="1.4" max="2.8" step="0.1"></label><label>عرض صفحة القراءة <output data-out="width"></output><input type="range" data-setting="width" min="560" max="1100" step="20"></label><label>سطوع الصفحة <output data-out="brightness"></output><input type="range" data-setting="brightness" min="45" max="100" step="5"></label><label>سرعة التمرير <output data-out="speed"></output><input type="range" data-setting="speed" min="5" max="120" step="5"></label><p class="ml-note">السطوع يؤثر على صفحة المتصفح فقط. عند لمس الشاشة أو تحريك عجلة الماوس يتوقف التحريك الآلي مؤقتًا ثم يستأنف بنفس السرعة.</p><button data-act="reset">استعادة الإعدادات الافتراضية</button></div>`;
document.body.prepend(bar);
const veil=document.createElement('div');veil.id='malakut-dimmer';veil.setAttribute('aria-hidden','true');document.body.append(veil);
const launcher=document.createElement('button');launcher.id='malakut-launcher';launcher.textContent='Aa';launcher.title='إظهار أدوات القراءة';launcher.hidden=true;document.body.append(launcher);
const panel=$('.ml-panel',bar);let playing=false,last=0,saveTimer=0,userInteracting=false,resumeAt=0,animationId=0;
const persist=()=>{try{localStorage.setItem(settingsKey,JSON.stringify(state))}catch{}};
const isPaged=()=>state.layout!=='scroll'&&content!==document.body;
// Screen Wake Lock: active only while auto-scroll runs and page is visible.
let wakeLock=null;
let wakeNoticeShown=false;
async function requestWakeLock(){
 if(!playing||document.visibilityState!=='visible'||wakeLock)return;
 if(!('wakeLock' in navigator)||!navigator.wakeLock?.request){
  if(!wakeNoticeShown){wakeNoticeShown=true;console.info('Wake Lock is not supported by this browser.');}
  return;
 }
 try{
  const lock=await navigator.wakeLock.request('screen');
  if(!playing||document.visibilityState!=='visible'){await lock.release();return;}
  wakeLock=lock;
  lock.addEventListener('release',()=>{if(wakeLock===lock)wakeLock=null;});
 }catch(error){console.info('Screen Wake Lock unavailable:',error?.name||error);}
}
function releaseWakeLock(){const lock=wakeLock;wakeLock=null;if(lock)lock.release().catch(()=>{});}
document.addEventListener('visibilitychange',()=>{
 if(document.visibilityState==='visible'&&playing)requestWakeLock();
 else releaseWakeLock();
});
function stopAuto(){playing=false;last=0;releaseWakeLock();cancelAnimationFrame(animationId);$('[data-act="play"]',bar).textContent='▶ تمرير'}
function apply(){
 document.body.classList.remove('malakut-paper','malakut-night','malakut-clean','malakut-white','malakut-focus','malakut-paged','malakut-spread','malakut-single');
 if(state.mode!=='original')document.body.classList.add('malakut-'+state.mode);
 if(state.focus)document.body.classList.add('malakut-focus');
 if(isPaged()){document.body.classList.add('malakut-paged','malakut-'+state.layout);stopAuto()}
 const root=document.documentElement.style;root.setProperty('--ml-font-size',state.size+'px');root.setProperty('--ml-line-height',state.line);root.setProperty('--ml-reader-width',state.width+'px');root.setProperty('--ml-dim',String((100-state.brightness)/100*.72));
 root.setProperty('--ml-font',({amiri:'"Amiri",serif',naskh:'"Noto Naskh Arabic",serif',ruqaa:'"Aref Ruqaa",serif',traditional:'"Traditional Arabic","Amiri",serif',sans:'"IBM Plex Sans Arabic",Tahoma,sans-serif'})[state.font]||'inherit');
 document.body.classList.toggle('malakut-custom-font',state.font!=='original');document.body.classList.add('malakut-custom-size');
 for(const el of bar.querySelectorAll('[data-setting]'))el.value=state[el.dataset.setting];
 for(const el of bar.querySelectorAll('[data-out]')){const k=el.dataset.out;el.textContent=state[k]+({size:'px',width:'px',brightness:'%'}[k]||'')}
 const paged=isPaged();$('[data-act="play"]',bar).hidden=paged;for(const b of bar.querySelectorAll('.ml-page-control'))b.hidden=!paged;
 $('[data-act="focus"]',bar).textContent=state.focus?'▣ إنهاء التركيز':'◫ تركيز';persist();requestAnimationFrame(progress);
}
function progress(){const info=$('.malakut-info',bar);if(isPaged()){const total=Math.max(1,Math.ceil(content.scrollWidth/Math.max(1,content.clientWidth)));const page=Math.max(1,Math.min(total,Math.round(Math.abs(content.scrollLeft)/Math.max(1,content.clientWidth))+1));info.textContent='صفحة '+page+' من '+total;return}const max=Math.max(1,document.documentElement.scrollHeight-innerHeight),fraction=Math.max(0,Math.min(1,scrollY/max)),words=(content.innerText.match(/\S+/g)||[]).length;info.textContent=Math.round(fraction*100)+'% • نحو '+Math.ceil((1-fraction)*words/180)+' دقيقة متبقية'}
function save(){try{localStorage.setItem(bookmarkKey,JSON.stringify({y:scrollY,x:content.scrollLeft,time:Date.now()}))}catch{}}
function tick(t){if(!playing||isPaged())return;if(!userInteracting&&t>=resumeAt&&last)window.scrollBy(0,Math.min(120,(t-last)/1000*state.speed));last=t;if(scrollY+innerHeight>=document.documentElement.scrollHeight-2){stopAuto();return}animationId=requestAnimationFrame(tick)}
function postpone(ms){resumeAt=performance.now()+ms;last=0}
function pageStep(direction){if(!isPaged())return;const step=content.clientWidth;content.scrollBy({left:direction*step,behavior:'smooth'});setTimeout(progress,450)}
bar.addEventListener('click',e=>{const b=e.target.closest('button[data-act]');if(!b)return;const act=b.dataset.act;
 if(act==='panel'){panel.hidden=!panel.hidden;b.setAttribute('aria-expanded',String(!panel.hidden))}
 if(act==='play'){if(playing)stopAuto();else{playing=true;last=0;b.textContent='⏸ إيقاف';requestWakeLock();animationId=requestAnimationFrame(tick)}}
 if(act==='next')pageStep(-1);if(act==='prev')pageStep(1);
 if(act==='smaller'||act==='bigger'){state.size=clamp(state.size+(act==='bigger'?2:-2),14,40,22);apply()}
 if(act==='save'){save();b.textContent='✓ تم الحفظ';setTimeout(()=>b.textContent='🔖 حفظ',1200)}
 if(act==='resume'){try{const v=JSON.parse(localStorage.getItem(bookmarkKey)||'{}');if(isPaged())content.scrollTo({left:v.x||0,behavior:'smooth'});else scrollTo({top:v.y||0,behavior:'smooth'})}catch{}}
 if(act==='focus'){state.focus=!state.focus;apply()}if(act==='print')print();if(act==='hide'){bar.classList.add('ml-hidden');launcher.hidden=false}if(act==='reset'){state={...defaults};apply()}
});
bar.addEventListener('input',e=>{const k=e.target.dataset.setting;if(!k)return;state[k]=e.target.type==='range'?Number(e.target.value):e.target.value;apply()});
bar.addEventListener('change',e=>{const k=e.target.dataset.setting;if(!k)return;state[k]=e.target.type==='range'?Number(e.target.value):e.target.value;apply()});
launcher.addEventListener('click',()=>{bar.classList.remove('ml-hidden');launcher.hidden=true});
addEventListener('touchstart',()=>{userInteracting=true;postpone(700)},{passive:true});
addEventListener('touchend',()=>{userInteracting=false;postpone(900)},{passive:true});
addEventListener('touchcancel',()=>{userInteracting=false;postpone(900)},{passive:true});
addEventListener('wheel',()=>postpone(650),{passive:true});
addEventListener('pointerdown',e=>{if(e.pointerType==='touch'||e.pointerType==='pen'){userInteracting=true;postpone(700)}},{passive:true});
addEventListener('pointerup',e=>{if(e.pointerType==='touch'||e.pointerType==='pen'){userInteracting=false;postpone(900)}},{passive:true});
addEventListener('pointercancel',()=>{userInteracting=false;postpone(900)},{passive:true});
addEventListener('scroll',()=>{if(!isPaged())progress();clearTimeout(saveTimer);saveTimer=setTimeout(save,1300)},{passive:true});
if(content!==document.body)content.addEventListener('scroll',()=>{if(isPaged()){progress();clearTimeout(saveTimer);saveTimer=setTimeout(save,1000)}},{passive:true});
addEventListener('resize',progress);addEventListener('pagehide',()=>{save();releaseWakeLock()});
addEventListener('keydown',e=>{if(e.altKey&&e.code==='Space'){e.preventDefault();$('[data-act="play"]',bar).click()}if(isPaged()&&!e.altKey&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();pageStep(e.key==='ArrowLeft'?-1:1)}}if(e.key==='Escape'&&!panel.hidden){panel.hidden=true;$('[data-act="panel"]',bar).setAttribute('aria-expanded','false')}});
apply();progress();
})();
