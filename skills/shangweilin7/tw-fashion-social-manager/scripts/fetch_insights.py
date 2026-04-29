"""
Meta Social Insights Fetcher
用途：每週自動抓取 IG / FB / Threads 數據，輸出 Excel 供 agent 分析
執行：python3 fetch_insights.py
輸出：~/.openclaw/workspace/socialMediaManager/reports/weekly_insights_YYYY-MM-DD.xlsx
"""

import os
import requests
import pandas as pd
from datetime import datetime

# --- 1. 從環境變數讀取設定 ---
ACCESS_TOKEN    = os.environ.get('META_ACCESS_TOKEN')
CLIENT_ID       = os.environ.get('META_CLIENT_ID')
CLIENT_SECRET   = os.environ.get('META_CLIENT_SECRET')
IG_ACCOUNT_SLUG = os.environ.get('META_IG_ACCOUNT_ID')  # 可能是 username 或 numeric ID
PAGE_ID         = os.environ.get('META_PAGE_ID')

API_VERSION       = 'v25.0'
BASE_URL          = f'https://graph.facebook.com/{API_VERSION}'
OUTPUT_DIR        = os.path.expanduser('~/.openclaw/workspace/socialMediaManager/reports')

# 執行時動態填入
PAGE_ACCESS_TOKEN = None
IG_ACCOUNT_ID     = None


# --- 2. Token 自動刷新（短效 → 長效）---
def refresh_access_token(token):
    url = f'{BASE_URL}/oauth/access_token'
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'fb_exchange_token': token,
    }
    resp = requests.get(url, params=params).json()
    new_token = resp.get('access_token')
    if new_token:
        print('✅ Token 刷新成功')
        return new_token
    print(f'⚠️ Token 刷新失敗：{resp}')
    return token


# --- 3. 取得 Page Access Token ---
# FB Page insights 必須用 Page Access Token，User Token 會回 200 但數據為空或報錯
def get_page_access_token(user_token):
    url = f'{BASE_URL}/{PAGE_ID}'
    params = {
        'fields': 'access_token',
        'access_token': user_token,
    }
    resp = requests.get(url, params=params).json()
    token = resp.get('access_token')
    if token:
        print('✅ Page Access Token 取得成功')
        return token
    print(f'⚠️ 無法取得 Page Access Token：{resp}')
    return user_token  # fallback，部分權限仍可運作


# --- 4. 解析 IG Business Account 數字 ID ---
# META_IG_ACCOUNT_ID 若設為 username（如 shop_real_live_authentic）需轉換
def get_ig_business_account_id(page_token):
    if IG_ACCOUNT_SLUG and IG_ACCOUNT_SLUG.isdigit():
        return IG_ACCOUNT_SLUG

    url = f'{BASE_URL}/{PAGE_ID}'
    params = {
        'fields': 'instagram_business_account',
        'access_token': page_token,
    }
    resp = requests.get(url, params=params).json()
    ig_id = resp.get('instagram_business_account', {}).get('id')
    if ig_id:
        print(f'✅ IG Business Account ID: {ig_id}')
        return ig_id
    print(f'⚠️ 無法取得 IG Business Account ID：{resp}')
    return None


# --- 5. 安全取出 insights 數值 ---
def extract_metric(ins_data, name, default=0):
    for m in ins_data:
        if m.get('name') == name:
            values = m.get('values', [])
            if values:
                return values[0].get('value', default)
    return default


# --- 6. Instagram Reels ---
def get_ig_reels():
    if not IG_ACCOUNT_ID:
        print('⚠️ 跳過 IG Reels：找不到有效的 IG Account ID')
        return []

    url = f'{BASE_URL}/{IG_ACCOUNT_ID}/media'
    params = {
        'fields': 'id,caption,media_type,timestamp,permalink',
        'access_token': ACCESS_TOKEN,
        'limit': 20,
    }
    response = requests.get(url, params=params).json()
    if 'error' in response:
        print(f'⚠️ IG media 抓取失敗：{response["error"].get("message")}')
        return []

    reels = [m for m in response.get('data', []) if m.get('media_type') == 'VIDEO']
    rows = []
    for reel in reels:
        ins_url = f'{BASE_URL}/{reel["id"]}/insights'
        ins_params = {
            # v21+ 起 saves → saved
            'metric': 'reach,plays,ig_reels_avg_watch_time,ig_reels_video_view_total_time,likes,comments,saved,shares',
            'access_token': ACCESS_TOKEN,
        }
        ins = requests.get(ins_url, params=ins_params).json()
        data = ins.get('data', [])

        reach      = extract_metric(data, 'reach')
        plays      = extract_metric(data, 'plays') or 1
        likes      = extract_metric(data, 'likes')
        comments   = extract_metric(data, 'comments')
        saves      = extract_metric(data, 'saved')
        shares     = extract_metric(data, 'shares')
        avg_watch  = extract_metric(data, 'ig_reels_avg_watch_time')
        engagement = likes + comments + saves + shares

        rows.append({
            '平台': 'Instagram Reels',
            '發布時間': reel['timestamp'],
            '內容摘要': (reel.get('caption') or '')[:30],
            '連結': reel.get('permalink', ''),
            '觸及人數': reach,
            '播放次數': plays,
            '平均觀看時長(秒)': round(avg_watch / 1000, 2) if avg_watch else 0,
            '按讚數': likes,
            '留言數': comments,
            '收藏數': saves,
            '分享數': shares,
            '互動總數': engagement,
            '互動率(%)': round(engagement / reach * 100, 2) if reach else 0,
        })
    return rows


# --- 7. Instagram 一般貼文（輪播 / 靜態圖）---
def get_ig_posts():
    if not IG_ACCOUNT_ID:
        print('⚠️ 跳過 IG 貼文：找不到有效的 IG Account ID')
        return []

    url = f'{BASE_URL}/{IG_ACCOUNT_ID}/media'
    params = {
        'fields': 'id,caption,media_type,timestamp,permalink',
        'access_token': ACCESS_TOKEN,
        'limit': 20,
    }
    response = requests.get(url, params=params).json()
    if 'error' in response:
        print(f'⚠️ IG posts 抓取失敗：{response["error"].get("message")}')
        return []

    posts = [m for m in response.get('data', []) if m.get('media_type') in ('IMAGE', 'CAROUSEL_ALBUM')]
    rows = []
    for post in posts:
        ins_url = f'{BASE_URL}/{post["id"]}/insights'
        ins_params = {
            'metric': 'reach,impressions,likes,comments,saved,shares',
            'access_token': ACCESS_TOKEN,
        }
        ins = requests.get(ins_url, params=ins_params).json()
        data = ins.get('data', [])

        reach      = extract_metric(data, 'reach')
        likes      = extract_metric(data, 'likes')
        comments   = extract_metric(data, 'comments')
        saves      = extract_metric(data, 'saved')
        shares     = extract_metric(data, 'shares')
        engagement = likes + comments + saves + shares

        rows.append({
            '平台': f'Instagram {post["media_type"]}',
            '發布時間': post['timestamp'],
            '內容摘要': (post.get('caption') or '')[:30],
            '連結': post.get('permalink', ''),
            '觸及人數': reach,
            '播放次數': extract_metric(data, 'impressions'),
            '平均觀看時長(秒)': None,
            '按讚數': likes,
            '留言數': comments,
            '收藏數': saves,
            '分享數': shares,
            '互動總數': engagement,
            '互動率(%)': round(engagement / reach * 100, 2) if reach else 0,
        })
    return rows


# --- 8. Facebook 粉專貼文 ---
def get_fb_posts():
    url = f'{BASE_URL}/{PAGE_ID}/posts'
    params = {
        'fields': 'id,message,created_time,permalink_url',
        'access_token': PAGE_ACCESS_TOKEN,
        'limit': 20,
    }
    response = requests.get(url, params=params).json()
    if 'error' in response:
        print(f'⚠️ FB posts 抓取失敗：{response["error"].get("message")}')
        return []

    rows = []
    for post in response.get('data', []):
        ins_url = f'{BASE_URL}/{post["id"]}/insights'
        ins_params = {
            'metric': 'post_impressions_unique,post_engaged_users,post_reactions_like_total,post_clicks',
            'period': 'lifetime',  # 不加 period 會回空 values
            'access_token': PAGE_ACCESS_TOKEN,
        }
        ins = requests.get(ins_url, params=ins_params).json()
        data = ins.get('data', [])

        reach    = extract_metric(data, 'post_impressions_unique')
        engaged  = extract_metric(data, 'post_engaged_users')

        rows.append({
            '平台': 'Facebook',
            '發布時間': post['created_time'],
            '內容摘要': (post.get('message') or '')[:30],
            '連結': post.get('permalink_url', ''),
            '觸及人數': reach,
            '播放次數': None,
            '平均觀看時長(秒)': None,
            '按讚數': extract_metric(data, 'post_reactions_like_total'),
            '留言數': None,
            '收藏數': None,
            '分享數': None,
            '互動總數': engaged,
            '互動率(%)': round(engaged / reach * 100, 2) if reach else 0,
        })
    return rows


# --- 9. Threads（optional，失敗時靜默略過）---
def get_threads_posts():
    if not IG_ACCOUNT_ID:
        return []

    url = f'{BASE_URL}/{IG_ACCOUNT_ID}/threads'
    params = {
        'fields': 'id,text,timestamp,permalink',
        'access_token': ACCESS_TOKEN,
        'limit': 20,
    }
    response = requests.get(url, params=params).json()
    if 'error' in response:
        print(f'ℹ️ Threads 數據不可用（{response["error"].get("message", "")}），略過')
        return []

    rows = []
    for post in response.get('data', []):
        ins_url = f'{BASE_URL}/{post["id"]}/insights'
        ins_params = {
            'metric': 'views,likes,replies,reposts,quotes',
            'access_token': ACCESS_TOKEN,
        }
        ins = requests.get(ins_url, params=ins_params).json()
        data = ins.get('data', [])

        views      = extract_metric(data, 'views')
        likes      = extract_metric(data, 'likes')
        replies    = extract_metric(data, 'replies')
        reposts    = extract_metric(data, 'reposts')
        quotes     = extract_metric(data, 'quotes')
        engagement = likes + replies + reposts + quotes

        rows.append({
            '平台': 'Threads',
            '發布時間': post['timestamp'],
            '內容摘要': (post.get('text') or '')[:30],
            '連結': post.get('permalink', ''),
            '觸及人數': views,
            '播放次數': None,
            '平均觀看時長(秒)': None,
            '按讚數': likes,
            '留言數': replies,
            '收藏數': reposts,
            '分享數': quotes,
            '互動總數': engagement,
            '互動率(%)': round(engagement / views * 100, 2) if views else 0,
        })
    return rows


# --- 10. 主程式 ---
def main():
    global ACCESS_TOKEN, PAGE_ACCESS_TOKEN, IG_ACCOUNT_ID

    if not ACCESS_TOKEN:
        print('❌ 找不到 META_ACCESS_TOKEN，請在 .env 中設定')
        return
    if not PAGE_ID:
        print('❌ 找不到 META_PAGE_ID，請在 .env 中設定')
        return

    ACCESS_TOKEN      = refresh_access_token(ACCESS_TOKEN)
    PAGE_ACCESS_TOKEN = get_page_access_token(ACCESS_TOKEN)
    IG_ACCOUNT_ID     = get_ig_business_account_id(PAGE_ACCESS_TOKEN)

    print('📥 抓取 Instagram Reels...')
    ig_reels = get_ig_reels()

    print('📥 抓取 Instagram 貼文...')
    ig_posts = get_ig_posts()

    print('📥 抓取 Facebook 貼文...')
    fb_posts = get_fb_posts()

    print('📥 抓取 Threads 貼文...')
    threads_posts = get_threads_posts()

    all_data = ig_reels + ig_posts + fb_posts + threads_posts
    if not all_data:
        print('⚠️ 沒有抓到任何數據，請確認 token 與帳號設定是否正確')
        return

    df = pd.DataFrame(all_data)
    # 統一轉為台灣時區顯示
    df['發布時間'] = (
        pd.to_datetime(df['發布時間'], utc=True)
        .dt.tz_convert('Asia/Taipei')
        .dt.strftime('%Y-%m-%d %H:%M')
    )
    df = df.sort_values('發布時間', ascending=False)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    output_path = os.path.join(OUTPUT_DIR, f'weekly_insights_{today}.xlsx')
    df.to_excel(output_path, index=False)

    print(f'✅ 報告已輸出：{output_path}')
    print(f'   共 {len(all_data)} 筆貼文數據')


if __name__ == '__main__':
    main()
