# -*- coding: utf-8 -*-
"""主流程：读 CSV → 去重 → 噪音过滤 → 分类 → 信息密度评分 → 应用人工覆盖

三件事必须解耦，否则精度会崩：
  ① 是不是问题     → complaint.py 门控（好评里大量出现功能词，L1 判不出这个）
  ② 属于哪个功能域 → taxonomy.L1_KEYWORDS（话题词）
  ③ 具体什么症状   → taxonomy.L2_RULES（症状词）
"""
import csv, glob, json, re, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
import confidence as CONF
import complaint as CMP
import negation as NEG

TX = K.load_taxonomy()
L1_KEYWORDS, L2_RULES = TX.L1_KEYWORDS, TX.L2_RULES
L1_PRIORITY = getattr(TX, 'L1_PRIORITY', list(L1_KEYWORDS))

PRAISE = [
 # 通用短好评 + 实际数据里一轮轮补出来的长尾（多为"1★ 但正文在夸"）
 r"^(جميل|رائع|ممتاز|ممتازة|حلو|جيد|جيده|تمام|طيب|روعه|روعة|قوه|قوة|سمح|راقي|امين|لا باس|شيلات|عالی|عالیه|خوبه|خوب|good|nice|ok+|okay|great|super|awesome|excellent|fantastic|best|bien|bueno|buena|muy buena|excelente|genial|top|bom|é bom|bagus|mantap|luumayan|good app|i like it|i love it|love it|very good|not bad|улет|топ|отлично|хорошо|👍|❤️|🥰|😘|😎|💯|⭐)[\s\.\!،,~⭐👍🔥💯✨😍🥰❤️😘]*$",
 r"^(عالیست|رئع|جيد جد|ممتاز جد|جميل جد|جدن|مشاالله|ماشالله|الله|رائع جد|بسیار خوب|خیلی خوب)",
 r"^(very good|really good|so good|pretty good|good app|great app|nice app|best app|best player|i like|i love|love this|amo|adoro|me gusta|j.aime|meilleur|bien fait|muy bien|muito bom|sangat bagus|very nice|so very|excelent)",
 r"^(excelente|exelente|incroyable|trop classe|very helpful|very practical|easy to use|favourite|favorite|all good|not bad|good spp|très bon|tres bon|bonne application|satisfeito|mui buena|muy bueno|e bom sim|c.est bon|güzel|ดีก่อน|telegere bien)",
 r"^(تطبيق (ممتاز|رائع|جميل|حلو)|برنامج (مديح|ممتاز|رائع)|احلا صوت|حلوه وقوي|حلو جدن|راقي|عالی است|برنامه عالی)",
 r"^(毎日便利|使いやすい|良いアプリ|最高です)",
 r"^(o melhor|é um aplicativo muito bom|nota-se que é um excelente)",
 r"^(用起来不错|很好用|不错|好用)",
]
RANT = [
 # 纯负面情绪、零信息量（无法定位任何功能点）
 r"^(bad|worst|worse|trash|garbage|rubbish|useless|poor|terrible|horrible|awful|shit|sucks|crap|waste|no good|not good|dislike|hate it|scam|fake|stupid|dumb)[\s\.\!,~👎😡🤬💩]*$",
 r"^(плохо|плохой|дрянь|отстой|шляпа|мусор|хлам|говно|фэйк|ужас|кошмар|барахло|не работает|ни о чем|не рекомендую|ужасно|отвратительн|бесполезн)",
 r"^(sampah|jelek|buruk|payah|gaguna|ga guna|parah)",
 r"^(malo|mala|muy mala|basura|horrible|pésimo|pesimo|muito ruim|ruim|péssimo|lixo)",
 r"^(zift|زفت|سيئ|سيء|ضعيف|عفن|يع|تطبيق سي)",
 r"^(مزخرف|افتضاح|مفت نمیرزه|چرت)",
 r"^(ゴミ|くそ|駄目|ダメ|最悪)",
 r"^(çöp|berbat|rezalet|beş para etmez|kötü)",
 r"^(ko tốt|không tốt|tệ)",
 r"^(垃圾|烂|爛|差劲|差勁|很差)",
 r"^(별로|최악|쓰레기)",
 r"^(dziadostwo|beznadzieja|tragedia)",
 r"^(โคตรแย่|แย่มาก|ไม่ดี)",
]
PRAISE_RE = [re.compile(p, re.I) for p in PRAISE]
RANT_RE   = [re.compile(p, re.I) for p in RANT]
L1_RE = {k: [re.compile(p, re.I) for p in v] for k, v in L1_KEYWORDS.items()}
L2_RE = [(a, b, [re.compile(p, re.I) for p in ps]) for a, b, ps in L2_RULES]

def clean(t):
    return re.sub(r'\s+', ' ', t).strip()

def has_topic_word(text):
    return any(NEG.hit(rs, text) for rs in L1_RE.values())

def noise_kind(text):
    t = text.strip()
    if len(t) <= 3 or re.fullmatch(r'[\W\d_]+', t):
        return 'tooshort'
    for r in PRAISE_RE:
        if r.match(t): return 'praise'
    for r in RANT_RE:
        if r.match(t):
            # 骂人但提到了具体功能 → 不是纯情绪，是有指向的抱怨，不能丢
            # 例：'не работает.звук'(不工作，声音) 开头命中 RANT，但 звук 是功能词
            return None if has_topic_word(t) else 'rant'
    return None

def no_signal(text, star):
    """低星短评论，既不在抱怨也没提任何功能 → 无有效信息。
    比穷举多语言好评词鲁棒：'excellent app' 被拦，'再生できない' 不会误杀。"""
    t = text.strip()
    if star > 3 or len(t) >= 45:
        return False
    return not CMP.is_complaint(t, star) and not has_topic_word(t)

def classify(text):
    hits_l1 = [l1 for l1, rs in L1_RE.items() if NEG.hit(rs, text)]
    hits_l2 = [(a, b) for a, b, rs in L2_RE if NEG.hit(rs, text)]
    for a, _ in hits_l2:
        if a not in hits_l1: hits_l1.append(a)
    primary = next((p for p in L1_PRIORITY if p in hits_l1), None)
    primary_l2 = next((b for a, b in hits_l2 if a == primary), None)
    return hits_l1, hits_l2, primary, primary_l2

def load_reviews():
    rows = []
    for f in sorted(glob.glob(os.path.join(K.ROOT, 'raw', '*.csv'))):
        enc = 'utf-16' if open(f, 'rb').read(2) == b'\xff\xfe' else 'utf-8-sig'
        with open(f, encoding=enc) as fh:
            rows.extend(list(csv.DictReader(fh)))
    if not rows:
        sys.exit(f"{K.ROOT}/raw/ 里没有评论 CSV。\n"
                 "Play Console → 下载报告 → 评论 → 选月份下载，放进 raw/")
    seen = {}
    for d in rows:
        k = d.get('Review Link') or (d.get('Review Submit Millis Since Epoch','') + d.get('Review Text','')[:50])
        prev = seen.get(k)
        if prev is None or d.get('Review Last Update Millis Since Epoch','') > prev.get('Review Last Update Millis Since Epoch',''):
            seen[k] = d
    return list(seen.values())

def load_override():
    fp = os.path.join(K.ROOT, 'data', 'manual_override.json')
    if not os.path.exists(fp): return {}
    return {k: v for k, v in json.load(open(fp, encoding='utf-8')).items() if not k.startswith('_')}

def main():
    rows = load_reviews()
    override = load_override()
    out = []
    # 用 Last Update 排序：用户改旧评论时 Submit 仍是首次提交时间，会把本期反馈排到几年前
    for i, d in enumerate(sorted(rows, key=lambda x: x.get('Review Last Update Millis Since Epoch',''))):
        text = clean(d.get('Review Text',''))
        if not text: continue
        star = int(d.get('Star Rating') or 0)
        rec = {
            'id': f'R{i+1:05d}', 'star': star,
            'lang': d.get('Reviewer Language',''), 'device': d.get('Device',''),
            'ver': d.get('App Version Name',''), 'vercode': d.get('App Version Code',''),
            'submit': d.get('Review Submit Date and Time','')[:10],
            'update': d.get('Review Last Update Date and Time','')[:10],
            'text': text, 'link': d.get('Review Link',''),
            'replied': bool((d.get('Developer Reply Text') or '').strip()),
        }
        nk = noise_kind(text) or ('no_signal' if no_signal(text, star) else None)
        h1, h2, p, p2 = classify(text)
        # 4-5★ 必须命中强信号才算问题：好评大量提到功能词
        if star >= 4 and not CMP.is_complaint(text, star):
            h1, h2, p, p2 = [], [], None, None
        if nk and not p:
            rec.update(noise=nk, l1=[], l2=[], primary=None, primary_l2=None)
        else:
            nk = None
            rec.update(noise=None, l1=h1, l2=[f'{a}::{b}' for a, b in h2], primary=p, primary_l2=p2)
        sc, sig = CONF.score(text, bool(p2), getattr(TX, 'DOMAIN_TERMS', None))
        rec.update(density=sc, signals=[CONF.SIGNAL_CN[x] for x in sig],
                   grade=CONF.grade(sc, nk), manual='')
        ov = override.get(rec['id'])
        if ov:
            if 'noise' in ov:
                rec.update(noise=ov['noise'], l1=[], l2=[], primary=None,
                           primary_l2=None, grade='D', manual=ov.get('note',''))
                out.append(rec); continue
            if 'primary' in ov:    rec['primary'] = ov['primary']
            if 'primary_l2' in ov: rec['primary_l2'] = ov['primary_l2']
            if 'grade' in ov:      rec['grade'] = ov['grade']
            tags = list(rec['l2'])
            if ov.get('primary') and ov.get('primary_l2'):
                m = f"{ov['primary']}::{ov['primary_l2']}"
                if m not in tags: tags.insert(0, m)
            for t in ov.get('extra', []):
                if t not in tags: tags.append(t)
            for t in ov.get('drop', []):
                if t in tags: tags.remove(t)
            rec['l2'] = tags
            rec['manual'] = ov.get('note', '已人工复核')
        out.append(rec)
    json.dump(out, open(K.data_path('classified.json'), 'w'), ensure_ascii=False, indent=1)
    low = [r for r in out if r['star'] <= 3]
    n = collections.Counter(r['noise'] or '有效' for r in low)
    print(f"带文本评论 {len(out)} 条 | 低星 {len(low)} 条")
    print(f"  低星噪音: 好评误打低星 {n['praise']} / 纯情绪 {n['rant']} / 无信号 {n['no_signal']} / 过短 {n['tooshort']}")
    print(f"  有效低星 {n['有效']} | 已归类 {sum(1 for r in out if r['primary'])}")

if __name__ == '__main__':
    main()
