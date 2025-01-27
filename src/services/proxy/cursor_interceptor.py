import random
import string
from mitmproxy import ctx

# Global checksum değişkeni
global_checksum = None

def generate_checksum():
    return "".join(random.choices(string.digits + "abcdef", k=64))

def request(flow):
    """Cursor isteklerini yakalar ve değiştirir"""
    global global_checksum
    try:
        if "api2.cursor.sh" in flow.request.pretty_host:
            if "X-Cursor-Checksum" in flow.request.headers:
                try:
                    current_checksum = flow.request.headers["X-Cursor-Checksum"]
                    parts = current_checksum.split("/")
                    if len(parts) > 1:
                        if global_checksum is None:
                            global_checksum = generate_checksum()
                        modified_checksum = f"{parts[0]}/{global_checksum}"
                        flow.request.headers["X-Cursor-Checksum"] = modified_checksum
                        ctx.log.info(f"-> {flow.request.pretty_url}")
                except Exception as e:
                    ctx.log.error(str(e))
    except Exception as e:
        ctx.log.error(str(e))

def response(flow):
    """Cursor cevaplarını yakalar ve değiştirir"""
    try:
        if "api2.cursor.sh" in flow.request.pretty_host:
            ctx.log.info(f"<- {flow.request.pretty_url} ({flow.response.status_code})")
    except Exception as e:
        ctx.log.error(str(e))
