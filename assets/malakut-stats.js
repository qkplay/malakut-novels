(()=>{'use strict';
const base='https://malakut-novels.goatcounter.com/counter/';
const badges=[...document.querySelectorAll('[data-ml-paths]')];
if(!badges.length)return;
const cache=new Map();
async function count(path){
  if(cache.has(path))return cache.get(path);
  const promise=(async()=>{
    const url=base+encodeURIComponent(decodeURIComponent(path))+'.json';
    const response=await fetch(url,{mode:'cors',cache:'no-store'});
    if(response.status===404)return 0;
    if(!response.ok)throw Error('Counter HTTP '+response.status);
    const data=await response.json();
    const n=Number(String(data.count||'0').replace(/[^0-9]/g,''));
    return Number.isFinite(n)?n:0;
  })();
  cache.set(path,promise);return promise;
}
for(const badge of badges){
  (async()=>{
    let paths;
    try{paths=JSON.parse(badge.dataset.mlPaths||'[]')}catch{badge.textContent='👁 غير متاح';return}
    try{
      const counts=await Promise.all(paths.map(count));
      badge.textContent='👁 '+new Intl.NumberFormat('ar-EG').format(counts.reduce((a,b)=>a+b,0))+' قراءة';
    }catch(error){
      badge.textContent='👁 الإحصاءات غير متاحة';
      badge.title='فعّل Allow adding visitor counts on your website في إعدادات GoatCounter';
    }
  })();
}
})();