# -*- coding: utf-8 -*-
"""负面语义门控 —— 判断一条评论是否在「抱怨」
L1 关键词只能判断【说的是哪个功能域】，判断不了【是不是问题】。
5★ 好评里 'quality'/'download'/'music' 大量出现，必须靠这道门拦住。
"""
import re
import negation as NEG

COMPLAINT = [
 # --- 英语 ---
 r"\b(can'?t|cannot|won'?t|doesn'?t|don'?t|didn'?t|isn'?t|aren'?t|wasn'?t|couldn'?t|unable)\b",
 r"\b(no longer|not work|not play|not show|not support|not load|not open|never work)",
 r"\b(bug|bugg?y|issue|problem|error|broken|glitch|crash|freeze|frozen|stuck|fail|failure)\b",
 r"\b(fix|repair|solve|resolve)\b", r"\b(worst|terrible|awful|horrible|useless|garbage|rubbish|trash)\b",
 r"\b(annoying|frustrat|disappoint|ruin|waste|pathetic|scam|fake|lie|liar)\b",
 r"\b(too many|too much|so many ads|stop asking|forced?|force[sd]? you)\b",
 r"\b(lag|lagg?ing|stutter|choppy|slow|delay|out of sync|drain|overheat|pixelat)\b",
 r"\b(missing|disappear|gone|lost|removed|deleted)\b", r"\b(why (is|does|do|can'?t|are))\b",
 r"\bplease (fix|add|bring back|improve|optimi)", r"\b(used to|before).{0,40}(but|now)\b",
 r"\bworse\b", r"\bdowngrade", r"\bnot as (good|before)", r"\bwish it\b", r"\bshould be\b",
 # --- 俄语/乌克兰语 ---
 r"\bне\s", r"\bнет\b", r"\bнельзя\b", r"\bневозможно\b", r"\bперестал", r"\bплох",
 r"\b(баг|ошибк|проблем|глюк|тормоз|виснет|вылет|лаг|сбой|косяк)", r"\bисправ", r"\bпочини",
 r"\b(ужас|отстой|шляп|мусор|хлам|дрянь|говно|развод|обман|фигн)", r"\bхуже\b",
 r"\bраньше\b.{0,60}\b(сейчас|теперь)", r"\bпочему\b", r"\bразочаров", r"\bбесит",
 r"\bне працює\b", r"\bне вдається\b",
 # --- 西/葡 ---
 r"\bno (se |me |puedo|funciona|reproduce|abre|carga|deja|sirve|es)", r"\bnunca\b", r"\bsin poder\b",
 r"\bnão (consigo|funciona|abre|reproduz|toca|da|é)", r"\bnao (consigo|funciona)",
 r"\b(error|fallo|falla|problema|bug|defecto)\b", r"\b(arregl|corrij|solucion|repar)",
 r"\b(pésimo|pesimo|terrible|horrible|malo|mala|basura|porquería|lixo|ruim|péssimo)\b",
 r"\bpeor\b", r"\bpior\b", r"\bantes\b.{0,50}\bahora\b", r"\bdeixou de\b", r"\bdejó de\b",
 r"\bpor qué\b", r"\bpor que\b", r"\bdecepcion", r"\bmolest",
 # --- 阿拉伯语/波斯语 ---
 r"\bلا (يعمل|يشتغل|استطيع|اقدر|يدعم|يظهر|يفتح)", r"\bما (يشتغل|اقدر|بيحمل|يظهر)",
 r"\b(مشكل|مشاكل|خلل|عطل|بطء|تعليق|خطأ)", r"\b(اصلاح|إصلاح|صلح|حل هذه)",
 r"\b(سيء|سيئ|زفت|عفن|ضعيف|فاشل|تعبان)", r"\bأسوأ\b", r"\bلماذا\b", r"\bليش\b", r"\bلا يوجد\b",
 r"\b(نمی|نمیشه|نمیتون|نداره|مشکل|خراب|افتضاح|بد است|چرا)",
 # --- CJK ---
 r"(不能|不可以|无法|無法|不支持|不支援|没有|沒有|不行|不好|不了|打不开|打不開)",
 r"(问题|問題|故障|错误|錯誤|失败|失敗|卡顿|卡頓|闪退|閃退|崩溃|崩潰|异常|異常|bug)",
 r"(修复|修復|解决|解決|改善|优化|優化|希望|建议|建議)", r"(垃圾|难用|難用|差劲|差勁|失望|坑)",
 r"(为什么|為什麼|怎么会|怎麼會)", r"(以前|之前).{0,25}(现在|現在|now)",
 r"(できない|できません|しない|されない|ない。|不具合|バグ|エラー|問題|故障|直して|修正)",
 r"(ひどい|最悪|ダメ|駄目|残念|不満|うざ|ストレス|なぜ|なんで|ゴミ)",
 r"(안 (되|돼|나|보|들)|못 |안돼|안됨|없어|없습니다|오류|버그|문제|고쳐|수정|안 됩니다)",
 r"(최악|별로|불편|실망|왜 )",
 # --- 东南亚/土耳其/欧陆 ---
 r"\b(tidak|gak|ga |nggak|kagak|belum) (bisa|dapat|muncul|jalan|work|berfungsi)",
 r"\b(masalah|error|rusak|jelek|buruk|parah|kecewa|ganggu|kenapa)\b",
 r"\b(çalışmıyor|açılmıyor|olmuyor|sorun|hata|bozuk|berbat|kötü|neden|niye)\b",
 r"\b(nie (działa|mogę|można)|problem|błąd|zepsut|beznadziej|dlaczego)\b",
 r"\b(funktioniert nicht|geht nicht|kein|fehler|problem|schlecht|warum)\b",
 r"\b(ne (fonctionne|marche|peut)|pas de|problème|erreur|dommage|pourquoi)\b",
 r"\b(non funziona|problema|errore|perché)\b",
 r"\b(không (thể|được|xem|chạy)|lỗi|hỏng|tệ|tại sao)\b",
 r"(ไม่(ได้|สามารถ|ดี)|ปัญหา|เสีย|แย่|ทำไม)",
 # --- 通用符号/句式 ---
 r"[😡🤬👎😤😠💩🫤😞😢]", r"\?{2,}",
 # 转折句式：好评里的「但是」才是真抱怨信号
 r"\bbut\b", r"\bhowever\b", r"\bexcept\b", r"\bonly (thing|problem|issue|downside)\b",
 r"\bно\b", r"\bоднако\b", r"\bтолько (вот|одно)\b", r"\bединственн", r"\bжаль\b",
 r"\bpero\b", r"\bsin embargo\b", r"\baunque\b", r"\bmas\b", r"\bporém\b", r"\bmais\b",
 r"\baber\b", r"\bjedoch\b", r"\bma\b", r"\bmaar\b", r"\bale\b",
 r"(しかし|でも|けど|ただ|残念|惜しい|欲しい|してほしい|改善)", r"(但是|不過|不过|可惜|唯一|希望能|建議|建议)",
 r"(하지만|그런데|아쉬|바랍니다)", r"\btapi\b", r"\bnamun\b", r"\bcuma\b", r"\bkecuali\b",
 r"\bama\b", r"\bfakat\b", r"\bancak\b", r"\blakin\b", r"\bلكن\b", r"\bاما\b", r"\bولی\b",
 r"\bnhưng\b", r"\bแต่\b",
]
NEG_RE = [re.compile(p, re.I) for p in COMPLAINT]

# ============ 强信号：明确指认「有个东西坏了」============
# ⚠ 铁律：这里只放【故障词】，绝不放【话题词】（广告/字幕/下载/画质…）。
#   放话题词会出两种错：① 好评提到该功能被误判在抱怨
#                      ② 撞上否定嵌套（"без рекламы"=没有广告 → 夸奖）
#   话题词属于 taxonomy.L1_KEYWORDS，两者职责不能混。
# 弱信号（否定词/转折词/情绪词）会被否定嵌套骗过：
#   "nunca me ha fallado"(从没出过问题) / "gak kecewa"(不失望) / "не ожидал, но понравился"
# 所以 4-5★ 只认强信号。
STRONG = [
 r"\b(bug|bugg?y|glitch|crash(es|ed|ing)?|freeze[sd]?|frozen|stuck|error|broken|malfunction)\b",
 r"\b(doesn'?t|does not|won'?t|can'?t|cannot|unable to|fails? to|no longer)\s+\w{0,12}\s?"
 r"(work|play|open|load|show|support|start|resume|save|sync|download|display|recogni|detect|connect|cast)",
 r"\b(not working|not playing|stopped working|out of sync|force ?clos)",
 r"\b(lag(s|gy|ging)?\b|lague\w*|stutter(s|ing)?|choppy|frame ?drops?|slow ?mo(tion)?|pixelat|overheat|drain)",
 r"\bplease (fix|repair|solve)", r"\bfix (this|it|the|your)", r"\bissue with\b", r"\bproblem with\b",
 # 俄/乌
 r"\b(не работает|не воспроизводит|не открыва|не показыва|не видит|не поддерживает|не запоминает)",
 r"\b(перестал|вылета|виснет|зависа|тормоз|глючит|лаги|баг|ошибк|сбой|рассинхрон)",
 r"\bисправьте\b", r"\bпочините\b", r"\bне працює\b",
 # 西/葡
 r"\bno (funciona|reproduce|abre|carga|se puede|guarda|reconoce|deja)",
 r"\bnão (funciona|reproduz|abre|carrega|toca|salva|reconhece)",
 r"\b(se cuelga|se traba|se pega|se cierra|se apaga|trava|congela|falha|fallo|falla)\b",
 r"\b(error|bug|problema)\b.{0,30}(con|al|de|em|no)", r"\barregl(en|ar)\b", r"\bcorrij\b",
 # 阿/波斯
 r"لا (يعمل|يشتغل|يفتح|يدعم|يظهر|يشغل)", r"ما (يشتغل|يفتح|بيحمل|يظهر)",
 r"(مشكلة|مشاكل|خلل|عطل|يتوقف|يعلق|بطيء)", r"(نمیشه|کار نمی|مشکل|خراب|هنگ|قطع میشه)",
 # CJK
 r"(不能|无法|無法|不支持|不支援|打不开|打不開|播放不了|读不出|讀不出|加载不|載入不)",
 r"(卡顿|卡頓|闪退|閃退|崩溃|崩潰|死机|當機|花屏|黑屏|不同步|失灵|失靈|报错|報錯|故障|异常|異常)",
 r"(できない|できません|再生されない|表示されない|動かない|不具合|バグ|エラー|落ちる|強制終了|カクつ|ズレ)",
 r"(안 (되|돼|나와|보여|들려)|안됨|안돼요|오류|버그|끊김|튕(김|겨)|먹통|안 됩니다)",
 # 东南亚/土/欧
 r"\b(tidak|gak|ga|nggak|kagak) (bisa|dapat|berfungsi|jalan|muncul|kebaca)",
 r"\b(rusak|error|macet|patah|ngelag|nge-?lag|force close)\b",
 r"\bkalah (sama|dari|dibanding|dibandingkan)\b",
 r"\b(çalışmıyor|açılmıyor|oynatmıyor|donuyor|takılıyor|hata|bozuk|sorun var)",
 r"\b(nie (działa|otwiera|odtwarza)|zawiesza|błąd|zepsut)",
 r"\b(funktioniert nicht|geht nicht|stürzt ab|ruckelt|fehler)",
 r"\b(ne (fonctionne|marche|lit) pas|plante|saccade|bug|erreur)",
 r"\b(non funziona|si blocca|errore|scatta)",
 r"\b(không (thể|được|chạy|mở)|lỗi|giật|đứng máy)",
 r"(ไม่(สามารถ|ได้|เล่น|ใช่|ฟรี)|ค้าง|กระตุก|ผิดพลาด|รำคาญ|แย่|เสีย|โฆษณา)",
 r"(тъп|глупав|иска пари|не работи|боклук|не мога)",
]
STRONG_RE = [re.compile(p, re.I) for p in STRONG]

def is_complaint(text, star=None):
    """star>=4 时只认强信号（明确指认某功能坏了）；否则弱信号也算。"""
    if star is not None and star >= 4:
        return NEG.hit(STRONG_RE, text)
    return NEG.hit(NEG_RE, text)

def complaint_hits(text):
    return [p.pattern for p in NEG_RE if p.search(text)][:3]
