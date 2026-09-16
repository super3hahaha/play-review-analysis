# -*- coding: utf-8 -*-
"""信息密度评分 —— 衡量单条评论对「复现」的贡献度
注意: 信息密度 != 问题真实性。低密度评论是计数器, 高密度评论是探针。
"""
import re

# ============ 线索信号词表（多语言）============
SIGNALS = {
# 对照实验：用户自己做了变量控制，复现价值最高
"control": (30, [
  # 与其他 App 对照
  r"mx ?player", r"\bvlc\b", r"kmplayer", r"nova ?player", r"next ?player", r"arc ?player",
  r"other (video )?players?", r"another (app|player)", r"otro reproductor", r"otras? apps?",
  r"outro (app|player)", r"другой (плеер|проигрыват)", r"других плеер", r"другие плееры",
  r"別の(アプリ|プレイヤー)", r"他の(アプリ|プレーヤー|プレイヤー|メディアプレーヤー)",
  r"其他播放器", r"別的播放器", r"다른 (앱|플레이어)", r"aplikasi lain", r"player lain",
  r"başka (uygulama|oynatıcı)", r"مشغل (آخر|اخر|ثاني)", r"برنامه.{0,10}دیگ",
  r"autre (application|lecteur)", r"andere app",
  # 与系统/自带应用对照
  r"(gallery|galeria|galería|galerie|ギャラリー|갤러리|المعرض|галере)",
  r"file ?manager", r"проводник", r"files? app", r"ファイルマネージャ", r"文件管理器",
  r"google (photos|files)", r"стандартный плеер", r"自带播放器", r"系统播放器",
  r"android files", r"antroid files",
  # 版本对照（以前 vs 现在）
  r"(before|prior to|until) (the )?(update|last version|recently)",
  r"used to (work|be|have)", r"it (was|worked) (fine|good|great|ok)",
  r"antes (funcionaba|era|sí|no pasaba)", r"anteriormente", r"antigamente",
  r"раньше (было|работал|норм)", r"до обновлени", r"было нормально", r"всё было хорошо",
  r"以前(は|不|沒|没|都)", r"前は", r"前まで", r"更新前", r"更新後", r"改版前",
  r"dulu (tidak|gak|ga|nggak|masih|bagus)", r"sebelumnya", r"eskiden", r"önceden",
  r"قبل التحديث", r"كان (رائع|تمام|جيد|أفضل)", r"قبلا", r"اول (بود|خوب)",
  r"avant (c|ç|il)", r"früher", r"wcześniej", r"предыдущ.{0,10}(версия|телефон)",
  r"이전(에|버전)", r"예전",
  # 其他文件/内容对照
  r"other (videos?|files?|movies?) (work|play|are fine)",
  r"otros? (videos?|archivos?) (sí|funcionan)", r"другие (видео|файлы) (работают|играют)",
  r"same (video|file).{0,30}(works|plays)", r"同じ(動画|ファイル)",
  # 其他设备对照
  r"(on|en|в) my (phone|tablet|celular|телефон).{0,40}(but|pero|но|works)",
  r"(tablet|планшет|タブレット).{0,40}(phone|телефон|スマホ)",
  r"new (phone|device).{0,40}(old|previous)", r"на (новом|старом) телефон",
  r"changed? (my )?(phone|device)", r"폰을 바꿔",
  # "另一台/别人的也一样" —— 强跨设备对照
  r"(も同様|も同じ|でも同じ|でも同様|too|as well|also)\s*(です|다|$)",
  r"(другом|второй|жены|дочери|сына).{0,25}(телефон|устройств).{0,25}(тоже|также)",
  r"\bтоже (самое|так|глючит|не работает)\b", r"\b(на|у) (другом|другого)\b",
  r"(otro|segundo|de mi (esposa|hijo|hija)).{0,25}(celular|teléfono|móvil).{0,25}(igual|también|mismo)",
  r"(também|igualmente) (no|em|acontece)", r"(same|identical) (on|with) (my )?(other|second|wife|daughter)",
  r"(娘|息子|妻|家族|友達|別)の(携帯|スマホ|端末|機種)", r"(另一|别的|其他)(台|部|个)?(手机|设备|平板)",
  r"(다른|아내|딸|아들).{0,10}(폰|기기|휴대폰)", r"(هاتف|جوال).{0,15}(آخر|ثاني|زوجتي|ابني)",
  r"(گوشی).{0,15}(دیگ|همسر)",
  # "只有 X 才/不" —— 隐含对照
  r"\bonly (with|when|on|this|in)\b", r"только (с|при|в|это|у)", r"solo (con|cuando|en|pasa)",
  r"\bonly\b.{0,70}\b(work|fine|ok|normal|good|problem|issue|lag|crash|happen)",
  r"\b(is|are|works?|plays?|played|running)\s+(just\s+)?(fine|ok|okay|normal|perfectly|smooth|good|no problem)",
  r"\bno (problem|issue)s?\b", r"\bwithout (any )?(problem|issue)", r"\bworks? (fine|well|great|perfectly)",
  r"(нет|без) (проблем|нареканий)", r"(работа|игра)(ет|ют) (нормально|отлично|хорошо|без)",
  r"(funciona|van|anda)n? (bien|perfecto|normal|sin problema)", r"(funciona|toca) (bem|normal|perfeitamente)",
  r"(問題|もんだい)(は)?(な|無)", r"(正常|沒問題|没问题|都正常|沒有問題)",
  r"(정상|잘 (되|돼|나와))", r"(normal|lancar|baik)( saja| aja)?\b",
  r"(sorunsuz|normal çalış)", r"(بشكل طبيعي|بدون مشاكل|تمام)", r"(بدون مشکل|درست کار)",
  r"apenas (com|quando)", r"únicamente", r"だけ(が|は|で)", r"只有", r"只在", r"하나만",
  r"hanya (di|saat|pada)", r"sadece", r"فقط (في|مع|عند)", r"فقط این",
]),

# 规避手段：用户说了怎么绕过 —— 直指代码分支
"workaround": (25, [
  r"(switch|change|changing|switching).{0,25}(hw|sw|hardware|software|decoder)",
  r"(hw|sw).{0,15}(to|→|->).{0,10}(sw|hw)", r"硬解.{0,8}软解", r"软解", r"硬件解码",
  r"(restart|reboot|relaunch).{0,30}(app|phone|fix|help|solve)",
  r"(reinstall|re-?install|uninstall and install).{0,40}(fix|work|help|solve|same)",
  r"clear (cache|data)", r"borrar (cache|datos)", r"очист.{0,15}(кэш|кеш|данн)",
  r"переустанов", r"перезагруз.{0,20}(помога|реша)", r"перезапус",
  r"reinstalar", r"reinstalei", r"desinstal.{0,25}(instal|volv)",
  r"再インストール", r"入れ直", r"アンインストールして",
  r"重装", r"重新安装", r"重新啟動", r"재설치", r"다시 설치",
  r"instal ulang", r"pasang ulang", r"أعدت (تثبيت|تنزيل)", r"حذفته ونزلته",
  r"pomůže restart", r"pomaga", r"solución.{0,20}(es|:)", r"workaround",
  r"i have to (play|open|go|switch)", r"приходится", r"tengo que", r"仕方なく",
  r"(play|open) (next|another) video then come back", r"tocar.{0,20}otro.{0,20}volver",
]),

# 精确数值：可直接写成断言
"metric": (20, [
  r"\b\d{1,3}\s?%", r"\b\d+\s?(seconds?|secs?|sec\b)", r"\b\d+\s?(minutes?|mins?\b)",
  r"\b\d+\s?(секунд|минут)", r"\b\d+\s?(segundos?|minutos?)", r"\b\d+\s?(秒|分)",
  r"\b\d+\s?(초|분)", r"\b\d+\s?(detik|menit)", r"\b\d+\s?(saniye|dakika)",
  r"\b\d+\s?(ثانية|ثواني|دقيقة|دقائق)", r"\b\d+\s?(ثانیه|دقیقه)",
  r"\b\d+\s?(mb|gb|kb)\b", r"\b\d+\s?(mbps|mb/s)", r"\b\d+\s?(fps|hz)",
  r"\b\d+\s?bit\b", r"\b\d+\s?kbps",
  r"\b\d+(\.\d+){1,3}\b",                      # 版本号 2.6.1
  r"\b(4k|1080p?|720p?|480p?|2160p?|360p?|8k)\b", r"\b\d+x\b",       # 分辨率/倍速
  r"less than \d+", r"меньше \d+", r"menos de \d+", r"more than \d+", r"больше \d+",
  r"\b\d+\s?(videos?|files?|songs?|tracks?|песен|видео|канц|items?)\b",
  r"\b(first|second|third|1st|2nd|3rd)\s+(frame|second|video|time)",
  r"(?<![\d.])(?!20[0-3]\d)(?!1\b)(?!2\b)(?!3\b)(?!4\b)(?!5\b)\d{2,4}(?![\d.])",
  r"第[一二三1-9]", r"最初の\d*", r"\b\d+\s?(hours?|часа?|時間)",
]),

# 触发条件：复现步骤主干
"trigger": (15, [
  r"\bwhen(ever)?\b", r"\bwhile\b", r"\bafter\b", r"\bduring\b", r"\bif i\b", r"\bevery time i\b",
  r"\bкогда\b", r"\bесли\b", r"\bпри\b", r"\bпосле\b", r"во время",
  r"\bcuando\b", r"\bsi (pongo|reproduzco|abro|le doy)\b", r"\bal (reproducir|abrir|poner|cambiar|darle)\b",
  r"después de", r"mientras",
  r"\bquando\b", r"\bao (reproduzir|abrir|tocar)\b", r"depois (de|que)",
  r"\blorsqu", r"\bquand\b", r"\baprès\b", r"\bwenn\b", r"\bnachdem\b", r"\bbeim\b",
  r"とき", r"ときに", r"すると", r"したら", r"の時", r"場合",
  r"(时|時)(候)?[，,、]", r"每当", r"一.{1,6}就", r"播放.{0,6}时", r"点击.{0,6}后",
  r"할 때", r"하면", r"한 후", r"후에",
  r"\bketika\b", r"\bsaat\b", r"\bkalau\b", r"\bsetelah\b", r"\bpas\b",
  r"\bعند\b", r"\bعندما\b", r"\bبعد\b", r"\bاذا\b", r"\bإذا\b", r"أثناء",
  r"وقتی", r"هنگام", r"بعد از", r"زمانی که",
  r"\b(ne zaman|iken|sonra|-ınca)\b", r"\bgdy\b", r"\bpo (aktualizacji|tym)\b",
  r"\bkhi\b", r"\bsau khi\b", r"\bเมื่อ\b", r"\bหลังจาก\b",
  # 具体操作动词
  r"(fast ?forward|skip|seek|pause|resume|switch|scrub|drag).{0,25}(then|and|,|the video|it)",
  r"(перемот|пауз|переключ|сверн).{0,30}(видео|звук|плеер)",
]),

# 具体技术标的：缩小测试矩阵。通用部分在这里，
# app 专属的技术名词（文件格式/功能名/协议）由项目 taxonomy.DOMAIN_TERMS 提供
"target": (10, [
  r"(android ?1[0-9]|one ?ui|miui|hyperos|emui|coloros|funtouch|oxygenos)",
  r"(snapdragon|exynos|dimensity|mediatek|kirin|tensor|unisoc)",
  r"(bluetooth|wi-?fi|hotspot|usb|otg|sd ?card|nas|smb|dlna|vpn|4g|5g)",
  r"(dark mode|widget|notification|shortcut|split ?screen)",
  r"(暗色模式|小组件|通知栏|分屏|快捷方式)",
]),

# 频率：决定复现要跑几轮
"frequency": (10, [
  r"\balways\b", r"\bevery ?time\b", r"\beach time\b", r"\bconstantly\b", r"\ball the time\b",
  r"\bsometimes\b", r"\boccasionally\b", r"\brandomly\b", r"\bnow and then\b", r"\boften\b",
  r"\bпостоянно\b", r"\bкажд(ый|ые|ый раз)\b", r"\bвсегда\b", r"\bиногда\b", r"\bвремя от времени\b",
  r"\bчасто\b", r"\bпериодически\b",
  r"\bsiempre\b", r"\bcada vez\b", r"\ba veces\b", r"\bsuele\b", r"\bfrecuente",
  r"\bsempre\b", r"\bàs vezes\b", r"\btoujours\b", r"\bparfois\b", r"\bsouvent\b",
  r"\bimmer\b", r"\bmanchmal\b", r"\bjedes ?mal\b",
  r"毎回", r"いつも", r"たまに", r"時々", r"ときどき", r"每次", r"总是", r"偶尔", r"有时",
  r"항상", r"매번", r"가끔", r"자주",
  r"\bselalu\b", r"\bsetiap\b", r"\bkadang\b", r"\bsering\b",
  r"\bher (zaman|seferinde)\b", r"\bbazen\b", r"\bsürekli\b",
  r"\bدائما\b", r"\bكل مرة\b", r"\bأحيان", r"\bهمیشه\b", r"\bگاهی\b", r"\bهر بار\b",
]),

# 时间/版本锚点：圈定回归范围
"temporal": (10, [
  r"\bsince (the )?(last |recent )?(update|version|week|month)", r"\bafter (the )?(last |recent )?update",
  r"\brecently\b", r"\blately\b", r"\bfor the (past|last) (few )?(days?|weeks?|months?)",
  r"\bnew update\b", r"\blatest (update|version)\b", r"\bnow\b.{0,20}\bbut\b",
  r"после (обновлени|последн)", r"в последнее время", r"последн.{0,15}(обновлени|верси|недел|месяц)",
  r"недавно", r"с недавних пор", r"уже (год|месяц|неделю)",
  r"desde (la )?(última )?actualización", r"últimamente", r"hace poco", r"recientemente",
  r"depois d[ao] (última )?atualização", r"ultimamente", r"recentemente",
  r"depuis (la )?(dernière )?mise à jour", r"récemment", r"seit dem? (letzten )?update",
  r"最近", r"最新.{0,6}(更新|版本)", r"更新(後|后)", r"アップデート(後|して)", r"このごろ",
  r"최근", r"업데이트 (후|이후)",
  r"(setelah|sejak) (update|pembaruan)", r"akhir-akhir ini", r"belakangan",
  r"son (güncelleme|zamanlarda)", r"güncellemeden sonra",
  r"بعد (التحديث|آخر تحديث)", r"مؤخرا", r"الفتره الاخيره", r"من فتره",
  r"بعد (بروزرسانی|آپدیت)", r"اخیرا", r"po (aktualizacji|ostatniej)",
  r"\b20(2[4-9])\b",   # 提到具体年份
]),
}

COMPILED = {k: (w, [re.compile(p, re.I) for p in ps]) for k, (w, ps) in SIGNALS.items()}

def _domain_regexes(terms):
    """app 专属技术词（由项目 taxonomy.DOMAIN_TERMS 提供），缓存编译结果"""
    if not terms:
        return []
    key = id(terms)
    if key not in _DOMAIN_CACHE:
        _DOMAIN_CACHE[key] = [re.compile(p, re.I) for p in terms]
    return _DOMAIN_CACHE[key]

_DOMAIN_CACHE = {}

SIGNAL_CN = {
 "control": "对照", "workaround": "规避", "metric": "数值",
 "trigger": "触发", "target": "标的", "frequency": "频率", "temporal": "锚点",
}

def score(text, has_l2=False, domain_terms=None):
    """返回 (分值0-100, 命中的信号列表)
    domain_terms: app 专属技术名词列表，命中也算 target 信号"""
    hits, s = [], 0
    for key, (w, regs) in COMPILED.items():
        if any(r.search(text) for r in regs):
            hits.append(key)
            s += w
    if 'target' not in hits and any(r.search(text) for r in _domain_regexes(domain_terms)):
        hits.append('target')
        s += COMPILED['target'][0]
    H = set(hits)
    # 组合加成：这些组合能直接构造出测试用例
    if "metric" in H and "trigger" in H:
        s += 10          # 精确的触发条件 → 可直接写断言
    if "control" in H and (H & {"trigger", "metric", "target"}):
        s += 10          # 对照 + 条件 → 变量已被控制
    if len(H) >= 4:
        s += 10          # 多维线索交叉
    if has_l2:
        s += 5
    n = len(text)
    if n >= 120:
        s += 5
    elif n < 25:
        s -= 10
    return max(0, min(100, s)), hits

def grade(s, noise=None):
    """D 只给噪音。有真实症状但零线索的评论是 C(计数器)，不是无效。"""
    if noise:
        return "D"
    if s >= 50: return "A"
    if s >= 25: return "B"
    return "C"

GRADE_DESC = {
 "A": "高置信-可直接尝试复现",
 "B": "中置信-需聚合同类证据",
 "C": "低置信-仅作计数/趋势",
 "D": "无效-噪音或零信息",
}
