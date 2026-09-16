# -*- coding: utf-8 -*-
"""月度趋势（表6）：版本 × 分类的问题密度，用来发现版本引入的回归。
用密度(‰)而非绝对数，否则装机量大的版本永远看起来问题最多。
"""
import json, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
MIN_BASE = 30

def cats_of(r):
    return set(r['l1']) if r['l1'] else ({r['primary']} if r['primary'] else set())

def main():
    rows = json.load(open(K.data_path('classified.json'), encoding='utf-8'))
    base, cells = collections.Counter(), collections.Counter()
    for r in rows:
        m, v = r['update'][:7], r['ver']
        if not v: continue
        base[(m, v)] += 1
        for c in cats_of(r): cells[(m, v, c)] += 1

    HEAD = ['月份','应用版本','一级分类','问题评论数','该版本当月总评论数','密度(‰)','环比变化','备注']
    out, prev = [HEAD], {}
    for (m, v, c), n in sorted(cells.items()):
        b = base[(m, v)]
        if b < MIN_BASE: continue
        d = n / b * 1000
        k, delta, note = (v, c), '', ''
        if k in prev:
            diff = d - prev[k]
            delta = f"{diff:+.1f}‰"
            if diff >= 10: note = '⚠ 该版本内环比明显上升'
        prev[k] = d
        out.append([m, v, c, n, b, round(d, 1), delta, note])
    json.dump(out, open(K.data_path('sheet6_trends.json'), 'w'), ensure_ascii=False)
    print(f"月度趋势 {len(out)-1} 行")

    vbase, vcells = collections.Counter(), collections.Counter()
    for r in rows:
        if r['ver']:
            vbase[r['ver']] += 1
            for c in cats_of(r): vcells[(r['ver'], c)] += 1
    MAIN = [v for v, n in vbase.most_common(8) if n >= 50]
    MAIN.sort()
    if MAIN:
        print("\n各分类按版本的密度(‰) —— 突增即疑似版本引入的回归：")
        cats = sorted({c for _, c in vcells}, key=lambda c: -sum(vcells[(v, c)] for v in MAIN))
        print(f"{'分类':<20}" + ''.join(f"{v:>9}" for v in MAIN))
        for c in cats[:10]:
            print(f"{c:<20}" + ''.join(f"{vcells[(v,c)]/vbase[v]*1000:>9.0f}" for v in MAIN))

if __name__ == '__main__':
    main()
