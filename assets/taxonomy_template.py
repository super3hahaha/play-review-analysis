# -*- coding: utf-8 -*-
"""<APP_NAME> 评论分类词表

═══ 这个文件是唯一需要按 app 定制的东西 ═══

三张表各司其职，职责千万别混：
  L1_KEYWORDS  【话题词】判断"在说哪个功能域"。好评里也会出现（"download 很快"），
               所以它判断不了"是不是问题"——那是 complaint.py 的活。
  L2_RULES     【症状词】判断"具体什么毛病"。命中 L2 才算「可细分」，否则进该域的笼统池。
  DOMAIN_TERMS 【技术名词】该 app 特有的格式/协议/功能名。命中会给信息密度加分，
               因为它能缩小测试矩阵。

下面 ① 通用域 对几乎所有 app 都适用，可以直接留着。
     ② 业务域 需要你按这个 app 的功能填——这是主要工作。

⚠ 加词前先自问：**这个词出现在好评里正常吗？** 正常就说明它是话题词，
   只能进 L1_KEYWORDS，绝不能进 complaint.py 的强信号表。
   （真实教训：往强信号塞了 реклам(广告)，结果俄语"без рекламы"=没有广告 被判成抱怨）
⚠ 非拉丁语种的短词必须加词边界。真实教训：
   俄语 ави←нр**ави**тся(喜欢) / фон←теле**фон**(手机) / 印尼语 seka←bagus **seka**li(非常好)
⚠ 改完跑 `python3 <skill>/scripts/audit_keywords.py` 自查误伤（用 5★ 好评当阴性对照组）
"""

L1_KEYWORDS = {
# ═══════════ ② 业务域：按这个 app 的功能填 ═══════════
# 示例（视频播放器）：
# "视频播放画质与流畅度": [r"\blag", r"stutter", r"卡顿", r"тормоз", r"カクつ", ...],
# "格式兼容":            [r"\bmkv\b", r"\bavi\b", r"hevc", r"格式", r"формат", ...],
# 提示：一个功能域配 15~40 条多语言关键词比较够用。
#      英/西/葡/俄/阿/印尼/日/韩/中/土/法/德 这 12 种覆盖约 85% 的评论量。
"TODO_业务域1": [
  r"TODO",
],

# ═══════════ ① 通用域：几乎所有 app 都适用，可直接保留 ═══════════
"广告体验": [
  r"\bads?\b", r"advertis", r"реклам", r"anunci", r"iklan", r"publicidad", r"propaganda",
  r"広告", r"廣告", r"广告", r"광고", r"إعلان", r"اعلان", r"تبلیغات", r"reklam", r"\bpubs?\b",
  r"werbung", r"pubblicit", r"reklamy", r"โฆษณา", r"quảng cáo", r"פרסומות", r"spam",
  r"judol", r"judi online",
],
"付费/会员权益": [
  r"premium", r"\bpaid\b", r"\bpay\b", r"purchase", r"subscri", r"refund", r"trial", r"lifetime",
  r"платн", r"подписк", r"куп", r"pagué", r"pago", r"suscripci", r"assinatura", r"berbayar",
  r"有料", r"課金", r"付费", r"付費", r"유료", r"구독", r"구매", r"평생", r"اشتراك", r"مدفوع",
  r"پولی", r"ücret", r"not free", r"no es gratis", r"gratis", r"money", r"деньг", r"price",
  r"цена", r"precio", r"debited", r"charged", r"billing",
],
"应用性能": [
  r"crash", r"force ?clos", r"app closes", r"se cierra", r"se apaga", r"fecha sozinho",
  r"desligando sozinho", r"вылета", r"выкидывает", r"падает", r"не отвеча", r"落ちる",
  r"強制終了", r"闪退", r"當機", r"\banr\b", r"keluar sendiri", r"يخرج من التطبيق", r"خارج میشه",
  r"무한로딩", r"buggy", r"багов", r"bug\b", r"глюч",
  r"batter", r"batre", r"bateria", r"batería", r"батаре", r"電池", r"耗电", r"overheat",
  r"heating", r"нагрев", r"перегрев", r"発熱", r"panas", r"발열",
  r"opening speed", r"startup", r"khởi động", r"起動", r"启动慢",
  r"(can'?t|won'?t|not|cannot|unable).{0,20}(install|update|uninstall)", r"no me deja instalar",
  r"не обновля", r"не устанавл", r"tidak bisa (install|update)", r"nie działa na", r"не совместимо",
  r"incompatib", r"안 깔",
],
"隐私与权限": [
  r"permission", r"privacy", r"personal data", r"data (steal|collect)", r"cookie", r"gdpr",
  r"разрешени", r"персональн", r"个人信息", r"個人情報", r"프라이버시", r"permiso",
  r"datos personales", r"izin", r"صلاحي", r"دسترسی", r"clipboard", r"クリップボード",
  r"vie privée", r"datenschutz", r"spyware",
],
"UI与交互": [
  r"\binterface\b", r"\bui\b", r"интерфейс", r"interfaz", r"界面", r"介面", r"인터페이스",
  r"インターフェース", r"واجهة", r"arayüz", r"antarmuka",
  r"(ugly|hideous|horrible|awful).{0,20}(screen|design|look|theme|background)",
  r"(fondo|tema|背景|テーマ|테마|خلفية).{0,25}(horrible|feo|malo|难看|丑)",
  r"убог", r"(too |muy |très )?(complex|complicad|complexe|复杂)",
  r"(button|botón|кнопк|按钮|ボタン).{0,30}(small|close together|难按|太近)", r"layout", r"布局",
],
"客服与响应": [
  r"fake email", r"(email|e-?mail|почт|correo|邮箱|メール).{0,30}(fake|invalid|wrong|假)",
  r"(no|never|not).{0,20}(reply|respond|answer|response)", r"разработчик.{0,25}не отвеча",
  r"не отвеча(ет|ют)", r"没有回复", r"返信(が)?(ない|来ない)", r"응답(이)? 없",
  r"customer (support|service)", r"客服", r"售后",
],
"评分弹窗骚扰": [
  r"(rate|rating|review).{0,20}(pop|request|prompt|message|asking)",
  r"asking me to (rate|review)", r"stop asking", r"выпрашива", r"отзыв.{0,15}прос",
  r"評価.{0,10}(要求|催促)", r"pedir.{0,15}calific", r"pestering",
],
}

# 一条评论命中多个一级分类时，主分类取这里靠前的。
# 原则：【具体功能问题】排在【体验/策略类】前面。
#   UI 抱怨通常是次要的（"主要讲解码问题，顺带说了句界面丑"）→ 排最后
#   广告/付费/评分弹窗是产品策略，不该抢走功能问题的主分类 → 靠后
L1_PRIORITY = [
  # ② 业务域放这里（按定位价值排序：越具体越靠前）
  "TODO_业务域1",
  # ① 通用域
  "应用性能", "客服与响应", "隐私与权限",
  "付费/会员权益", "广告体验", "评分弹窗骚扰",
  "UI与交互",
]

# 这些二级分类是产品策略而非缺陷，状态直接标「非缺陷-产品策略」，不进复现队列。
# 「广告太多」「太贵」这类笼统就是终点，只跟趋势不做复现。
POLICY_L2 = {
  '抱怨有广告/数量多', '抱怨有付费/强制订阅', '付费价格高', '广告时长过长',
  '广告展示位置不当', '广告内容不当：病毒/诈骗/成人内容',
  '频繁弹出评分请求', '付费后仍弹评分请求',
}

# 该 app 特有的技术名词。命中会给信息密度 +10 分，因为它能缩小测试矩阵。
# 示例（视频播放器）：[r"\b(mkv|avi|hevc|h\.?265|hdr10|dolby)\b", r"chromecast", r"字幕同步"]
DOMAIN_TERMS = [
  # r"TODO",
]

# (一级, 二级, [症状词])。只有命中 L2 才算「可细分」，否则进该域的笼统池。
L2_RULES = [
 # ═══════════ ② 业务域 ═══════════
 # ("TODO_业务域1", "TODO_具体症状", [r"TODO"]),

 # ═══════════ ① 通用域 ═══════════
 ("广告体验", "广告内容不当：病毒/诈骗/成人内容", [
   r"judol", r"judi online", r"slot", r"gambl", r"scam", r"phishing", r"virus", r"malicious",
   r"18\+", r"porn", r"성인광고", r"мошенн", r"вирус", r"estafa", r"病毒", r"賭", r"inappropriate",
 ]),
 ("广告体验", "广告无法关闭/关闭困难", [
   r"can'?t close", r"cannot close", r"крестик", r"закрыть.{0,15}реклам", r"閉じれない",
   r"fechar o.{0,10}anúncio", r"cerrar.{0,15}anuncio", r"关不掉", r"forces you to (play|watch)",
 ]),
 ("广告体验", "广告影响操作", [
   r"covers the button", r"遮挡", r"画面の真ん中", r"وسط الشاشه", r"banner.{0,20}(cover|block)",
 ]),
 ("广告体验", "抱怨有广告/数量多", [
   r"too many", r"so many", r"lots of", r"muitos", r"muchos", r"banyak", r"много", r"куча",
   r"多すぎ", r"太多", r"많", r"كثير", r"زیاد", r"trop de", r"zuviel", r"every time", r"sürekli",
 ]),
 ("付费/会员权益", "会员身份失效/已付费仍有广告", [
   r"paid.{0,40}(still|ads)", r"premium.{0,40}(still|ads|lost)", r"lifetime.{0,30}(still|ads)",
   r"куп.{0,25}реклам", r"課金.{0,20}広告", r"restore purchase", r"평생.{0,30}광고",
   r"구매내역.{0,10}없", r"buyer beware",
 ]),
 ("付费/会员权益", "退款/误扣费", [
   r"refund", r"debited", r"charged", r"unauthori[sz]ed", r"استرداد", r"扣费", r"환불",
 ]),
 ("付费/会员权益", "付费价格高", [
   r"expensive", r"pricey", r"too much money", r"дорого", r"caro", r"价格", r"przegięcie",
 ]),
 ("付费/会员权益", "抱怨有付费/强制订阅", [
   r"not free", r"no es gratis", r"tidak gratis", r"платн",
   r"force.{0,20}(subscri|trial|sign up)", r"must (pay|buy)", r"за деньги", r"money grabbing",
 ]),
 ("应用性能", "应用崩溃/闪退", [
   r"crash", r"force ?clos", r"se cierra", r"se apaga", r"fecha sozinho", r"desligando sozinho",
   r"вылета", r"выкидывает", r"падает", r"落ちる", r"強制終了", r"闪退", r"當機", r"\banr\b",
   r"keluar sendiri", r"يخرج من التطبيق", r"무한로딩",
 ]),
 ("应用性能", "程序耗电高/设备过热", [
   r"batter", r"batre", r"bateria", r"батаре", r"電池", r"耗电", r"overheat", r"heating",
   r"нагрев", r"перегрев", r"発熱", r"panas", r"발열", r"drain",
 ]),
 ("应用性能", "应用启动慢", [
   r"opening speed", r"startup", r"slow to (open|start|launch)", r"khởi động quá chậm",
   r"起動.{0,10}(遅|重)", r"медленно.{0,15}открыва", r"启动慢", r"demora muito ao abrir",
 ]),
 ("应用性能", "部分设备不支持", [
   r"no longer compatible", r"не совместимо", r"incompatib", r"nie działa na",
   r"(can'?t|cannot|unable to).{0,20}install", r"no me deja instalar", r"не обновля",
   r"app (don'?t|doesn'?t|won'?t) (update|install)",
 ]),
 ("隐私与权限", "权限请求过度/要求全部文件访问", [
   r"(all|entire|full).{0,25}(files?|photo library|storage)", r"requires? full access",
   r"alle dateien", r"доступ.{0,20}(ко всем|файл)", r"todos los (archivos|permisos)",
   r"(permission|permiso|izin|разрешени|権限|권한).{0,40}(too many|unnecessary|не нужн|berlebihan)",
 ]),
 ("隐私与权限", "Cookie/GDPR 同意流程问题", [
   r"cookie", r"gdpr", r"consent", r"vendors?", r"reject all", r"widersprechen",
   r"согласи.{0,20}(данн|обработк)", r"обработку персональных данных",
 ]),
 ("隐私与权限", "怀疑窃取/滥用个人数据", [
   r"(steal|stealing|stolen).{0,20}(data|video|photo|file)", r"data ?(stealer|theft)", r"spyware",
   r"личные данные", r"крад", r"個人情報.{0,10}泥棒", r"collects? .{0,25}(data|information)",
 ]),
 ("隐私与权限", "强制注册/登录才能使用", [
   r"(forced?|obligat|must|have to|требу|заставля|必须|harus|zorunlu).{0,35}"
   r"(register|sign ?up|log ?in|account|регистр|cuenta|注册|登录|계정|حساب)",
   r"giving my personal info",
 ]),
 ("UI与交互", "界面观感差/操作复杂", [
   r"(bad|ugly|horrible|awful|terrible|poor|confusing).{0,15}(interface|ui|design|layout)",
   r"(interfaz|интерфейс|界面|인터페이스).{0,20}(mala|feo|убог|难用|差|复杂|나쁘|complic)",
   r"муторн", r"muy complejo", r"too complicated",
 ]),
 ("UI与交互", "主题/背景样式差", [
   r"(fondo|fundo|background|тема|theme|背景|테마|خلفية).{0,25}(horrible|feo|ugly|难看|丑|ужас)",
 ]),
 ("UI与交互", "控件布局/误触", [
   r"(button|icon|botón|кнопк|按钮|버튼).{0,35}(too close|small|overlap|误触|近すぎ)",
 ]),
 ("客服与响应", "联系方式无效/无法联系开发者", [
   r"fake email", r"(email|correo|почт|邮箱).{0,25}(fake|invalid|不存在|假的)",
   r"against google play (store )?policy",
 ]),
 ("客服与响应", "开发者不回复/长期无响应", [
   r"(no|never|not).{0,20}(reply|respond|answer)", r"разработчик.{0,25}не отвеча",
   r"не отвеча(ет|ют)", r"没有回复", r"返信(が)?(ない|来ない)", r"응답(이)? 없",
   r"(telling|told).{0,25}(team|developer).{0,25}many times",
 ]),
 ("评分弹窗骚扰", "付费后仍弹评分请求", [
   r"(paid|premium|purchase).{0,60}(rate|rating|review).{0,20}(pop|message|asking)",
   r"купил.{0,40}отзыв",
 ]),
 ("评分弹窗骚扰", "频繁弹出评分请求", [
   r"stop (asking|pestering)", r"asking me to (rate|review)", r"keeps? popping up",
   r"выпрашива", r"отзыв.{0,15}прос", r"評価.{0,10}(要求|催促)", r"pedir.{0,15}calific",
 ]),
]
