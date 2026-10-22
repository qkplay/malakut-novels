from pathlib import Path
from html import escape
from urllib.parse import quote
import os,re,json,shutil
ROOT=Path(os.environ.get('SOURCE_DIR','.')).resolve()
OUT=Path(os.environ.get('OUTPUT_DIR','_site')).resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for p in ROOT.iterdir():
    if p.name in {'.git','.github','tools','_site'}: continue
    if p.is_dir(): shutil.copytree(p,OUT/p.name,dirs_exist_ok=True)
    elif p.is_file(): shutil.copy2(p,OUT/p.name)
COVERS={'ذات الرجع':'return.webp','خارج الكادر':'outside-frame.webp','الشقة ١٣٣':'shaqqa-133.webp','وتلك الأيام':'days.webp','ما لم تأخذه السنين':'years.webp'}
BLURBS={'ذات الرجع':'رحلة إلى المجهول، حيث تتجاوز الأسرار حدود ما نعرفه عن الكون.','خارج الكادر':'ما الذي تخفيه العدسة، وما الذي لم يكن ينبغي أن يظهر في الصورة؟','الشقة ١٣٣':'غلطة في رقم شقة تفتح الباب لمواقف مصرية لا تُنسى.','وتلك الأيام':'حكايات تتقاطع فيها مصائر المصريين بين الضحك والألم وتقلبات الأيام.','ما لم تأخذه السنين':'حكاية حب وذكريات تتحدى الفراق وتبقى رغم مرور السنين.'}
TRAILERS={'الشقة ١٣٣':'https://www.youtube.com/watch?v=rdk7Ps0fLnc'}
GENRES={'ذات الرجع':'خيال علمي','خارج الكادر':'غموض وتشويق','الشقة ١٣٣':'كوميديا اجتماعية','وتلك الأيام':'دراما اجتماعية','ما لم تأخذه السنين':'رواية تاريخية'}
def norm(s):
    return re.sub(r'\s+',' ',re.sub(r'[-_]+',' ',s)).strip().translate(str.maketrans('0123456789','٠١٢٣٤٥٦٧٨٩'))
def identify(stem):
    s=norm(stem)
    for title in COVERS:
        if norm(title) in s:return title
    return re.split(r'\s*الفصل\s+',s,maxsplit=1)[0].strip() or s
books={}
for p in sorted(OUT.glob('*.html')):
    if p.name.lower() in {'index.html','reader.html'}:continue
    name=identify(p.stem)
    book=books.setdefault(name,{'title':name,'cover':'assets/covers/'+COVERS[name] if name in COVERS else '', 'description':BLURBS.get(name,'اكتشف حكاية جديدة من مكتبة الملكوت المكتوب.'),'genre':GENRES.get(name,'رواية'),'trailer':TRAILERS.get(name,''),'chapters':[]})
    book['chapters'].append({'title':norm(p.stem),'url':quote(p.name)})
    html=p.read_text(encoding='utf-8',errors='replace')
    if re.search(r'</head\s*>',html,re.I) and 'malakut-reader.css' not in html:
        html=re.sub(r'</head\s*>','<link rel="stylesheet" href="./assets/malakut-reader.css"></head>',html,count=1,flags=re.I)
    if re.search(r'</body\s*>',html,re.I) and 'malakut-reader.js' not in html:
        html=re.sub(r'</body\s*>','<script src="./assets/malakut-reader.js" defer></script></body>',html,count=1,flags=re.I)
    p.write_text(html,encoding='utf-8')
entries=list(books.values())
(OUT/'catalog.json').write_text(json.dumps({'count':len(entries),'books':entries},ensure_ascii=False,indent=2),encoding='utf-8')
index=OUT/'index.html'
if index.exists():
    html=index.read_text(encoding='utf-8',errors='replace')
    cards=[]
    for b in entries:
        first='./'+b['chapters'][0]['url']
        cover='./'+b['cover'] if b['cover'] and (OUT/b['cover']).exists() else ''
        image=f'<img src="{escape(cover,quote=True)}" alt="غلاف {escape(b["title"])}" loading="lazy">' if cover else f'<span class="ml-no-cover">{escape(b["title"])}</span>'
        chapters=''.join(f'<a href="./{escape(c["url"],quote=True)}">{escape(c["title"])}</a>' for c in b['chapters'])
        more=f'<details class="ml-chapters"><summary>الفصول المتاحة ({len(b["chapters"])})</summary>{chapters}</details>' if len(b['chapters'])>1 else ''
        trailer=f'<a class="ml-trailer" href="{escape(b["trailer"],quote=True)}" target="_blank" rel="noopener noreferrer">▶ شاهد التريلر</a>' if b['trailer'] else ''
        cards.append(f'''<article class="ml-card"><a class="ml-image" href="{first}" aria-label="قراءة {escape(b['title'])}">{image}<span class="ml-hover"><strong>{escape(b['title'])}</strong><span>{escape(b['description'])}</span><em>اضغط لبدء القراءة ←</em></span></a><div class="ml-meta"><span>{escape(b['genre'])} · {len(b['chapters'])} فصل/ملف</span><div class="ml-actions"><a href="{first}">اقرأ الآن</a>{trailer}</div>{more}</div></article>''')
    shelf='\n'.join(cards)
    html,n=re.subn(r'<div\s+class=["\']books["\'][^>]*>.*?</div>\s*</main>',lambda m:'<div class="books" id="smart-books">'+shelf+'</div></main>',html,count=1,flags=re.S|re.I)
    if not n:
        # Fallback for a differently structured index: replace its shelf only if a clear marker exists.
        html,n=re.subn(r'<div\s+class=["\']books["\'][^>]*>.*?(?=<section\s+class=["\']quote)',lambda m:'<div class="books" id="smart-books">'+shelf+'</div></main>\n',html,count=1,flags=re.S|re.I)
    if not n:raise RuntimeError('لم أجد قسم .books في index.html — لم يتم تغيير الصفحة الأصلية')
    css='''<style id="ml-card-style">.books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px;max-width:1100px;margin:auto}.ml-card{border:1px solid #39455b;border-radius:17px;overflow:hidden;background:#152238}.ml-image{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;background:#233149}.ml-image>img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .3s}.ml-card:hover img{transform:scale(1.025)}.ml-hover{position:absolute;inset:0;background:#07101de8;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-align:center;padding:20px;opacity:0;transition:opacity .2s;color:#fff}.ml-hover strong{font-size:1.6rem;color:#e7bb78}.ml-hover span{max-width:420px}.ml-hover em{color:#e7bb78;font-style:normal}.ml-card:hover .ml-hover,.ml-image:focus-visible .ml-hover{opacity:1}.ml-meta{padding:14px 17px;color:#b6c2d2;font-size:.86rem}.ml-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}.ml-actions a{background:#e7bb78;color:#152238;padding:5px 14px;border-radius:8px;font-weight:700}.ml-actions .ml-trailer{background:transparent;color:#e7bb78;border:1px solid #e7bb78}.ml-chapters{margin-top:10px}.ml-chapters summary{cursor:pointer;color:#e7bb78}.ml-chapters a{display:block;padding:3px 8px}.ml-no-cover{display:grid;place-items:center;height:100%;font-size:2rem;color:#e7bb78}@media(max-width:650px){.books{grid-template-columns:1fr}.ml-hover{display:none}.ml-card:focus-within .ml-hover{display:flex;opacity:1}}</style>'''
    html=re.sub(r'</head\s*>',css+'</head>',html,count=1,flags=re.I)
    html=re.sub(r'أربع روايات\s*•\s*منها رواية قيد الكتابة',f'{len(entries)} روايات • تحديث تلقائي',html)
    index.write_text(html,encoding='utf-8')
print('Published',len(entries),'novels and',sum(len(b['chapters']) for b in entries),'HTML files')

