import os
import uuid
import tempfile
import traceback
import requests
import json
import time
from flask import Flask, render_template, request, jsonify, send_file, Response
from moviepy.editor import VideoFileClip

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

# Pasta temporária para armazenar downloads
TEMP_DIR = tempfile.gettempdir()

# Headers para simular navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.tiktok.com/',
}


def get_video_info_tikwm(url):
    """
    Obtém informações do vídeo usando a API tikwm.com
    """
    try:
        api_url = "https://www.tikwm.com/api/"
        params = {
            'url': url,
            'count': 12,
            'cursor': 0,
            'web': 1,
            'hd': 1
        }
        
        response = requests.post(api_url, data=params, headers=HEADERS, timeout=30)
        data = response.json()
        
        if data.get('code') == 0 and data.get('data'):
            video_data = data['data']
            
            def fix_url(url_value):
                if url_value and not url_value.startswith('http'):
                    return 'https://www.tikwm.com' + url_value
                return url_value
            
            return {
                'success': True,
                'video_url': fix_url(video_data.get('play')),
                'video_url_hd': fix_url(video_data.get('hdplay')),
                'video_url_wm': fix_url(video_data.get('wmplay')),
                'music_url': fix_url(video_data.get('music')),
                'title': video_data.get('title', 'TikTok Video'),
                'author': video_data.get('author', {}).get('nickname', 'Unknown'),
                'cover': fix_url(video_data.get('cover'))
            }
        else:
            return {
                'success': False,
                'error': data.get('msg', 'Erro ao obter informações do vídeo')
            }
    
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Tempo limite excedido. Tente novamente.'}
    except Exception as e:
        return {'success': False, 'error': f'Erro: {str(e)}'}


def download_video_from_url(video_url, filename, progress_callback=None):
    """
    Baixa o vídeo com progresso
    """
    try:
        filepath = os.path.join(TEMP_DIR, filename)
        
        response = requests.get(video_url, headers=HEADERS, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        progress_callback(percent)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {'success': True, 'filepath': filepath, 'filename': filename}
        else:
            return {'success': False, 'error': 'Arquivo vazio'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def extract_audio_from_video(video_path, audio_filename):
    """
    Extrai áudio do vídeo
    """
    try:
        audio_path = os.path.join(TEMP_DIR, audio_filename)
        video = VideoFileClip(video_path)
        
        if video.audio is None:
            video.close()
            return {'success': False, 'error': 'Este vídeo não possui áudio'}
        
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()
        
        return {'success': True, 'audio_path': audio_path, 'audio_filename': audio_filename}
    
    except Exception as e:
        return {'success': False, 'error': f'Erro ao extrair áudio: {str(e)}'}


def clean_temp_file(filepath):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download_stream')
def download_stream():
    """
    Endpoint SSE para download com progresso em tempo real
    """
    url = request.args.get('url', '').strip()
    
    def generate():
        try:
            # Etapa 1: Validação
            yield f"data: {json.dumps({'step': 'validating', 'progress': 5, 'message': '🔍 Validando link...'})}\n\n"
            time.sleep(0.3)
            
            if not url:
                yield f"data: {json.dumps({'step': 'error', 'message': 'URL não fornecida'})}\n\n"
                return
            
            if 'tiktok.com' not in url and 'vm.tiktok.com' not in url:
                yield f"data: {json.dumps({'step': 'error', 'message': 'URL inválida do TikTok'})}\n\n"
                return
            
            # Etapa 2: Buscando informações
            yield f"data: {json.dumps({'step': 'fetching', 'progress': 15, 'message': '📡 Conectando ao TikTok...'})}\n\n"
            time.sleep(0.3)
            
            yield f"data: {json.dumps({'step': 'fetching', 'progress': 25, 'message': '🔎 Buscando informações do vídeo...'})}\n\n"
            
            info = get_video_info_tikwm(url)
            
            if not info.get('success'):
                yield f"data: {json.dumps({'step': 'error', 'message': info.get('error', 'Erro ao buscar vídeo')})}\n\n"
                return
            
            title = info.get('title', 'TikTok Video')
            author = info.get('author', 'Unknown')
            
            yield f"data: {json.dumps({'step': 'found', 'progress': 35, 'message': f'✅ Vídeo encontrado: {title[:50]}...', 'title': title, 'author': author})}\n\n"
            time.sleep(0.3)
            
            # Etapa 3: Preparando download
            yield f"data: {json.dumps({'step': 'preparing', 'progress': 40, 'message': '📦 Preparando download HD...'})}\n\n"
            
            video_url = info.get('video_url_hd') or info.get('video_url')
            
            if not video_url:
                yield f"data: {json.dumps({'step': 'error', 'message': 'URL do vídeo não encontrada'})}\n\n"
                return
            
            video_id = uuid.uuid4().hex
            filename = f"tiktok_video_{video_id}.mp4"
            
            # Etapa 4: Baixando
            yield f"data: {json.dumps({'step': 'downloading', 'progress': 45, 'message': '⬇️ Baixando vídeo sem marca dágua...'})}\n\n"
            
            # Download com progresso simulado (já que não podemos usar callback com SSE facilmente)
            filepath = os.path.join(TEMP_DIR, filename)
            
            try:
                response = requests.get(video_url, headers=HEADERS, stream=True, timeout=60)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                last_percent = 45
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                # Progresso de 45 a 90
                                percent = 45 + int((downloaded / total_size) * 45)
                                if percent > last_percent + 5:  # Atualiza a cada 5%
                                    last_percent = percent
                                    yield f"data: {json.dumps({'step': 'downloading', 'progress': percent, 'message': f'⬇️ Baixando... {percent}%'})}\n\n"
                
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    yield f"data: {json.dumps({'step': 'finalizing', 'progress': 95, 'message': '✨ Finalizando...'})}\n\n"
                    time.sleep(0.2)
                    
                    yield f"data: {json.dumps({'step': 'complete', 'progress': 100, 'message': '🎉 Download concluído!', 'video_filename': filename, 'title': title, 'author': author})}\n\n"
                else:
                    yield f"data: {json.dumps({'step': 'error', 'message': 'Erro ao salvar o vídeo'})}\n\n"
                    
            except Exception as e:
                # Tentar URL alternativa
                yield f"data: {json.dumps({'step': 'retrying', 'progress': 50, 'message': '🔄 Tentando servidor alternativo...'})}\n\n"
                
                alt_url = info.get('video_url') if video_url == info.get('video_url_hd') else info.get('video_url_wm')
                if alt_url:
                    try:
                        response = requests.get(alt_url, headers=HEADERS, stream=True, timeout=60)
                        response.raise_for_status()
                        
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=32768):
                                if chunk:
                                    f.write(chunk)
                        
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            yield f"data: {json.dumps({'step': 'complete', 'progress': 100, 'message': '🎉 Download concluído!', 'video_filename': filename, 'title': title, 'author': author})}\n\n"
                        else:
                            yield f"data: {json.dumps({'step': 'error', 'message': 'Erro ao baixar vídeo'})}\n\n"
                    except:
                        yield f"data: {json.dumps({'step': 'error', 'message': f'Erro no download: {str(e)}'})}\n\n"
                else:
                    yield f"data: {json.dumps({'step': 'error', 'message': f'Erro no download: {str(e)}'})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': f'Erro: {str(e)}'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/download', methods=['POST'])
def download():
    """Mantido para compatibilidade"""
    try:
        url = request.form.get('url', '').strip()
        
        if not url or ('tiktok.com' not in url and 'vm.tiktok.com' not in url):
            return jsonify({'success': False, 'error': 'URL inválida'})
        
        info = get_video_info_tikwm(url)
        if not info.get('success'):
            return jsonify(info)
        
        video_url = info.get('video_url_hd') or info.get('video_url')
        if not video_url:
            return jsonify({'success': False, 'error': 'URL do vídeo não encontrada'})
        
        video_id = uuid.uuid4().hex
        filename = f"tiktok_video_{video_id}.mp4"
        
        result = download_video_from_url(video_url, filename)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'video_filename': filename,
                'title': info.get('title', 'TikTok Video'),
                'author': info.get('author', '')
            })
        else:
            return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/extract_audio', methods=['POST'])
def extract_audio_route():
    try:
        video_filename = request.form.get('video_filename', '').strip()
        
        if not video_filename:
            return jsonify({'success': False, 'error': 'Arquivo não fornecido'})
        
        video_path = os.path.join(TEMP_DIR, video_filename)
        
        if not os.path.exists(video_path):
            return jsonify({'success': False, 'error': 'Vídeo não encontrado'})
        
        audio_filename = video_filename.replace('.mp4', '.mp3').replace('video', 'audio')
        result = extract_audio_from_video(video_path, audio_filename)
        
        if result.get('success'):
            return jsonify({'success': True, 'audio_filename': result.get('audio_filename')})
        else:
            return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/get_file/<filename>')
def get_file(filename):
    try:
        filename = os.path.basename(filename)
        filepath = os.path.join(TEMP_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        custom_name = request.args.get('name', '').strip()
        
        def sanitize_filename(name):
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                name = name.replace(char, '')
            name = ' '.join(name.split())[:100]
            return name if name else None
        
        if filename.endswith('.mp4'):
            mimetype = 'video/mp4'
            ext = '.mp4'
            default_name = 'tiktok_video.mp4'
        elif filename.endswith('.mp3'):
            mimetype = 'audio/mpeg'
            ext = '.mp3'
            default_name = 'tiktok_audio.mp3'
        else:
            mimetype = 'application/octet-stream'
            ext = ''
            default_name = filename
        
        if custom_name:
            sanitized = sanitize_filename(custom_name)
            download_name = (sanitized + ext) if sanitized else default_name
        else:
            download_name = default_name
        
        return send_file(filepath, mimetype=mimetype, as_attachment=True, download_name=download_name)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/cleanup', methods=['POST'])
def cleanup():
    try:
        data = request.get_json() or {}
        filenames = data.get('filenames', [])
        
        for filename in filenames:
            if filename:
                filepath = os.path.join(TEMP_DIR, os.path.basename(filename))
                clean_temp_file(filepath)
        
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})


if __name__ == '__main__':
    print(f"Pasta temporária: {TEMP_DIR}")
    print("Servidor iniciado em http://127.0.0.1:5000")
    app.run(debug=True, port=5000, threaded=True)