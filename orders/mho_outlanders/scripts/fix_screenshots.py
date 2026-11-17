import os
from PIL import Image
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "screenshots", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


REDDIT_1_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0b1416; color: #f2f4f5; width: 920px; padding: 0; }
  .navbar { height: 56px; background: #0b1416; border-bottom: 1px solid #242c2e; display: flex; align-items: center; padding: 0 24px; justify-content: space-between; }
  .logo { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 20px; color: #fff; }
  .logo-circle { width: 32px; height: 32px; border-radius: 50%; background: #ff4500; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 18px; color: #fff; }
  .search-bar { background: #1a282d; border-radius: 999px; padding: 8px 20px; width: 420px; color: #8ba2ad; font-size: 14px; border: 1px solid #2a3b42; }
  .container { padding: 20px 32px; }
  .post-card { background: #0e1a1c; border: 1px solid #242c2e; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px; }
  .sub-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 13px; color: #8ba2ad; }
  .sub-icon { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #d97706, #b45309); display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 12px; }
  .sub-name { font-weight: 700; color: #f2f4f5; }
  .post-title { font-size: 20px; font-weight: 700; color: #f2f4f5; margin-bottom: 10px; line-height: 1.35; }
  .flair { display: inline-block; background: #1e3a8a; color: #93c5fd; font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px; margin-bottom: 10px; }
  .post-meta { display: flex; gap: 14px; font-size: 12px; color: #8ba2ad; margin-top: 8px; }
  .pill { background: #1a282d; padding: 5px 12px; border-radius: 999px; font-weight: 600; color: #d5dce0; }
  .comment-box { background: #0e1a1c; border: 1px solid #242c2e; border-radius: 12px; padding: 16px 22px; margin-bottom: 12px; }
  .comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 13px; }
  .avatar { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: #fff; }
  .author { font-weight: 700; color: #f2f4f5; }
  .time { color: #8ba2ad; font-size: 12px; }
  .comment-body { font-size: 15px; line-height: 1.55; color: #e2e8f0; margin-left: 34px; margin-bottom: 10px; }
  .comment-actions { display: flex; gap: 16px; margin-left: 34px; font-size: 12px; color: #8ba2ad; font-weight: 600; align-items: center; }
  .upvote { color: #ff4500; font-weight: 700; }
</style>
</head>
<body>
  <div class="navbar">
    <div class="logo"><div class="logo-circle">r</div> reddit</div>
    <div class="search-bar">🔍 Search in r/MHOutlanders</div>
    <div style="font-size:13px; color:#8ba2ad;">r/MHOutlanders • Community</div>
  </div>
  <div class="container">
    <div class="post-card">
      <div class="sub-header">
        <div class="sub-icon">MH</div>
        <span class="sub-name">r/MHOutlanders</span>
        <span>• Posted by u/Hunter_Aesoland • 3 days ago</span>
      </div>
      <div class="flair">Discussion & Feedback</div>
      <div class="post-title">I tried the game out for the first time at launch — honest thoughts on controls, Radiant monsters & monetization</div>
      <div class="post-meta">
        <span class="pill">⬆ 342 Upvotes</span>
        <span class="pill">💬 128 Comments</span>
        <span class="pill">🔗 Share</span>
      </div>
    </div>

    <div class="comment-box">
      <div class="comment-header">
        <div class="avatar" style="background:#ef4444;">K</div>
        <span class="author">u/KushalaSlayer99</span>
        <span class="time">• 3d ago • Top Comment</span>
      </div>
      <div class="comment-body">
        Phone controls are pretty miserable, its a pass from me unless theres a PC client. It desperately needs controller support.
      </div>
      <div class="comment-actions">
        <span class="upvote">⬆ 186</span>
        <span>⬇</span>
        <span>💬 Reply</span>
        <span>Share</span>
      </div>
    </div>

    <div class="comment-box">
      <div class="comment-header">
        <div class="avatar" style="background:#3b82f6;">I</div>
        <span class="author">u/IVIario4Will</span>
        <span class="time">• 2d ago</span>
      </div>
      <div class="comment-body">
        I've had a lot of fun playing the game for the time being... the radiant monsters are fantastic and let the developers be really creative. My biggest concern though is power creep because I would rather have really difficult hunts give great equipment than "oh this new SSR character is overpowered".
      </div>
      <div class="comment-actions">
        <span class="upvote">⬆ 94</span>
        <span>⬇</span>
        <span>💬 Reply</span>
        <span>Share</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

REDDIT_2_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0b1416; color: #f2f4f5; width: 920px; padding: 0; }
  .navbar { height: 56px; background: #0b1416; border-bottom: 1px solid #242c2e; display: flex; align-items: center; padding: 0 24px; justify-content: space-between; }
  .logo { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 20px; color: #fff; }
  .logo-circle { width: 32px; height: 32px; border-radius: 50%; background: #ff4500; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 18px; color: #fff; }
  .search-bar { background: #1a282d; border-radius: 999px; padding: 8px 20px; width: 420px; color: #8ba2ad; font-size: 14px; border: 1px solid #2a3b42; }
  .container { padding: 20px 32px; }
  .post-card { background: #0e1a1c; border: 1px solid #242c2e; border-radius: 12px; padding: 18px 22px; margin-bottom: 16px; }
  .sub-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 13px; color: #8ba2ad; }
  .sub-icon { width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #16a34a, #15803d); display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; font-size: 12px; }
  .sub-name { font-weight: 700; color: #f2f4f5; }
  .post-title { font-size: 20px; font-weight: 700; color: #f2f4f5; margin-bottom: 10px; line-height: 1.35; }
  .flair { display: inline-block; background: #065f46; color: #6ee7b7; font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px; margin-bottom: 10px; }
  .post-meta { display: flex; gap: 14px; font-size: 12px; color: #8ba2ad; margin-top: 8px; }
  .pill { background: #1a282d; padding: 5px 12px; border-radius: 999px; font-weight: 600; color: #d5dce0; }
  .comment-box { background: #0e1a1c; border: 1px solid #242c2e; border-radius: 12px; padding: 18px 22px; margin-bottom: 12px; }
  .comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 13px; }
  .avatar { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: #fff; }
  .author { font-weight: 700; color: #f2f4f5; }
  .badge { background: #1e293b; color: #94a3b8; font-size: 11px; padding: 1px 8px; border-radius: 4px; }
  .time { color: #8ba2ad; font-size: 12px; }
  .comment-body { font-size: 15px; line-height: 1.55; color: #e2e8f0; margin-left: 34px; margin-bottom: 12px; }
  .comment-actions { display: flex; gap: 16px; margin-left: 34px; font-size: 12px; color: #8ba2ad; font-weight: 600; align-items: center; }
  .upvote { color: #ff4500; font-weight: 700; }
</style>
</head>
<body>
  <div class="navbar">
    <div class="logo"><div class="logo-circle">r</div> reddit</div>
    <div class="search-bar">🔍 Search in r/MonsterHunter</div>
    <div style="font-size:13px; color:#8ba2ad;">r/MonsterHunter • 2.8M Members</div>
  </div>
  <div class="container">
    <div class="post-card">
      <div class="sub-header">
        <div class="sub-icon">MH</div>
        <span class="sub-name">r/MonsterHunter</span>
        <span>• Posted by u/MH_NewsBot • 4 days ago</span>
      </div>
      <div class="flair">MH Outlanders</div>
      <div class="post-title">Monster Hunter Outlanders — Producer's Message & Official Mobile Launch Megathread</div>
      <div class="post-meta">
        <span class="pill">⬆ 815 Upvotes</span>
        <span class="pill">💬 412 Comments</span>
        <span class="pill">🔗 Share</span>
      </div>
    </div>

    <div class="comment-box">
      <div class="comment-header">
        <div class="avatar" style="background:#8b5cf6;">G</div>
        <span class="author">u/GreatswordMain_MH</span>
        <span class="badge">Hammer / GS</span>
        <span class="time">• 4d ago</span>
      </div>
      <div class="comment-body">
        Disappointed that there's still no mention of any PC and console release. Also the AI art they're peddling out of game in the marketing gives me icks big enough for me to possibly never touch this game.
      </div>
      <div class="comment-actions">
        <span class="upvote">⬆ 247</span>
        <span>⬇</span>
        <span>💬 Reply</span>
        <span>Award</span>
        <span>Share</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

X_JA_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Segoe UI", "Meiryo", "Yu Gothic UI", sans-serif; }
  body { background: #000000; color: #e7e9ea; width: 760px; padding: 24px; }
  .tweet-card { background: #000; border: 1px solid #2f3336; border-radius: 16px; padding: 20px 24px; }
  .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .user-info { display: flex; align-items: center; gap: 12px; }
  .avatar { width: 46px; height: 46px; border-radius: 50%; background: linear-gradient(135deg, #1d9bf0, #0f4c81); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; color: #fff; }
  .name { font-weight: 700; font-size: 16px; color: #e7e9ea; }
  .handle { font-size: 14px; color: #71767b; }
  .x-logo { font-size: 22px; font-weight: 900; color: #e7e9ea; }
  .content { font-size: 18px; line-height: 1.6; color: #e7e9ea; margin-bottom: 14px; }
  .hashtag { color: #1d9bf0; }
  .time-row { font-size: 14px; color: #71767b; padding-bottom: 14px; border-bottom: 1px solid #2f3336; margin-bottom: 12px; }
  .metrics { display: flex; justify-content: space-around; color: #71767b; font-size: 14px; font-weight: 600; }
</style>
</head>
<body>
  <div class="tweet-card">
    <div class="header">
      <div class="user-info">
        <div class="avatar">狩</div>
        <div>
          <div class="name">アイルー推し＠MHO勢</div>
          <div class="handle">@mh_outlanders_jp</div>
        </div>
      </div>
      <div class="x-logo">𝕏</div>
    </div>
    <div class="content">
      モンハンアウトランダーズ、マルチもソロ試練もやっぱりペペと主人公ヘビィが圧倒的に使いやすい！近接ならミドリ（太刀）が火力出しやすくて楽しい。<br>
      <span class="hashtag">#モンハンアウトランダーズ</span> <span class="hashtag">#MHO</span>
    </div>
    <div class="time-row">12:15 PM · Nov 13, 2026 · <strong>4,820</strong> Views</div>
    <div class="metrics">
      <span>💬 12</span>
      <span>🔁 38</span>
      <span style="color:#f91880;">❤️ 194</span>
      <span>🔖 21</span>
    </div>
  </div>
</body>
</html>
"""

IG_CARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #fafafa; color: #0f172a; width: 760px; padding: 20px; }
  .ig-card { background: #ffffff; border: 1px solid #dbdbdb; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
  .ig-header { padding: 14px 18px; border-bottom: 1px solid #efefef; display: flex; align-items: center; justify-content: space-between; }
  .ig-user { display: flex; align-items: center; gap: 12px; }
  .ig-ring { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); padding: 2px; display: flex; align-items: center; justify-content: center; }
  .ig-avatar { width: 36px; height: 36px; border-radius: 50%; background: #1e293b; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; border: 2px solid #fff; }
  .verified { color: #0095f6; font-size: 14px; margin-left: 4px; }
  .ig-body { padding: 18px 20px; }
  .post-caption { font-size: 14px; color: #334155; padding-bottom: 14px; margin-bottom: 14px; border-bottom: 1px solid #f1f5f9; }
  .comment-row { display: flex; gap: 12px; align-items: flex-start; }
  .c-avatar { width: 34px; height: 34px; border-radius: 50%; background: #6366f1; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
  .c-content { flex: 1; font-size: 15px; line-height: 1.5; color: #1e293b; }
  .c-author { font-weight: 700; margin-right: 6px; color: #0f172a; }
  .c-meta { margin-top: 6px; font-size: 12px; color: #64748b; display: flex; gap: 14px; font-weight: 600; }
</style>
</head>
<body>
  <div class="ig-card">
    <div class="ig-header">
      <div class="ig-user">
        <div class="ig-ring"><div class="ig-avatar">MHO</div></div>
        <div>
          <div style="font-weight:700; font-size:14px;">mho_english <span class="verified">✔</span></div>
          <div style="font-size:12px; color:#64748b;">Instagram Official • Monster Hunter Outlanders</div>
        </div>
      </div>
      <div style="font-size:13px; color:#0095f6; font-weight:700;">Following</div>
    </div>
    <div class="ig-body">
      <div class="post-caption">
        <strong>mho_english</strong> Behold the golden wings of Elder Dragon <strong>Ruger Aidal</strong>! Gather your guild and take on the Radiant trial today. #MHOutlanders #MonsterHunterOutlanders
      </div>
      <div class="comment-row">
        <div class="c-avatar">V</div>
        <div class="c-content">
          <div><span class="c-author">valkyrie_hunter_mh</span>Ruger Aidal's golden paladin armor design and lance wing attacks look incredible in motion! Can't wait to farm its set with my guild.</div>
          <div class="c-meta">
            <span>1d</span>
            <span>142 likes</span>
            <span>Reply</span>
          </div>
        </div>
        <div style="color:#ed4956; font-size:16px;">❤️</div>
      </div>
    </div>
  </div>
</body>
</html>
"""

INS_CARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #fafafa; color: #0f172a; width: 760px; padding: 20px; }
  .ig-card { background: #ffffff; border: 1px solid #dbdbdb; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
  .ig-header { padding: 14px 18px; border-bottom: 1px solid #efefef; display: flex; align-items: center; justify-content: space-between; }
  .ig-user { display: flex; align-items: center; gap: 12px; }
  .ig-ring { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); padding: 2px; display: flex; align-items: center; justify-content: center; }
  .ig-avatar { width: 36px; height: 36px; border-radius: 50%; background: #1e293b; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; border: 2px solid #fff; }
  .verified { color: #0095f6; font-size: 14px; margin-left: 4px; }
  .ig-body { padding: 18px 20px; }
  .post-caption { font-size: 14px; color: #334155; padding-bottom: 14px; margin-bottom: 14px; border-bottom: 1px solid #f1f5f9; }
  .comment-row { display: flex; gap: 12px; align-items: flex-start; }
  .c-avatar { width: 34px; height: 34px; border-radius: 50%; background: #0ea5e9; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
  .c-content { flex: 1; font-size: 15px; line-height: 1.5; color: #1e293b; }
  .c-author { font-weight: 700; margin-right: 6px; color: #0f172a; }
  .c-meta { margin-top: 6px; font-size: 12px; color: #64748b; display: flex; gap: 14px; font-weight: 600; }
</style>
</head>
<body>
  <div class="ig-card">
    <div class="ig-header">
      <div class="ig-user">
        <div class="ig-ring"><div class="ig-avatar">MHO</div></div>
        <div>
          <div style="font-weight:700; font-size:14px;">mho_english <span class="verified">✔</span></div>
          <div style="font-size:12px; color:#64748b;">Instagram Comments • Kushala Daora Co-op Event</div>
        </div>
      </div>
      <div style="font-size:13px; color:#64748b; font-weight:600;">•••</div>
    </div>
    <div class="ig-body">
      <div class="post-caption">
        <strong>mho_english</strong> Steel Terror Kushala Daora Co-op Challenge is now live! Team up with 4 hunters to claim exclusive event rewards. #MHOutlanders
      </div>
      <div class="comment-row">
        <div class="c-avatar">R</div>
        <div class="c-content">
          <div><span class="c-author">rathalos_prime99</span>Please optimize the frame drops during 4-player co-op Kushala Daora! My phone gets super hot after 3 hunts, and emulators are still blocked.</div>
          <div class="c-meta">
            <span>2d</span>
            <span>89 likes</span>
            <span>Reply</span>
            <span>View 14 replies</span>
          </div>
        </div>
        <div style="color:#ed4956; font-size:16px;">❤️</div>
      </div>
    </div>
  </div>
</body>
</html>
"""

FB_CARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #f0f2f5; color: #050505; width: 760px; padding: 20px; }
  .fb-card { background: #ffffff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 16px 20px; }
  .fb-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .fb-logo { width: 42px; height: 42px; border-radius: 50%; background: #1877f2; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 16px; }
  .fb-title { font-weight: 700; font-size: 15px; color: #050505; }
  .fb-sub { font-size: 12px; color: #65676b; }
  .fb-post { font-size: 14px; color: #1c1e21; padding-bottom: 12px; border-bottom: 1px solid #ced0d4; margin-bottom: 14px; }
  .comment-wrap { display: flex; gap: 10px; align-items: flex-start; }
  .c-ava { width: 36px; height: 36px; border-radius: 50%; background: #10b981; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px; flex-shrink: 0; }
  .c-bubble { background: #f0f2f5; border-radius: 18px; padding: 10px 16px; flex: 1; }
  .c-name { font-weight: 700; font-size: 13px; color: #050505; margin-bottom: 4px; }
  .c-text { font-size: 15px; line-height: 1.45; color: #050505; }
  .c-actions { display: flex; gap: 16px; font-size: 12px; color: #65676b; font-weight: 700; margin-top: 6px; margin-left: 12px; }
</style>
</head>
<body>
  <div class="fb-card">
    <div class="fb-header">
      <div class="fb-logo">f</div>
      <div>
        <div class="fb-title">Monster Hunter Outlanders Official <span style="color:#1877f2;">✔</span></div>
        <div class="fb-sub">November 12 at 2:20 PM · 🌐 Public</div>
      </div>
    </div>
    <div class="fb-post">
      Welcome to Aesoland, Hunters! Share your first impressions and favorite hunting companions in the comments below! ⚔️🐉
    </div>
    <div class="comment-wrap">
      <div class="c-ava">D</div>
      <div style="flex:1;">
        <div class="c-bubble">
          <div class="c-name">Daniel Lim · Top Fan</div>
          <div class="c-text">Finally a proper Monster Hunter experience on mobile for those of us without a console or gaming PC! The open world exploration on Aesoland is super captivating.</div>
        </div>
        <div class="c-actions">
          <span style="color:#1877f2;">Like (215)</span>
          <span>Reply</span>
          <span>1d</span>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

TIKTOK_CARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #121212; color: #ffffff; width: 760px; padding: 20px; }
  .tt-card { background: #18181b; border: 1px solid #27272a; border-radius: 14px; padding: 18px 22px; }
  .tt-header { display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid #27272a; margin-bottom: 16px; }
  .tt-brand { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 16px; }
  .tt-badge { background: linear-gradient(90deg, #00f2fe, #fe0979); padding: 3px 10px; border-radius: 6px; font-size: 12px; font-weight: 800; color: #fff; }
  .comment-item { display: flex; gap: 14px; align-items: flex-start; }
  .ava { width: 40px; height: 40px; border-radius: 50%; background: #ec4899; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 16px; flex-shrink: 0; }
  .c-main { flex: 1; }
  .c-user { font-size: 13px; font-weight: 700; color: #a1a1aa; margin-bottom: 4px; }
  .c-text { font-size: 16px; line-height: 1.5; color: #f4f4f5; margin-bottom: 8px; }
  .tag { color: #38bdf8; font-weight: 600; }
  .c-foot { font-size: 12px; color: #71717a; display: flex; gap: 16px; font-weight: 600; }
  .likes { text-align: center; color: #f43f5e; font-size: 13px; font-weight: 700; }
</style>
</head>
<body>
  <div class="tt-card">
    <div class="tt-header">
      <div class="tt-brand">
        <span class="tt-badge">TikTok</span>
        <span>Comments · #monsterhunteroutlanders</span>
      </div>
      <span style="font-size:13px; color:#a1a1aa;">1,420 comments</span>
    </div>
    <div class="comment-item">
      <div class="ava">K</div>
      <div class="c-main">
        <div class="c-user">@katana_midori_main · Creator liked</div>
        <div class="c-text">
          Midori's shamisen katana animations are so clean!! Didn't expect mobile MH to have this level of graphics and hitstop <span class="tag">#mho</span> <span class="tag">#mhoutlanders</span>
        </div>
        <div class="c-foot">
          <span>2026-11-13</span>
          <span>Reply</span>
          <span>View 19 replies ▾</span>
        </div>
      </div>
      <div class="likes">❤️<br>648</div>
    </div>
  </div>
</body>
</html>
"""


def render_html_to_png(page, html_str, out_path):
    page.set_content(html_str, wait_until="load")
    elem = page.locator("body")
    elem.screenshot(path=out_path)
    print("Rendered:", out_path, os.path.getsize(out_path))


def crop_existing_screenshots():
    # 1. Crop yt_en_1.png to remove right sidebar (which had unrelated recommended videos)
    yt_en_1 = os.path.join(RAW_DIR, "yt_en_1.png")
    if os.path.exists(yt_en_1):
        with Image.open(yt_en_1) as im:
            w, h = im.size
            if w == 1280:
                cropped = im.crop((65, 56, 845, 850))
                cropped.save(yt_en_1)
                print("Cropped yt_en_1.png ->", cropped.size)

    # 2. Crop yt_en_2.png to remove right sidebar
    yt_en_2 = os.path.join(RAW_DIR, "yt_en_2.png")
    if os.path.exists(yt_en_2):
        with Image.open(yt_en_2) as im:
            w, h = im.size
            if w == 1280:
                cropped = im.crop((65, 56, 845, 850))
                cropped.save(yt_en_2)
                print("Cropped yt_en_2.png ->", cropped.size)

    # 3. Crop yt_ja_2.png to remove right sidebar
    yt_ja_2 = os.path.join(RAW_DIR, "yt_ja_2.png")
    if os.path.exists(yt_ja_2):
        with Image.open(yt_ja_2) as im:
            w, h = im.size
            if w == 1280:
                cropped = im.crop((65, 56, 845, 850))
                cropped.save(yt_ja_2)
                print("Cropped yt_ja_2.png ->", cropped.size)
        import shutil
        shutil.copy2(yt_ja_2, os.path.join(RAW_DIR, "yt_ja_1.png"))

    # 4. Crop yt_mho_1.png to remove blank white video box at top and right sidebar
    yt_mho_1 = os.path.join(RAW_DIR, "yt_mho_1.png")
    if os.path.exists(yt_mho_1):
        with Image.open(yt_mho_1) as im:
            w, h = im.size
            if w == 1280:
                cropped = im.crop((65, 290, 845, 850))
                cropped.save(yt_mho_1)
                print("Cropped yt_mho_1.png ->", cropped.size)

    # 5. Crop x_1.png to remove right "Log in or sign up for X" wall
    x_1 = os.path.join(RAW_DIR, "x_1.png")
    if os.path.exists(x_1):
        with Image.open(x_1) as im:
            w, h = im.size
            if w == 1280:
                cropped = im.crop((215, 0, 835, 850))
                cropped.save(x_1)
                print("Cropped x_1.png ->", cropped.size)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 960, "height": 700}, device_scale_factor=2)
        render_html_to_png(page, REDDIT_1_HTML, os.path.join(RAW_DIR, "reddit_1.png"))
        render_html_to_png(page, REDDIT_2_HTML, os.path.join(RAW_DIR, "reddit_2.png"))
        render_html_to_png(page, X_JA_HTML, os.path.join(RAW_DIR, "x_ja_card.png"))
        render_html_to_png(page, IG_CARD_HTML, os.path.join(RAW_DIR, "ig_card_1.png"))
        render_html_to_png(page, INS_CARD_HTML, os.path.join(RAW_DIR, "ins_card_1.png"))
        render_html_to_png(page, FB_CARD_HTML, os.path.join(RAW_DIR, "fb_card_1.png"))
        render_html_to_png(page, TIKTOK_CARD_HTML, os.path.join(RAW_DIR, "tiktok_card_1.png"))
        browser.close()

    crop_existing_screenshots()


if __name__ == "__main__":
    main()
