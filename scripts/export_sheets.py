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
    hi  = [r for r in rows if r['star'] >= 4 and r['grade'] in ('A','B') and r['primary']]
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

if __name__ == '__main__':
    main()
