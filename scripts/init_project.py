# -*- coding: utf-8 -*-
"""初始化一个新 app 的知识库项目。

    python3 <skill>/scripts/init_project.py --app XRecorder --package com.xxx.recorder

建出来的目录结构：
    kb_config.json      应用名/包名/Sheets ID（ID 首次 upload 时自动填）
    taxonomy.py         ★该 app 的分类词表——唯一需要按 app 定制的东西
    raw/                放 Play Console 导出的评论 CSV
    data/               中间产物，不用管
"""
import argparse, json, os, shutil, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', required=True, help='应用名，如 XRecorder')
    ap.add_argument('--package', default='', help='包名，如 com.example.app')
    ap.add_argument('--dir', default='.', help='项目目录，默认当前目录')
    a = ap.parse_args()

    root = os.path.abspath(a.dir)
    os.makedirs(os.path.join(root, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(root, 'data'), exist_ok=True)

    cfg_fp = os.path.join(root, 'kb_config.json')
    if os.path.exists(cfg_fp):
        print(f"已存在 {cfg_fp}，跳过")
    else:
        json.dump({'app_name': a.app, 'package_name': a.package,
                   'sheet_id': '', 'sheet_title': f'{a.app} 评论知识库'},
                  open(cfg_fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"✓ {cfg_fp}")

    tx_fp = os.path.join(root, 'taxonomy.py')
    if os.path.exists(tx_fp):
        print(f"已存在 {tx_fp}，跳过")
    else:
        shutil.copy(os.path.join(HERE, 'assets', 'taxonomy_template.py'), tx_fp)
        print(f"✓ {tx_fp}（模板，需要按该 app 改分类）")

    ov_fp = os.path.join(root, 'data', 'manual_override.json')
    if not os.path.exists(ov_fp):
        json.dump({'_说明': '人工复核覆盖表。脚本判错的写这里，下次跑分类自动生效，不会重犯。',
                   '_字段': 'primary+primary_l2=强制主分类 / extra=[追加标签] / drop=[删误报标签] '
                            '/ noise=praise|rant|no_signal|tooshort / grade=A|B|C|D / note=原因'},
                  open(ov_fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"✓ {ov_fp}")

    print(f"\n下一步：")
    print(f"  1. 把 Play Console 导出的评论 CSV 放进 {root}/raw/")
    print(f"  2. 按该 app 改 {tx_fp} 的分类词表（没有现成体系的话，让 Claude 读数据归纳一版）")
    print(f"  3. cd {root} && python3 {HERE}/scripts/run_all.py")

if __name__ == '__main__':
    main()
