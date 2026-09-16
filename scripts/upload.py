# -*- coding: utf-8 -*-
"""上传到 Google Sheets（表1/表2/表6）。首次运行会自动建表。

两个不能省的机制：
1. 翻译列必须 USER_ENTERED，否则 GOOGLETRANSLATE 变成纯文本
2. ★人工填写的列（状态/负责人/历史BUG/备注）在覆盖前先读回合并——那是人的劳动
"""
import os, json, sys
import gspread
from google.oauth2.credentials import Credentials
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K

CRED = os.path.expanduser('~/.claude/credentials/google-workspace/authorized_user.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
TABS = ['1_评论库','2_问题档案','3_复现尝试记录','4_历史BUG','5_分类词典','6_月度趋势']
HUMAN_STATES = {'可复现-已提单','已修复待验证','已关闭','无法复现-挂起'}
HUMAN_COLS = ['关联历史BUG','负责人','备注']

def a1_col(idx):
    """0-based 列号 → A1 字母。chr(ord('A')+idx) 超过 Z 列会得到 '[' 等垃圾字符"""
    s, idx = '', idx + 1
    while idx:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s

def ensure_sheet(gc, cfg):
    """没有 sheet_id 就新建一个，并写回 kb_config.json"""
    if cfg.get('sheet_id'):
        return gc.open_by_key(cfg['sheet_id'])
    title = cfg.get('sheet_title') or f"{cfg['app_name']} 评论知识库"
    sh = gc.create(title)
    for i, t in enumerate(TABS):
        if i == 0: sh.sheet1.update_title(t)
        else:      sh.add_worksheet(title=t, rows=1000, cols=30)
    cfg['sheet_id'] = sh.id
    K.save_config(cfg)
    print(f"已新建表格: {title}\n  https://docs.google.com/spreadsheets/d/{sh.id}/edit")
    return sh

def read_human_edits(ws, id_col='问题ID'):
    try: cur = ws.get_all_values()
    except Exception: return {}
    if not cur or len(cur) < 2 or id_col not in cur[0]: return {}
    ci = {n: i for i, n in enumerate(cur[0])}
    saved = {}
    for row in cur[1:]:
        if not row or not row[ci[id_col]]: continue
        keep = {}
        st = row[ci['状态']] if '状态' in ci and len(row) > ci['状态'] else ''
        if st in HUMAN_STATES: keep['状态'] = st
        for c in HUMAN_COLS:
            if c in ci and len(row) > ci[c] and str(row[ci[c]]).strip():
                keep[c] = row[ci[c]]
        if keep: saved[row[ci[id_col]]] = keep
    return saved

def merge_human(data, saved, id_col='问题ID'):
    ci = {n: i for i, n in enumerate(data[0])}
    hit = 0
    for row in data[1:]:
        if row[ci[id_col]] in saved:
            for col, val in saved[row[ci[id_col]]].items():
                if col in ci: row[ci[col]] = val
            hit += 1
    return hit

def main():
    cfg = K.load_config()
    gc = gspread.authorize(Credentials.from_authorized_user_file(CRED, SCOPES))
    sh = ensure_sheet(gc, cfg)

    # 表2 先读回人工内容再覆盖
    d2 = json.load(open(K.data_path('sheet2_issues.json'), encoding='utf-8'))
    ws2 = sh.worksheet("2_问题档案")
    hit = merge_human(d2, read_human_edits(ws2))
    ws2.batch_clear(["A1:AB500"])
    ws2.update(values=d2, range_name='A1', value_input_option='RAW')
    print(f"2_问题档案: {len(d2)-1} 条 | 保留人工填写 {hit} 条")

    # 表1
    d = json.load(open(K.data_path('sheet1_reviews.json'), encoding='utf-8'))
    ws = sh.worksheet("1_评论库")
    ws.batch_clear(["A1:Z5000"])
    ws.update(values=d, range_name='A1', value_input_option='RAW')
    print(f"1_评论库: {len(d)-1} 行")

    # 翻译列：A 档人工翻译优先，其余公式
    ci = {n: i for i, n in enumerate(d[0])}
    src, dst = a1_col(ci['原文']), a1_col(ci['中文'])
    fp = K.data_path('translations_A.json')
    T = json.load(open(fp, encoding='utf-8')) if os.path.exists(fp) else {}
    col, man = [["中文"]], 0
    for i, row in enumerate(d[1:], start=2):
        rid, g = row[ci['评论ID']], row[ci['置信度']]
        if g == 'A' and rid in T: col.append([T[rid]]); man += 1
        else: col.append([f'=IFERROR(GOOGLETRANSLATE({src}{i},"auto","zh-CN"),"")'])
    ws.update(values=col, range_name=f'{dst}1', value_input_option='USER_ENTERED')
    print(f"  翻译列: 人工 {man} / 公式 {len(col)-1-man}（异步计算，约 1 分钟填满）")

    # 表6
    fp6 = K.data_path('sheet6_trends.json')
    if os.path.exists(fp6):
        d6 = json.load(open(fp6, encoding='utf-8'))
        ws6 = sh.worksheet("6_月度趋势")
        ws6.batch_clear(["A1:H500"])
        ws6.update(values=d6, range_name='A1', value_input_option='RAW')
        print(f"6_月度趋势: {len(d6)-1} 行")

    print(f"\nhttps://docs.google.com/spreadsheets/d/{cfg['sheet_id']}/edit")

if __name__ == '__main__':
    main()
