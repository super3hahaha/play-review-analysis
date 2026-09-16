# -*- coding: utf-8 -*-
"""项目配置与路径解析（所有脚本共用）

Skill 里的脚本是通用的；每个 app 的专属内容放在【项目目录】里：
    <project>/kb_config.json   应用名、包名、Sheets ID
    <project>/taxonomy.py      该 app 的分类词表（唯一需要按 app 定制的东西）
    <project>/raw/*.csv        Play Console 导出的评论
    <project>/data/*           中间产物
"""
import json, os, sys, importlib.util

def project_root():
    """项目根目录：环境变量 KB_PROJECT > 向上找 kb_config.json > 当前目录"""
    env = os.environ.get('KB_PROJECT')
    if env:
        return os.path.abspath(env)
    d = os.getcwd()
    while True:
        if os.path.exists(os.path.join(d, 'kb_config.json')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.getcwd()
        d = parent

ROOT = project_root()

def load_config():
    fp = os.path.join(ROOT, 'kb_config.json')
    if not os.path.exists(fp):
        sys.exit(f"找不到 {fp}\n先跑: python3 <skill>/scripts/init_project.py --app <应用名>")
    return json.load(open(fp, encoding='utf-8'))

def load_taxonomy():
    """加载项目专属分类词表。找不到就报错——这是每个 app 必须自己定的东西。"""
    fp = os.path.join(ROOT, 'taxonomy.py')
    if not os.path.exists(fp):
        sys.exit(f"找不到 {fp}\n每个 app 的分类词表都不一样，需要先建。"
                 f"可从 <skill>/assets/taxonomy_template.py 复制后修改。")
    spec = importlib.util.spec_from_file_location('app_taxonomy', fp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def data_path(*parts):
    p = os.path.join(ROOT, 'data', *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def save_config(cfg):
    json.dump(cfg, open(os.path.join(ROOT, 'kb_config.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

# 公共设备目录（跨 app 共用，不属于任何项目）
DEVICE_CATALOG = os.path.expanduser('~/.claude/shared/device-catalog')
if os.path.isdir(DEVICE_CATALOG):
    sys.path.insert(0, DEVICE_CATALOG)

# 公共实体测试机资产（跨 app 共用，同一批公司设备，不属于任何项目）
TEST_PHONE_CATALOG = os.path.expanduser('~/.claude/shared/test-phones')
if os.path.isdir(TEST_PHONE_CATALOG):
    sys.path.insert(0, TEST_PHONE_CATALOG)
