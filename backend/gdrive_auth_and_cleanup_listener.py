"""HTTP listener on port 3000 to automatically capture Google OAuth redirect and clean all documents from Google Drive."""
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step6_mcp.google.auth import exchange_code_for_tokens
from backend.delete_all_gdrive_docs import main as delete_gdrive_docs_main

PORT = 3000
REDIRECT_URI = "http://localhost:3000/oauth2callback"
CLIENT_ID = "703200458994-e2c4m1vnrfmf23saca4fp354fots2deo.apps.googleusercontent.com"

auth_code_holder = []
server_instance = []

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/oauth2callback":
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            error = params.get("error", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            if code:
                auth_code_holder.append(code)
                html = """
                <html>
                <body style="font-family: sans-serif; background: #0B0E14; color: #E2E8F0; display:flex; justify-content:center; align-items:center; height: 90vh;">
                  <div style="background: #151A24; padding: 40px; border-radius: 12px; border: 1px solid #22D3EE; text-align: center; max-width: 500px;">
                    <h1 style="color: #22D3EE; margin-bottom: 12px;">Authentication Successful!</h1>
                    <p style="color: #94A3B8; font-size: 16px;">Authorization code received. Cleaning up all article documents in Google Drive now...</p>
                    <p style="color: #4ADE80; font-weight: bold; margin-top: 24px;">You can now close this tab and return to Antigravity.</p>
                  </div>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
                # Stop server in background thread after sending response
                def stop_srv():
                    time.sleep(1)
                    if server_instance:
                        server_instance[0].shutdown()
                threading.Thread(target=stop_srv, daemon=True).start()
            else:
                html = f"""
                <html>
                <body style="font-family: sans-serif; background: #0B0E14; color: #EF4444; padding: 50px;">
                  <h2>OAuth Error: {error}</h2>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress standard logging
        pass

def run():
    # Construct auth URL with localhost redirect URI
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urllib.parse.urlencode(params)}"

    print("=" * 70)
    print("READY TO AUTHORIZE GOOGLE DRIVE CLEANUP")
    print("=" * 70)
    print("Please click the link below in your browser:")
    print(auth_url)
    print("=" * 70)

    # Start listener on port 3000
    server = socketserver.TCPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
    server_instance.append(server)
    print(f"\n[Listening] Waiting for OAuth callback on {REDIRECT_URI}...")
    
    server.serve_forever()

    if auth_code_holder:
        code = auth_code_holder[0]
        print(f"\n[OAuth] Code captured successfully: {code[:12]}...")
        exchange_code_for_tokens(code, redirect_uri=REDIRECT_URI)
        print("[OAuth] Tokens saved! Now deleting all article documents from Google Drive...")
        delete_gdrive_docs_main()

if __name__ == "__main__":
    run()
