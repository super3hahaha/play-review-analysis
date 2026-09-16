# -*- coding: utf-8 -*-
"""聚合问题档案（表2）

两个关键设计：
1. 多标签——一条评论报告多个问题时同时计入多个档案，但分主/次证据，次证据权重减半
   （多重关键词命中含误报，不减半会污染优先级排序）
2. 稳定 ID——(一级::二级) → ISS-ID 永久映射存在 data/issue_registry.json
   ID 若随排序漂移，表2 里人工填的状态/负责人会集体错位
"""
import json, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
from device_lookup import lookup, soc_family

TX = K.load_taxonomy()
VAGUE = '（笼统未细分）'
POLICY = set(getattr(TX, 'POLICY_L2', []))   # 产品策略类，不进复现队列
REGISTRY = K.data_path('issue_registry.json')

def vendor(d):
    x = lookup(d)
    return (x.get('vendor') or x.get('brand') or '') if x else ''

def form(d):
    x = lookup(d)
    return x.get('form', '') if x else ''

def load_registry():
    if os.path.exists(REGISTRY):
        return json.load(open(REGISTRY, encoding='utf-8'))
    return {'_说明': '问题ID永久注册表。key=一级::二级，value=ISS-ID。'
                    'ID 一经分配不再改变，表2 的状态/负责人/历史BUG 都挂在它上面。',
            '_next': 1}

def assign_id(reg, l1, l2):
    key = f'{l1}::{l2}'
    if key not in reg:
        reg[key] = f"ISS-{reg['_next']:03d}"
        reg['_next'] += 1
    return reg[key]

def main():
    rows = json.load(open(K.data_path('classified.json'), encoding='utf-8'))
    byid = {r['id']: r for r in rows}
    reg = load_registry()

    B = {'vendor': collections.Counter(vendor(r['device']) for r in rows),
         'soc':    collections.Counter(soc_family(r['device']) for r in rows),
         'form':   collections.Counter(form(r['device']) for r in rows),
         'ver':    collections.Counter(r['ver'] for r in rows if r['ver'])}
    TOT = {k: sum(v.values()) for k, v in B.items()}

    g = collections.defaultdict(list)
    for r in rows:
        if not r['primary']:
            continue
        main_key = (r['primary'], r['primary_l2']) if r['primary_l2'] else (r['primary'], VAGUE)
        seen = {main_key}
        g[main_key].append((r, True))
        for tag in r['l2']:
            if '::' not in tag: continue
            l1, l2 = tag.split('::', 1)
            if (l1, l2) in seen: continue
            seen.add((l1, l2))
            g[(l1, l2)].append((r, False))

    cand = []
    for (l1, l2), pairs in g.items():
        prim = [r for r, p in pairs if p]
        sec  = [r for r, p in pairs if not p]
        gc, gcs = collections.Counter(r['grade'] for r in prim), collections.Counter(r['grade'] for r in sec)
        strength = (gc['A']*5 + gc['B']*2 + gc['C']) + (gcs['A']*5 + gcs['B']*2 + gcs['C']) // 2
        cand.append((strength, l1, l2, [r for r, _ in pairs], gc, prim, sec))
    cand.sort(reverse=True, key=lambda x: x[0])

    def conc(rs, dim, fn, minn=2, thr=2.0):
        c = collections.Counter((fn(r['device']) if dim != 'ver' else r['ver']) for r in rs)
        n = sum(v for k, v in c.items() if k)
        res = []
        for k, v in c.most_common(5):
            if not k or v < minn: continue
            exp = B[dim].get(k, 0) / TOT[dim] * n
            if exp > 0 and v / exp >= thr:
                res.append((k, v, v / exp))
        return res

    HEAD = ['问题ID','问题标题','一级分类','二级分类','状态','首次出现','最近出现','证据条数',
            '主证据','次证据','伴随度','A档','B档','C档','证据强度','涉及版本','涉及厂商',
            '涉及芯片平台','涉及机型TOP','涉及语言地区','关键线索摘要','系统提示',
            '关联历史BUG','关联评论ID','负责人','更新时间','备注']
    out, rev2iss = [HEAD], {}
    today = __import__('datetime').date.today().isoformat()
    for s, l1, l2, rs, gc, prim, sec in cand:
        n = len(rs)
        vs = collections.Counter(r['ver'] for r in rs if r['ver']).most_common(5)
        vd = collections.Counter(vendor(r['device']) for r in rs).most_common(4)
        sc = collections.Counter(soc_family(r['device']) for r in rs).most_common(4)
        md = collections.Counter((lookup(r['device']) or {}).get('model','') for r in rs).most_common(4)
        ls = collections.Counter(r['lang'] for r in rs).most_common(4)
        clues = []
        for k, v, x in conc(rs, 'vendor', vendor):       clues.append(f"⚑厂商 {k} {v}/{n} 集中{x:.1f}×")
        for k, v, x in conc(rs, 'soc', soc_family):      clues.append(f"⚑芯片 {k} {v}/{n} 集中{x:.1f}×")
        for k, v, x in conc(rs, 'form', form, thr=2.5):  clues.append(f"⚑形态 {k} {v}/{n} 集中{x:.1f}×")
        for k, v, x in conc(rs, 'ver', None, thr=1.8):   clues.append(f"⚑版本 {k} {v}/{n} 集中{x:.1f}×")
        for aid in [r['id'] for r in prim if r['grade'] == 'A'][:3]:
            clues.append(f"[{aid}] {byid[aid]['text'][:110]}")

        iss_id = assign_id(reg, l1, l2)
        for r in prim: rev2iss.setdefault(r['id'], []).append(iss_id + '★')
        for r in sec:  rev2iss.setdefault(r['id'], []).append(iss_id)

        if l2 == VAGUE:
            st = '笼统池-仅跟趋势' if (gc['A'] + gc['B']) == 0 else '笼统池-已有可用线索'
            title = f"{l1} · 笼统未细分"
        elif l2 in POLICY:             st, title = '非缺陷-产品策略', l2
        elif s >= 20 and gc['A'] >= 2: st, title = '线索收敛中-建议复现', l2
        elif s >= 10:                  st, title = '待确认', l2
        else:                          st, title = '证据不足-观察中', l2

        out.append([iss_id, title, l1, l2, st,
            min(r['update'] for r in rs), max(r['update'] for r in rs),
            n, len(prim), len(sec), f"{len(sec)/n*100:.0f}%" if n else '',
            gc['A'], gc['B'], gc['C'], s,
            ' / '.join(f"{v}({c})" for v, c in vs),
            ' / '.join(f"{v}({c})" for v, c in vd if v),
            ' / '.join(f"{v}({c})" for v, c in sc if v),
            ' / '.join(f"{v}({c})" for v, c in md if v),
            ' / '.join(f"{v}({c})" for v, c in ls),
            ' ｜ '.join(clues)[:950],
            '⚠ 几乎不单独出现，多为其他问题的伴随症状——优先怀疑与主症状同根因'
            if (n >= 5 and len(sec)/n >= 0.7) else '',
            '', ','.join(r['id'] for r in rs[:200]), '', today, ''])

    json.dump(reg, open(REGISTRY, 'w'), ensure_ascii=False, indent=1)
    json.dump(out, open(K.data_path('sheet2_issues.json'), 'w'), ensure_ascii=False)
    json.dump({k: ','.join(v) for k, v in rev2iss.items()},
              open(K.data_path('review_to_issue.json'), 'w'), ensure_ascii=False)
    multi = sum(1 for v in rev2iss.values() if len(v) > 1)
    print(f"问题档案 {len(out)-1} 条 | 回填 {len(rev2iss)} 条评论→ISS（{multi} 条关联多个档案）")
    print(f"ID 注册表 {len([k for k in reg if not k.startswith('_')])} 条（ID 稳定）")
    print(" ", dict(collections.Counter(r[4] for r in out[1:])))

if __name__ == '__main__':
    main()
