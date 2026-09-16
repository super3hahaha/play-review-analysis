# -*- coding: utf-8 -*-
"""生成表1 评论库上传数据。必须在 build_issues.py 之后跑——它要用后者产出的 ID 映射回填。"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K
from device_lookup import lookup, soc_family

def main():
    rows = json.load(open(K.data_path('classified.json'), encoding='utf-8'))
    fp = K.data_path('review_to_issue.json')
    rev2iss = json.load(open(fp, encoding='utf-8')) if os.path.exists(fp) else {}
    if not rev2iss:
        print("⚠ 没找到 review_to_issue.json —— 请先跑 build_issues.py，否则「关联问题ID」列会是空的")

    low = [r for r in rows if r['star'] <= 3 and not r['noise']]
    # grade='D' 专指 noise（见 confidence.py:grade()），C 是"低置信但非噪音"的合法计数器证据，
    # 不能跟着 D 一起被排除——否则 build_issues.py 计入表2 的 C 档高星证据会永远进不了表1。
    hi  = [r for r in rows if r['star'] >= 4 and r['grade'] != 'D' and r['primary']]
    sel = sorted(low + hi, key=lambda r: (r['update'], r['id']))

    HEAD = ['评论ID','最后更新','星级','语言','设备代号','厂商','机型名','芯片平台','SoC','形态',
            '应用版本','主一级分类','主二级分类','命中分类数','全部命中分类','置信度','密度分',
            '线索标签','关联问题ID','原文','中文','评论链接','人工复核']
    out, hit = [HEAD], 0
    for r in sel:
        d = lookup(r['device'])
        if d: hit += 1
        out.append([r['id'], r['update'], r['star'], r['lang'], r['device'],
            (d.get('vendor') or d.get('brand') or '') if d else '',
            d['model'] if d else '', soc_family(r['device']),
            d.get('soc','') if d else '', d.get('form','') if d else '',
            r['ver'], r['primary'] or '', r['primary_l2'] or '',
            len(r['l2']), ' ｜ '.join(r['l2']), r['grade'], r['density'],
            '/'.join(r['signals']), rev2iss.get(r['id']) or '（未分类·待补词表）',
            r['text'], '', r['link'], r.get('manual','')])
    json.dump(out, open(K.data_path('sheet1_reviews.json'), 'w'), ensure_ascii=False)
    A = [r for r in sel if r['grade'] == 'A']
    mt = sum(1 for r in sel if len(r['l2']) > 1)
    linked = sum(1 for r in sel if rev2iss.get(r['id']))
    print(f"表1 {len(out)-1} 行 | 设备代号命中 {hit/len(sel)*100:.1f}% | A档 {len(A)} 条")
    print(f"  多标签 {mt} 条 ({mt/len(sel)*100:.1f}%) | 已关联档案 {linked}/{len(sel)} = {linked/len(sel)*100:.1f}%")
    if linked < len(sel):
        print(f"  ⚠ 「未分类·待补词表」{len(sel)-linked} 条 —— 筛这一列逐条判定，"
              f"结果写进 data/manual_override.json，可泛化的补进 taxonomy.py")

    check_sheet2_ids_exist_in_sheet1(sel)

def check_sheet2_ids_exist_in_sheet1(sel):
    """断言：表2「关联评论ID」提到的每个ID都必须能在表1里查到。
    教训：曾经 hi 的筛选条件比 build_issues.py 计入证据的条件更严格（漏了 grade=C），
    导致表2 计入证据、但表1 永远找不到对应行，人读证据时会撞见"链接点不进去的ID"却毫无察觉。
    这条检查把这类筛选口径不一致，从"人工核对才会发现"变成"跑一次就报错"。"""
    fp = K.data_path('sheet2_issues.json')
    if not os.path.exists(fp):
        return
    rows2 = json.load(open(fp, encoding='utf-8'))
    head2 = rows2[0]
    i = head2.index('关联评论ID')
    sheet1_ids = {r['id'] for r in sel}
    missing = collections.Counter()
    for row in rows2[1:]:
        for rid in (row[i] or '').split(','):
            rid = rid.strip()
            if rid and rid not in sheet1_ids:
                missing[rid] += 1
    if missing:
        print(f"  ✗ 一致性检查失败：表2 引用了 {len(missing)} 个不在表1 里的评论ID"
              f"（如 {', '.join(list(missing)[:5])}）——多半是 hi/低 星筛选条件跟 build_issues.py"
              f" 计入证据的条件对不上，去 classified.json 按 ID 查这几条的 star/grade/noise/primary")
    else:
        print(f"  ✓ 一致性检查通过：表2 引用的评论ID 全部能在表1 里查到")

if __name__ == '__main__':
    main()
