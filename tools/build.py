from pathlib import Path
from html import escape
from urllib.parse import quote
import os, re, json, shutil

ROOT = Path(os.environ.get('SOURCE_DIR', '.')).resolve()
OUT = Path(os.environ.get('OUTPUT_DIR', '_site')).resolve()
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for p in ROOT.iterdir():
    if p.name in {'.git', '.github', 'tools', '_site'}:
        continue
    if p.is_dir():
        shutil.copytree(p, OUT / p.name, dirs_exist_ok=True)
    elif p.is_file():
        shutil.copy2(p, OUT / p.name)

COVERS = {'ذات الرجع': 'return.webp', 'خارج الكادر': 'outside-frame.webp', 'الشقة ١٣٣': 'shaqqa-133.webp', 'وتلك الأيام': 'days.webp', 'ما لم تأخذه السنين': 'years.webp'}
BLURBS = {'ذات الرجع': 'رحلة إلى المجهول، حيث تتجاوز الأسرار حدود ما نعرفه عن الكون.', 'خارج الكادر': 'ما الذي تخفيه العدسة، وما الذي لم يكن ينبغي أن يظهر في الصورة؟', 'الشقة ١٣٣': 'غلطة في رقم شقة تفتح الباب لمواقف مصرية لا تُنسى.', 'وتلك الأيام': 'حكايات تتقاطع فيها مصائر المصريين بين الضحك والألم وتقلبات الأيام.', 'ما لم تأخذه السنين': 'حكاية حب وذكريات تتحدى الفراق وتبقى رغم مرور السنين.'}
TRAILERS = {'الشقة ١٣٣': 'https://www.youtube.com/watch?v=rdk7Ps0fLnc'}
GENRES = {'ذات الرجع': 'خيال علمي', 'خارج الكادر': 'غموض وتشويق', 'الشقة ١٣٣': 'كوميديا اجتماعية', 'وتلك الأيام': 'دراما اجتماعية', 'ما لم تأخذه السنين': 'رواية تاريخية'}
GOAT = '<script data-goatcounter="https://malakut-novels.goatcounter.com/count" data-goatcounter-settings="{&quot;no_session&quot;:true}" async src="https://gc.zgo.at/count.js"></script>'
YEARS_TITLE = 'ما لم تأخذه السنين'
YEARS_LANDING = 'years.html'


def add_counter(html):
    if 'data-goatcounter=' not in html:
        html = re.sub(r'</body\s*>', lambda m: GOAT + m.group(0), html, count=1, flags=re.I)
    return html


def norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'[-_]+', ' ', s)).strip().translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))


def identify(stem):
    s = norm(stem)
    for title in COVERS:
        if norm(title) in s:
            return title
    return re.split(r'\s*الفصل\s+', s, maxsplit=1)[0].strip() or s


# صفحة years.html فهرس للرواية، وليست رواية إضافية.
# الملفات years-chapter-01... فصول للرواية ذاتها، وليست بطاقات منفصلة.
years_landing_exists = (OUT / YEARS_LANDING).is_file()
years_chapter_files = sorted(OUT.glob('years-chapter-*.html'))
prefer_new_years_chapters = bool(years_landing_exists and years_chapter_files)

books = {}
for p in sorted(OUT.glob('*.html')):
    if p.name.lower() in {'index.html', 'reader.html', YEARS_LANDING, 'start_here.html'} or re.fullmatch(r'years[-_]chapter[-_]\d+\.html',p.name,re.I) and not years_landing_exists:
        continue

    is_years_chapter = bool(re.fullmatch(r'years-chapter-(\d+)\.html', p.name, flags=re.I))
    if is_years_chapter:
        if not years_landing_exists:
            # لا ندرج فصولًا إنجليزية بغير صفحة الفهرس؛ نتجنب بطاقات غريبة.
            continue
        name = YEARS_TITLE
        number = int(re.fullmatch(r'years-chapter-(\d+)\.html', p.name, flags=re.I).group(1))
        chapter_label = 'الفصل ' + ({1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع'}.get(number, str(number)))
    else:
        name = identify(p.stem)
        if name == YEARS_TITLE and prefer_new_years_chapters:
            # النسخ القديمة ذات الأسماء العربية: نتجنب عرض الفصول مرتين.
            continue
        chapter_label = norm(p.stem)

    book = books.setdefault(name, {
        'title': name,
        'cover': 'assets/covers/' + COVERS[name] if name in COVERS else '',
        'description': BLURBS.get(name, 'اكتشف حكاية جديدة من مكتبة الملكوت المكتوب.'),
        'genre': GENRES.get(name, 'رواية'),
        'trailer': TRAILERS.get(name, ''),
        'chapters': [],
    })
    book['chapters'].append({'title': chapter_label, 'url': quote(p.name)})

    html = p.read_text(encoding='utf-8', errors='replace')
    if re.search(r'</head\s*>', html, re.I) and 'malakut-reader.css' not in html:
        html = re.sub(r'</head\s*>', '<link rel="stylesheet" href="./assets/malakut-reader.css"></head>', html, count=1, flags=re.I)
    if re.search(r'</body\s*>', html, re.I) and 'malakut-reader.js' not in html:
        html = re.sub(r'</body\s*>', '<script src="./assets/malakut-reader.js" defer></script></body>', html, count=1, flags=re.I)
    p.write_text(add_counter(html), encoding='utf-8')

# تسجيل قراءة صفحة التجميع في نفس أداة الإحصاءات.
if years_landing_exists:
    p = OUT / YEARS_LANDING
    p.write_text(add_counter(p.read_text(encoding='utf-8', errors='replace')), encoding='utf-8')

# ترتيب ثابت للبطاقات، كما كانت في الصفحة الرئيسية قبل النشر الآلي.
entries = sorted(books.values(), key=lambda b: (list(COVERS).index(b['title']) if b['title'] in COVERS else 999, b['title']))
(OUT / 'catalog.json').write_text(json.dumps({'count': len(entries), 'books': entries}, ensure_ascii=False, indent=2), encoding='utf-8')

index = OUT / 'index.html'
if index.exists():
    html = index.read_text(encoding='utf-8', errors='replace')
    cards = []
    for b in entries:
        special_years = b['title'] == YEARS_TITLE and years_landing_exists
        # الضغط على بطاقة «ما لم تأخذه السنين» يذهب إلى صفحة تجميع الفصول.
        first = './' + YEARS_LANDING if special_years else './' + b['chapters'][0]['url']
        cover = './' + b['cover'] if b['cover'] and (OUT / b['cover']).exists() else ''
        image = (f'<img src="{escape(cover, quote=True)}" alt="غلاف {escape(b["title"])}" loading="lazy">'
                 if cover else f'<span class="ml-no-cover">{escape(b["title"])}</span>')
        chapters = ''.join(f'<a href="./{escape(c["url"], quote=True)}">{escape(c["title"])}</a>' for c in b['chapters'])
        # على البطاقة نظهر مدخلًا واحدًا، والفهرس الخاص بالرواية يتولى اختيار الفصل.
        more = '' if special_years else (f'<details class="ml-chapters"><summary>الفصول المتاحة ({len(b["chapters"])})</summary>{chapters}</details>' if len(b['chapters']) > 1 else '')
        trailer = f'<a class="ml-trailer" href="{escape(b["trailer"], quote=True)}" target="_blank" rel="noopener noreferrer">▶ شاهد التريلر</a>' if b['trailer'] else ''
        paths = ['/malakut-novels/' + c['url'] for c in b['chapters']]
        if special_years:
            paths.append('/malakut-novels/' + YEARS_LANDING)
        stats_attr = escape(json.dumps(paths, ensure_ascii=False), quote=True)
        call_to_action = 'استعرض الفصول ←' if special_years else 'اضغط لبدء القراءة ←'
        read_action = 'الفصول الأربعة' if special_years else 'اقرأ الآن'
        cards.append(f'''<article class="ml-card"><a class="ml-image" href="{escape(first, quote=True)}" aria-label="{'فصول' if special_years else 'قراءة'} {escape(b['title'])}">{image}<span class="ml-views" data-ml-paths="{stats_attr}" title="مرات فتح صفحات الرواية">👁 جارٍ التحميل</span><span class="ml-hover"><strong>{escape(b['title'])}</strong><span>{escape(b['description'])}</span><em>{call_to_action}</em></span></a><div class="ml-meta"><span>{escape(b['genre'])} · {len(b['chapters'])} فصل/ملف</span><div class="ml-actions"><a href="{escape(first, quote=True)}">{read_action}</a>{trailer}</div>{more}</div></article>''')
    shelf = '\n'.join(cards)
    # استبدال رف الروايات فقط، دون مساس بواجهة الموقع الأخرى.
    html, n = re.subn(r'<div\s+class=["\']books["\'][^>]*>.*?</div>\s*</main>', lambda m: '<div class="books" id="smart-books">' + shelf + '</div></main>', html, count=1, flags=re.S | re.I)
    if not n:
        html, n = re.subn(r'<div\s+class=["\']books["\'][^>]*>.*?(?=<section\s+class=["\']quote)', lambda m: '<div class="books" id="smart-books">' + shelf + '</div></main>\n', html, count=1, flags=re.S | re.I)
    if not n:
        raise RuntimeError('لم أجد قسم .books في index.html — لم يتم تغيير الصفحة الأصلية')
    css = '''<style id="ml-card-style">.books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px;max-width:1100px;margin:auto}.ml-card{border:1px solid #39455b;border-radius:17px;overflow:hidden;background:#152238}.ml-image{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;background:#233149}.ml-image>img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .3s}.ml-card:hover img{transform:scale(1.025)}.ml-hover{position:absolute;inset:0;background:#07101de8;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-align:center;padding:20px;opacity:0;transition:opacity .2s;color:#fff}.ml-hover strong{font-size:1.6rem;color:#e7bb78}.ml-hover span{max-width:420px}.ml-hover em{color:#e7bb78;font-style:normal}.ml-card:hover .ml-hover,.ml-image:focus-visible .ml-hover{opacity:1}.ml-meta{padding:14px 17px;color:#b6c2d2;font-size:.86rem}.ml-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}.ml-actions a{background:#e7bb78;color:#152238;padding:5px 14px;border-radius:8px;font-weight:700}.ml-actions .ml-trailer{background:transparent;color:#e7bb78;border:1px solid #e7bb78}.ml-chapters{margin-top:10px}.ml-chapters summary{cursor:pointer;color:#e7bb78}.ml-chapters a{display:block;padding:3px 8px}.ml-no-cover{display:grid;place-items:center;height:100%;font-size:2rem;color:#e7bb78}@media(max-width:650px){.books{grid-template-columns:1fr}.ml-hover{display:none}.ml-card:focus-within .ml-hover{display:flex;opacity:1}}</style>'''
    html = re.sub(r'</head\s*>', css + '</head>', html, count=1, flags=re.I)
    html = re.sub(r'[٠-٩0-9]+\s*روايات\s*•\s*اختر عالمك', f'{len(entries)} روايات • اختر عالمك', html)
    html = re.sub(r'أربع روايات\s*•\s*منها رواية قيد الكتابة', f'{len(entries)} روايات • تحديث تلقائي', html)
    if 'malakut-stats.js' not in html:
        html = re.sub(r'</body\s*>', '<script src="./assets/malakut-stats.js" defer></script></body>', html, count=1, flags=re.I)
    html = html.replace('</head>', '<style>.ml-image .ml-views{position:absolute;top:12px;right:12px;z-index:2;background:#0b1324e8;color:#f3d39c;padding:6px 11px;border:1px solid #e7bb7866;border-radius:99px;font:700 13px Tahoma,sans-serif;pointer-events:none}.ml-image:hover .ml-views{opacity:1}</style></head>', 1)
    # الضغط على أي مساحة خالية في البطاقة يفتح وجهتها، دون تعطيل الأزرار والروابط.
    card_click = '''<script>document.querySelectorAll('.ml-card').forEach(card=>{card.style.cursor='pointer';card.addEventListener('click',e=>{if(e.target.closest('a,button,details,summary'))return;const link=card.querySelector('.ml-image');if(link)window.location.href=link.href;});});</script>'''
    html = re.sub(r'</body\s*>', card_click + '</body>', html, count=1, flags=re.I)
    index.write_text(add_counter(html), encoding='utf-8')

SKY_ART = '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice"><defs>\n<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#07152e"/><stop offset=".42" stop-color="#112451"/><stop offset=".71" stop-color="#17264a"/><stop offset="1" stop-color="#090f20"/></linearGradient>\n<radialGradient id="nebula"><stop stop-color="#425c98" stop-opacity=".24"/><stop offset="1" stop-color="#213c6a" stop-opacity="0"/></radialGradient>\n<radialGradient id="moon"><stop stop-color="#fff7d4"/><stop offset=".85" stop-color="#f1edcf"/><stop offset="1" stop-color="#f1e0b0"/></radialGradient>\n<linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#182442"/><stop offset="1" stop-color="#050c1e"/></linearGradient>\n</defs><rect width="1920" height="1080" fill="url(#sky)"/>\n<ellipse cx="1320" cy="310" rx="1100" ry="430" fill="url(#nebula)"/>\n<circle cx="266" cy="202" r="66" fill="#e9e7cf" opacity=".08"/>\n<circle cx="266" cy="202" r="38" fill="url(#moon)" opacity=".90"/>\n<circle cx="253" cy="187" r="6" fill="#b6b4ac" opacity=".25"/>\n<circle cx="276" cy="210" r="9" fill="#b6b4ac" opacity=".17"/>\n<circle cx="504" cy="806" r="1.8" fill="#e2ecff" opacity="0.30"/><circle cx="96" cy="208" r="0.65" fill="#e2ecff" opacity="0.35"/><circle cx="230" cy="110" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="836" cy="807" r="0.65" fill="#e2ecff" opacity="0.19"/><circle cx="957" cy="74" r="0.85" fill="#e2ecff" opacity="0.48"/><circle cx="1094" cy="275" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="1043" cy="798" r="0.7" fill="#e2ecff" opacity="0.24"/><circle cx="471" cy="623" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="1779" cy="140" r="0.85" fill="#e2ecff" opacity="0.55"/><circle cx="787" cy="228" r="1" fill="#e2ecff" opacity="0.72"/><circle cx="393" cy="450" r="1.45" fill="#e2ecff" opacity="0.25"/><circle cx="866" cy="86" r="0.65" fill="#e2ecff" opacity="0.48"/><circle cx="818" cy="572" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="942" cy="638" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="376" cy="184" r="0.7" fill="#e2ecff" opacity="0.72"/><circle cx="1010" cy="666" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="1252" cy="767" r="1.8" fill="#e2ecff" opacity="0.47"/><circle cx="596" cy="440" r="0.7" fill="#e2ecff" opacity="0.65"/><circle cx="1380" cy="51" r="1.8" fill="#e2ecff" opacity="0.85"/><circle cx="982" cy="38" r="0.85" fill="#e2ecff" opacity="0.35"/><circle cx="714" cy="613" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="1850" cy="762" r="1.45" fill="#e2ecff" opacity="0.26"/><circle cx="1759" cy="110" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="437" cy="638" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="239" cy="138" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="1663" cy="221" r="0.65" fill="#e2ecff" opacity="0.25"/><circle cx="1530" cy="268" r="1.8" fill="#e2ecff" opacity="0.72"/><circle cx="1276" cy="789" r="1.1" fill="#e2ecff" opacity="0.24"/><circle cx="309" cy="339" r="1.45" fill="#e2ecff" opacity="0.72"/><circle cx="1501" cy="477" r="0.7" fill="#e2ecff" opacity="0.55"/><circle cx="1016" cy="274" r="1.1" fill="#e2ecff" opacity="0.85"/><circle cx="606" cy="477" r="0.85" fill="#e2ecff" opacity="0.85"/><circle cx="772" cy="855" r="1.1" fill="#e2ecff" opacity="0.26"/><circle cx="885" cy="200" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="1018" cy="616" r="1.8" fill="#e2ecff" opacity="0.48"/><circle cx="1737" cy="806" r="1" fill="#e2ecff" opacity="0.19"/><circle cx="1101" cy="114" r="1.8" fill="#e2ecff" opacity="0.43"/><circle cx="1229" cy="870" r="1" fill="#e2ecff" opacity="0.14"/><circle cx="1308" cy="179" r="1.1" fill="#e2ecff" opacity="0.48"/><circle cx="1420" cy="653" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="1318" cy="315" r="0.7" fill="#e2ecff" opacity="0.65"/><circle cx="1614" cy="218" r="1.45" fill="#e2ecff" opacity="0.48"/><circle cx="944" cy="234" r="1" fill="#e2ecff" opacity="0.55"/><circle cx="1700" cy="572" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="649" cy="542" r="1" fill="#e2ecff" opacity="0.55"/><circle cx="1155" cy="673" r="0.85" fill="#e2ecff" opacity="0.35"/><circle cx="1512" cy="925" r="1.1" fill="#e2ecff" opacity="0.30"/><circle cx="758" cy="68" r="1.8" fill="#e2ecff" opacity="0.72"/><circle cx="446" cy="49" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="1226" cy="67" r="1.1" fill="#e2ecff" opacity="0.55"/><circle cx="841" cy="778" r="1" fill="#e2ecff" opacity="0.47"/><circle cx="696" cy="850" r="1.1" fill="#e2ecff" opacity="0.19"/><circle cx="1122" cy="477" r="0.65" fill="#e2ecff" opacity="0.65"/><circle cx="678" cy="217" r="0.7" fill="#e2ecff" opacity="0.55"/><circle cx="797" cy="485" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="1411" cy="341" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="967" cy="271" r="1.1" fill="#e2ecff" opacity="0.65"/><circle cx="972" cy="290" r="1.1" fill="#e2ecff" opacity="0.85"/><circle cx="491" cy="794" r="1" fill="#e2ecff" opacity="0.36"/><circle cx="926" cy="620" r="1.45" fill="#e2ecff" opacity="0.85"/><circle cx="1333" cy="519" r="0.65" fill="#e2ecff" opacity="0.72"/><circle cx="1264" cy="60" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="945" cy="723" r="0.7" fill="#e2ecff" opacity="0.25"/><circle cx="1364" cy="84" r="1" fill="#e2ecff" opacity="0.55"/><circle cx="166" cy="157" r="1.8" fill="#e2ecff" opacity="0.25"/><circle cx="919" cy="561" r="1.45" fill="#e2ecff" opacity="0.43"/><circle cx="453" cy="274" r="0.65" fill="#e2ecff" opacity="0.43"/><circle cx="306" cy="868" r="1.8" fill="#e2ecff" opacity="0.19"/><circle cx="1075" cy="881" r="1.1" fill="#e2ecff" opacity="0.30"/><circle cx="859" cy="432" r="1.1" fill="#e2ecff" opacity="0.65"/><circle cx="199" cy="741" r="1" fill="#e2ecff" opacity="0.55"/><circle cx="937" cy="535" r="0.65" fill="#e2ecff" opacity="0.35"/><circle cx="839" cy="457" r="0.7" fill="#e2ecff" opacity="0.43"/><circle cx="673" cy="165" r="1.8" fill="#e2ecff" opacity="0.85"/><circle cx="742" cy="311" r="0.65" fill="#e2ecff" opacity="0.72"/><circle cx="1655" cy="528" r="0.7" fill="#e2ecff" opacity="0.25"/><circle cx="1172" cy="688" r="0.85" fill="#e2ecff" opacity="0.85"/><circle cx="845" cy="203" r="0.85" fill="#e2ecff" opacity="0.48"/><circle cx="378" cy="467" r="1" fill="#e2ecff" opacity="0.65"/><circle cx="1769" cy="339" r="0.85" fill="#e2ecff" opacity="0.35"/><circle cx="1789" cy="332" r="1.45" fill="#e2ecff" opacity="0.35"/><circle cx="1193" cy="265" r="1.8" fill="#e2ecff" opacity="0.25"/><circle cx="639" cy="406" r="0.7" fill="#e2ecff" opacity="0.35"/><circle cx="115" cy="404" r="1.8" fill="#e2ecff" opacity="0.55"/><circle cx="498" cy="325" r="0.7" fill="#e2ecff" opacity="0.72"/><circle cx="72" cy="790" r="1.8" fill="#e2ecff" opacity="0.40"/><circle cx="1471" cy="127" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="729" cy="263" r="0.65" fill="#e2ecff" opacity="0.72"/><circle cx="888" cy="493" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="1565" cy="121" r="1" fill="#e2ecff" opacity="0.35"/><circle cx="931" cy="649" r="1.8" fill="#e2ecff" opacity="0.43"/><circle cx="1492" cy="110" r="1.8" fill="#e2ecff" opacity="0.85"/><circle cx="465" cy="879" r="1.8" fill="#e2ecff" opacity="0.40"/><circle cx="1091" cy="937" r="0.7" fill="#e2ecff" opacity="0.40"/><circle cx="1553" cy="430" r="0.7" fill="#e2ecff" opacity="0.72"/><circle cx="1293" cy="482" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="1305" cy="595" r="1.8" fill="#e2ecff" opacity="0.48"/><circle cx="1387" cy="647" r="0.85" fill="#e2ecff" opacity="0.25"/><circle cx="59" cy="729" r="0.7" fill="#e2ecff" opacity="0.48"/><circle cx="356" cy="56" r="1.45" fill="#e2ecff" opacity="0.55"/><circle cx="687" cy="316" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="715" cy="337" r="1.8" fill="#e2ecff" opacity="0.85"/><circle cx="649" cy="717" r="0.65" fill="#e2ecff" opacity="0.85"/><circle cx="130" cy="833" r="1.45" fill="#e2ecff" opacity="0.47"/><circle cx="447" cy="688" r="0.7" fill="#e2ecff" opacity="0.55"/><circle cx="316" cy="791" r="1.1" fill="#e2ecff" opacity="0.26"/><circle cx="584" cy="409" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="1064" cy="702" r="1.8" fill="#e2ecff" opacity="0.55"/><circle cx="582" cy="468" r="1" fill="#e2ecff" opacity="0.65"/><circle cx="1383" cy="329" r="0.65" fill="#e2ecff" opacity="0.43"/><circle cx="1753" cy="582" r="1.1" fill="#e2ecff" opacity="0.55"/><circle cx="864" cy="315" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="266" cy="824" r="1" fill="#e2ecff" opacity="0.47"/><circle cx="770" cy="332" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="1494" cy="796" r="1" fill="#e2ecff" opacity="0.40"/><circle cx="1895" cy="568" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="263" cy="708" r="1.8" fill="#e2ecff" opacity="0.55"/><circle cx="1648" cy="805" r="1.8" fill="#e2ecff" opacity="0.26"/><circle cx="563" cy="315" r="1.45" fill="#e2ecff" opacity="0.55"/><circle cx="264" cy="77" r="0.65" fill="#e2ecff" opacity="0.65"/><circle cx="991" cy="616" r="0.85" fill="#e2ecff" opacity="0.55"/><circle cx="896" cy="137" r="1.8" fill="#e2ecff" opacity="0.25"/><circle cx="1678" cy="853" r="1" fill="#e2ecff" opacity="0.40"/><circle cx="791" cy="547" r="1" fill="#e2ecff" opacity="0.65"/><circle cx="25" cy="651" r="1.8" fill="#e2ecff" opacity="0.48"/><circle cx="80" cy="614" r="1" fill="#e2ecff" opacity="0.72"/><circle cx="702" cy="126" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="495" cy="531" r="0.7" fill="#e2ecff" opacity="0.35"/><circle cx="1707" cy="530" r="1.45" fill="#e2ecff" opacity="0.72"/><circle cx="248" cy="699" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="1673" cy="429" r="0.7" fill="#e2ecff" opacity="0.35"/><circle cx="1549" cy="659" r="0.85" fill="#e2ecff" opacity="0.65"/><circle cx="1778" cy="496" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="964" cy="371" r="1.45" fill="#e2ecff" opacity="0.72"/><circle cx="551" cy="584" r="1.1" fill="#e2ecff" opacity="0.48"/><circle cx="871" cy="295" r="1.1" fill="#e2ecff" opacity="0.85"/><circle cx="1670" cy="101" r="0.7" fill="#e2ecff" opacity="0.55"/><circle cx="866" cy="719" r="1.45" fill="#e2ecff" opacity="0.85"/><circle cx="1542" cy="656" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="696" cy="269" r="0.7" fill="#e2ecff" opacity="0.25"/><circle cx="1418" cy="680" r="1.8" fill="#e2ecff" opacity="0.85"/><circle cx="1307" cy="470" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="617" cy="250" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="1012" cy="733" r="1" fill="#e2ecff" opacity="0.72"/><circle cx="1360" cy="819" r="1.45" fill="#e2ecff" opacity="0.19"/><circle cx="534" cy="455" r="1.1" fill="#e2ecff" opacity="0.55"/><circle cx="160" cy="623" r="1" fill="#e2ecff" opacity="0.65"/><circle cx="1099" cy="64" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="1053" cy="70" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="378" cy="690" r="1.8" fill="#e2ecff" opacity="0.35"/><circle cx="587" cy="740" r="1.1" fill="#e2ecff" opacity="0.85"/><circle cx="415" cy="475" r="1.1" fill="#e2ecff" opacity="0.72"/><circle cx="337" cy="41" r="1.1" fill="#e2ecff" opacity="0.25"/><circle cx="1785" cy="619" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="110" cy="236" r="0.85" fill="#e2ecff" opacity="0.65"/><circle cx="1544" cy="81" r="1" fill="#e2ecff" opacity="0.72"/><circle cx="698" cy="844" r="0.85" fill="#e2ecff" opacity="0.40"/><circle cx="895" cy="252" r="1.45" fill="#e2ecff" opacity="0.55"/><circle cx="1805" cy="372" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="1209" cy="603" r="0.65" fill="#e2ecff" opacity="0.72"/><circle cx="1844" cy="835" r="1.1" fill="#e2ecff" opacity="0.26"/><circle cx="76" cy="233" r="0.85" fill="#e2ecff" opacity="0.25"/><circle cx="414" cy="674" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="69" cy="568" r="0.7" fill="#e2ecff" opacity="0.55"/><circle cx="1805" cy="64" r="0.65" fill="#e2ecff" opacity="0.43"/><circle cx="510" cy="918" r="1.1" fill="#e2ecff" opacity="0.26"/><circle cx="1406" cy="33" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="362" cy="120" r="1.1" fill="#e2ecff" opacity="0.55"/><circle cx="131" cy="658" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="503" cy="250" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="1409" cy="11" r="0.7" fill="#e2ecff" opacity="0.85"/><circle cx="162" cy="783" r="0.85" fill="#e2ecff" opacity="0.14"/><circle cx="1597" cy="735" r="0.85" fill="#e2ecff" opacity="0.55"/><circle cx="1755" cy="473" r="0.85" fill="#e2ecff" opacity="0.48"/><circle cx="945" cy="918" r="0.7" fill="#e2ecff" opacity="0.40"/><circle cx="1672" cy="560" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="1181" cy="729" r="1.8" fill="#e2ecff" opacity="0.55"/><circle cx="649" cy="740" r="0.85" fill="#e2ecff" opacity="0.65"/><circle cx="1144" cy="739" r="0.85" fill="#e2ecff" opacity="0.48"/><circle cx="1312" cy="635" r="1.45" fill="#e2ecff" opacity="0.25"/><circle cx="1090" cy="7" r="0.65" fill="#e2ecff" opacity="0.43"/><circle cx="1453" cy="655" r="0.65" fill="#e2ecff" opacity="0.48"/><circle cx="776" cy="660" r="1" fill="#e2ecff" opacity="0.43"/><circle cx="1138" cy="773" r="0.7" fill="#e2ecff" opacity="0.24"/><circle cx="1804" cy="499" r="1" fill="#e2ecff" opacity="0.72"/><circle cx="1889" cy="592" r="1.8" fill="#e2ecff" opacity="0.72"/><circle cx="1607" cy="255" r="1.45" fill="#e2ecff" opacity="0.25"/><circle cx="1638" cy="18" r="1.45" fill="#e2ecff" opacity="0.35"/><circle cx="167" cy="487" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="1797" cy="390" r="1.8" fill="#e2ecff" opacity="0.25"/><circle cx="1802" cy="129" r="0.85" fill="#e2ecff" opacity="0.72"/><circle cx="874" cy="319" r="1" fill="#e2ecff" opacity="0.35"/><circle cx="280" cy="196" r="1.8" fill="#e2ecff" opacity="0.65"/><circle cx="1051" cy="509" r="1.45" fill="#e2ecff" opacity="0.35"/><circle cx="1350" cy="177" r="0.85" fill="#e2ecff" opacity="0.55"/><circle cx="167" cy="196" r="0.85" fill="#e2ecff" opacity="0.65"/><circle cx="631" cy="442" r="0.65" fill="#e2ecff" opacity="0.72"/><circle cx="538" cy="474" r="0.7" fill="#e2ecff" opacity="0.43"/><circle cx="1146" cy="67" r="0.7" fill="#e2ecff" opacity="0.65"/><circle cx="1836" cy="491" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="96" cy="843" r="0.85" fill="#e2ecff" opacity="0.19"/><circle cx="591" cy="225" r="0.85" fill="#e2ecff" opacity="0.72"/><circle cx="1451" cy="816" r="1" fill="#e2ecff" opacity="0.47"/><circle cx="871" cy="879" r="0.65" fill="#e2ecff" opacity="0.40"/><circle cx="318" cy="79" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="1183" cy="447" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="20" cy="69" r="0.65" fill="#e2ecff" opacity="0.35"/><circle cx="375" cy="919" r="1" fill="#e2ecff" opacity="0.47"/><circle cx="1636" cy="529" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="236" cy="641" r="1.45" fill="#e2ecff" opacity="0.43"/><circle cx="667" cy="427" r="1.1" fill="#e2ecff" opacity="0.65"/><circle cx="1055" cy="549" r="1.8" fill="#e2ecff" opacity="0.55"/><circle cx="1487" cy="846" r="1.45" fill="#e2ecff" opacity="0.19"/><circle cx="619" cy="791" r="1" fill="#e2ecff" opacity="0.24"/><circle cx="1232" cy="842" r="1.45" fill="#e2ecff" opacity="0.26"/><circle cx="1650" cy="570" r="0.7" fill="#e2ecff" opacity="0.72"/><circle cx="881" cy="49" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="617" cy="614" r="1.1" fill="#e2ecff" opacity="0.35"/><circle cx="45" cy="900" r="1" fill="#e2ecff" opacity="0.14"/><circle cx="961" cy="429" r="0.85" fill="#e2ecff" opacity="0.72"/><circle cx="1453" cy="519" r="1.45" fill="#e2ecff" opacity="0.65"/><circle cx="138" cy="207" r="1.8" fill="#e2ecff" opacity="0.55"/><circle cx="1066" cy="300" r="0.7" fill="#e2ecff" opacity="0.65"/><circle cx="417" cy="569" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="466" cy="150" r="1.45" fill="#e2ecff" opacity="0.55"/><circle cx="1692" cy="255" r="1.8" fill="#e2ecff" opacity="0.72"/><circle cx="1015" cy="160" r="0.7" fill="#e2ecff" opacity="0.55"/><circle cx="687" cy="557" r="0.7" fill="#e2ecff" opacity="0.35"/><circle cx="1075" cy="321" r="0.7" fill="#e2ecff" opacity="0.48"/><circle cx="33" cy="357" r="1.8" fill="#e2ecff" opacity="0.85"/><circle cx="1444" cy="21" r="1.8" fill="#e2ecff" opacity="0.65"/><circle cx="911" cy="270" r="1.1" fill="#e2ecff" opacity="0.48"/><circle cx="614" cy="852" r="1" fill="#e2ecff" opacity="0.14"/><circle cx="456" cy="524" r="0.85" fill="#e2ecff" opacity="0.43"/><circle cx="1707" cy="861" r="1.45" fill="#e2ecff" opacity="0.24"/><circle cx="187" cy="421" r="1.1" fill="#e2ecff" opacity="0.48"/><circle cx="1595" cy="789" r="0.7" fill="#e2ecff" opacity="0.14"/><circle cx="179" cy="689" r="1" fill="#e2ecff" opacity="0.25"/><circle cx="754" cy="881" r="0.7" fill="#e2ecff" opacity="0.30"/><circle cx="1433" cy="68" r="1.1" fill="#e2ecff" opacity="0.43"/><circle cx="157" cy="511" r="1.8" fill="#e2ecff" opacity="0.72"/><circle cx="1480" cy="476" r="1.8" fill="#e2ecff" opacity="0.25"/><circle cx="541" cy="934" r="1.45" fill="#e2ecff" opacity="0.14"/><circle cx="353" cy="315" r="1.1" fill="#e2ecff" opacity="0.65"/><circle cx="1209" cy="718" r="1" fill="#e2ecff" opacity="0.72"/><circle cx="280" cy="925" r="0.7" fill="#e2ecff" opacity="0.47"/><circle cx="674" cy="858" r="1" fill="#e2ecff" opacity="0.26"/><circle cx="1577" cy="525" r="1.45" fill="#e2ecff" opacity="0.55"/><circle cx="202" cy="304" r="1" fill="#e2ecff" opacity="0.85"/><circle cx="93" cy="914" r="0.65" fill="#e2ecff" opacity="0.40"/><circle cx="222" cy="739" r="1.1" fill="#e2ecff" opacity="0.48"/><circle cx="1851" cy="780" r="0.85" fill="#e2ecff" opacity="0.19"/><circle cx="1706" cy="840" r="1.8" fill="#e2ecff" opacity="0.14"/><circle cx="883" cy="308" r="0.85" fill="#e2ecff" opacity="0.35"/><circle cx="863" cy="944" r="0.7" fill="#e2ecff" opacity="0.40"/><circle cx="1603" cy="514" r="1" fill="#e2ecff" opacity="0.35"/><circle cx="1879" cy="821" r="1.8" fill="#e2ecff" opacity="0.26"/><circle cx="1625" cy="733" r="0.7" fill="#e2ecff" opacity="0.65"/><circle cx="445" cy="60" r="0.85" fill="#e2ecff" opacity="0.85"/><circle cx="1497" cy="223" r="0.85" fill="#e2ecff" opacity="0.55"/><circle cx="108" cy="166" r="0.7" fill="#e2ecff" opacity="0.35"/><circle cx="876" cy="470" r="0.85" fill="#e2ecff" opacity="0.35"/><circle cx="1072" cy="841" r="0.65" fill="#e2ecff" opacity="0.24"/><circle cx="1368" cy="228" r="1" fill="#e2ecff" opacity="0.65"/><circle cx="826" cy="134" r="0.65" fill="#e2ecff" opacity="0.43"/><circle cx="1731" cy="498" r="0.7" fill="#e2ecff" opacity="0.48"/><circle cx="1777" cy="305" r="1" fill="#e2ecff" opacity="0.65"/><circle cx="1275" cy="454" r="1.45" fill="#e2ecff" opacity="0.55"/><circle cx="1796" cy="346" r="1.1" fill="#e2ecff" opacity="0.85"/><circle cx="333" cy="27" r="1" fill="#e2ecff" opacity="0.55"/><circle cx="716" cy="450" r="1" fill="#e2ecff" opacity="0.35"/><circle cx="1286" cy="882" r="0.85" fill="#e2ecff" opacity="0.26"/><circle cx="1588" cy="686" r="0.85" fill="#e2ecff" opacity="0.72"/><circle cx="1300" cy="747" r="0.85" fill="#e2ecff" opacity="0.72"/><circle cx="1818" cy="884" r="1.45" fill="#e2ecff" opacity="0.40"/><circle cx="842" cy="131" r="1.1" fill="#e2ecff" opacity="0.25"/><circle cx="515" cy="538" r="1.1" fill="#e2ecff" opacity="0.55"/><circle cx="792" cy="225" r="0.85" fill="#e2ecff" opacity="0.85"/><circle cx="305" cy="376" r="0.7" fill="#e2ecff" opacity="0.35"/><circle cx="1475" cy="631" r="1" fill="#e2ecff" opacity="0.85"/><path d="M182 94h16 M190 86v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="190" cy="94" r="2.4" fill="#dbe8ff"/><path d="M477 241h16 M485 233v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="485" cy="241" r="2.4" fill="#dbe8ff"/><path d="M862 138h16 M870 130v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="870" cy="138" r="2.4" fill="#dbe8ff"/><path d="M1282 210h16 M1290 202v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="1290" cy="210" r="2.4" fill="#dbe8ff"/><path d="M1552 88h16 M1560 80v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="1560" cy="88" r="2.4" fill="#dbe8ff"/><path d="M1742 325h16 M1750 317v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="1750" cy="325" r="2.4" fill="#dbe8ff"/><path d="M572 430h16 M580 422v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="580" cy="430" r="2.4" fill="#dbe8ff"/><path d="M1022 280h16 M1030 272v16" stroke="#ceddff" stroke-width="1" opacity=".55"/><circle cx="1030" cy="280" r="2.4" fill="#dbe8ff"/>\n<!-- Silhouette of a riverside settlement along the bottom edge, kept soft so text stays legible. -->\n<path d="M0 930 Q190 870 420 925 Q580 860 790 929 Q980 882 1140 936 Q1430 850 1650 933 Q1790 883 1920 908V1080H0Z" fill="#0a142b" opacity=".70"/>\n<g fill="url(#horizon)" opacity=".80"><path d="M0 996H110V920H153V944H215V884H255V884H267V822H284V884H330V934H415V900H450V988H486V918H526V980H600V922H632V870H641V844H651V870H664V922H700V1000H740V940H787V980H920V921H943V870H952V844H961V870H974V921H1035V987H1150V939H1190V891H1220V839H1238V891H1270V937H1376V974H1448V902H1491V867H1515V902H1560V980H1660V930H1700V872H1711V835H1722V872H1741V930H1810V975H1920V1080H0Z"/>\n<path d="M592 920 Q645 863 704 920M1441 902 Q1498 837 1556 902" fill="none" stroke="#17223c" stroke-width="13"/></g>\n<path d="M0 1010 Q420 995 830 1010 Q1240 988 1920 1010V1080H0Z" fill="#081024" opacity=".9"/>\n</svg>'
FLOAT_STYLE = '#mlFloatAccess{position:fixed;z-index:11000;inset:auto 15px auto auto;top:52vh;transform:translateY(-50%);width:54px;height:54px;border-radius:50%;border:1px solid rgba(240,213,168,.75);background:rgba(53,34,53,.55);color:#ffedc8;box-shadow:0 6px 20px rgba(7,11,26,.26);font:700 27px Arial,sans-serif;display:grid;place-items:center;cursor:grab;touch-action:none;user-select:none;backdrop-filter:blur(5px);opacity:.40;transition:opacity .3s,box-shadow .3s,background .3s}\n#mlFloatAccess:hover,#mlFloatAccess:focus-visible,#mlFloatAccess.ml-moving{opacity:1;background:rgba(74,41,64,.9);box-shadow:0 5px 25px rgba(14,9,27,.3)}\n#mlFloatAccess[hidden]{display:none!important}\n#mlFloatAccess:focus-visible{outline:3px solid #ecc681;outline-offset:3px}\n@media print{#mlFloatAccess{display:none!important}}\n@media(prefers-reduced-motion:reduce){#mlFloatAccess{transition:none}}'
FLOAT_SCRIPT = "(()=>{'use strict';\nif(document.getElementById('mlFloatAccess'))return;\nconst opener=document.getElementById('accessOpen');\nif(!opener)return;\nconst button=document.createElement('button');button.id='mlFloatAccess';button.type='button';\nbutton.textContent='☷';button.setAttribute('aria-label','فتح قائمة الوصول وأدوات القراءة');\nbutton.setAttribute('title','قائمة الوصول — اضغط لفتحها أو اسحب الزر');\ndocument.body.appendChild(button);\nconst drawer=document.getElementById('accessDrawer');if(drawer){const sync=()=>{button.hidden=!drawer.hidden};new MutationObserver(sync).observe(drawer,{attributes:true,attributeFilter:['hidden']});sync();}\nconst key='malakut:access:position';let moved=false,down=null;\nfunction clamp(v,min,max){return Math.max(min,Math.min(max,v))}\nfunction place(x,y){let ww=window.innerWidth,hh=window.innerHeight;button.style.left=clamp(x,4,ww-58)+'px';button.style.top=clamp(y,4,hh-58)+'px';button.style.right='auto';button.style.bottom='auto';button.style.transform='none'}\ntry{const pos=JSON.parse(localStorage.getItem(key));if(pos&&Number.isFinite(pos.x)&&Number.isFinite(pos.y))place(pos.x*(innerWidth-54),pos.y*(innerHeight-54))}catch(e){}\nbutton.addEventListener('pointerdown',e=>{if(e.button!==0)return;down={x:e.clientX,y:e.clientY,left:button.getBoundingClientRect().left,top:button.getBoundingClientRect().top};moved=false;button.classList.add('ml-moving');button.setPointerCapture(e.pointerId)});\nbutton.addEventListener('pointermove',e=>{if(!down)return;const dx=e.clientX-down.x,dy=e.clientY-down.y;if(Math.hypot(dx,dy)>6)moved=true;if(moved)place(down.left+dx,down.top+dy)});\nbutton.addEventListener('pointerup',()=>{if(!down)return;button.classList.remove('ml-moving');if(moved){let r=button.getBoundingClientRect();try{localStorage.setItem(key,JSON.stringify({x:r.left/Math.max(1,innerWidth-54),y:r.top/Math.max(1,innerHeight-54)}))}catch(e){}}down=null;});\nbutton.addEventListener('pointercancel',()=>{button.classList.remove('ml-moving');down=null;});\nbutton.addEventListener('click',e=>{if(moved){e.preventDefault();e.stopPropagation();moved=false;return;}opener.click();});\nwindow.addEventListener('resize',()=>{const r=button.getBoundingClientRect();if(button.style.left)place(r.left,r.top)});\n})();"

# --- Universally applied visual and reader improvements (2026) ---

# Generate the decorative backdrop as an actual local SVG image at build time.
# The chapter pages keep their own backgrounds and print styles.
ASSETS = OUT / 'assets'
ASSETS.mkdir(exist_ok=True)
(ASSETS / 'library-night-sky.svg').write_text(SKY_ART, encoding='utf-8')
(ASSETS / 'malakut-floating-access.css').write_text(FLOAT_STYLE, encoding='utf-8')
(ASSETS / 'malakut-floating-access.js').write_text(FLOAT_SCRIPT, encoding='utf-8')

cosmic_css = """<style id="malakut-night-theme">
body{background-color:#071429!important;background-image:linear-gradient(to bottom,rgba(5,11,29,.14) 0%,rgba(5,11,29,.45) 48%,rgba(5,11,29,.85) 100%),url("./assets/library-night-sky.svg")!important;background-repeat:no-repeat!important;background-size:cover!important;background-position:center top!important;background-attachment:fixed!important;isolation:isolate}
body>.hero,body>main,body>.quote,body>footer{position:relative;z-index:1}
header{background:rgba(6,13,31,.81)!important}
.ml-shooting-stars{position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0}
.ml-meteor{position:absolute;top:11%;left:-160px;width:105px;height:1px;opacity:0;background:linear-gradient(to right,transparent,rgba(154,199,255,.3),rgba(234,244,255,.85));filter:drop-shadow(0 0 3px #a5bdff);transform:rotate(23deg);animation:ml-meteor-move 19s linear infinite}
.ml-meteor:nth-child(2){top:29%;animation-delay:8.5s;animation-duration:25s;width:75px;filter:drop-shadow(0 0 2px #d9d2ff)}
.ml-meteor:nth-child(3){top:8%;animation-delay:15s;animation-duration:31s;width:58px}
@keyframes ml-meteor-move{0%,11%{opacity:0;transform:translate3d(0,0,0) rotate(23deg)}12%{opacity:.65}16%{opacity:0;transform:translate3d(125vw,28vh,0) rotate(23deg)}100%{opacity:0;transform:translate3d(125vw,28vh,0) rotate(23deg)}}
@media(max-width:600px){body{background-attachment:scroll!important}.ml-meteor{width:65px}}
@media(prefers-reduced-motion:reduce){.ml-meteor{animation:none!important;display:none}}
@media print{.ml-shooting-stars{display:none!important}body{background:white!important}}
</style>"""
cosmic_decor = '<div class="ml-shooting-stars" aria-hidden="true"><span class="ml-meteor"></span><span class="ml-meteor"></span><span class="ml-meteor"></span></div>'
if index.exists():
    html = index.read_text(encoding='utf-8')
    if 'malakut-night-theme' not in html:
        html = re.sub(r'</head\s*>', lambda m: cosmic_css + m.group(0), html, count=1, flags=re.I)
        html = re.sub(r'<body([^>]*)>', lambda m:m.group(0) + cosmic_decor, html, count=1, flags=re.I)
        index.write_text(html, encoding='utf-8')
# Adding the floating access button leaves the original access drawer in control.
# The live scripts and print settings in each chapter remain untouched.
for chap in OUT.glob('*.html'):
    if chap.name.lower() in {'index.html','years.html'}:continue
    h=chap.read_text(encoding='utf-8', errors='replace')
    if 'id="accessOpen"' not in h and "id='accessOpen'" not in h:continue
    if 'malakut-floating-access.js' in h:continue
    h = re.sub(r'</head\s*>', '<link rel="stylesheet" href="./assets/malakut-floating-access.css"></head>', h, count=1, flags=re.I)
    h = re.sub(r'</body\s*>', '<script src="./assets/malakut-floating-access.js" defer></script></body>', h, count=1, flags=re.I)
    chap.write_text(h, encoding='utf-8')

print('Published', len(entries), 'novels and', sum(len(b['chapters']) for b in entries), 'HTML chapters')

# ----------------- Moonlit desert video background -----------------
# Home page only. Chapters / years.html keep their own reader themes.
# Audio starts muted; visitors may opt in to the gentle wind.
video_asset = OUT / 'assets' / 'library-night.mp4'
if index.exists() and video_asset.exists():
    html = index.read_text(encoding='utf-8')
    video_css = '''<style id="malakut-video-night-style">
body{background-color:#030b18!important;background-image:linear-gradient(to bottom,rgba(1,8,23,.36),rgba(1,8,23,.48)),url("./assets/library-night-poster.webp")!important;background-position:center center!important;background-size:cover!important}
#malakut-night-video{position:fixed;inset:0;display:block;width:100%;height:100%;object-fit:cover;object-position:center center;z-index:0;pointer-events:none;filter:brightness(.7) saturate(.92)}
#malakut-night-shade{position:fixed;inset:0;z-index:0;pointer-events:none;background:linear-gradient(to bottom,rgba(2,7,21,.20) 0%,rgba(3,9,23,.27) 30%,rgba(3,9,23,.62) 100%)}
.ml-shooting-stars{display:none!important} /* The video already includes rare meteors. */
#malakut-night-controls{position:fixed;left:14px;bottom:13px;display:flex;gap:8px;z-index:101;direction:rtl;flex-wrap:wrap}
#malakut-night-controls button{background:rgba(5,17,38,.8);border:1px solid rgba(226,192,132,.46);border-radius:100px;padding:7px 13px;color:#f2d9b6;font:500 13px Tahoma,Arial,sans-serif;cursor:pointer;backdrop-filter:blur(5px);touch-action:manipulation}
#malakut-night-controls button:hover{background:rgba(29,43,68,.94)}
#malakut-night-controls button:focus-visible{outline:2px solid #e7bb78;outline-offset:3px}
@media(max-width:680px){#malakut-night-video{object-position:74% center}#malakut-night-controls{bottom:7px;left:8px}#malakut-night-controls button{padding:6px 10px;font-size:11px}}
@media(prefers-reduced-motion:reduce){#malakut-night-video{display:none!important}}
@media print{#malakut-night-video,#malakut-night-shade,#malakut-night-controls{display:none!important}body{background:#fff!important;color:#111!important}}
</style>'''
    video_dom = '''<video id="malakut-night-video" aria-hidden="true" autoplay muted loop playsinline preload="metadata" poster="./assets/library-night-poster.webp"><source src="./assets/library-night.mp4" type="video/mp4"></video><div id="malakut-night-shade" aria-hidden="true"></div><div id="malakut-night-controls"><button id="malakut-wind" type="button" aria-pressed="false" title="تشغيل أو كتم نسيم الرياح">♫ تشغيل النسيم</button><button id="malakut-motion" type="button" aria-pressed="true" title="إيقاف أو تشغيل حركة الخلفية">❚❚ إيقاف الحركة</button></div>'''
    video_js = '''<script id="malakut-night-logic">(()=>{
const video=document.getElementById('malakut-night-video');
const sound=document.getElementById('malakut-wind');
const motion=document.getElementById('malakut-motion');
if(!video || !sound || !motion)return;
video.volume=0.17;
let allowMotion=!window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if(!allowMotion)video.pause();
const draw=()=>{motion.textContent=video.paused?'▶ تشغيل الحركة':'❚❚ إيقاف الحركة';motion.setAttribute('aria-pressed',String(!video.paused));sound.textContent=video.muted?'♫ تشغيل النسيم':'♪ كتم النسيم';sound.setAttribute('aria-pressed',String(!video.muted))};
sound.addEventListener('click',()=>{video.muted=!video.muted;if(!video.muted&&video.paused&&allowMotion)video.play().catch(()=>{});draw()});
motion.addEventListener('click',()=>{if(video.paused){allowMotion=true;video.play().catch(()=>{});}else{allowMotion=false;video.pause();video.muted=true;}draw()});
video.addEventListener('play',draw);video.addEventListener('pause',draw);
document.addEventListener('visibilitychange',()=>{if(document.hidden)video.pause();else if(allowMotion)video.play().catch(()=>{});draw()});
if(allowMotion)video.play().catch(()=>{});draw();
})();</script>'''
    if 'id="malakut-night-video"' not in html:
        html = re.sub(r'</head\s*>',lambda m:video_css + m.group(0),html,count=1,flags=re.I)
        html = re.sub(r'<body([^>]*)>',lambda m:m.group(0)+video_dom,html,count=1,flags=re.I)
        html = re.sub(r'</body\s*>',lambda m:video_js+m.group(0),html,count=1,flags=re.I)
        index.write_text(html,encoding='utf-8')
