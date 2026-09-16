# -*- coding: utf-8 -*-
"""完整流水线。

顺序是有依赖的，不是随便排的：
  preflight  先拦住已知的坑（正则静默失效、词表结构缺失、CSV 编码错）
  classify   分类 + 评分
  build_issues  聚合问题档案，★产出 review_to_issue.json★
  export_sheets 生成评论库，★消费上一步的 ID 映射回填「关联问题ID」★
  build_trends  算趋势
  upload     上传（会先读回人工填写的内容再合并）

用法：
  python3 run_all.py                  完整跑
  python3 run_all.py --no-upload      只算不传
  python3 run_all.py --skip-preflight 跳过检查（不建议）
"""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = []
if '--skip-preflight' not in sys.argv:
    STEPS.append(('飞行前检查', 'preflight.py', True))    # True = 失败即中止
STEPS += [('分类', 'classify.py', True),
          ('问题档案', 'build_issues.py', True),
          ('评论库', 'export_sheets.py', True),
          ('月度趋势', 'build_trends.py', True)]
if '--no-upload' not in sys.argv:
    STEPS.append(('上传', 'upload.py', True))

for name, script, fatal in STEPS:
    print(f"\n{'─'*62}\n▶ {name}  ({script})\n{'─'*62}")
    r = subprocess.run([sys.executable, os.path.join(HERE, script)])
    if r.returncode != 0 and fatal:
        if script == 'preflight.py':
            print(f"\n✗ 飞行前检查没过。这些检查对应的都是实际踩过的坑，"
                  f"建议修完再跑。\n  确实要继续：python3 run_all.py --skip-preflight")
        else:
            print(f"\n✗ {name} 失败，流水线中止")
        sys.exit(1)
print(f"\n{'─'*62}\n✓ 完成")
