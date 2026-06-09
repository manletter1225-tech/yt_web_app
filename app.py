import os
import re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()
    download_type = data.get('type', 'mp4')

    if not url:
        return jsonify({'success': False, 'error': '請輸入正確的 YouTube 連結！'})

    outtmpl_path = os.path.join(DOWNLOAD_FOLDER, '%(title)s_%(id)s.%(ext)s')

    # 🚀 專為雲端免費伺服器（低記憶體）設計的優化參數
    ydl_opts = {
        'outtmpl': outtmpl_path,
        'nocheckcertificate': True,
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024,  # 限制最大下載 50MB 的影片，防止記憶體爆掉
    }

    if download_type == 'mp4':
        ydl_opts.update({
            # 💡 關鍵優化：直接下載 YouTube 官方已經封裝好、自帶聲音的單一 MP4 檔案（通常是 720p 或 360p）
            # 這樣做完全不需要經過 FFmpeg 合併，速度極快且絕不爆記憶體
            'format': 'ext=mp4[vcodec^=avc1][acodec^=mp4a]/best[ext=mp4]/best',
        })
    else:  # mp3
        ydl_opts.update({
            # 優先下載 M4A 格式音訊（M4A 在手機上與 MP3 一樣可以直接播放）
            # 如果免費伺服器缺少 FFmpeg，M4A 可以直接輸出，不會卡死
            'format': 'm4a/bestaudio/best',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info_dict)
            
            # 安全取得下載後的純檔名
            just_filename = os.path.basename(final_filename)
            
        return jsonify({
            'success': True, 
            'filename': just_filename,
            'download_url': f'/fetch/{just_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/fetch/<filename>')
def fetch_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "檔案不存在", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)