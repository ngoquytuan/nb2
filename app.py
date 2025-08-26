from flask import Flask, render_template, request, jsonify
import sqlite3 
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime

from config import DynamicConfig 
from database.db_manager import DatabaseManager
from models.naive_bayes import NaiveBayesFilter
from models.llm_analyzer import LLMAnalyzer

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Khởi tạo DatabaseManager TRƯỚC
# Giả sử DATABASE_URL được định nghĩa tĩnh hoặc từ biến môi trường
# Vì trong code của bạn không có, mình sẽ tạm hardcode nó ở đây.
DATABASE_URL = 'database/spam_filter.db' 
db = DatabaseManager(DATABASE_URL)

# 4. Khởi tạo DynamicConfig bằng cách truyền db manager vào
# và lưu nó vào app context để các route có thể dùng
app.dynamic_config = DynamicConfig(db)

# 5. Khởi tạo các component khác sử dụng config động
nb_filter = NaiveBayesFilter() # Giả sử nb_filter cũng cần config
llm_analyzer = LLMAnalyzer(app.dynamic_config) # Giả sử llm_analyzer cũng cần config

# Background processor
class MessageProcessor:
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_loop)
            self.thread.daemon = True
            self.thread.start()
            print("Message processor started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("Message processor stopped")
    
    def _process_loop(self):
        """Vòng lặp xử lý messages"""
        while self.running:
            try:
                pending_messages = db.get_pending_messages()
                
                for message in pending_messages:
                    if not self.running:
                        break
                    
                    self._process_message(message)
                    
                    # Emit update to clients
                    socketio.emit('message_processed', {
                        'message_id': message['id'],
                        'status': 'processed'
                    })
                
                time.sleep(2)  # Kiểm tra mỗi 2 giây
                
            except Exception as e:
                print(f"Error in process loop: {e}")
                time.sleep(5)
    
    def _process_message(self, message):
        """Xử lý một message qua pipeline filter"""
        
        message_id = message['id']
        content = message['content']
        print(f"🔄 Processing message {message_id}: {content[:50]}...")

        try:
            # Step 1: Naive Bayes Classification
            prediction, probabilities = nb_filter.predict(content)
            nb_classification = nb_filter.get_classification_name(prediction)
            max_prob = max(probabilities)
            
            db.log_filter_step(
                message_id, 
                'naive_bayes', 
                nb_classification,
                f'Prediction: {prediction}, Max_prob: {max_prob:.3f}, All_probs: {probabilities}'
            )
            
            # IMPROVED DECISION LOGIC
            if prediction == 0 and max_prob >= app.dynamic_config.NAIVE_BAYES_THRESHOLD:
                # Legitimate với confidence cao → Pass
                final_status = 'approved'
                final_classification = 'legitimate'
                db.log_filter_step(message_id, 'decision', 'approved', f'NB high confidence legitimate: {max_prob:.3f}')
                
            elif prediction == 2 and max_prob >= app.dynamic_config.NAIVE_BAYES_THRESHOLD:
                # Spam với confidence cao → Block
                final_status = 'blocked'
                final_classification = 'spam'
                db.log_filter_step(message_id, 'decision', 'blocked', f'NB high confidence spam: {max_prob:.3f}')
                
            elif prediction == 0 and max_prob >= app.dynamic_config.SUSPICIOUS_THRESHOLD:
                # Legitimate với confidence trung bình → Pass luôn
                final_status = 'approved'
                final_classification = 'legitimate'
                db.log_filter_step(message_id, 'decision', 'approved', f'NB medium confidence legitimate: {max_prob:.3f}')
                
            elif prediction == 2 and max_prob >= app.dynamic_config.SUSPICIOUS_THRESHOLD:
                # Spam với confidence trung bình → Block luôn
                final_status = 'blocked'
                final_classification = 'spam'
                db.log_filter_step(message_id, 'decision', 'blocked', f'NB medium confidence spam: {max_prob:.3f}')
                
            else:
                # Chỉ gửi LLM khi thực sự cần thiết (very low confidence)
                db.log_filter_step(message_id, 'llm_analysis', 'started', f'Very low NB confidence ({max_prob:.3f}), escalating to LLM')
                
                try:
                    print(f"📡 Calling LLM for message {message_id}")
                    llm_result = llm_analyzer.analyze_message(content)
                    print(f"✅ LLM Response for {message_id}: {llm_result}")
                    
                    db.log_filter_step(
                        message_id, 
                        'llm_analysis', 
                        llm_result['classification'],
                        f"Confidence: {llm_result['confidence']:.3f}, Reason: {llm_result['reason'][:100]}"
                    )
                    
                    # LLM decision với fallback an toàn hơn
                    if llm_result['confidence'] >= 0.7:  # Chỉ tin LLM khi confidence cao
                        if llm_result['is_spam']:
                            final_status = 'blocked'
                            final_classification = 'spam'
                            db.log_filter_step(message_id, 'decision', 'blocked', 'LLM high confidence spam')
                        else:
                            final_status = 'approved'
                            final_classification = 'legitimate'
                            db.log_filter_step(message_id, 'decision', 'approved', 'LLM high confidence legitimate')
                    else:
                        # LLM không chắc chắn → dựa vào NB prediction
                        if prediction == 2:  # NB says spam
                            final_status = 'flagged'
                            final_classification = 'suspicious'
                            db.log_filter_step(message_id, 'decision', 'flagged', 'LLM uncertain + NB spam → flagged')
                        else:  # NB says legitimate or suspicious
                            final_status = 'approved'
                            final_classification = 'legitimate'
                            db.log_filter_step(message_id, 'decision', 'approved', 'LLM uncertain + NB non-spam → approved')
                            
                except Exception as llm_error:
                    print(f"❌ LLM Error for message {message_id}: {llm_error}")
                    print(f"❌ Error type: {type(llm_error)}")
                    print(f"❌ Error details: {str(llm_error)}")
                    # LLM failed → fallback dựa vào NB
                    db.log_filter_step(message_id, 'llm_analysis', 'failed', str(llm_error))
                    
                    if prediction == 2:  # NB says spam
                        final_status = 'flagged'  # Không block cứng
                        final_classification = 'suspicious'
                        db.log_filter_step(message_id, 'decision', 'flagged', 'LLM failed + NB spam → flagged for review')
                    else:
                        final_status = 'approved'  # Ưu tiên cho user experience
                        final_classification = 'legitimate'
                        db.log_filter_step(message_id, 'decision', 'approved', 'LLM failed + NB non-spam → approved')
            
            # Update message status
            db.update_message_status(
                message_id,
                final_status,
                final_classification,
                max_prob,
                llm_result.get('confidence') if 'llm_result' in locals() else None
            )
            
            print(f"✅ Processed message {message_id}: {final_status} ({final_classification}) - NB: {max_prob:.3f}")
            
        except Exception as e:
            print(f"❌ Error processing message {message_id}: {e}")
            db.log_filter_step(message_id, 'error', 'failed', str(e))
            # Conservative fallback - approve unknown errors
            db.update_message_status(message_id, 'approved', 'legitimate')

# Khởi tạo processor
processor = MessageProcessor()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/send_message', methods=['POST'])
def send_message():
    """API nhận message mới"""
    data = request.json
    content = data.get('content', '').strip()
    sender = data.get('sender', 'Anonymous')
    
    if not content:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Thêm vào queue
    message_id = db.add_message(content, sender)
    
    return jsonify({
        'success': True,
        'message_id': message_id,
        'message': 'Message added to queue for processing'
    })

@app.route('/api/inbox')
def get_inbox():
    """Lấy messages trong inbox"""
    status = request.args.get('status', 'approved')
    messages = db.get_inbox_messages(status)
    return jsonify(messages)

@app.route('/api/admin/messages')
def get_all_messages():
    """Admin: xem tất cả messages và logs"""
    messages = db.get_all_messages_with_logs()
    return jsonify(messages)

# Thêm vào app.py sau route '/api/admin/messages'

@app.route('/api/stats')
def get_stats():
    """Thống kê tổng quan từ database"""
    # FIX: Sử dụng biến DATABASE_URL đã định nghĩa ở đầu file app.py
    conn = sqlite3.connect(DATABASE_URL) 
    cursor = conn.cursor()
    
    # Đếm theo classification
    cursor.execute("""
        SELECT 
            classification,
            COUNT(*) as count
        FROM messages 
        WHERE status != 'pending'
        GROUP BY classification
    """)
    
    classification_counts = dict(cursor.fetchall())
    
    # Đếm theo status
    cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count
        FROM messages 
        GROUP BY status
    """)
    
    status_counts = dict(cursor.fetchall())
    
    # Tổng số đã xử lý
    cursor.execute("SELECT COUNT(*) FROM messages WHERE status != 'pending'")
    total_processed = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_processed': total_processed,
        'legitimate': classification_counts.get('legitimate', 0),
        'suspicious': classification_counts.get('suspicious', 0),
        'spam': classification_counts.get('spam', 0),
        'blocked': status_counts.get('blocked', 0),
        'flagged': status_counts.get('flagged', 0),
        'approved': status_counts.get('approved', 0)
    })

# Thêm vào app.py
@app.route('/api/settings')
def get_settings():
    """Lấy tất cả settings"""
    settings = db.get_all_settings()
    
    # Mask passwords
    for category in settings:
        for setting in settings[category]:
            if setting['data_type'] == 'password' and setting['value']:
                setting['value'] = '***masked***'
    
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Cập nhật settings"""
    data = request.json
    updated_keys = []
    
    for key, value in data.items():
        # Validate key exists
        current = db.get_setting(key)
        if current is not None:
            db.update_setting(key, value)
            updated_keys.append(key)
            
            # Clear config cache
            if hasattr(app, 'dynamic_config'):
                app.dynamic_config.clear_cache()
    
    return jsonify({
        'success': True,
        'updated_keys': updated_keys,
        'message': f'Updated {len(updated_keys)} settings'
    })

@app.route('/api/llm/health')
def check_llm_health():
    """Kiểm tra health của LLM providers"""
    provider = app.dynamic_config.LLM_PROVIDER
    
    health_result = llm_analyzer.health_monitor.check_provider_health(
        provider, 
        app.dynamic_config.get(f'{provider}_api_key', '')
    )
    
    # Thêm error summary
    error_summary = llm_analyzer.get_error_summary()
    
    return jsonify({
        'current_provider': provider,
        'health': health_result,
        'error_summary': error_summary
    })

@app.route('/api/llm/test', methods=['POST'])
def test_llm_connection():
    """Test LLM connection với message mẫu"""
    data = request.json
    test_message = data.get('message', 'This is a test message.')
    
    result = llm_analyzer.analyze_message(test_message)
    
    return jsonify({
        'success': True,
        'test_result': result,
        'provider': app.dynamic_config.LLM_PROVIDER
    })
    
# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to spam filter system'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Start background processor when app starts
#@app.before_first_request
#def start_processor():
#    processor.start()

if __name__ == '__main__':
    import os

    # Create necessary directories
    os.makedirs('database', exist_ok=True)

    print("=== Spam Filter Demo Starting ===")
    print("1. Training/Loading Naive Bayes model...")
    # The NaiveBayesFilter class already handles loading or training on initialization

    print("2. Initializing database...")
    # The DatabaseManager class handles DB creation on initialization

    print("3. Starting background message processor...")
    # Chỉ khởi động processor trong tiến trình con của Flask
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("Starting background message processor in worker process...")
        processor.start()

    print("Starting Flask app...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)