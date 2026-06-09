import os
import re
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# 設定暫存下載資料夾
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
    download_type = data.get('type', 'mp4') # 'mp4' 或 'mp3'

    if not url:
        return jsonify({'success': False, 'error': '請輸入正確的 YouTube 連結！'})

    # 建立唯一的檔名範本
    outtmpl_path = os.path.join(DOWNLOAD_FOLDER, '%(title)s_%(id)s.%(ext)s')

    # yt-dlp 設定
    ydl_opts = {
        'outtmpl': outtmpl_path,
        'nocheckcertificate': True,
        'quiet': True,
    }

    if download_type == 'mp4':
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4'
        })
    else:  # mp3
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info_dict)
            
            # 如果是 MP3，手動導正副檔名
            if download_type == 'mp3':
                final_filename = os.path.splitext(final_filename)[0] + '.mp3'
            
            # 安全取得下載後的純檔名
            just_filename = os.path.basename(final_filename)
            
        return jsonify({
            'success': True, 
            'filename': just_filename,
            'download_url': f'/fetch/{just_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 供前端瀏覽器下載實體檔案的路由
@app.route('/fetch/<filename>')
def fetch_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        # as_attachment=True 會強制瀏覽器跳出「下載/儲存」視窗，而不是直接在網頁播放
        return send_file(file_path, as_attachment=True)
    return "檔案不存在", 404

if __name__ == '__main__':
    # 預設在本機執行
    app.run(debug=True, host='0.0.0.0', port=5000)