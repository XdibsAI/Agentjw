#!/bin/bash

# Text to Video App - Auto Install Script
# For Ubuntu/Debian VPS with 4GB RAM

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Get VPS IP address
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')

print_status "Starting Text-to-Video App Installation on VPS: $VPS_IP"
print_warning "This installation will take 10-15 minutes. Please be patient!"

# Step 1: Update system
print_step "Step 1: Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y

# Step 2: Install dependencies
print_step "Step 2: Installing system dependencies..."
apt install -y python3 python3-pip python3-venv redis-server nginx ffmpeg git curl software-properties-common

# Step 3: Create application directory
print_step "Step 3: Creating application directory..."
mkdir -p /var/www/textovideo
cd /var/www/textovideo

# Step 4: Create virtual environment
print_step "Step 4: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 5: Create requirements.txt and install packages
print_step "Step 5: Installing Python packages (this may take 5-10 minutes)..."
cat > requirements.txt << 'EOF'
Flask==2.3.3
moviepy==1.0.3
Pillow==10.0.1
redis==5.0.1
celery==5.3.4
gunicorn==21.2.0
EOF

pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Create directories
print_step "Step 6: Creating necessary directories..."
mkdir -p temp_videos templates static logs

# Step 7: Create main application file
print_step "Step 7: Creating Flask application..."
cat > app.py << 'EOF'
from flask import Flask, request, render_template, jsonify, send_file
import os
import uuid
import redis
from celery import Celery
import json
from datetime import datetime, timedelta
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'textovideo-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'temp_videos'
app.config['MAX_VIDEO_DURATION'] = 60
app.config['MAX_TEXT_LENGTH'] = 500

redis_client = redis.Redis(host='localhost', port=6379, db=0)
celery = Celery(app.name, broker='redis://localhost:6379')
celery.conf.update(app.config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        duration = min(int(data.get('duration', 30)), app.config['MAX_VIDEO_DURATION'])
        background_color = data.get('background_color', '#000000')
        text_color = data.get('text_color', '#ffffff')
        font_size = min(int(data.get('font_size', 48)), 72)
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        if len(text) > app.config['MAX_TEXT_LENGTH']:
            return jsonify({'error': 'Text too long'}), 400
        
        job_id = str(uuid.uuid4())
        
        task = generate_video_task.delay(
            job_id, text, duration, background_color, text_color, font_size
        )
        
        job_info = {
            'job_id': job_id,
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'text_preview': text[:50] + '...' if len(text) > 50 else text
        }
        redis_client.setex(f"job:{job_id}", timedelta(hours=2), json.dumps(job_info))
        
        return jsonify({
            'job_id': job_id,
            'message': 'Video generation started',
            'estimated_time': f"{duration // 10 + 5} seconds"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<job_id>')
def check_status(job_id):
    try:
        job_data = redis_client.get(f"job:{job_id}")
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = json.loads(job_data)
        return jsonify(job_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<job_id>')
def download_video(job_id):
    try:
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}.mp4")
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video not found'}), 404
        
        return send_file(video_path, as_attachment=True, download_name=f"video_{job_id}.mp4")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@celery.task
def generate_video_task(job_id, text, duration, bg_color, text_color, font_size):
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        import gc
        
        update_job_status(job_id, 'processing', 'Generating video...')
        
        bg_clip = ColorClip(size=(1280, 720), color=hex_to_rgb(bg_color), duration=duration)
        
        wrapped_text = wrap_text(text, 40)
        
        txt_clip = TextClip(
            wrapped_text,
            fontsize=font_size,
            color=text_color,
            font='Arial',
            method='caption',
            size=(1100, 600),
            align='center'
        ).set_position('center').set_duration(duration)
        
        if duration > 10:
            txt_clip = txt_clip.crossfadein(2).crossfadeout(2)
        
        final_clip = CompositeVideoClip([bg_clip, txt_clip])
        
        output_path = os.path.join('temp_videos', f"{job_id}.mp4")
        
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            bitrate='1000k',
            preset='fast',
            threads=2,
            verbose=False,
            logger=None
        )
        
        bg_clip.close()
        txt_clip.close()
        final_clip.close()
        del bg_clip, txt_clip, final_clip
        gc.collect()
        
        update_job_status(job_id, 'completed', f'Video ready for download')
        
        cleanup_file.apply_async(args=[output_path], countdown=3600)
        
        return f"Video generated successfully: {output_path}"
        
    except Exception as e:
        update_job_status(job_id, 'failed', f'Error: {str(e)}')
        return f"Error generating video: {str(e)}"

@celery.task
def cleanup_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        pass

def update_job_status(job_id, status, message):
    try:
        job_data = redis_client.get(f"job:{job_id}")
        if job_data:
            job_info = json.loads(job_data)
            job_info['status'] = status
            job_info['message'] = message
            job_info['updated_at'] = datetime.now().isoformat()
            redis_client.setex(f"job:{job_id}", timedelta(hours=2), json.dumps(job_info))
    except Exception as e:
        pass

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def wrap_text(text, width):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def cleanup_old_files():
    try:
        temp_dir = app.config['UPLOAD_FOLDER']
        current_time = datetime.now()
        
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if current_time - file_time > timedelta(hours=2):
                    os.remove(file_path)
                    
    except Exception as e:
        pass

if __name__ == '__main__':
    cleanup_old_files()
    app.run(debug=False, host='0.0.0.0', port=5000)
EOF

# Step 8: Create HTML template
print_step "Step 8: Creating web interface..."
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text to Video Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        input, textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea {
            height: 120px;
            resize: vertical;
            font-family: inherit;
        }
        .color-input {
            width: 60px;
            height: 50px;
            padding: 0;
            border: 3px solid #e1e5e9;
            cursor: pointer;
            border-radius: 10px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .char-counter {
            font-size: 12px;
            color: #666;
            text-align: right;
            margin-top: 5px;
        }
        .generate-btn {
            width: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
            font-weight: 600;
            transition: transform 0.2s ease;
        }
        .generate-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .generate-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .progress {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            display: none;
            text-align: center;
        }
        .progress.show { display: block; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .download-btn {
            background: linear-gradient(45deg, #56ab2f, #a8e6cf);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            margin-top: 15px;
            transition: transform 0.2s ease;
        }
        .download-btn:hover {
            transform: translateY(-2px);
        }
        .error {
            color: #e74c3c;
            background: rgba(231, 76, 60, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 4px solid #e74c3c;
        }
        .success {
            color: #27ae60;
            background: rgba(39, 174, 96, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 4px solid #27ae60;
        }
        @media (max-width: 768px) {
            .container { padding: 20px; }
            .form-row { grid-template-columns: 1fr; }
            h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Text to Video</h1>
        <p class="subtitle">Transform your text into engaging videos instantly!</p>
        
        <form id="videoForm">
            <div class="form-group">
                <label for="text">📝 Your Text Content</label>
                <textarea id="text" name="text" placeholder="Enter your amazing text here..." maxlength="500" required></textarea>
                <div class="char-counter">Characters: <span id="charCount">0</span>/500</div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="duration">⏱️ Duration (seconds)</label>
                    <input type="number" id="duration" name="duration" min="5" max="60" value="30" required>
                </div>
                <div class="form-group">
                    <label for="fontSize">🔤 Font Size</label>
                    <input type="number" id="fontSize" name="fontSize" min="20" max="72" value="48" required>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="backgroundColor">🎨 Background Color</label>
                    <input type="color" id="backgroundColor" name="backgroundColor" value="#000000" class="color-input">
                </div>
                <div class="form-group">
                    <label for="textColor">✏️ Text Color</label>
                    <input type="color" id="textColor" name="textColor" value="#ffffff" class="color-input">
                </div>
            </div>
            
            <button type="submit" id="generateBtn" class="generate-btn">
                🚀 Generate Video
            </button>
        </form>
        
        <div id="progress" class="progress">
            <div class="spinner"></div>
            <div id="status" style="font-weight: bold; margin-bottom: 10px;">Processing your video...</div>
            <div id="message"></div>
            <button id="downloadBtn" class="download-btn" style="display: none;">📥 Download Video</button>
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
    </div>

    <script>
        let currentJobId = null;
        let statusInterval = null;

        document.getElementById('text').addEventListener('input', function() {
            const count = this.value.length;
            document.getElementById('charCount').textContent = count;
            document.getElementById('charCount').style.color = count > 450 ? '#e74c3c' : '#666';
        });

        document.getElementById('videoForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                text: document.getElementById('text').value,
                duration: parseInt(document.getElementById('duration').value),
                background_color: document.getElementById('backgroundColor').value,
                text_color: document.getElementById('textColor').value,
                font_size: parseInt(document.getElementById('fontSize').value)
            };
            
            generateVideo(formData);
        });

        async function generateVideo(formData) {
            try {
                const generateBtn = document.getElementById('generateBtn');
                generateBtn.disabled = true;
                generateBtn.textContent = '⏳ Processing...';
                
                document.getElementById('progress').classList.add('show');
                document.getElementById('error').style.display = 'none';
                
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'Unknown error occurred');
                }
                
                currentJobId = result.job_id;
                document.getElementById('message').textContent = `Estimated time: ${result.estimated_time}`;
                
                statusInterval = setInterval(checkStatus, 2000);
                
            } catch (error) {
                showError(error.message);
                resetForm();
            }
        }

        async function checkStatus() {
            if (!currentJobId) return;
            
            try {
                const response = await fetch(`/status/${currentJobId}`);
                const status = await response.json();
                
                document.getElementById('status').textContent = `Status: ${status.status.toUpperCase()}`;
                document.getElementById('message').textContent = status.message || '';
                
                if (status.status === 'completed') {
                    clearInterval(statusInterval);
                    document.getElementById('progress').innerHTML = `
                        <div class="success" style="margin: 0;">
                            ✅ Video generated successfully!
                        </div>
                        <button id="downloadBtn" class="download-btn" onclick="downloadVideo('${currentJobId}')">
                            📥 Download Your Video
                        </button>
                    `;
                    resetForm();
                } else if (status.status === 'failed') {
                    clearInterval(statusInterval);
                    showError(status.message || 'Video generation failed');
                    resetForm();
                }
                
            } catch (error) {
                console.error('Error checking status:', error);
            }
        }

        function downloadVideo(jobId) {
            const link = document.createElement('a');
            link.href = `/download/${jobId}`;
            link.download = `video_${jobId}.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function showError(message) {
            document.getElementById('error').textContent = `❌ ${message}`;
            document.getElementById('error').style.display = 'block';
            document.getElementById('progress').classList.remove('show');
        }

        function resetForm() {
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.disabled = false;
            generateBtn.textContent = '🚀 Generate Video';
        }
    </script>
</body>
</html>
EOF

# Step 9: Set up Redis
print_step "Step 9: Configuring Redis..."
systemctl start redis-server
systemctl enable redis-server

# Test Redis
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis is running successfully"
else
    print_error "Redis failed to start"
    exit 1
fi

# Step 10: Create systemd services
print_step "Step 10: Creating system services..."

# Flask app service
cat > /etc/systemd/system/textovideo.service << EOF
[Unit]
Description=Text to Video Flask App
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/textovideo
Environment="PATH=/var/www/textovideo/venv/bin"
ExecStart=/var/www/textovideo/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app --timeout 300
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Celery worker service
cat > /etc/systemd/system/celery-textovideo.service << EOF
[Unit]
Description=Celery Worker for Text to Video
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/textovideo
Environment="PATH=/var/www/textovideo/venv/bin"
ExecStart=/var/www/textovideo/venv/bin/celery -A app.celery worker --loglevel=info --concurrency=1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Step 11: Configure Nginx
print_step "Step 11: Configuring Nginx..."
cat > /etc/nginx/sites-available/textovideo << EOF
server {
    listen 80;
    server_name $VPS_IP;
    
    client_max_body_size 50M;
    client_body_timeout 300s;
    proxy_read_timeout 300s;
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site and remove default
ln -sf /etc/nginx/sites-available/textovideo /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
if nginx -t; then
    print_status "Nginx configuration is valid"
else
    print_error "Nginx configuration is invalid"
    exit 1
fi

# Step 12: Set permissions
print_step "Step 12: Setting file permissions..."
chown -R www-data:www-data /var/www/textovideo
chmod -R 755 /var/www/textovideo

# Step 13: Start all services
print_step "Step 13: Starting all services..."
systemctl daemon-reload

# Start and enable services
systemctl start textovideo
systemctl start celery-textovideo
systemctl enable textovideo
systemctl enable celery-textovideo
systemctl restart nginx

# Step 14: Wait for services to start
print_step "Step 14: Waiting for services to start..."
sleep 5

# Step 15: Check service status
print_step "Step 15: Checking service status..."
services_ok=true

if systemctl is-active --quiet textovideo; then
    print_status "✅ Flask app is running"
else
    print_error "❌ Flask app failed to start"
    services_ok=false
fi

if systemctl is-active --quiet celery-textovideo; then
    print_status "✅ Celery worker is running"
else
    print_error "❌ Celery worker failed to start"
    services_ok=false
fi

if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx failed to start"
    services_ok=false
fi

# Step 16: Create monitoring script
print_step "Step 16: Creating monitoring tools..."
cat > /var/www/textovideo/monitor.py << 'EOF'
#!/usr/bin/env python3
import psutil
import redis
import subprocess
import sys
from datetime import datetime

def check_services():
    services = ['textovideo', 'celery-textovideo', 'nginx', 'redis-server']
    print(f"\n🔍 Service Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    for service in services:
        try:
            result = subprocess.run(['systemctl', 'is-active', service], 
                                 capture_output=True, text=True)
            status = "🟢 RUNNING" if result.stdout.strip() == 'active' else "🔴 STOPPED"
            print(f"{service:20} : {status}")
        except:
            print(f"{service:20} : 🔴 ERROR")

def check_resources():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/')
    
    print(f"\n💻 System Resources")
    print("-" * 60)
    print(f"Memory Usage    : {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)")
    print(f"CPU Usage       : {cpu:.1f}%")
    print(f"Disk Usage      : {(disk.used/disk.total)*100:.1f}% ({disk.free/1024**3:.1f}GB free)")
    
    # Warnings
    if memory.percent > 80:
        print("⚠️  HIGH MEMORY USAGE!")
    if cpu > 80:
        print("⚠️  HIGH CPU USAGE!")
    if (disk.used/disk.total)*100 > 90:
        print("⚠️  LOW DISK SPACE!")

def check_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        active_jobs = len(r.keys("job:*"))
        print(f"\n📊 Redis Status")
        print("-" * 60)
        print(f"Redis           : 🟢 CONNECTED")
        print(f"Active Jobs     : {active_jobs}")
    except:
        print(f"Redis           : 🔴 DISCONNECTED")

def main():
    print("="*60)
    print("🎬 TEXT-TO-VIDEO APP MONITOR")
    print("="*60)
    
    check_services()
    check_resources()
    check_redis()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
EOF

chmod +x /var/www/textovideo/monitor.py

# Step 17: Create restart script
cat > /var/www/textovideo/restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Text-to-Video App..."
systemctl restart textovideo
systemctl restart celery-textovideo
systemctl restart nginx
sleep 3
echo "✅ Restart complete!"
/var/www/textovideo/venv/bin/python3 /var/www/textovideo/monitor.py
EOF

chmod +x /var/www/textovideo/restart.sh

# Step 18: Test application
print_step "Step 18: Testing application..."
sleep 3

if curl -s http://localhost > /dev/null; then
    print_status "✅ Application is responding"
else
    print_error "❌ Application is not responding"
    services_ok=false
fi

# Step 19: Configure firewall (if ufw is available)
if command -v ufw > /dev/null; then
    print_step "Step 19: Configuring