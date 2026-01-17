from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import queue
import threading
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent_improved import TutoringAgent

app = Flask(__name__)
CORS(app)  # Allow Next.js to connect

# Global State
event_queue = queue.Queue()
current_agent = None
agent_thread = None

def event_callback(data):
    """Puts agent events into the queue for SSE"""
    event_queue.put(data)

@app.route('/api/start', methods=['POST'])
def start_agent():
    global current_agent, agent_thread
    
    if current_agent and hasattr(current_agent, 'running') and current_agent.running:
        return jsonify({"error": "Agent already running"}), 400
        
    set_type = request.json.get('set_type', 'mini_dev')
    
    # Clear queue
    with event_queue.mutex:
        event_queue.queue.clear()
        
    # Create agent
    current_agent = TutoringAgent(use_llm=True, event_callback=event_callback)
    
    # Run in background thread
    agent_thread = threading.Thread(
        target=current_agent.run_all_sessions,
        args=(set_type,)
    )
    agent_thread.start()
    
    return jsonify({"status": "started", "set": set_type})

@app.route('/api/stop', methods=['POST'])
def stop_agent():
    global current_agent
    if current_agent:
        current_agent.stop_requested = True
    return jsonify({"status": "stopping"})

@app.route('/api/stream')
def stream():
    def event_stream():
        while True:
            # Wait for new data
            data = event_queue.get()
            yield f"data: {json.dumps(data)}\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "agent_running": current_agent.running if current_agent else False
    })

if __name__ == '__main__':
    print("🚀 Flask Backend running on http://localhost:5000")
    app.run(port=5000, threaded=True)