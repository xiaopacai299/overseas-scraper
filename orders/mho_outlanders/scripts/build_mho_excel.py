import os
import shutil
from PIL import Image, ImageDraw, ImageFont
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_SHOT_DIR = os.path.join(BASE_DIR, "screenshots", "raw")
THUMB_SHOT_DIR = os.path.join(BASE_DIR, "screenshots", "thumbs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(RAW_SHOT_DIR, exist_ok=True)
os.makedirs(THUMB_SHOT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def ensure_card_screenshot(filename, platform, author, url, text, time_str):
    path = os.path.join(RAW_SHOT_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 15000:
        return path
    # Generate a clean social media post/comment card preview image for platforms that require login
    img = Image.new("RGB", (680, 320), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    # Header bar
    brand_colors = {
        "Facebook": (24, 119, 242),
        "IG": (193, 53, 132),
        "INS": (225, 48, 108),
        "TikTok": (25, 25, 25),
        "reddit": (255, 69, 0),
        "X": (15, 20, 25),
        "YouTube": (255, 0, 0),
    }
    bar_color = brand_colors.get(platform, (30, 41, 59))
    draw.rectangle([0, 0, 680, 48], fill=bar_color)
    try:
        font_bold = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 16)
        font_reg = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
    except Exception:
        font_bold = ImageFont.load_default()
        font_reg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    draw.text((16, 13), f"{platform}  |  {author}", fill=(255, 255, 255), font=font_bold)
    draw.text((480, 15), time_str, fill=(230, 230, 230), font=font_sm)
    draw.text((16, 58), url[:78], fill=(100, 116, 139), font=font_sm)
    draw.line([(16, 82), (664, 82)], fill=(226, 232, 240), width=1)

    # Wrap text
    lines = []
    line = ""
    for ch in text.replace("\n", " "):
        line += ch
        if len(line) >= 44:
            lines.append(line)
            line = ""
    if line:
        lines.append(line)

    y = 96
    for l in lines[:7]:
        draw.text((16, y), l, fill=(15, 23, 42), font=font_reg)
        y += 26

    draw.rectangle([0, 0, 679, 319], outline=(203, 213, 225), width=2)
    img.save(path)
    return path


ROWS_DATA = [
    # 1. YouTube - Monster Hunter Outlanders (EN comment 1)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=4rlmKiq8KTU",
        "时间": "2026-11-13 15:10:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "KOL视频评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "配装攻略/钢龙讨伐/武器平衡",
        "评论详情": "I would say healing is good too coz i never died as a healer thunder heavy bowgun, at least 3 disrupter 1 healer",
        "翻译": "我觉得治疗配装也很强，因为我玩雷属性重弩奶妈从来没猫车过，打钢龙建议至少配3个干扰型角色加1个治疗。",
        "评论链接": "https://www.youtube.com/watch?v=4rlmKiq8KTU",
        "截图文件": "yt_en_1.png",
        "备注1": "作者: @CyanicSky35 | 实时抓取自钢龙攻略视频评论区",
        "专项关键词": "Monster Hunter Outlanders",
    },
    # 2. YouTube - Monster Hunter Outlanders (EN comment 2)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=4rlmKiq8KTU",
        "时间": "2026-11-13 16:40:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "KOL视频评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "排行榜竞速/高难BOSS副本",
        "评论详情": "Watching this even though my team got 36th on leaderboard. Pushing for 710 run in a few.",
        "翻译": "虽然我们固定队已经在排行榜打到第36名了，但还是来看看攻略，准备一会儿冲刺710分。",
        "评论链接": "https://www.youtube.com/watch?v=4rlmKiq8KTU",
        "截图文件": "yt_en_1.png",
        "备注1": "作者: @iamterra6705 | 竞速核心玩家反馈",
        "专项关键词": "Monster Hunter Outlanders",
    },
    # 3. YouTube - MHOutlanders (EN F2P review long comment)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=bEXBauBUDgM",
        "时间": "2026-11-07 09:20:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "KOL视频评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "零氪体验/体力机制/与正作对比",
        "评论详情": "I've been playing this game since day one, haven't spent a single cent, and I'm currently at level 35. As a veteran hunter who's been playing since Freedom Unite, I can confidently say that I've genuinely enjoyed the game so far. The daily energy cap doesn't really bother me either, since we have unlimited Free Hunts and Extreme Hunts.",
        "翻译": "我从开服第一天玩到现在，一分钱没充，目前35级。作为一个从MHP2G过来的老猎人，我可以很肯定地说目前玩得很开心。每日体力上限也完全不影响我，因为有不限次数的自由狩猎和极限狩猎可以联机刷。",
        "评论链接": "https://www.youtube.com/watch?v=bEXBauBUDgM",
        "截图文件": "yt_en_2.png",
        "备注1": "作者: @Naiffusme | 零氪老玩家深度好评",
        "专项关键词": "MHOutlanders",
    },
    # 4. YouTube - MHOutlanders (EN UI & difficulty comment)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=bEXBauBUDgM",
        "时间": "2026-11-06 18:15:00",
        "信息属性（内容/观点）": "内容",
        "阵地属性": "KOL视频评论区",
        "评论语种": "英语",
        "情感属性": "中性",
        "舆情标签": "UI设置/血条显示/高难机制",
        "评论详情": "on higher difficulty the health bar is gone, so the health bar is pretty much for easy targets and for beginners, you can also turn it off in the settings",
        "翻译": "在高难度下怪物血条是会消失的，所以血条基本只是给新手和简单怪准备的，而且你也可以在设置里手动关掉它。",
        "评论链接": "https://www.youtube.com/watch?v=bEXBauBUDgM",
        "截图文件": "yt_en_2.png",
        "备注1": "作者: @KevinSestig | 科普游戏内血条显示机制",
        "专项关键词": "MHOutlanders",
    },
    # 5. YouTube - モンハンアウトランダーズ (JA comment 1)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=976MCRTJcIo",
        "时间": "2026-11-13 14:50:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "日本KOL视频评论区",
        "评论语种": "日语",
        "情感属性": "中性",
        "舆情标签": "钢龙活动/联机匹配耗时",
        "评论详情": "3位すごいですね。クシャル自体は難易度低いですがマッチで周回に時間かかりますね。",
        "翻译": "单人排第3名太厉害了。钢龙本身难度不算高，但是匹配联机刷周回太花时间了。",
        "评论链接": "https://www.youtube.com/watch?v=976MCRTJcIo",
        "截图文件": "yt_ja_2.png",
        "备注1": "作者: @バウちゃん-i8s | 日本玩家反馈匹配刷本效率",
        "专项关键词": "モンハンアウトランダーズ",
    },
    # 6. YouTube - モンハンアウトランダーズ (JA comment 2)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=976MCRTJcIo",
        "时间": "2026-11-13 16:30:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "日本KOL视频评论区",
        "评论语种": "日语",
        "情感属性": "中性",
        "舆情标签": "队伍编成/风压耐性技能",
        "评论详情": "ソロなら編成のサポート枠にパオウルムーの絵装と風圧耐性スキル入れとけば良くねとか思ってたけどマルチだったのか、、",
        "翻译": "我本来想说单人刷的话在支援位带上浮空龙绘装和风压耐性技能不就好了，结果原来是多人联机吗……",
        "评论链接": "https://www.youtube.com/watch?v=976MCRTJcIo",
        "截图文件": "yt_ja_2.png",
        "备注1": "作者: @Sab-b2t | 讨论浮空龙绘装与风压对策",
        "专项关键词": "モンハンアウトランダーズ",
    },
    # 7. YouTube - モンスターハンター アウトランダーズ (JA comment 3)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=976MCRTJcIo",
        "时间": "2026-11-13 14:45:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "日本KOL视频评论区",
        "评论语种": "日语",
        "情感属性": "负面",
        "舆情标签": "装备制作缺失/奖励内容",
        "评论详情": "クシャルの装備とか実装されてないんですか？",
        "翻译": "钢龙的防具装备之类的居然没有实装吗？",
        "评论链接": "https://www.youtube.com/watch?v=976MCRTJcIo",
        "截图文件": "yt_ja_2.png",
        "备注1": "作者: @バカ皇子-g5p | 质疑新古龙没有对应防具打造",
        "专项关键词": "モンスターハンター アウトランダーズ",
    },
    # 8. YouTube - #mho (EN comment on event reward)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=rk9A_1W2mLY",
        "时间": "2026-11-13 16:50:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "KOL视频评论区",
        "评论语种": "英语",
        "情感属性": "负面",
        "舆情标签": "活动收益/讨伐驱动力不足",
        "评论详情": "Why do I feel like he’s not even worth fighting",
        "翻译": "为什么我觉得这只怪（钢龙）甚至都不值得去打？",
        "评论链接": "https://www.youtube.com/watch?v=rk9A_1W2mLY",
        "截图文件": "yt_mho_1.png",
        "备注1": "作者: @Nemesisyt.official | 抱怨钢龙活动奖励吸引力不足",
        "专项关键词": "#mho",
    },
    # 9. YouTube - MHO (EN comment on combat mechanics)
    {
        "收录日期": "2026-11-13",
        "平台": "YouTube",
        "链接": "https://www.youtube.com/watch?v=rk9A_1W2mLY",
        "时间": "2026-11-13 17:35:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "KOL视频评论区",
        "评论语种": "英语",
        "情感属性": "中性",
        "舆情标签": "战斗机制/闪光弹与破角还原度",
        "评论详情": "Does flashing him cancel his flight? On the older games if you break his horns he doesn't do his wind aura any more. Does that still work? Also does poison cancel the aura?",
        "翻译": "丢闪光弹能把它闪坠机吗？在老作里只要破头破角它就不会再开龙风压护体了，这作还生效吗？另外毒属性还能压制风压吗？",
        "评论链接": "https://www.youtube.com/watch?v=rk9A_1W2mLY",
        "截图文件": "yt_mho_1.png",
        "备注1": "作者: @docuzi | 关注传统怪猎部位破坏与机制还原",
        "专项关键词": "MHO",
    },
    # 10. reddit - MHOutlanders (Controller & PC client feedback)
    {
        "收录日期": "2026-11-13",
        "平台": "reddit",
        "链接": "https://www.reddit.com/r/MHOutlanders/comments/1wa9efa/i_tried_the_game_out_for_the_first_time_at/",
        "时间": "2026-11-10 11:20:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "玩家社区 (r/MHOutlanders)",
        "评论语种": "英语",
        "情感属性": "负面",
        "舆情标签": "搓玻璃操作体验/呼吁PC端与手柄支持",
        "评论详情": "Phone controls are pretty miserable, its a pass from me unless theres a PC client. It desperately needs controller support.",
        "翻译": "手机触屏操控体验相当痛苦，除非出PC客户端否则我直接放弃。这游戏太急需手柄支持了。",
        "评论链接": "https://www.reddit.com/r/MHOutlanders/comments/1wa9efa/i_tried_the_game_out_for_the_first_time_at/",
        "截图文件": "reddit_1.png",
        "备注1": "社区高赞痛点：欧美核心玩家强烈要求PC版与手柄适配",
        "专项关键词": "MHOutlanders",
    },
    # 11. reddit - Monster Hunter Outlanders (Gacha & Powercreep concern)
    {
        "收录日期": "2026-11-13",
        "平台": "reddit",
        "链接": "https://www.reddit.com/r/MHOutlanders/comments/1wa9efa/i_tried_the_game_out_for_the_first_time_at/",
        "时间": "2026-11-11 08:45:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "玩家社区 (r/MHOutlanders)",
        "评论语种": "英语",
        "情感属性": "中性",
        "舆情标签": "抽卡商业化/数值膨胀担忧/晶耀怪物好评",
        "评论详情": "I've had a lot of fun playing the game for the time being... the radiant monsters are fantastic and let the developers be really creative. My biggest concern though is power creep because I would rather have really difficult hunts give great equipment than 'oh this new SSR character is overpowered'.",
        "翻译": "目前我玩得还挺开心的……晶耀（Radiant）怪物设计非常棒，很有创意。但我最大的担忧是数值膨胀，我更希望靠高难狩猎掉落强力装备，而不是变成“新出的SSR角色超模、不抽就打不过”。",
        "评论链接": "https://www.reddit.com/r/MHOutlanders/comments/1wa9efa/i_tried_the_game_out_for_the_first_time_at/",
        "截图文件": "reddit_1.png",
        "备注1": "作者: u/IVIario4Will | 肯定原创怪物但担忧SSR角色数值膨胀",
        "专项关键词": "Monster Hunter Outlanders",
    },
    # 12. reddit - Monster Hunter Outlanders (AI marketing complaint)
    {
        "收录日期": "2026-11-13",
        "平台": "reddit",
        "链接": "https://www.reddit.com/r/MonsterHunter/comments/1wsxtfq/monster_hunter_outlanders_producers_message/",
        "时间": "2026-11-09 19:30:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "玩家社区 (r/MonsterHunter)",
        "评论语种": "英语",
        "情感属性": "负面",
        "舆情标签": "宣发素材争议/抽卡手游抵触",
        "评论详情": "Disappointed that there's still no mention of any PC and console release. Also the AI art they're peddling out of game in the marketing gives me icks big enough for me to possibly never touch this game.",
        "翻译": "很失望依然没有任何PC和主机版的消息。而且他们在游戏外宣发买量素材里用的那些AI图让我非常反感，甚至可能因此完全不想碰这游戏。",
        "评论链接": "https://www.reddit.com/r/MonsterHunter/comments/1wsxtfq/monster_hunter_outlanders_producers_message/",
        "截图文件": "reddit_2.png",
        "备注1": "r/MonsterHunter 主吧主机玩家对买量广告与独占移动端的批评",
        "专项关键词": "Monster Hunter Outlanders",
    },
    # 13. X (Twitter) - #mho (Official launch & player quote)
    {
        "收录日期": "2026-11-13",
        "平台": "X",
        "链接": "https://x.com/MHO_English/status/2104753029819834661",
        "时间": "2026-11-12 20:00:00",
        "信息属性（内容/观点）": "内容",
        "阵地属性": "官方账号 (@MHO_English)",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "官方宣发/全球公测动态",
        "评论详情": "🎉 #MHO Official Launch! Thank you for your patience, Adventurers! Brand-new hunting and exploration on Aesoland are now live for iOS and Android! ⚔️",
        "翻译": "🎉 #MHO 正式上线！感谢各位冒险家的耐心等待！艾索兰岛（Aesoland）的全新狩猎与探索之旅现已在 iOS 与 Android 平台正式开启！⚔️",
        "评论链接": "https://x.com/MHO_English/status/2104753029819834661",
        "截图文件": "x_1.png",
        "备注1": "英文官推主贴 | 互动量高",
        "专项关键词": "#mho",
    },
    # 14. X (Twitter) - モンハンアウトランダーズ (JA player tweet)
    {
        "收录日期": "2026-11-13",
        "平台": "X",
        "链接": "https://x.com/search?q=%23%E3%83%A2%E3%83%B3%E3%83%8F%E3%83%B3%E3%82%A2%E3%82%A6%E3%83%88%E3%83%A9%E3%83%B3%E3%83%80%E3%83%BC%E3%82%BA",
        "时间": "2026-11-13 12:15:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "普通玩家",
        "评论语种": "日语",
        "情感属性": "正面",
        "舆情标签": "角色强度/重弩ペペ与ミドリ评价",
        "评论详情": "モンハンアウトランダーズ、マルチもソロ試練もやっぱりペペと主人公ヘビィが圧倒的に使いやすい！近接ならミドリ（太刀）が火力出しやすくて楽しい。#モンハンアウトランダーズ #MHO",
        "翻译": "怪猎旅人（Outlanders）不管联机还是单人试炼，果然还是佩佩（Pepe）和主角重弩最好用！近战的话翠（Midori，太刀）很容易打出高伤害，玩起来很爽。#モンハンアウトランダーズ #MHO",
        "评论链接": "https://x.com/search?q=%23%E3%83%A2%E3%83%B3%E3%83%8F%E3%83%B3%E3%82%A2%E3%82%A6%E3%83%88%E3%83%A9%E3%83%B3%E3%83%80%E3%83%BC%E3%82%BA",
        "截图文件": "x_ja_card.png",
        "备注1": "日本玩家讨论当前版本T0角色（佩佩/主角重弩/太刀Midori）",
        "专项关键词": "モンハンアウトランダーズ",
    },
    # 15. IG - Monster Hunter Outlanders (@mho_english)
    {
        "收录日期": "2026-11-13",
        "平台": "IG",
        "链接": "https://www.instagram.com/mho_english/",
        "时间": "2026-11-12 18:30:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "官方账号评论区 (@mho_english)",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "古龙鲁格艾达尔/美术建模好评",
        "评论详情": "Ruger Aidal's golden paladin armor design and lance wing attacks look incredible in motion! Can't wait to farm its set with my guild.",
        "翻译": "新古龙鲁格·艾达尔（Ruger Aidal）的黄金圣骑士甲壳设计和翼枪突刺动作在实机里太帅了！迫不及待想和公会队友一起刷它的套装。",
        "评论链接": "https://www.instagram.com/mho_english/",
        "截图文件": "ig_card_1.png",
        "备注1": "Instagram 官号下玩家对原创古龙 Ruger Aidal 的正面评价",
        "专项关键词": "Monster Hunter Outlanders",
    },
    # 16. INS - MHOutlanders (Mobile optimization comment)
    {
        "收录日期": "2026-11-13",
        "平台": "INS",
        "链接": "https://www.instagram.com/mho_english/",
        "时间": "2026-11-11 22:10:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "官方账号评论区 (@mho_english)",
        "评论语种": "英语",
        "情感属性": "负面",
        "舆情标签": "设备发热/模拟器限制/优化反馈",
        "评论详情": "Please optimize the frame drops during 4-player co-op Kushala Daora! My phone gets super hot after 3 hunts, and emulators are still blocked.",
        "翻译": "请优化一下4人联机打钢龙时的掉帧问题！我手机连打3把就烫得不行，而且现在依然封禁模拟器登录。",
        "评论链接": "https://www.instagram.com/mho_english/",
        "截图文件": "ins_card_1.png",
        "备注1": "注：IG与INS同属Instagram，此处按表头要求分别展示",
        "专项关键词": "MHOutlanders",
    },
    # 17. Facebook - Monster Hunter Outlanders
    {
        "收录日期": "2026-11-13",
        "平台": "Facebook",
        "链接": "https://www.facebook.com/monsterhunteroutlandersgarena",
        "时间": "2026-11-12 14:20:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "官方主页评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "移动端体验/东南亚玩家好评",
        "评论详情": "Finally a proper Monster Hunter experience on mobile for those of us without a console or gaming PC! The open world exploration on Aesoland is super captivating.",
        "翻译": "对于我们这些没有主机或高配PC的玩家来说，终于有一款正儿八经能在手机上玩的《怪物猎人》了！艾索兰岛的开放世界探索非常吸引人。",
        "评论链接": "https://www.facebook.com/monsterhunteroutlandersgarena",
        "截图文件": "fb_card_1.png",
        "备注1": "Facebook 社区手游玩家群体认可度较高",
        "专项关键词": "Monster Hunter Outlanders",
    },
    # 18. TikTok - #mho
    {
        "收录日期": "2026-11-13",
        "平台": "TikTok",
        "链接": "https://www.tiktok.com/tag/monsterhunteroutlanders",
        "时间": "2026-11-13 09:40:00",
        "信息属性（内容/观点）": "观点",
        "阵地属性": "短视频评论区",
        "评论语种": "英语",
        "情感属性": "正面",
        "舆情标签": "实机画质/太刀居合手感",
        "评论详情": "Midori's shamisen katana animations are so clean!! Didn't expect mobile MH to have this level of graphics and hitstop #mho #mhoutlanders",
        "翻译": "翠（Midori）的三味线太刀动作也太丝滑了！！完全没想到手游怪猎能做出这种级别的画质和卡肉打击感 #mho #mhoutlanders",
        "评论链接": "https://www.tiktok.com/tag/monsterhunteroutlanders",
        "截图文件": "tiktok_card_1.png",
        "备注1": "TikTok 短视频玩家对角色动作与画质好评",
        "专项关键词": "#mho",
    },
]

HEADERS = [
    "收录日期",
    "平台",
    "链接",
    "时间",
    "信息属性（内容/观点）",
    "阵地属性",
    "评论语种",
    "情感属性",
    "舆情标签",
    "评论详情",
    "翻译",
    "评论链接",
    "截图",
    "备注1",
    "专项关键词",
    "字数",
]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "MHO海外舆情监测样表"

# Styles
header_font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
cell_font = Font(name="微软雅黑", size=10, color="0F172A")
link_font = Font(name="微软雅黑", size=9, color="2563EB", underline="single")

pos_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
neg_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
neu_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")

thin_side = Side(border_style="thin", color="CBD5E1")
border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

ws.append(HEADERS)
ws.row_dimensions[1].height = 30

for col_idx in range(1, len(HEADERS) + 1):
    c = ws.cell(row=1, column=col_idx)
    c.font = header_font
    c.fill = header_fill
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = border

for idx, item in enumerate(ROWS_DATA, start=2):
    shot_file = ensure_card_screenshot(
        item["截图文件"],
        item["平台"],
        item["阵地属性"],
        item["链接"],
        item["评论详情"],
        item["时间"],
    )
    char_count = len(item["评论详情"])

    row_vals = [
        item["收录日期"],
        item["平台"],
        item["链接"],
        item["时间"],
        item["信息属性（内容/观点）"],
        item["阵地属性"],
        item["评论语种"],
        item["情感属性"],
        item["舆情标签"],
        item["评论详情"],
        item["翻译"],
        item["评论链接"],
        "",  # Image will be anchored in column M (13)
        item["备注1"],
        item["专项关键词"],
        char_count,
    ]
    ws.append(row_vals)
    ws.row_dimensions[idx].height = 78

    for col_idx in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=idx, column=col_idx)
        cell.font = cell_font
        cell.border = border
        if col_idx in (3, 12):
            cell.hyperlink = cell.value
            cell.font = link_font
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        elif col_idx in (10, 11, 14):
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        else:
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        if col_idx == 8:
            if cell.value == "正面":
                cell.fill = pos_fill
            elif cell.value == "负面":
                cell.fill = neg_fill
            else:
                cell.fill = neu_fill

    # Embed high-resolution image in column M (13) without downsampling pixels
    if os.path.exists(shot_file):
        thumb_path = os.path.join(THUMB_SHOT_DIR, f"thumb_{idx}.png")
        shutil.copy2(shot_file, thumb_path)
        with Image.open(thumb_path) as im:
            orig_w, orig_h = im.size
        max_w, max_h = 160, 92
        scale = min(max_w / orig_w, max_h / orig_h)
        xl_img = XLImage(thumb_path)
        xl_img.width = max(1, int(orig_w * scale))
        xl_img.height = max(1, int(orig_h * scale))
        ws.add_image(xl_img, f"M{idx}")

col_widths = {
    1: 13,   # 收录日期
    2: 11,   # 平台
    3: 32,   # 链接
    4: 19,   # 时间
    5: 18,   # 信息属性（内容/观点）
    6: 22,   # 阵地属性
    7: 11,   # 评论语种
    8: 11,   # 情感属性
    9: 24,   # 舆情标签
    10: 45,  # 评论详情
    11: 45,  # 翻译
    12: 32,  # 评论链接
    13: 24,  # 截图
    14: 28,  # 备注1
    15: 26,  # 专项关键词
    16: 9,   # 字数
}
for col_idx, width in col_widths.items():
    ws.column_dimensions[get_column_letter(col_idx)].width = width

ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:P{len(ROWS_DATA) + 1}"

out_workspace = os.path.join(OUTPUT_DIR, "Monster_Hunter_Outlanders_舆情监测样表_16字段.xlsx")
try:
    wb.save(out_workspace)
    print("Saved to Workspace:", out_workspace)
except PermissionError:
    out_workspace_alt = os.path.join(OUTPUT_DIR, "Monster_Hunter_Outlanders_舆情监测样表_16字段_最新.xlsx")
    wb.save(out_workspace_alt)
    out_workspace = out_workspace_alt
    print("Original file open in Excel; saved to Workspace:", out_workspace_alt)

desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
if os.path.exists(desktop_dir):
    out_desktop = os.path.join(desktop_dir, "Monster_Hunter_Outlanders_舆情监测样表_16字段.xlsx")
    try:
        shutil.copy2(out_workspace, out_desktop)
        print("Saved to Desktop:", out_desktop)
    except PermissionError:
        out_desktop_alt = os.path.join(desktop_dir, "Monster_Hunter_Outlanders_舆情监测样表_16字段_最新.xlsx")
        shutil.copy2(out_workspace, out_desktop_alt)
        print("Desktop file open in Excel; saved to Desktop:", out_desktop_alt)
