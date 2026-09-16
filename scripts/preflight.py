# -*- coding: utf-8 -*-
"""飞行前检查 —— 把 gotchas 里能机器验的经验变成断言

设计原则：**同一个坑被踩第二次，就说明它不该靠文档提醒，该靠脚本拦。**
每条检查下面都注明它对应哪条血泪教训。

退出码：0=通过 1=有 ERROR（run_all 会中止）；WARN 不阻断。
单独跑：python3 <skill>/scripts/preflight.py
"""
import re, sys, os, json, csv, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
import complaint as CMP

ERRORS, WARNS, OKS = [], [], []
def err(m):  ERRORS.append(m)
def warn(m): WARNS.append(m)
def ok(m):   OKS.append(m)

def all_patterns(TX):
    """遍历 L1 + L2 的全部正则。
    教训：子串检测一度只扫 L1_KEYWORDS，而 `ави` 恰好在 L2_RULES 里，注入测试才发现漏了。"""
    for l1, ps in TX.L1_KEYWORDS.items():
        for p in ps:
            yield f'L1[{l1}]', p
    for a, b, ps in TX.L2_RULES:
        for p in ps:
            yield f'L2[{a}::{b}]', p
    for p in getattr(TX, 'DOMAIN_TERMS', []):
        yield 'DOMAIN', p

def load_sample_texts():
    """读全部评论文本。必须用全量——抽样会让"这条规则没命中"变成假警报，
    而假警报会让人忽略真警报，比没有检查更糟。"""
    seen, out = set(), []
    for f in sorted(glob.glob(os.path.join(K.ROOT, 'raw', '*.csv'))):
        enc = 'utf-16' if open(f, 'rb').read(2) == b'\xff\xfe' else 'utf-8-sig'
        with open(f, encoding=enc) as fh:
            for d in csv.DictReader(fh):
                t = (d.get('Review Text') or '').strip()
                k = d.get('Review Link') or t[:60]
                if t and k not in seen:
                    seen.add(k)
                    out.append((int(d.get('Star Rating') or 0), t))
    return out

# ══════════════════════════════════════════════════════════
def check_taxonomy_structure(TX):
    """结构完整性。教训：L1_PRIORITY 漏了某个分类 → 它永远拿不到主分类，静默失效"""
    for name in ('L1_KEYWORDS', 'L2_RULES'):
        if not hasattr(TX, name):
            err(f"taxonomy.py 缺少 {name}")
            return False
    l1s = set(TX.L1_KEYWORDS)
    prio = getattr(TX, 'L1_PRIORITY', None)
    if prio is None:
        warn("taxonomy.py 没有 L1_PRIORITY，将按字典序取主分类——建议显式指定优先级")
    else:
        missing = l1s - set(prio)
        extra = set(prio) - l1s
        if missing:
            err(f"L1_PRIORITY 漏了 {sorted(missing)} → 这些分类永远拿不到主分类（静默失效）")
        else:
            ok(f"L1_PRIORITY 覆盖全部 {len(l1s)} 个一级分类")
        if extra:
            warn(f"L1_PRIORITY 里有 L1_KEYWORDS 不存在的分类: {sorted(extra)}")
    bad = {a for a, b, ps in TX.L2_RULES} - l1s
    if bad:
        err(f"L2_RULES 引用了不存在的一级分类: {sorted(bad)}")
    else:
        ok(f"L2_RULES {len(TX.L2_RULES)} 条，一级分类引用全部有效")
    pol = getattr(TX, 'POLICY_L2', set())
    l2names = {b for a, b, ps in TX.L2_RULES}
    ghost = set(pol) - l2names
    if ghost:
        warn(f"POLICY_L2 里这些二级分类在 L2_RULES 中不存在（打错字？）: {sorted(ghost)}")
    if not getattr(TX, 'DOMAIN_TERMS', None):
        warn("DOMAIN_TERMS 为空 —— 该 app 特有的格式/功能名填上能提高信息密度评分准确度")
    return True

def check_regex_compiles(TX):
    """语法。教训：re.X(VERBOSE) 会忽略空格，让所有含空格的模式静默失效"""
    bad = []
    for where, p in all_patterns(TX):
        try: re.compile(p)
        except re.error as e: bad.append(f"{where} {p!r}: {e}")
    if bad:
        for b in bad[:10]: err(f"正则语法错误 {b}")
    else:
        ok("全部正则语法正确")

def check_dead_rules(TX, samples):
    """★最重要的一条★ 每条正则至少要能匹配到一条真实评论。

    匹配 0 条的规则要么写错了、要么过时了，而它【不会报错】——这是最危险的失效方式。
    真实案例两则（同一类错误被独立踩到两次）：
      · `\\bseká?\\b` 想表达"seka 或 seká"，实际是 "sek"+可选"á"，匹配不了原词 seka
      · `替换?([A-Za-z])` 想让"替换"整体可选，实际只有"换"可选，所有单字母简写提取全失败
    共同点：量词只作用于紧邻的单个字符/组，写错了不报错，只是永远匹配不上。
    """
    blob = '\n'.join(t for _, t in samples)      # 拼成一个大串，每条正则只搜一次
    dead = []
    for l1, ps in TX.L1_KEYWORDS.items():
        for p in ps:
            try:
                if not re.search(p, blob, re.I): dead.append(('L1', l1, p))
            except re.error: pass
    for a, b, ps in TX.L2_RULES:
        for p in ps:
            try:
                if not re.search(p, blob, re.I): dead.append(('L2', f'{a}::{b}', p))
            except re.error: pass
    total = sum(len(v) for v in TX.L1_KEYWORDS.values()) + sum(len(ps) for _,_,ps in TX.L2_RULES)
    if dead:
        pct = len(dead) / total * 100
        # 本期没出现的表达 ≠ 写错了，所以只提示不报错；但比例异常高说明有系统性问题
        lvl = warn if pct < 60 else err
        lvl(f"{len(dead)}/{total} ({pct:.0f}%) 条正则在全部 {len(samples)} 条评论里零命中。"
            f"多数是本期没出现的表达（正常），但【新加的规则】若在这里面，"
            f"八成是量词/词边界写错了——写错不会报错，只会静默失效。")
        WARNS.append(f"      完整清单见 data/preflight_dead_rules.txt")
        with open(K.data_path('preflight_dead_rules.txt'), 'w') as f:
            for kind, where, p in dead:
                f.write(f"{kind}\t{where}\t{p}\n")
    else:
        ok(f"所有 {total} 条正则在 {len(samples)} 条评论中均有命中")

def check_praise_contamination(TX, samples):
    """教训：往 complaint.STRONG 塞话题词(реклам)，导致 'без рекламы'(没有广告)被判成抱怨。
    用纯 5★ 好评当阴性对照组：强信号本不该在好评里大量出现。"""
    pos = [t for s, t in samples if s == 5 and not CMP.is_complaint(t, 5)]
    if len(pos) < 50:
        warn("5★ 样本不足，跳过强信号污染检查")
        return
    hits = []
    for p in CMP.STRONG:
        try: rg = re.compile(p, re.I)
        except re.error: continue
        n = sum(1 for t in pos if rg.search(t))
        if n / len(pos) > 0.01:      # 1% 的纯好评命中同一条"故障词" → 它多半是话题词
            hits.append((n, p))
    if hits:
        hits.sort(reverse=True)
        err(f"complaint.STRONG 里有 {len(hits)} 条在纯 5★ 好评中命中率 >1% —— "
            f"它们多半是【话题词】而非【故障词】，应移到 taxonomy.L1_KEYWORDS：")
        for n, p in hits[:5]:
            ERRORS.append(f"      {n}/{len(pos)} 条好评命中: {p!r}")
    else:
        ok(f"强信号表干净（{len(pos)} 条纯好评对照，无高命中话题词）")

# 只有【用空格分词的字母语言】才有"词边界"概念。
# CJK 不分词（"広告"前后必然是别的汉字）、阿拉伯语常带定冠词前缀，
# 对它们做词边界检测只会产生假警报——这类语言的子串误伤只能靠人读。
SPACED_SCRIPT = re.compile(r'^[\u0020-\u024f\u0370-\u03ff\u0400-\u04ff]+$')

def check_substring_traps(TX, samples):
    """教训：短词不加边界会被【嵌在别的词里】命中。
      ави ← нр**ави**тся(喜欢) / фон ← теле**фон**(手机) / seka ← bagus **seka**li(非常好)

    难在要跟【故意的词干匹配】区分：`реклам` 命中 рекламы/рекламу 是对的（俄语变格），
    `качеств` 命中 качество 也是对的。两者同样"嵌在更长的词里"。

    两条判据：
      ① 落在【词中】(左边仍是字母) → 几乎必是误伤。词干匹配总是落在词首
      ② 落在词首但【几乎从不独立出现】(右边>85%接字母) → 可能匹配到同前缀的别的词
    适用范围仅限拉丁/西里尔/希腊字母；CJK 与阿拉伯语跳过（见上方注释）。
    """
    blob = '\n'.join(t for _, t in samples)
    LETTER = re.compile(r'[^\W\d_]', re.U)
    midword, glued = [], []
    skipped = 0
    for where, p in all_patterns(TX):
        core = p.strip()
        if len(core) > 8 or re.search(r'[\\()\[\]|?*+{}.^$]', core):
            continue
        if not SPACED_SCRIPT.match(core):
            skipped += 1
            continue
        total = inside = rightglued = 0
        for m in re.finditer(re.escape(core), blob, re.I):
            total += 1
            if total > 400: break
            a, b = m.start() - 1, m.end()
            if a >= 0 and LETTER.match(blob[a]):
                inside += 1
            elif b < len(blob) and LETTER.match(blob[b]):
                rightglued += 1
        if total < 6:
            continue
        if inside / total >= 0.4:
            midword.append((inside, total, where, core))
        elif rightglued / total >= 0.85:
            glued.append((rightglued, total, where, core))
    if midword:
        midword.sort(reverse=True)
        err(f"{len(midword)} 条裸词有 ≥40% 命中落在【词中】—— 几乎必是子串误伤，加 \\b 词边界：")
        for inside, total, where, p in midword[:6]:
            ERRORS.append(f"      {inside}/{total} 次落在词中  {where} {p!r}")
    if glued:
        glued.sort(reverse=True)
        warn(f"{len(glued)} 条裸词几乎从不独立出现（右侧总接着字母）—— "
             f"确认是词干匹配(故意)还是匹配到了同前缀的别的词(如 seka←sekali)：")
        for rg, total, where, p in glued[:5]:
            WARNS.append(f"      {rg}/{total} 次右侧粘连  {where} {p!r}")
    if not midword and not glued:
        ok(f"未发现子串误伤（{skipped} 条 CJK/阿语词不适用此检测，需人工判断）")

def check_data():
    """CSV 编码与字段。教训：Play Console 导出是 UTF-16LE，不是 UTF-8"""
    files = sorted(glob.glob(os.path.join(K.ROOT, 'raw', '*.csv')))
    if not files:
        err(f"{K.ROOT}/raw/ 里没有评论 CSV")
        return
    need = {'Review Text', 'Star Rating', 'Review Last Update Date and Time', 'Device'}
    for f in files:
        enc = 'utf-16' if open(f, 'rb').read(2) == b'\xff\xfe' else 'utf-8-sig'
        try:
            with open(f, encoding=enc) as fh:
                head = set(next(csv.reader(fh)))
        except Exception as e:
            err(f"读不了 {os.path.basename(f)}（编码 {enc}）: {e}")
            continue
        miss = need - head
        if miss:
            err(f"{os.path.basename(f)} 缺少必要列: {sorted(miss)}")
    ok(f"raw/ 下 {len(files)} 个 CSV，编码与必要列检查通过")

def check_device_catalog():
    if not os.path.isdir(K.DEVICE_CATALOG):
        warn(f"公共设备目录不存在 ({K.DEVICE_CATALOG}) —— "
             f"机型/芯片维度会缺失，集中度分析会弱很多")
        return
    try:
        from device_lookup import stats
        s = stats()
        ok(f"设备目录 {s['devices']} 个代号可用")
    except Exception as e:
        warn(f"设备目录加载失败: {e}")

def check_outputs():
    """产出健康度。教训：表6 建完就没再更新过，腐烂了都不知道"""
    fp = K.data_path('sheet1_reviews.json')
    if not os.path.exists(fp):
        return
    d = json.load(open(fp, encoding='utf-8'))
    if len(d) < 2: return
    ci = {n: i for i, n in enumerate(d[0])}
    rows = d[1:]
    unc = sum(1 for r in rows if r[ci['关联问题ID']] == '（未分类·待补词表）')
    rate = unc / len(rows) * 100
    if rate > 15:
        warn(f"未分类率 {rate:.1f}%（{unc}/{len(rows)}）偏高 —— 逐条精读后写 manual_override，"
             f"可泛化的补进 taxonomy.py")
    else:
        ok(f"未分类率 {rate:.1f}%")
    dev = sum(1 for r in rows if r[ci['机型名']])
    if dev / len(rows) < 0.8:
        warn(f"设备代号命中率仅 {dev/len(rows)*100:.0f}% —— 设备目录可能该更新了")

def main():
    print("═" * 64)
    print("  飞行前检查（把踩过的坑变成断言）")
    print("═" * 64)
    TX = K.load_taxonomy()
    samples = load_sample_texts()
    if not samples:
        err("raw/ 里读不到任何评论文本")
    else:
        ok(f"样本 {len(samples)} 条评论")
    check_data()
    if check_taxonomy_structure(TX):
        check_regex_compiles(TX)
        if samples:
            check_dead_rules(TX, samples)
            check_praise_contamination(TX, samples)
            check_substring_traps(TX, samples)
    check_device_catalog()
    check_outputs()

    for m in OKS:    print(f"  ✓ {m}")
    for m in WARNS:  print(f"  ⚠ {m}")
    for m in ERRORS: print(f"  ✗ {m}")
    print("─" * 64)
    print(f"  {len(OKS)} 通过 / {len(WARNS)} 警告 / {len(ERRORS)} 错误")
    if ERRORS:
        print("  ✗ 有错误，流水线中止。修完再跑，或加 --skip-preflight 强制继续")
        return 1
    print("  ✓ 检查通过")
    return 0

if __name__ == '__main__':
    sys.exit(main())
