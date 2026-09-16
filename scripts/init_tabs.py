# -*- coding: utf-8 -*-
"""给表3(复现尝试记录)/表4(历史BUG)/表5(分类词典) 写入表头。首次建表后跑一次。"""
import os, sys, json
import gspread
from google.oauth2.credentials import Credentials
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kb_common as K

CRED = os.path.expanduser('~/.claude/credentials/google-workspace/authorized_user.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
TX = K.load_taxonomy()

T3 = [["尝试ID","问题ID","日期","执行人","设备型号","系统版本","App版本","测试素材",
       "尝试的步骤","结果","现象描述","★本次排除了什么","下一步建议"],
      ["TRY-001","（示例行，可删）","","","Pixel 8","Android 15","","1080p H.264 MP4 / 42min",
       "播放→拖动进度条 00:34→00:50→观察 10 秒","未复现","拖动后正常播放，无冻结",
       "已排除：H.264+中等码率+骁龙平台；已排除：单纯 seek 动作本身",
       "评论集中在 vivo(7.0×)与 realme(8.7×)，下次换 vivo 机型 + 高码率 HEVC 素材重试"]]
T4 = [["BUG ID","标题","模块","发现版本","修复版本","复现步骤","根本原因","关联问题ID","来源链接","导入日期"],
      ["（示例行，可删）","从缺陷系统导出后按此列映射","","","",
       "历史复现步骤原样贴过来——这是最值钱的一列","如已定位则填","","",""]]

def main():
    cfg = K.load_config()
    gc = gspread.authorize(Credentials.from_authorized_user_file(CRED, SCOPES))
    sh = gc.open_by_key(cfg['sheet_id'])
    sh.worksheet("3_复现尝试记录").update(values=T3, range_name='A1', value_input_option='RAW')
    sh.worksheet("4_历史BUG").update(values=T4, range_name='A1', value_input_option='RAW')
    t5 = [["一级分类","二级分类","多语言关键词(正则,用 | 分隔)","备注","最后更新"]]
    for l1, ps in TX.L1_KEYWORDS.items():
        t5.append([l1, "(一级识别词)", " | ".join(ps)[:45000],
                   "判断【属于哪个功能域】，不判断是否问题", ""])
    for l1, l2, ps in TX.L2_RULES:
        t5.append([l1, l2, " | ".join(ps)[:45000], "", ""])
    ws5 = sh.worksheet("5_分类词典")
    ws5.batch_clear(["A1:E500"])
    ws5.update(values=t5, range_name='A1', value_input_option='RAW')
    print(f"表3/表4 表头已写入；表5 分类词典 {len(t5)-1} 行")

if __name__ == '__main__':
    main()
