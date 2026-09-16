# -*- coding: utf-8 -*-
"""月度趋势（表6）：按月 × 分类统计问题密度，看整体趋势是否在恶化。
同一个月同一分类下可能横跨多个版本，评论数直接加总；「应用版本」列只列出该月出现过哪些版本，仅供追溯，不参与分组/环比计算。
用密度(‰)而非绝对数，否则评论总量大的月份永远看起来问题最多。
版本粒度的回归定位（哪个版本引入的）看下面的控制台打印（按版本汇总，不分月）。
"""
import json, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
MIN_BASE = 30

def cats_of(r):
    return set(r['l1']) if r['l1'] else ({r['primary']} if r['primary'] else set())

def main():
    rows = json.load(open(K.data_path('classified.json'), encoding='utf-8'))
    base, cells, vers = collections.Counter(), collections.Counter(), collections.defaultdict(set)
    for r in rows:
        m, v = r['update'][:7], r['ver']
        if not v: continue
        base[m] += 1
        for c in cats_of(r):
            cells[(m, c)] += 1
            vers[(m, c)].add(v)

    MIN_COUNT_RISE = 3  # 密度差再大，问题评论数绝对增量不到这个数就不算"明显上升"——避免小样本(1→2条)被误判

    HEAD = ['月份','出现的应用版本','一级分类','问题评论数','该月总评论数','密度(‰)','环比变化','备注']
    out, prev = [HEAD], {}
    for (m, c), n in sorted(cells.items()):
        b = base[m]
        if b < MIN_BASE: continue
        d = n / b * 1000
        vlist = ','.join(sorted(vers[(m, c)]))
        delta, note = '', ''
        if c in prev:
            prev_d, prev_n = prev[c]
            diff = d - prev_d
            delta = f"{diff:+.1f}‰"
            if diff >= 10 and (n - prev_n) >= MIN_COUNT_RISE: note = '⚠ 该分类环比明显上升'
        prev[c] = (d, n)
        out.append([m, vlist, c, n, b, round(d, 1), delta, note])
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
