from pathlib import Path
from html import escape
import re, shutil, json, os
from urllib.parse import quote
from bs4 import BeautifulSoup
ROOT=Path(os.environ.get('SOURCE_DIR','.')).resolve(); OUT=Path(os.environ.get('OUTPUT_DIR','_site')).resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for p in ROOT.iterdir():
 if p.name in {'.git','.github','tools','_site'}:continue
 if p.is_dir():shutil.copytree(p,OUT/p.name,dirs_exist_ok=True)
 elif p.is_file():shutil.copy2(p,OUT/p.name)
COVERS={'ذات الرجع':'return.webp','خارج الكادر':'outside-frame.webp','الشقة ١٣٣':'shaqqa-133.webp','وتلك الأيام':'days.webp','ما لم تأخذه السنين':'years.webp'}
GENRES={'ذات الرجع':'خيال علمي','خارج الكادر':'غموض وتشويق','الشقة ١٣٣':'كوميديا اجتماعية','وتلك الأيام':'دراما سياسية واجتماعية','ما لم تأخذه السنين':'دراما تاريخية'}
BLURBS={'ذات الرجع':'رحلة تتقاطع فيها أسرار الكون مع أسئلة الوجود، حين يصبح الصمت أعظم من كل تفسير.','خارج الكادر':'حكاية تبدأ بتفاصيل تبدو عادية، ثم تكشف ما لم يكن ينبغي لأحد أن يراه.','الشقة ١٣٣':'غلطة في رقم شقة تقلب حياة أسرة مصرية رأسًا على عقب، وسط مواقف كوميدية ومفاجآت.','وتلك الأيام':'حكايات مصرية تتقاطع فيها حياة الناس داخل الوطن وخارجه بين الضحك والألم وتقلبات الأيام.','ما لم تأخذه السنين':'حكاية حب وذكريات تمتد عبر السنين، وما تحتفظ به القلوب رغم الفراق.'}
TRAILERS={} # add entries e.g. 'ذات الرجع':'https://www.youtube.com/watch?v=...'
def normalize(s):
 s=re.sub(r'[-_]+',' ',s);s=re.sub(r'\s+',' ',s).strip();return s.translate(str.maketrans('0123456789','٠١٢٣٤٥٦٧٨٩'))
def identify(stem):
 s=normalize(stem); s=re.sub(r'\s*الفصل\s+(?:ال[اأإآء-ي]+|[٠-٩]+|[0-9]+).*$', '',s).strip()
 for title in COVERS:
  if normalize(title)==s or normalize(title) in s:return title
 return s
books={}
for p in sorted(OUT.glob('*.html')):
 if p.name.lower() in ('index.html','reader.html'):continue
 name=identify(p.stem)
 if not name:continue
 entry=books.setdefault(name,{'title':name,'genre':GENRES.get(name,'رواية أدبية'),'description':BLURBS.get(name,'حكاية جديدة من مكتبة الملكوت المكتوب.'),'cover':('assets/covers/'+COVERS[name]) if name in COVERS else '', 'trailer':TRAILERS.get(name,''),'chapters':[]})
 entry['chapters'].append({'title':normalize(p.stem.replace(name,'')).strip(' -') or 'اقرأ الرواية','url':quote(p.name)})
 # add shared reader enhancements only to published copies
 html=p.read_text(encoding='utf-8',errors='replace')
 if '<head' in html.lower() and 'malakut-reader.css' not in html:
  html=re.sub(r'(?i)</head\s*>','<link rel="stylesheet" href="./assets/malakut-reader.css"></head>',html,count=1)
 if '</body' in html.lower() and 'malakut-reader.js' not in html:
  html=re.sub(r'(?i)</body\s*>','<script src="./assets/malakut-reader.js" defer></script></body>',html,count=1)
 p.write_text(html,encoding='utf-8')
entries=list(books.values());(OUT/'catalog.json').write_text(json.dumps({'books':entries,'count':len(entries)},ensure_ascii=False,indent=2),encoding='utf-8')
index=OUT/'index.html'
if index.exists():
 soup=BeautifulSoup(index.read_text(encoding='utf-8',errors='replace'),'html.parser')
 shelf=soup.select_one('.books')
 if shelf:
  shelf.clear();shelf['id']='smart-books'
  for book in entries:
   card=soup.new_tag('article',attrs={'class':'book smart-card'})
   art=soup.new_tag('div',attrs={'class':'smart-art'})
   if book['cover']:
    img=soup.new_tag('img',src='./'+book['cover'],alt='غلاف '+book['title'],loading='lazy');art.append(img)
   else:art.string='✦'
   layer=soup.new_tag('div',attrs={'class':'smart-overlay'}); layer.string=book['description'];art.append(layer)
   card.append(art)
   info=soup.new_tag('div',attrs={'class':'info'})
   label=soup.new_tag('div',attrs={'class':'tag'});label.string=book['genre'];info.append(label)
   title=soup.new_tag('h3');title.string=book['title'];info.append(title)
   count=soup.new_tag('p');count.string=f"{len(book['chapters'])} فصل/ملف متاح";info.append(count)
   buttons=soup.new_tag('div',attrs={'class':'smart-actions'})
   a=soup.new_tag('a',href='./'+book['chapters'][0]['url']);a.string='اقرأ الرواية';buttons.append(a)
   if book['trailer']:
    tr=soup.new_tag('a',href=book['trailer'],target='_blank',rel='noopener noreferrer');tr.string='شاهد التريلر';buttons.append(tr)
   if len(book['chapters'])>1:
    details=soup.new_tag('details');summary=soup.new_tag('summary');summary.string='الفصول المتاحة';details.append(summary)
    for ch in book['chapters']:
     l=soup.new_tag('a',href='./'+ch['url']);l.string=ch['title'];details.append(l)
    info.append(details)
   info.append(buttons);card.append(info);shelf.append(card)
  head=soup.select_one('.section-head small:last-child')
  if head:head.string=f'{len(entries)} روايات • تتحدث تلقائيًا'
  style=soup.new_tag('style');style.string='''
.smart-card .smart-art{position:relative;aspect-ratio:16/9;overflow:hidden;background:#26354a;display:flex;align-items:center;justify-content:center}.smart-art img{width:100%;height:100%;object-fit:cover;transition:transform .4s}.smart-card:hover img{transform:scale(1.045)}.smart-overlay{position:absolute;inset:0;background:#07111de6;color:#fff;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center;opacity:0;transition:opacity .25s;font-size:1rem;line-height:1.9}.smart-card:hover .smart-overlay,.smart-card:focus-within .smart-overlay{opacity:1}.smart-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto}.smart-actions a{padding:8px 13px;background:#e7bb78;color:#172338;border-radius:9px;font-weight:700}.smart-actions a+a{background:transparent;color:#e7bb78;border:1px solid #e7bb78}details{margin-bottom:12px;color:#e7bb78}details a{display:block;padding:4px 10px;color:#eee} @media(hover:none){.smart-overlay{display:none}.smart-art:active .smart-overlay{display:flex;opacity:1}}'''
  soup.head.append(style)
  index.write_text(str(soup),encoding='utf-8')
print('Published',len(entries),'novels',sum(len(b['chapters']) for b in entries),'files')
