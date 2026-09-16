# -*- coding: utf-8 -*-
"""关键词误伤审计 —— 用 5★ 好评当阴性对照组
好评不应命中问题关键词；命中多的就是可疑规则（子串误伤 / 话题词误当问题词）。
每次改词表后跑一遍。
"""
import sys, re, json, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
import complaint as CMP
TX = K.load_taxonomy()
L1_KEYWORDS, L2_RULES = TX.L1_KEYWORDS, TX.L2_RULES

rows = json.load(open(K.data_path('classified.json'), encoding='utf-8'))
# 阴性对照：5★ 且不在抱怨（纯好评）
pos = [r['text'] for r in rows if r['star'] == 5 and not CMP.is_complaint(r['text'])]
neg = [r['text'] for r in rows if r['star'] <= 2]
print(f"阴性对照(纯5★好评) {len(pos)} / 阳性(1-2★) {len(neg)}\n")

sus = []
def audit(label, pat):
    try: rg = re.compile(pat, re.I)
    except re.error: return
    p = sum(1 for t in pos if rg.search(t))
    n = sum(1 for t in neg if rg.search(t))
    if p >= 5:
        sus.append((p, n, n/(p+.01), label, pat))

for l1, ps in L1_KEYWORDS.items():
    for p in ps: audit(f"L1:{l1}", p)
for l1, l2, ps in L2_RULES:
    for p in ps: audit(f"L2:{l1}::{l2}", p)

sus.sort(key=lambda x: -x[0])
bad = [x for x in sus if x[2] < 0.15]
print(f"{'好评':>5}{'差评':>5}{'比值':>7}  规则")
for p, n, r, label, pat in sus[:20]:
    flag = "❌" if r < 0.15 else ("⚠️ " if r < 0.4 else "  ")
    print(f"{flag}{p:4d}{n:5d}{r:7.2f}  {label}  {pat!r}")
print(f"\n可疑规则 {len(sus)} 条，其中高危(比值<0.15) {len(bad)} 条")
print("提示：高危规则多为【话题词】（如 quality/download），靠 complaint 门控拦截即可；")
print("      若是【子串误伤】（如 ави←нравится），必须加词边界修正则。")
