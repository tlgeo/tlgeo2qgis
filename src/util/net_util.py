import socket 
def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # Connect to an external server
        ip = s.getsockname()[0]  # Get the local IP used for the connection
    except Exception:
        ip = "127.0.0.1"  # Fallback to localhost if error occurs
    finally:
        s.close()
    return ip