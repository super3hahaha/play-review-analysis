# -*- coding: utf-8 -*-
"""否定词窗口 —— 只用于「故障词」（lag/crash/error 之类，否定后代表夸奖），
不适用于「功能词」（play/support/sync 之类，否定后才是投诉，比如 "no subtitle sync"）。
两者混在同一批正则规则里，所以用 FLIP_PATTERNS 白名单挑出「故障词」规则逐条打否定标记，
不在白名单里的规则完全不受影响，按原来的方式直接 search。

窗口本身还要防止跨到下一个独立分句（用户常不打逗号就换主语，比如
"it doesn't support 4k it lags too much" —— "doesn't" 修饰的是 support，
和后面独立起句的 "it lags" 无关），否则窗口开大了会把无关的否定词也算进来。
做法：找到窗口内最靠后的否定词，若否定词和故障词命中之间出现了新主语标记
（it/this/the app 等 + 空格），就认为已经换了分句，否定词作废。
"""
import re

NEGATORS_RE = re.compile(
    r"\b(not|no|never|n't|without|nor)\b"
    r"|\b(nunca|jamás|jamas|sin)\b"
    r"|\bне\b|\bни\b|\bбез\b"
    r"|不|没|無|无|沒|別|别"
    r"|ない|じゃない|ではない|なく"
    r"|안\s|못\s|없"
    r"|\b(tidak|nggak|gak|ga|kagak|belum|bukan)\b"
    r"|\b(değil|yok)\b"
    r"|لا\s|ليس\s|لم\s|ما\s|غير\s"
    r"|نه\s|بدون\s"
    r"|\b(nicht|kein|keine)\b"
    r"|\bnie\b"
    r"|\bkhông\b"
    r"|ไม่",
    re.I,
)

# 新分句起点标记：否定词和故障词之间出现这些，说明否定词管的是前一句，跟这个故障词无关
NEW_CLAUSE_RE = re.compile(r"\b(it|this|that|the app|i|you|he|she|they)\s", re.I)

WINDOW = 30

# 「故障词」白名单：本身是负面状态词，否定后就是夸奖（"not lag" / "no bug" / "не тормозит"）。
# 只挑纯故障词规则，混了「否定短语本身就是投诉」的规则（如 "no subtitle sync"、"doesn't work"、
# "не работает"、"打不开"）绝不放进来——那些规则的否定词是投诉的一部分，不是要排除的噪音。
FLIP_PATTERNS = {
    # taxonomy.py 视频播放画质与流畅度 L1 + 卡顿/掉帧/冻结 L2
    r"\blag(s|gy|ging)?\b", r"\blague\w*", r"stutter", r"choppy", r"frame ?drop", r"freez", r"buffering",
    r"slow ?mo", r"pixelat", r"卡顿", r"卡頓", r"頓", r"カクつ", r"тормоз", r"подвис",
    r"рывк", r"замедл", r"se traba", r"se pega", r"ralentiz", r"trava", r"sacadat",
    r"\bsek[aá]\b", r"macet", r"버벅", r"يعلق", r"يتقطع", r"takılı", r"kasma",
    r"zawiesza", r"si blocca", r"burik", r"yeti",
    # complaint.py STRONG_RE / NEG_RE 里纯故障名词/形容词（英/俄/西葡/阿/中日韩）
    r"\b(bug|bugg?y|glitch|crash(es|ed|ing)?|freeze[sd]?|frozen|stuck|error|broken|malfunction)\b",
    r"\b(lag(s|gy|ging)?\b|lague\w*|stutter(s|ing)?|choppy|frame ?drops?|slow ?mo(tion)?|pixelat|overheat|drain)",
    r"\b(перестал|вылета|виснет|зависа|тормоз|глючит|лаги|баг|ошибк|сбой|рассинхрон)",
    r"\b(se cuelga|se traba|se pega|se cierra|se apaga|trava|congela|falha|fallo|falla)\b",
    r"(مشكلة|مشاكل|خلل|عطل|يتوقف|يعلق|بطيء)",
    r"(卡顿|卡頓|闪退|閃退|崩溃|崩潰|死机|當機|花屏|黑屏|不同步|失灵|失靈|报错|報錯|故障|异常|異常)",
    r"\b(bug|bugg?y|issue|problem|error|broken|glitch|crash|freeze|frozen|stuck|fail|failure)\b",
    r"\b(lag|lagg?ing|stutter|choppy|slow|delay|out of sync|drain|overheat|pixelat)\b",
    r"\b(баг|ошибк|проблем|глюк|тормоз|виснет|вылет|лаг|сбой|косяк)",
}

def _negated(text, start):
    pre = text[max(0, start - WINDOW):start]
    for nm in reversed(list(NEGATORS_RE.finditer(pre))):
        between = pre[nm.end():]
        if not NEW_CLAUSE_RE.search(between):
            return True
    return False

def hit(regs, text):
    """任一 reg 命中即算命中；命中的 reg 若在 FLIP_PATTERNS 白名单里，
    还要求命中前没有一个「同分句内、没被换主语隔断」的否定词，否则视为
    「否定故障词=夸奖」不算命中。"""
    for r in regs:
        guarded = r.pattern in FLIP_PATTERNS
        for m in r.finditer(text):
            if guarded and _negated(text, m.start()):
                continue
            return True
    return False
