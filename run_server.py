import os
import sys
import time
import socket
import webbrowser
import threading

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PORT = int(os.environ.get("PORT", 8080))

def open_browser():
    time.sleep(1.5)
    url = f"http://127.0.0.1:{PORT}"
    print(f"\n[+] Opening VisionX portal in your laptop browser: {url}\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn

    lan_ip = get_lan_ip()

    print("=" * 72)
    print("      VISIONX — LEGAL METROLOGY COMPLIANCE ENFORCEMENT SYSTEM")
    print("=" * 72)
    print(f" [*] Laptop / Local Browser : http://127.0.0.1:{PORT}")
    print(f" [*] Smartphone (Same Wi-Fi): http://{lan_ip}:{PORT}")
    print(f" [*] Interactive API Docs   : http://127.0.0.1:{PORT}/docs")
    print("=" * 72)
    print(" NOTE: Keep this Command Prompt window open while using the app.")
    print("=" * 72)
    print(" QUICK DEMO CREDENTIALS:")
    print("  • Inspector : inspector@visionx.gov.in  /  inspector123")
    print("  • Admin     : admin@visionx.gov.in      /  admin123")
    print("  • Viewer    : viewer@visionx.gov.in     /  viewer123")
    print("=" * 72)
    print(" Press Ctrl + C to stop the server.\n")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)
