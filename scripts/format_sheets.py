# -*- coding: utf-8 -*-
"""给 Sheets 上色/冻结/设列宽/加筛选器。列位置按表头名动态定位，改了列顺序也不会错。
只需在首次建表后跑一次；之后数据刷新不影响格式。"""
import os, sys, json
import gspread
from google.oauth2.credentials import Credentials
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K

CRED = os.path.expanduser('~/.claude/credentials/google-workspace/authorized_user.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
STATES = ["线索收敛中-建议复现","待确认","证据不足-观察中","可复现-已提单","已修复待验证",
          "已关闭","无法复现-挂起","非缺陷-产品策略","笼统池-已有可用线索","笼统池-仅跟趋势"]
# 列宽规则：表头名关键词 → 像素
WIDTH = {'原文':390,'中文':390,'全部命中分类':430,'关键线索摘要':500,'系统提示':180,'人工复核':250,
         '问题标题':215,'二级分类':200,'主二级分类':195,'一级分类':135,'主一级分类':140,'状态':128,
         '机型名':170,'SoC':130,'涉及版本':170,'涉及厂商':155,'涉及芯片平台':155,'涉及机型TOP':195,
         '涉及语言地区':125,'关联评论ID':180,'关联问题ID':130,'线索标签':120,'尝试的步骤':330,
         '★本次排除了什么':360,'现playback步骤':300,'复现步骤':420,'备注':300}

def rng(sid, r0, r1, c0, c1):
    return {'sheetId': sid, 'startRowIndex': r0, 'endRowIndex': r1,
            'startColumnIndex': c0, 'endColumnIndex': c1}

def main():
    cfg = K.load_config()
    if not cfg.get('sheet_id'):
        sys.exit("kb_config.json 里没有 sheet_id，先跑 upload.py")
    gc = gspread.authorize(Credentials.from_authorized_user_file(CRED, SCOPES))
    sh = gc.open_by_key(cfg['sheet_id'])
    reqs = []
    for ws in sh.worksheets():
        head = ws.row_values(1)
        if not head: continue
        sid, n = ws.id, len(head)
        rows = max(ws.row_count, 2)
        reqs += [
          {'updateSheetProperties': {'properties': {'sheetId': sid,
              'gridProperties': {'frozenRowCount': 1}}, 'fields': 'gridProperties.frozenRowCount'}},
          {'repeatCell': {'range': rng(sid,0,1,0,n), 'cell': {'userEnteredFormat': {
              'backgroundColor': {'red':.12,'green':.22,'blue':.39},
              'textFormat': {'bold': True, 'fontSize': 10,
                             'foregroundColor': {'red':1,'green':1,'blue':1}},
              'horizontalAlignment':'CENTER','verticalAlignment':'MIDDLE','wrapStrategy':'WRAP'}},
              'fields':'userEnteredFormat'}},
          {'updateDimensionProperties': {'range': {'sheetId': sid,'dimension':'ROWS',
              'startIndex':0,'endIndex':1}, 'properties': {'pixelSize': 42}, 'fields':'pixelSize'}},
          {'repeatCell': {'range': rng(sid,1,rows,0,n), 'cell': {'userEnteredFormat': {
              'verticalAlignment':'TOP','wrapStrategy':'CLIP','textFormat':{'fontSize':10}}},
              'fields':'userEnteredFormat(verticalAlignment,wrapStrategy,textFormat.fontSize)'}},
          {'setBasicFilter': {'filter': {'range': rng(sid,0,rows,0,n)}}},
        ]
        for i, name in enumerate(head):
            w = WIDTH.get(name)
            if w:
                reqs.append({'updateDimensionProperties': {'range': {'sheetId': sid,
                    'dimension':'COLUMNS','startIndex':i,'endIndex':i+1},
                    'properties': {'pixelSize': w}, 'fields':'pixelSize'}})
            if name in ('原文','中文','全部命中分类','关键线索摘要','系统提示','人工复核',
                        '问题标题','复现步骤','★本次排除了什么','尝试的步骤','备注'):
                reqs.append({'repeatCell': {'range': rng(sid,1,rows,i,i+1),
                    'cell': {'userEnteredFormat': {'wrapStrategy':'WRAP'}},
                    'fields':'userEnteredFormat.wrapStrategy'}})
        # 置信度 A/B/C 上色
        if '置信度' in head:
            c = head.index('置信度')
            for val, rgb in [('A',(.85,.33,.31)), ('B',(.94,.68,.31)), ('C',(.93,.93,.93))]:
                reqs.append({'addConditionalFormatRule': {'rule': {
                    'ranges': [rng(sid,1,rows,c,c+1)],
                    'booleanRule': {'condition': {'type':'TEXT_EQ',
                        'values':[{'userEnteredValue': val}]},
                        'format': {'backgroundColor': {'red':rgb[0],'green':rgb[1],'blue':rgb[2]},
                            'textFormat': {'bold': val!='C',
                                'foregroundColor': {'red':1,'green':1,'blue':1} if val!='C'
                                                   else {'red':.53,'green':.53,'blue':.53}}}}},
                    'index': 0}})
        # 状态下拉 + 上色
        if '状态' in head and '问题ID' in head:
            c = head.index('状态')
            reqs.append({'setDataValidation': {'range': rng(sid,1,rows,c,c+1),
                'rule': {'condition': {'type':'ONE_OF_LIST',
                    'values':[{'userEnteredValue': s} for s in STATES]},
                    'showCustomUi': True, 'strict': False}}})
            for val, rgb, white in [('线索收敛中-建议复现',(.85,.33,.31),True),
                                    ('待确认',(.94,.68,.31),True),
                                    ('非缺陷-产品策略',(.87,.87,.87),False),
                                    ('无法复现-挂起',(.61,.35,.71),True)]:
                reqs.append({'addConditionalFormatRule': {'rule': {
                    'ranges': [rng(sid,1,rows,c,c+1)],
                    'booleanRule': {'condition': {'type':'TEXT_EQ',
                        'values':[{'userEnteredValue': val}]},
                        'format': {'backgroundColor': {'red':rgb[0],'green':rgb[1],'blue':rgb[2]},
                            **({'textFormat':{'foregroundColor':{'red':1,'green':1,'blue':1}}}
                               if white else {})}}}, 'index': 0}})
    sh.batch_update({'requests': reqs})
    print(f"已格式化 {len(sh.worksheets())} 个工作表（{len(reqs)} 个请求）")

if __name__ == '__main__':
    main()
