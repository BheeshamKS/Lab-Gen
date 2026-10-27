"""
Security Visual Studio for LabGenius.
Generates authentic Information Security visual artifacts, including:
1. Authentic Wireshark Packet Sniffer GUI screenshots
2. Data Integrity & Checksum Verification architecture diagrams
3. Caesar Cipher modular shift wheels and substitution diagrams
4. AES-128 Symmetric Block Cipher pipeline diagrams
5. Statistical Malware Anomaly Detection (Z-Score) distribution plots
6. HTTP Client-Server packet sequence ladder diagrams
"""

import os
import math
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from PIL import Image, ImageDraw, ImageFont


class SecurityVisualStudio:
    """Generates authentic Information Security and network protocol visual artifacts."""

    @staticmethod
    def _get_font(size: int = 12, bold: bool = False, mono: bool = False) -> ImageFont.ImageFont:
        """Helper to load system TTF fonts safely."""
        candidates = []
        if mono:
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "/usr/share/fonts/truetype/custom/fonts/ttf/JetBrainsMono-Regular.ttf",
            ]
        elif bold:
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]
        else:
            candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]

        for p in candidates:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    # =========================================================================
    # 1. AUTHENTIC WIRESHARK PACKET SNIFFER SCREENSHOT GENERATOR
    # =========================================================================
    @classmethod
    def generate_wireshark_screenshot(
        cls,
        dest_path: Path,
        scenario: str = "http_basic",
        title_suffix: str = "",
        width: int = 960,
    ) -> Path:
        """
        Synthesizes an authentic Wireshark packet capture window.
        Scenarios supported:
        - 'http_basic': HTTP GET and 200 OK
        - 'http_conditional': Conditional GET with If-Modified-Since and 304 Not Modified
        - 'http_long_doc': TCP segment reassembly of multi-packet HTTP transfer
        - 'http_embedded': HTML GET followed by image requests
        - 'http_auth': 401 Unauthorized and Authorization: Basic credentials
        """
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        scenarios_data = {
            "http_basic": {
                "filter": "http",
                "selected_row": 0,
                "packets": [
                    ("1", "0.000000", "192.168.1.105", "128.119.245.12", "HTTP", "524", "GET /wireshark-labs/HTTP-wireshark-file1.html HTTP/1.1"),
                    ("2", "0.045231", "128.119.245.12", "192.168.1.105", "HTTP", "682", "HTTP/1.1 200 OK  (text/html)"),
                    ("3", "0.045310", "192.168.1.105", "128.119.245.12", "TCP", "54", "54124 → 80 [ACK] Seq=471 Ack=629 Win=64240 Len=0"),
                    ("4", "1.230491", "192.168.1.105", "128.119.245.12", "TCP", "54", "54124 → 80 [FIN, ACK] Seq=471 Ack=629 Win=64240 Len=0"),
                    ("5", "1.275812", "128.119.245.12", "192.168.1.105", "TCP", "54", "80 → 54124 [ACK] Seq=629 Ack=472 Win=64240 Len=0"),
                ],
                "details": [
                    "▸ Frame 1: 524 bytes on wire (4192 bits), 524 bytes captured on interface eth0",
                    "▸ Ethernet II, Src: Realtek_12:34:56 (00:e0:4c:12:34:56), Dst: Cisco_65:43:21 (00:0c:29:65:43:21)",
                    "▸ Internet Protocol Version 4, Src: 192.168.1.105, Dst: 128.119.245.12",
                    "▸ Transmission Control Protocol, Src Port: 54124, Dst Port: 80, Seq: 1, Ack: 1, Len: 470",
                    "▾ Hypertext Transfer Protocol",
                    "    Expert Info (Chat/Sequence): GET /wireshark-labs/HTTP-wireshark-file1.html HTTP/1.1\\r\\n",
                    "    Request Method: GET",
                    "    Request URI: /wireshark-labs/HTTP-wireshark-file1.html",
                    "    Request Version: HTTP/1.1",
                    "    Host: gaia.cs.umass.edu\\r\\n",
                    "    User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36\\r\\n",
                    "    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\\r\\n",
                    "    Accept-Language: en-US,en;q=0.9\\r\\n",
                    "    Accept-Encoding: gzip, deflate\\r\\n",
                    "    Connection: keep-alive\\r\\n",
                    "    \\r\\n",
                    "    [Full request URI: http://gaia.cs.umass.edu/wireshark-labs/HTTP-wireshark-file1.html]",
                ],
                "hex_dump": [
                    "0000  00 0c 29 65 43 21 00 e0  4c 12 34 56 08 00 45 00   ..)eC!..L.4V..E.",
                    "0010  01 f6 1b 45 40 00 40 06  b2 31 c0 a8 01 69 80 77   ...E@.@..1...i.w",
                    "0020  f5 0c d3 6c 00 50 12 34  56 78 9a bc de f0 50 18   ...l.P.4Vx....P.",
                    "0030  01 f5 a4 12 00 00 47 45  54 20 2f 77 69 72 65 73   ......GET /wires",
                    "0040  68 61 72 6b 2d 6c 61 62  73 2f 48 54 54 50 2d 77   hark-labs/HTTP-w",
                    "0050  69 72 65 73 68 61 72 6b  2d 66 69 6c 65 31 2e 68   ireshark-file1.h",
                    "0060  74 6d 6c 20 48 54 54 50  2f 31 2e 31 0d 0a 48 6f   tml HTTP/1.1..Ho",
                    "0070  73 74 3a 20 67 61 69 61  2e 63 73 2e 75 6d 61 73   st: gaia.cs.umas",
                ],
            },
            "http_conditional": {
                "filter": "http",
                "selected_row": 2,
                "packets": [
                    ("1", "0.000000", "192.168.1.105", "128.119.245.12", "HTTP", "524", "GET /wireshark-labs/HTTP-wireshark-file2.html HTTP/1.1"),
                    ("2", "0.046102", "128.119.245.12", "192.168.1.105", "HTTP", "670", "HTTP/1.1 200 OK  (text/html)"),
                    ("3", "1.104230", "192.168.1.105", "128.119.245.12", "HTTP", "572", "GET /wireshark-labs/HTTP-wireshark-file2.html HTTP/1.1"),
                    ("4", "1.149810", "128.119.245.12", "192.168.1.105", "HTTP", "232", "HTTP/1.1 304 Not Modified"),
                ],
                "details": [
                    "▸ Frame 3: 572 bytes on wire (4576 bits), 572 bytes captured on interface eth0",
                    "▸ Ethernet II, Src: Realtek_12:34:56, Dst: Cisco_65:43:21",
                    "▸ Internet Protocol Version 4, Src: 192.168.1.105, Dst: 128.119.245.12",
                    "▸ Transmission Control Protocol, Src Port: 54130, Dst Port: 80, Seq: 1, Ack: 1",
                    "▾ Hypertext Transfer Protocol",
                    "    Request Method: GET",
                    "    Request URI: /wireshark-labs/HTTP-wireshark-file2.html",
                    "    Request Version: HTTP/1.1",
                    "    Host: gaia.cs.umass.edu\\r\\n",
                    "    If-Modified-Since: Tue, 27 Oct 2026 06:12:00 GMT\\r\\n",
                    "    If-None-Match: \"7e4-54c8b21ef00c0\"\\r\\n",
                    "    Connection: keep-alive\\r\\n",
                    "    \\r\\n",
                    "    [Response in frame: 4]",
                ],
                "hex_dump": [
                    "0000  00 0c 29 65 43 21 00 e0  4c 12 34 56 08 00 45 00   ..)eC!..L.4V..E.",
                    "0010  02 26 1c 45 40 00 40 06  b2 01 c0 a8 01 69 80 77   .&.E@.@..1...i.w",
                    "0020  f5 0c d3 72 00 50 12 34  56 78 9a bc de f0 50 18   ...r.P.4Vx....P.",
                    "0030  01 f5 a4 12 00 00 47 45  54 20 2f 77 69 72 65 73   ......GET /wires",
                    "0040  49 66 2d 4d 6f 64 69 66  69 65 64 2d 53 69 6e 63   If-Modified-Sinc",
                    "0050  65 3a 20 54 75 65 2c 20  32 37 20 4f 63 74 20 32   e: Tue, 27 Oct 2",
                ],
            },
            "http_long_doc": {
                "filter": "http || tcp.port == 80",
                "selected_row": 3,
                "packets": [
                    ("1", "0.000000", "192.168.1.105", "128.119.245.12", "HTTP", "526", "GET /wireshark-labs/HTTP-wireshark-file3.html HTTP/1.1"),
                    ("2", "0.045100", "128.119.245.12", "192.168.1.105", "TCP", "1514", "[TCP segment of a reassembled PDU] Seq=1 Ack=473 Len=1460"),
                    ("3", "0.045105", "128.119.245.12", "192.168.1.105", "TCP", "1514", "[TCP segment of a reassembled PDU] Seq=1461 Ack=473 Len=1460"),
                    ("4", "0.045110", "128.119.245.12", "192.168.1.105", "HTTP", "1514", "HTTP/1.1 200 OK  (text/html) [4 Reassembled TCP Segments: 4500 bytes]"),
                    ("5", "0.045200", "192.168.1.105", "128.119.245.12", "TCP", "54", "54138 → 80 [ACK] Seq=473 Ack=4501 Win=64240 Len=0"),
                ],
                "details": [
                    "▸ Frame 4: 1514 bytes on wire (12112 bits), 1514 bytes captured on eth0",
                    "▸ Ethernet II, Src: Cisco_65:43:21, Dst: Realtek_12:34:56",
                    "▸ Internet Protocol Version 4, Src: 128.119.245.12, Dst: 192.168.1.105",
                    "▾ Transmission Control Protocol, Src Port: 80, Dst Port: 54138",
                    "    [4 Reassembled TCP Segments (4500 bytes): #2(1460), #3(1460), #4(1460), #5(120)]",
                    "▾ Hypertext Transfer Protocol",
                    "    HTTP/1.1 200 OK\\r\\n",
                    "    Date: Tue, 27 Oct 2026 09:15:22 GMT\\r\\n",
                    "    Server: Apache/2.4.41 (Unix)\\r\\n",
                    "    Content-Length: 4500\\r\\n",
                    "    Content-Type: text/html; charset=ISO-8859-1\\r\\n",
                    "    \\r\\n",
                    "    [Line-based text data: text/html (4500 bytes)]",
                ],
                "hex_dump": [
                    "0000  00 e0 4c 12 34 56 00 0c  29 65 43 21 08 00 45 00   ..L.4V..)eC!..E.",
                    "0010  05 dc 82 14 40 00 34 06  4a 88 80 77 f5 0c c0 a8   ....@.4.J..w....",
                    "0020  01 69 00 50 d3 7a 00 00  05 b5 00 00 01 d9 50 18   .i.P.z........P.",
                    "0030  01 f5 b4 20 00 00 48 54  54 50 2f 31 2e 31 20 32   ... ..HTTP/1.1 2",
                    "0040  30 30 20 4f 4b 0d 0a 44  61 74 65 3a 20 54 75 65   00 OK..Date: Tue",
                ],
            },
            "http_embedded": {
                "filter": "http",
                "selected_row": 1,
                "packets": [
                    ("1", "0.000000", "192.168.1.105", "128.119.245.12", "HTTP", "528", "GET /wireshark-labs/HTTP-wireshark-file4.html HTTP/1.1"),
                    ("2", "0.046120", "128.119.245.12", "192.168.1.105", "HTTP", "740", "HTTP/1.1 200 OK  (text/html)"),
                    ("3", "0.051200", "192.168.1.105", "128.119.245.12", "HTTP", "532", "GET /wireshark-labs/cover_9e.jpg HTTP/1.1"),
                    ("4", "0.052100", "192.168.1.105", "172.217.16.206", "HTTP", "546", "GET /pearson.png HTTP/1.1"),
                    ("5", "0.098400", "128.119.245.12", "192.168.1.105", "HTTP", "1514", "HTTP/1.1 200 OK  (image/jpeg)"),
                    ("6", "0.104200", "172.217.16.206", "192.168.1.105", "HTTP", "1514", "HTTP/1.1 200 OK  (image/png)"),
                ],
                "details": [
                    "▸ Frame 2: 740 bytes on wire, 740 bytes captured on eth0",
                    "▸ Ethernet II, Src: Cisco_65:43:21, Dst: Realtek_12:34:56",
                    "▸ Internet Protocol Version 4, Src: 128.119.245.12, Dst: 192.168.1.105",
                    "▸ Transmission Control Protocol, Src Port: 80, Dst Port: 54142",
                    "▾ Hypertext Transfer Protocol",
                    "    HTTP/1.1 200 OK\\r\\n",
                    "    Content-Type: text/html\\r\\n",
                    "    Content-Length: 420\\r\\n",
                    "    \\r\\n",
                    "    <img src=\"cover_9e.jpg\">",
                    "    <img src=\"http://media.pearsoncmg.com/pearson.png\">",
                ],
                "hex_dump": [
                    "0000  00 e0 4c 12 34 56 00 0c  29 65 43 21 08 00 45 00   ..L.4V..)eC!..E.",
                    "0010  02 e4 1a 22 40 00 34 06  4c 2a 80 77 f5 0c c0 a8   ...\"@.4.L*.w....",
                    "0020  01 69 00 50 d3 82 00 00  01 b5 00 00 01 d9 50 18   .i.P..........P.",
                    "0030  01 f5 b4 20 00 00 48 54  54 50 2f 31 2e 31 20 32   ... ..HTTP/1.1 2",
                ],
            },
            "http_auth": {
                "filter": "http",
                "selected_row": 2,
                "packets": [
                    ("1", "0.000000", "192.168.1.105", "128.119.245.12", "HTTP", "530", "GET /wireshark-labs/protected_pages/HTTP-wireshark-file5.html HTTP/1.1"),
                    ("2", "0.046100", "128.119.245.12", "192.168.1.105", "HTTP", "482", "HTTP/1.1 401 Unauthorized"),
                    ("3", "2.124500", "192.168.1.105", "128.119.245.12", "HTTP", "614", "GET /wireshark-labs/protected_pages/HTTP-wireshark-file5.html HTTP/1.1"),
                    ("4", "2.170200", "128.119.245.12", "192.168.1.105", "HTTP", "720", "HTTP/1.1 200 OK  (text/html)"),
                ],
                "details": [
                    "▸ Frame 3: 614 bytes on wire (4912 bits), 614 bytes captured on eth0",
                    "▸ Ethernet II, Src: Realtek_12:34:56, Dst: Cisco_65:43:21",
                    "▸ Internet Protocol Version 4, Src: 192.168.1.105, Dst: 128.119.245.12",
                    "▸ Transmission Control Protocol, Src Port: 54150, Dst Port: 80",
                    "▾ Hypertext Transfer Protocol",
                    "    Request Method: GET",
                    "    Request URI: /wireshark-labs/protected_pages/HTTP-wireshark-file5.html",
                    "    Host: gaia.cs.umass.edu\\r\\n",
                    "    ▾ Authorization: Basic d2lyZXNoYXJrLXN0dWRlbnRzOm5ldHdvcms=\\r\\n",
                    "        Credentials: wireshark-students:network",
                    "    Connection: keep-alive\\r\\n",
                    "    \\r\\n",
                ],
                "hex_dump": [
                    "0000  00 0c 29 65 43 21 00 e0  4c 12 34 56 08 00 45 00   ..)eC!..L.4V..E.",
                    "0010  02 50 1e 10 40 00 40 06  b1 00 c0 a8 01 69 80 77   .P..@.@......i.w",
                    "0020  f5 0c d3 8a 00 50 12 34  56 78 9a bc de f0 50 18   .....P.4Vx....P.",
                    "0030  41 75 74 68 6f 72 69 7a  61 74 69 6f 6e 3a 20 42   Authorization: B",
                    "0040  61 73 69 63 20 64 32 6c  79 5a 58 4e 6f 59 58 4a   asic d2lyZXNoYXJ",
                    "0050  72 4c 58 4e 30 64 57 52  6c 62 6e 52 7a 4f 6d 35   rLXN0dWRlbnRzOm5",
                    "0060  6c 64 48 64 76 63 6d 73  3d 0d 0a 0d 0a            ldHdvcms=....",
                ],
            },
        }

        data = scenarios_data.get(scenario, scenarios_data["http_basic"])

        # Canvas Dimensions
        height = 680
        img = Image.new("RGB", (width, height), (245, 246, 248))
        draw = ImageDraw.Draw(img)

        # Fonts
        font_ui = cls._get_font(12)
        font_bold = cls._get_font(12, bold=True)
        font_small = cls._get_font(11)
        font_mono = cls._get_font(12, mono=True)
        font_mono_small = cls._get_font(11, mono=True)

        # -------------------------------------------------------------
        # 1. WINDOW TITLE BAR & MENU
        # -------------------------------------------------------------
        title_bg = (38, 50, 56)
        draw.rectangle([(0, 0), (width, 32)], fill=title_bg)
        # Window control dots
        draw.ellipse([(12, 10), (22, 20)], fill=(255, 95, 86))
        draw.ellipse([(28, 10), (38, 20)], fill=(255, 189, 46))
        draw.ellipse([(44, 10), (54, 20)], fill=(39, 201, 63))

        window_title = f"Wireshark · [Trace Analysis — HTTP Protocol Inspection] {title_suffix}".strip()
        draw.text((68, 8), window_title, font=font_bold, fill=(236, 239, 241))

        # Menu bar
        menu_bg = (238, 240, 244)
        draw.rectangle([(0, 32), (width, 56)], fill=menu_bg)
        draw.line([(0, 56), (width, 56)], fill=(207, 216, 220), width=1)
        menus = ["File", "Edit", "View", "Go", "Capture", "Analyze", "Statistics", "Telephony", "Tools", "Help"]
        mx = 14
        for m in menus:
            draw.text((mx, 38), m, font=font_small, fill=(55, 71, 79))
            mx += int(draw.textlength(m, font=font_small)) + 16

        # -------------------------------------------------------------
        # 2. FILTER TOOLBAR
        # -------------------------------------------------------------
        draw.rectangle([(0, 57), (width, 88)], fill=(245, 247, 250))
        draw.text((14, 66), "Apply a display filter ...", font=font_small, fill=(120, 144, 156))

        # Filter Input box (Green background indicating valid Wireshark filter syntax)
        filter_box_rect = [(160, 62), (width - 120, 84)]
        draw.rectangle(filter_box_rect, fill=(218, 245, 218), outline=(76, 175, 80), width=1)
        draw.text((170, 66), data["filter"], font=font_mono, fill=(27, 94, 32))

        # Filter buttons
        draw.rectangle([(width - 110, 62), (width - 64, 84)], fill=(224, 224, 224), outline=(189, 189, 189))
        draw.text((width - 100, 67), "Apply", font=font_small, fill=(33, 33, 33))
        draw.rectangle([(width - 58, 62), (width - 14, 84)], fill=(224, 224, 224), outline=(189, 189, 189))
        draw.text((width - 50, 67), "Clear", font=font_small, fill=(33, 33, 33))

        draw.line([(0, 88), (width, 88)], fill=(207, 216, 220), width=1)

        # -------------------------------------------------------------
        # 3. PACKET LIST PANE (Top Half)
        # -------------------------------------------------------------
        table_top = 89
        header_h = 24
        draw.rectangle([(0, table_top), (width, table_top + header_h)], fill=(227, 232, 239))
        draw.line([(0, table_top + header_h), (width, table_top + header_h)], fill=(176, 190, 197), width=1)

        cols = [
            ("No.", 50),
            ("Time", 90),
            ("Source", 140),
            ("Destination", 140),
            ("Protocol", 80),
            ("Length", 70),
            ("Info", width - 570),
        ]
        cx = 12
        for cname, cw in cols:
            draw.text((cx, table_top + 5), cname, font=font_bold, fill=(38, 50, 56))
            cx += cw

        # Packet Rows
        row_y = table_top + header_h + 1
        row_h = 22
        sel_idx = data["selected_row"]

        for idx, pkt in enumerate(data["packets"]):
            is_selected = (idx == sel_idx)
            row_bg = (33, 115, 204) if is_selected else ((255, 255, 255) if idx % 2 == 0 else (245, 248, 252))
            draw.rectangle([(0, row_y), (width, row_y + row_h)], fill=row_bg)

            # Columns
            text_color = (255, 255, 255) if is_selected else (33, 33, 33)
            cx = 12
            for val, (_, cw) in zip(pkt, cols):
                # Color code HTTP protocol
                if not is_selected and val == "HTTP":
                    draw.text((cx, row_y + 3), val, font=font_mono_small, fill=(46, 125, 50))
                else:
                    draw.text((cx, row_y + 3), val, font=font_mono_small, fill=text_color)
                cx += cw

            row_y += row_h

        # Pane separator
        list_bottom = max(row_y, 250)
        if list_bottom > row_y:
            draw.rectangle([(0, row_y), (width, list_bottom)], fill=(255, 255, 255))
        draw.rectangle([(0, list_bottom), (width, list_bottom + 5)], fill=(207, 216, 220))

        # -------------------------------------------------------------
        # 4. PACKET DETAILS PANE (Middle)
        # -------------------------------------------------------------
        det_top = list_bottom + 5
        det_h = 230
        draw.rectangle([(0, det_top), (width, det_top + det_h)], fill=(255, 255, 255))

        dy = det_top + 6
        for line in data["details"]:
            if dy + 18 > det_top + det_h:
                break
            is_header = line.startswith("▾") or line.startswith("▸")
            f_color = (13, 71, 161) if "Hypertext" in line else ((0, 0, 0) if is_header else (66, 66, 66))
            f_to_use = font_bold if is_header else font_mono_small
            draw.text((16, dy), line, font=f_to_use, fill=f_color)
            dy += 17

        # Pane separator
        bytes_top = det_top + det_h
        draw.rectangle([(0, bytes_top), (width, bytes_top + 5)], fill=(207, 216, 220))

        # -------------------------------------------------------------
        # 5. PACKET BYTES PANE (Bottom Hex Dump)
        # -------------------------------------------------------------
        by_top = bytes_top + 5
        by_h = 175
        draw.rectangle([(0, by_top), (width, by_top + by_h)], fill=(250, 250, 250))

        hy = by_top + 6
        draw.text((16, hy), "Frame Bytes (Hex / ASCII Dissection):", font=font_bold, fill=(84, 110, 122))
        hy += 18

        for hline in data["hex_dump"]:
            if hy + 16 > by_top + by_h:
                break
            draw.text((16, hy), hline, font=font_mono_small, fill=(33, 33, 33))
            hy += 16

        # -------------------------------------------------------------
        # 6. STATUS BAR
        # -------------------------------------------------------------
        status_y = height - 24
        draw.rectangle([(0, status_y), (width, height)], fill=(236, 239, 241))
        draw.line([(0, status_y), (width, status_y)], fill=(176, 190, 197), width=1)
        stat_text = f"Packets: 48 · Displayed: {len(data['packets'])} · Scenario: {scenario} · Selected: Packet {data['packets'][sel_idx][0]} · Profile: Default"
        draw.text((14, status_y + 4), stat_text, font=font_small, fill=(55, 71, 79))

        # Outer border
        draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(120, 144, 156), width=1)

        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    # =========================================================================
    # 2. DATA INTEGRITY & CHECKSUM VERIFICATION FLOWCHART
    # =========================================================================
    @classmethod
    def generate_checksum_flow_diagram(
        cls,
        dest_path: Path,
        sample_str: str = "HELLO",
        tampered_str: str = "HELLA",
        width: int = 860,
        height: int = 420,
    ) -> Path:
        """Renders publication-quality Data Integrity & Checksum Verification architecture diagram."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_title = cls._get_font(15, bold=True)
        font_sub = cls._get_font(12, bold=True)
        font_text = cls._get_font(11)
        font_small = cls._get_font(10)
        font_mono = cls._get_font(11, mono=True)

        # Title Header
        draw.rectangle([(0, 0), (width, 42)], fill=(24, 43, 73))
        draw.text((20, 12), "Information Security Architecture: Data Integrity & Checksum Verification Model", font=font_title, fill=(255, 255, 255))

        # 1. Sender Box (Left)
        draw.rounded_rectangle([(30, 70), (250, 360)], radius=8, fill=(243, 246, 252), outline=(41, 98, 255), width=2)
        draw.rectangle([(30, 70), (250, 102)], fill=(41, 98, 255))
        draw.text((50, 78), "SENDER NODE", font=font_sub, fill=(255, 255, 255))

        draw.text((45, 118), "Original Plaintext:", font=font_sub, fill=(33, 33, 33))
        draw.rectangle([(45, 138), (235, 168)], fill=(255, 255, 255), outline=(189, 189, 189))
        draw.text((55, 146), f'"{sample_str}"', font=font_mono, fill=(13, 71, 161))

        draw.text((45, 184), "Checksum Engine:", font=font_sub, fill=(33, 33, 33))
        draw.rectangle([(45, 204), (235, 254)], fill=(227, 242, 253), outline=(100, 181, 246))
        draw.text((55, 212), "∑ ord(c)", font=font_mono, fill=(1, 87, 155))
        orig_sum = sum(ord(c) for c in sample_str)
        draw.text((55, 232), f"Checksum = {orig_sum}", font=font_mono, fill=(1, 87, 155))

        draw.text((45, 274), "Transmitted Payload:", font=font_sub, fill=(33, 33, 33))
        draw.text((50, 296), f"• Data: {sample_str}", font=font_text, fill=(55, 71, 79))
        draw.text((50, 316), f"• Token: {orig_sum}", font=font_text, fill=(55, 71, 79))

        # 2. Insecure Transmission Channel (Middle)
        draw.rounded_rectangle([(310, 140), (530, 290)], radius=8, fill=(254, 243, 242), outline=(229, 57, 53), width=2)
        draw.rectangle([(310, 140), (530, 170)], fill=(229, 57, 53))
        draw.text((328, 146), "INSECURE CHANNEL", font=font_sub, fill=(255, 255, 255))

        draw.text((325, 184), "Active Tamper / Noise:", font=font_sub, fill=(183, 28, 28))
        draw.text((325, 206), f'Original: "{sample_str}"', font=font_mono, fill=(85, 85, 85))
        draw.text((325, 226), f'Corrupted: "{tampered_str}"', font=font_mono, fill=(198, 40, 40))
        draw.text((325, 254), "Bit Flip / Man-In-The-Middle", font=font_text, fill=(183, 28, 28))

        # Arrows: Sender -> Channel
        draw.line([(252, 215), (308, 215)], fill=(41, 98, 255), width=3)
        draw.polygon([(308, 210), (308, 220), (318, 215)], fill=(41, 98, 255))

        # 3. Receiver Node (Right)
        draw.rounded_rectangle([(590, 70), (820, 360)], radius=8, fill=(243, 246, 252), outline=(46, 125, 50), width=2)
        draw.rectangle([(590, 70), (820, 102)], fill=(46, 125, 50))
        draw.text((615, 78), "RECEIVER NODE", font=font_sub, fill=(255, 255, 255))

        draw.text((605, 118), "Received Payload:", font=font_sub, fill=(33, 33, 33))
        draw.rectangle([(605, 138), (805, 168)], fill=(255, 255, 255), outline=(189, 189, 189))
        draw.text((615, 146), f'"{tampered_str}"', font=font_mono, fill=(198, 40, 40))

        draw.text((605, 184), "Integrity Verification:", font=font_sub, fill=(33, 33, 33))
        recv_sum = sum(ord(c) for c in tampered_str)
        draw.rectangle([(605, 204), (805, 254)], fill=(255, 243, 224), outline=(255, 152, 0))
        draw.text((615, 212), f"Recalc: {recv_sum}", font=font_mono, fill=(230, 81, 0))
        draw.text((615, 232), f"Expect: {orig_sum}", font=font_mono, fill=(230, 81, 0))

        draw.text((605, 274), "Decision Gate:", font=font_sub, fill=(33, 33, 33))
        is_intact = (recv_sum == orig_sum)
        dec_color = (46, 125, 50) if is_intact else (198, 40, 40)
        dec_text = "VERIFIED (INTACT)" if is_intact else "FAILED (TAMPERED!)"
        draw.rectangle([(605, 296), (805, 336)], fill=(232, 245, 233) if is_intact else (255, 235, 238), outline=dec_color, width=2)
        draw.text((618, 308), dec_text, font=font_sub, fill=dec_color)

        # Arrows: Channel -> Receiver
        draw.line([(532, 215), (588, 215)], fill=(229, 57, 53), width=3)
        draw.polygon([(588, 210), (588, 220), (598, 215)], fill=(229, 57, 53))

        # Bottom summary pill
        draw.rectangle([(30, 380), (width - 30, 408)], fill=(245, 245, 245), outline=(224, 224, 224))
        draw.text((45, 388), f"Mathematical Basis: Checksum C = ∑ ASCII(char). Detection: C(Received) ≠ C(Sent) detects any single or multi-character mutation.", font=font_small, fill=(66, 66, 66))

        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    # =========================================================================
    # 3. CAESAR CIPHER SHIFT WHEEL & MODULAR MAPPING DIAGRAM
    # =========================================================================
    @classmethod
    def generate_caesar_cipher_diagram(
        cls,
        dest_path: Path,
        shift: int = 3,
        width: int = 860,
        height: int = 400,
    ) -> Path:
        """Renders visual Caesar Cipher shift mapping and modular wheel."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_title = cls._get_font(15, bold=True)
        font_sub = cls._get_font(12, bold=True)
        font_mono = cls._get_font(12, mono=True)
        font_small = cls._get_font(10)

        # Header
        draw.rectangle([(0, 0), (width, 42)], fill=(30, 41, 59))
        draw.text((20, 12), f"Caesar Cipher Cryptographic Model (Fixed Shift k = {shift})", font=font_title, fill=(255, 255, 255))

        # Plaintext Alphabet vs Ciphertext Alphabet Table
        plain_alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        cipher_alpha = plain_alpha[shift:] + plain_alpha[:shift]

        cell_w = 30
        cell_h = 32
        start_x = (width - len(plain_alpha) * cell_w) // 2
        top_y = 65

        # Plaintext Row
        draw.text((start_x, top_y - 18), "Plaintext Alphabet (P):", font=font_sub, fill=(15, 23, 42))
        for i, ch in enumerate(plain_alpha):
            x = start_x + i * cell_w
            draw.rectangle([(x, top_y), (x + cell_w, top_y + cell_h)], fill=(241, 245, 249), outline=(148, 163, 184))
            draw.text((x + 9, top_y + 8), ch, font=font_mono, fill=(15, 23, 42))

        # Downward Shift Arrows
        arrow_y = top_y + cell_h + 4
        for i in range(len(plain_alpha)):
            x = start_x + i * cell_w + cell_w // 2
            draw.line([(x, arrow_y), (x, arrow_y + 16)], fill=(59, 130, 246), width=2)
            draw.polygon([(x - 3, arrow_y + 14), (x + 3, arrow_y + 14), (x, arrow_y + 19)], fill=(59, 130, 246))

        # Ciphertext Row
        c_top_y = arrow_y + 24
        draw.text((start_x, c_top_y - 18), f"Ciphertext Alphabet (C = (P + {shift}) mod 26):", font=font_sub, fill=(30, 58, 138))
        for i, ch in enumerate(cipher_alpha):
            x = start_x + i * cell_w
            draw.rectangle([(x, c_top_y), (x + cell_w, c_top_y + cell_h)], fill=(219, 234, 254), outline=(59, 130, 246))
            draw.text((x + 9, c_top_y + 8), ch, font=font_mono, fill=(30, 58, 138))

        # Visual Example Transformation Box
        demo_y = c_top_y + cell_h + 35
        draw.rounded_rectangle([(start_x, demo_y), (start_x + 380, demo_y + 120)], radius=6, fill=(248, 250, 252), outline=(203, 213, 225), width=2)
        draw.text((start_x + 16, demo_y + 12), "Demonstration Transformations:", font=font_sub, fill=(15, 23, 42))

        demos = [
            ("ATTACK", "DWWDFN"),
            ("DAWOOD", "GDZRRJ"),
            ("SECURITY", "VHFXULWB"),
        ]
        dy = demo_y + 36
        for p, c in demos:
            draw.text((start_x + 16, dy), f"• {p}  →  {c}", font=font_mono, fill=(30, 58, 138))
            dy += 24

        # Modular Arithmetic Formula Box
        math_x = start_x + 400
        math_w = (start_x + len(plain_alpha) * cell_w) - math_x
        draw.rounded_rectangle([(math_x, demo_y), (math_x + math_w, demo_y + 120)], radius=6, fill=(240, 253, 244), outline=(134, 239, 172), width=2)
        draw.text((math_x + 16, demo_y + 12), "Cryptographic Formulas:", font=font_sub, fill=(22, 101, 52))
        draw.text((math_x + 16, demo_y + 40), "Encryption:  C = (P + k) mod 26", font=font_mono, fill=(21, 128, 61))
        draw.text((math_x + 16, demo_y + 66), "Decryption:  P = (C - k + 26) mod 26", font=font_mono, fill=(21, 128, 61))
        draw.text((math_x + 16, demo_y + 92), "Keyspace:    |K| = 25 (Vulnerable to Brute Force)", font=font_small, fill=(71, 85, 105))

        # Bottom summary pill
        draw.rectangle([(20, height - 32), (width - 20, height - 10)], fill=(241, 245, 249))
        draw.text((30, height - 26), "Security Note: Monoalphabetic substitution ciphers maintain letter frequency distributions, making them susceptible to frequency analysis.", font=font_small, fill=(100, 116, 139))

        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    # =========================================================================
    # 4. AES-128 SYMMETRIC BLOCK CIPHER ARCHITECTURE
    # =========================================================================
    @classmethod
    def generate_aes_architecture_diagram(
        cls,
        dest_path: Path,
        width: int = 860,
        height: int = 420,
    ) -> Path:
        """Renders authentic AES Block Cipher Architecture Diagram."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_title = cls._get_font(15, bold=True)
        font_sub = cls._get_font(12, bold=True)
        font_mono = cls._get_font(11, mono=True)
        font_small = cls._get_font(10)

        # Header
        draw.rectangle([(0, 0), (width, 42)], fill=(17, 24, 39))
        draw.text((20, 12), "Advanced Encryption Standard (AES-128) Architecture & Round Pipeline", font=font_title, fill=(255, 255, 255))

        # Left Column: Plaintext Block & Initial Round
        draw.rounded_rectangle([(30, 65), (200, 145)], radius=6, fill=(238, 242, 255), outline=(99, 102, 241), width=2)
        draw.text((45, 78), "128-bit Plaintext", font=font_sub, fill=(49, 46, 129))
        draw.text((45, 100), "16-byte State Matrix", font=font_mono, fill=(79, 70, 229))
        draw.text((45, 120), "4x4 byte array", font=font_small, fill=(107, 114, 128))

        # Initial Transformation
        draw.line([(115, 147), (115, 180)], fill=(99, 102, 241), width=2)
        draw.polygon([(112, 178), (118, 178), (115, 185)], fill=(99, 102, 241))

        draw.rounded_rectangle([(30, 185), (200, 245)], radius=6, fill=(254, 243, 199), outline=(245, 158, 11), width=2)
        draw.text((45, 198), "Initial Round:", font=font_sub, fill=(146, 64, 14))
        draw.text((45, 220), "AddRoundKey (K₀)", font=font_mono, fill=(180, 83, 9))

        # Arrow to Main Round Loop
        draw.line([(202, 215), (248, 215)], fill=(99, 102, 241), width=2)
        draw.polygon([(246, 212), (246, 218), (252, 215)], fill=(99, 102, 241))

        # Middle Column: Main Rounds (1 to 9)
        draw.rounded_rectangle([(250, 65), (550, 360)], radius=8, fill=(240, 253, 250), outline=(20, 184, 166), width=2)
        draw.rectangle([(250, 65), (550, 95)], fill=(20, 184, 166))
        draw.text((275, 72), "STANDARD ROUNDS (Rounds 1 through 9)", font=font_sub, fill=(255, 255, 255))

        steps = [
            ("1. SubBytes", "Non-linear byte substitution using Rijndael S-Box (Confusion)"),
            ("2. ShiftRows", "Cyclic permutation of rows (0, 1, 2, 3 bytes) (Diffusion)"),
            ("3. MixColumns", "Linear matrix multiplication over Galois Field GF(2⁸)"),
            ("4. AddRoundKey", "Bitwise XOR with 128-bit derived Round Key (Kᵣ)"),
        ]
        sy = 110
        for sname, sdesc in steps:
            draw.rounded_rectangle([(265, sy), (535, sy + 50)], radius=4, fill=(255, 255, 255), outline=(204, 251, 241))
            draw.text((275, sy + 8), sname, font=font_sub, fill=(15, 118, 110))
            draw.text((275, sy + 28), sdesc, font=font_small, fill=(75, 85, 99))
            sy += 60

        # Arrow from Rounds to Final Round
        draw.line([(552, 215), (598, 215)], fill=(20, 184, 166), width=2)
        draw.polygon([(596, 212), (596, 218), (602, 215)], fill=(20, 184, 166))

        # Right Column: Final Round 10 & Ciphertext Output
        draw.rounded_rectangle([(600, 65), (820, 230)], radius=8, fill=(254, 242, 242), outline=(239, 68, 68), width=2)
        draw.rectangle([(600, 65), (820, 95)], fill=(239, 68, 68))
        draw.text((630, 72), "FINAL ROUND (Round 10)", font=font_sub, fill=(255, 255, 255))

        draw.text((615, 110), "• SubBytes", font=font_mono, fill=(185, 28, 28))
        draw.text((615, 135), "• ShiftRows", font=font_mono, fill=(185, 28, 28))
        draw.text((615, 160), "• (No MixColumns)", font=font_small, fill=(156, 163, 175))
        draw.text((615, 185), "• AddRoundKey (K₁₀)", font=font_mono, fill=(185, 28, 28))

        # Arrow to Ciphertext
        draw.line([(710, 232), (710, 265)], fill=(239, 68, 68), width=2)
        draw.polygon([(707, 263), (713, 263), (710, 270)], fill=(239, 68, 68))

        draw.rounded_rectangle([(600, 270), (820, 360)], radius=6, fill=(238, 242, 255), outline=(99, 102, 241), width=2)
        draw.text((625, 285), "128-bit Ciphertext", font=font_sub, fill=(49, 46, 129))
        draw.text((620, 310), "Hex Fortress Output", font=font_mono, fill=(79, 70, 229))
        draw.text((620, 330), "Restored via Inverse S-Box", font=font_small, fill=(107, 114, 128))

        # Bottom summary pill
        draw.rectangle([(30, 380), (width - 30, 408)], fill=(249, 250, 251), outline=(229, 231, 235))
        draw.text((45, 388), "Key Features: 128-bit symmetric block size, 10 transform rounds, SPN (Substitution-Permutation Network) architecture.", font=font_small, fill=(55, 65, 81))

        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    # =========================================================================
    # 5. STATISTICAL MALWARE ANOMALY DETECTION (Z-SCORE) PLOT
    # =========================================================================
    @classmethod
    def generate_anomaly_detection_plot(
        cls,
        dest_path: Path,
        width: int = 860,
        height: int = 420,
    ) -> Path:
        """Renders authentic statistical anomaly detection plot with Gaussian curve and outlier markers."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np

            fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

            # Normal Distribution curve
            mu = 50.0
            sigma = 12.0
            x = np.linspace(10, 95, 300)
            y = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

            ax.plot(x, y, color="#1e3a8a", linewidth=2.5, label="Normal System Activity Distribution (N(μ, σ²))")

            # Normal Region fill (μ ± 2σ)
            norm_mask = (x >= mu - 2 * sigma) & (x <= mu + 2 * sigma)
            ax.fill_between(x[norm_mask], y[norm_mask], color="#3b82f6", alpha=0.15, label="Normal Activity Region (|Z| ≤ 2.0)")

            # Anomaly Threshold lines
            thresh_high = mu + 2.0 * sigma
            thresh_low = mu - 2.0 * sigma
            ax.axvline(thresh_high, color="#ef4444", linestyle="--", linewidth=1.8, label=f"Anomaly Threshold (|Z| = 2.0, x = {thresh_high:.1f})")
            ax.axvline(thresh_low, color="#ef4444", linestyle="--", linewidth=1.8)

            # Scatter sample data points
            normal_pts_x = [38, 44, 48, 51, 53, 56, 62]
            normal_pts_y = [(1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((px - mu) / sigma) ** 2) for px in normal_pts_x]
            ax.scatter(normal_pts_x, normal_pts_y, color="#059669", s=60, zorder=5, label="Benign Network Traffic Points")

            # Outlier points
            outlier_pts_x = [85, 92]
            outlier_pts_y = [(1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((px - mu) / sigma) ** 2) for px in outlier_pts_x]
            ax.scatter(outlier_pts_x, outlier_pts_y, color="#dc2626", marker="X", s=130, zorder=6, label="Detected Malware Outliers (Z > 2.0)")

            # Annotate outliers
            for px, py in zip(outlier_pts_x, outlier_pts_y):
                z_val = (px - mu) / sigma
                ax.annotate(
                    f"Outlier Spike!\nx={px}, Z={z_val:.2f}",
                    xy=(px, py),
                    xytext=(px - 14, py + 0.008),
                    arrowprops=dict(facecolor="#dc2626", shrink=0.08, width=1.5, headwidth=6),
                    fontsize=9,
                    fontweight="bold",
                    color="#991b1b",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#fee2e2", edgecolor="#ef4444", lw=1),
                )

            ax.set_title("Information Security: Malware Anomaly Detection via Z-Score Method", fontsize=13, fontweight="bold", pad=12, color="#0f172a")
            ax.set_xlabel("Feature Metric: Network Packet Frequency / Process Invocations per Sec", fontsize=10, color="#334155")
            ax.set_ylabel("Probability Density", fontsize=10, color="#334155")
            ax.grid(True, linestyle=":", alpha=0.6)
            ax.legend(loc="upper right", fontsize=8.5, framealpha=0.95)

            fig.tight_layout()
            fig.savefig(dest_path, format="png", dpi=120)
            plt.close(fig)
            return dest_path
        except Exception:
            # Pillow fallback if matplotlib encounters any issue
            return cls.generate_checksum_flow_diagram(dest_path)

    # =========================================================================
    # 6. HTTP CLIENT-SERVER PROTOCOL SEQUENCE LADDER DIAGRAM
    # =========================================================================
    @classmethod
    def generate_http_sequence_diagram(
        cls,
        dest_path: Path,
        scenario: str = "http_basic",
        width: int = 860,
        height: int = 420,
    ) -> Path:
        """Renders authentic HTTP Client-Server packet transaction sequence ladder."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_title = cls._get_font(15, bold=True)
        font_sub = cls._get_font(12, bold=True)
        font_mono = cls._get_font(11, mono=True)
        font_small = cls._get_font(10)

        # Header
        draw.rectangle([(0, 0), (width, 42)], fill=(15, 23, 42))
        draw.text((20, 12), f"Network Protocol Analysis: HTTP Exchange Sequence ({scenario.replace('_', ' ').title()})", font=font_title, fill=(255, 255, 255))

        client_x = 180
        server_x = 680

        # Lifeline headers
        draw.rounded_rectangle([(client_x - 90, 58), (client_x + 90, 94)], radius=6, fill=(238, 242, 255), outline=(99, 102, 241), width=2)
        draw.text((client_x - 70, 68), "Client (Browser)\n192.168.1.105", font=font_sub, fill=(49, 46, 129))

        draw.rounded_rectangle([(server_x - 90, 58), (server_x + 90, 94)], radius=6, fill=(240, 253, 244), outline=(34, 197, 94), width=2)
        draw.text((server_x - 82, 68), "Server (gaia.cs.umass.edu)\n128.119.245.12", font=font_sub, fill=(20, 83, 45))

        # Vertical lifelines
        draw.line([(client_x, 96), (client_x, 380)], fill=(148, 163, 184), width=2)
        draw.line([(server_x, 96), (server_x, 380)], fill=(148, 163, 184), width=2)

        if scenario == "http_conditional":
            exchanges = [
                (120, "1. HTTP GET /wireshark-labs/HTTP-wireshark-file2.html HTTP/1.1", True, (37, 99, 235), True),
                (155, "2. HTTP/1.1 200 OK  (Last-Modified: Tue, 27 Oct 2026, File Cached)", False, (22, 163, 74), True),
                (200, "3. Browser Refresh / Subsequent Visit (Local Cache Valid)", True, (100, 116, 139), False),
                (235, "4. HTTP GET /wireshark-labs/HTTP-wireshark-file2.html HTTP/1.1", True, (217, 119, 6), True),
                (265, "   [Header: If-Modified-Since: Tue, 27 Oct 2026 06:12:00 GMT]", True, (180, 83, 9), False),
                (310, "5. HTTP/1.1 304 Not Modified  (Zero payload, Bandwidth Conserved)", False, (180, 83, 9), True),
                (350, "6. Browser renders document directly from local disk cache", True, (16, 185, 129), False),
            ]
            summary_txt = "Protocol Summary: Demonstrates Conditional GET. The 304 Not Modified response prevents retransmission of unchanged web pages."
        elif scenario == "http_long_doc":
            exchanges = [
                (120, "1. HTTP GET /wireshark-labs/HTTP-wireshark-file3.html (Bill of Rights)", True, (37, 99, 235), True),
                (160, "2. TCP Segment #2 [Seq=1, Len=1460 bytes] Port 80 → 54138", False, (14, 116, 144), False),
                (195, "3. TCP Segment #3 [Seq=1461, Len=1460 bytes] Port 80 → 54138", False, (14, 116, 144), False),
                (230, "4. TCP Segment #4 [Seq=2921, Len=1460 bytes] Port 80 → 54138", False, (14, 116, 144), False),
                (265, "5. HTTP/1.1 200 OK [4 Reassembled TCP Segments: 4500 bytes total]", False, (22, 163, 74), True),
                (310, "6. TCP [ACK] Ack=4501 Win=64240 Len=0", True, (100, 116, 139), False),
                (345, "7. TCP [FIN, ACK] Connection Teardown Complete", True, (100, 116, 139), False),
            ]
            summary_txt = "Protocol Summary: Demonstrates TCP segmentation and PDU reassembly. The 4500-byte file exceeds Ethernet MTU and is split into 4 segments."
        elif scenario == "http_embedded":
            exchanges = [
                (120, "1. HTTP GET /wireshark-labs/HTTP-wireshark-file4.html HTTP/1.1", True, (37, 99, 235), True),
                (155, "2. HTTP/1.1 200 OK (HTML document contains 2 <img> reference tags)", False, (22, 163, 74), True),
                (200, "3. HTTP GET /wireshark-labs/cover_9e.jpg (gaia.cs.umass.edu)", True, (99, 102, 241), True),
                (235, "4. HTTP GET /pearson.png (media.pearsoncmg.com) [Parallel TCP]", True, (168, 85, 247), True),
                (280, "5. HTTP/1.1 200 OK [cover_9e.jpg image/jpeg, Len=1514 bytes]", False, (99, 102, 241), True),
                (315, "6. HTTP/1.1 200 OK [pearson.png image/png, Len=1514 bytes]", False, (168, 85, 247), True),
                (350, "7. Browser renders base HTML page with both downloaded images in parallel", True, (16, 185, 129), False),
            ]
            summary_txt = "Protocol Summary: Demonstrates embedded object retrieval. The browser sends multiple concurrent GET requests to fetch images in parallel."
        elif scenario == "http_auth":
            exchanges = [
                (120, "1. HTTP GET /wireshark-labs/protected_pages/HTTP-wireshark-file5.html", True, (37, 99, 235), True),
                (160, "2. HTTP/1.1 401 Unauthorized [WWW-Authenticate: Basic realm=...]", False, (220, 38, 38), True),
                (205, "3. User enters credentials: wireshark-students : network", True, (100, 116, 139), False),
                (245, "4. HTTP GET (includes Authorization: Basic d2lyZXNoYXJrLXN0dWRlbnRzOm5ldHdvcms=)", True, (217, 119, 6), True),
                (290, "5. HTTP/1.1 200 OK (text/html, Access Granted to protected resource)", False, (22, 163, 74), True),
                (335, "6. Security note: Basic Auth transmits Base64 credentials unencrypted over plaintext", True, (220, 38, 38), False),
            ]
            summary_txt = "Protocol Summary: Demonstrates HTTP Basic Authentication. Unprotected credentials can be intercepted by eavesdroppers without HTTPS."
        else:
            exchanges = [
                (120, "1. TCP [SYN] Port 54124 → 80", True, (100, 116, 139), False),
                (150, "2. TCP [SYN, ACK] Port 80 → 54124", False, (100, 116, 139), False),
                (180, "3. TCP [ACK] Handshake Complete", True, (100, 116, 139), False),
                (215, "4. HTTP GET /wireshark-labs/HTTP-wireshark-file1.html HTTP/1.1", True, (37, 99, 235), True),
                (255, "5. HTTP/1.1 200 OK  (Content-Type: text/html, Len=682 bytes)", False, (22, 163, 74), True),
                (295, "6. TCP [FIN, ACK] Seq=471 Ack=629", True, (100, 116, 139), False),
                (330, "7. TCP [ACK] Seq=629 Ack=472 Connection Closed", False, (100, 116, 139), False),
            ]
            summary_txt = "Protocol Summary: Demonstrates fundamental HTTP request-response transaction over standard TCP transport."

        for y, label, is_forward, col, is_bold in exchanges:
            f_use = font_mono if is_bold else font_small
            if is_forward:
                draw.line([(client_x, y), (server_x, y)], fill=col, width=2 if is_bold else 1)
                draw.polygon([(server_x - 10, y - 4), (server_x - 10, y + 4), (server_x, y)], fill=col)
                draw.text((client_x + 25, y - 16), label, font=f_use, fill=col)
            else:
                draw.line([(server_x, y), (client_x, y)], fill=col, width=2 if is_bold else 1)
                draw.polygon([(client_x + 10, y - 4), (client_x + 10, y + 4), (client_x, y)], fill=col)
                draw.text((client_x + 25, y - 16), label, font=f_use, fill=col)

        # Bottom summary pill
        draw.rectangle([(20, height - 28), (width - 20, height - 6)], fill=(248, 250, 252))
        draw.text((30, height - 22), summary_txt, font=font_small, fill=(71, 85, 105))

        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    # =========================================================================
    # 7. CIA TRIAD SECURITY ARCHITECTURE DIAGRAM (FOR IS LAB 01)
    # =========================================================================
    @classmethod
    def generate_cia_triad_diagram(
        cls,
        dest_path: Path,
        width: int = 860,
        height: int = 440,
    ) -> Path:
        """Renders authentic CIA Triad Information Security Architecture model."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_title = cls._get_font(15, bold=True)
        font_sub = cls._get_font(12, bold=True)
        font_mono = cls._get_font(11, mono=True)
        font_small = cls._get_font(10)

        # Title Bar
        draw.rectangle([(0, 0), (width, 42)], fill=(15, 23, 42))
        draw.text((20, 12), "Information Security Foundations: The CIA Triad & Defensive Controls", font=font_title, fill=(255, 255, 255))

        col_w = 250
        gap = 25
        top_y = 65
        box_h = 300

        # Column 1: Confidentiality (Blue)
        c1_x = 35
        draw.rounded_rectangle([(c1_x, top_y), (c1_x + col_w, top_y + box_h)], radius=8, fill=(238, 242, 255), outline=(79, 70, 229), width=2)
        draw.rectangle([(c1_x, top_y), (c1_x + col_w, top_y + 36)], fill=(79, 70, 229))
        draw.text((c1_x + 40, top_y + 9), "CONFIDENTIALITY", font=font_sub, fill=(255, 255, 255))

        draw.text((c1_x + 14, top_y + 48), "Objective: Prevent Unauthorized Disclosure", font=font_small, fill=(67, 56, 202))
        c1_bullets = [
            ("• Symmetric Key Encryption", "AES-128, Fernet, bitwise XOR"),
            ("• Access Control Lists (ACLs)", "Username / Password authentication"),
            ("• Cryptographic Key Secrets", "Secure generation & key storage"),
            ("• Transport Layer Security", "TLS/HTTPS encrypted tunnels"),
        ]
        by = top_y + 80
        for title_b, sub_b in c1_bullets:
            draw.text((c1_x + 14, by), title_b, font=font_sub, fill=(30, 27, 75))
            draw.text((c1_x + 24, by + 18), sub_b, font=font_small, fill=(79, 70, 229))
            by += 44

        # Column 2: Integrity (Green)
        c2_x = c1_x + col_w + gap
        draw.rounded_rectangle([(c2_x, top_y), (c2_x + col_w, top_y + box_h)], radius=8, fill=(240, 253, 244), outline=(34, 197, 94), width=2)
        draw.rectangle([(c2_x, top_y), (c2_x + col_w, top_y + 36)], fill=(34, 197, 94))
        draw.text((c2_x + 65, top_y + 9), "INTEGRITY", font=font_sub, fill=(255, 255, 255))

        draw.text((c2_x + 14, top_y + 48), "Objective: Prevent Unauthorized Alteration", font=font_small, fill=(21, 128, 61))
        c2_bullets = [
            ("• Additive Character Checksums", "Sum modulo verification & error checks"),
            ("• Cryptographic Hash Functions", "SHA-256, HMAC digest validation"),
            ("• Digital Signatures", "Non-repudiation & origin verification"),
            ("• Tamper Detection Audits", "Flags modified packets during transit"),
        ]
        by = top_y + 80
        for title_b, sub_b in c2_bullets:
            draw.text((c2_x + 14, by), title_b, font=font_sub, fill=(20, 83, 45))
            draw.text((c2_x + 24, by + 18), sub_b, font=font_small, fill=(22, 163, 74))
            by += 44

        # Column 3: Availability (Amber/Gold)
        c3_x = c2_x + col_w + gap
        draw.rounded_rectangle([(c3_x, top_y), (c3_x + col_w, top_y + box_h)], radius=8, fill=(254, 243, 199), outline=(245, 158, 11), width=2)
        draw.rectangle([(c3_x, top_y), (c3_x + col_w, top_y + 36)], fill=(245, 158, 11))
        draw.text((c3_x + 55, top_y + 9), "AVAILABILITY", font=font_sub, fill=(255, 255, 255))

        draw.text((c3_x + 14, top_y + 48), "Objective: Ensure Timely, Reliable Access", font=font_small, fill=(180, 83, 9))
        c3_bullets = [
            ("• Fault-Tolerant Redundancy", "Clustered server mirrors & load balancing"),
            ("• DDoS Mitigation", "Rate limiting & anomalous traffic filters"),
            ("• Statistical Outlier Monitoring", "Z-Score network traffic anomaly alerts"),
            ("• Disaster Recovery & Backups", "Immutable snapshots & quick restoration"),
        ]
        by = top_y + 80
        for title_b, sub_b in c3_bullets:
            draw.text((c3_x + 14, by), title_b, font=font_sub, fill=(120, 53, 15))
            draw.text((c3_x + 24, by + 18), sub_b, font=font_small, fill=(217, 119, 6))
            by += 44

        # Bottom Foundation Banner
        draw.rounded_rectangle([(35, top_y + box_h + 16), (width - 35, height - 12)], radius=6, fill=(248, 250, 252), outline=(203, 213, 225), width=1)
        draw.text((50, top_y + box_h + 24), "Supporting Pillars: Authentication (Identity Proofing) · Authorization (Least Privilege) · Non-Repudiation (Audit Trail)", font=font_small, fill=(51, 65, 85))

        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    # =========================================================================
    # 8. SYMMETRIC ENCRYPTION DATA FLOW PIPELINE (FOR IS LAB 01)
    # =========================================================================
    @classmethod
    def generate_symmetric_crypto_flow_diagram(
        cls,
        dest_path: Path,
        sample_msg: str = "Dawood University",
        sample_key: str = "SecretKeyK",
        width: int = 860,
        height: int = 420,
    ) -> Path:
        """Renders authentic Symmetric Key Cryptography Data Flow diagram."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        font_title = cls._get_font(15, bold=True)
        font_sub = cls._get_font(12, bold=True)
        font_mono = cls._get_font(11, mono=True)
        font_small = cls._get_font(10)

        # Title
        draw.rectangle([(0, 0), (width, 42)], fill=(24, 43, 73))
        draw.text((20, 12), "Information Security Model: Symmetric Key Cryptography Pipeline", font=font_title, fill=(255, 255, 255))

        # 1. Plaintext Box (Left)
        draw.rounded_rectangle([(30, 80), (190, 200)], radius=6, fill=(243, 246, 252), outline=(41, 98, 255), width=2)
        draw.text((45, 95), "Plaintext (P):", font=font_sub, fill=(33, 33, 33))
        draw.rectangle([(45, 120), (175, 160)], fill=(255, 255, 255), outline=(189, 189, 189))
        draw.text((52, 132), f'"{sample_msg[:12]}"', font=font_mono, fill=(13, 71, 161))
        draw.text((45, 175), "Readable Data", font=font_small, fill=(100, 116, 139))

        # Arrow to Encryption
        draw.line([(192, 140), (248, 140)], fill=(41, 98, 255), width=2)
        draw.polygon([(246, 136), (246, 144), (252, 140)], fill=(41, 98, 255))

        # 2. Encryption Engine
        draw.rounded_rectangle([(250, 70), (410, 210)], radius=6, fill=(238, 242, 255), outline=(99, 102, 241), width=2)
        draw.rectangle([(250, 70), (410, 100)], fill=(99, 102, 241))
        draw.text((275, 76), "ENCRYPTION (E)", font=font_sub, fill=(255, 255, 255))
        draw.text((265, 115), "Shared Secret Key (K)", font=font_mono, fill=(49, 46, 129))
        draw.text((265, 140), f"Key: '{sample_key}'", font=font_small, fill=(79, 70, 229))
        draw.text((265, 175), "C = E_K(P) = P ⊕ K", font=font_mono, fill=(30, 27, 75))

        # Arrow to Insecure Channel
        draw.line([(412, 140), (468, 140)], fill=(99, 102, 241), width=2)
        draw.polygon([(466, 136), (466, 144), (472, 140)], fill=(99, 102, 241))

        # 3. Insecure Channel / Ciphertext (Middle)
        draw.rounded_rectangle([(470, 80), (610, 200)], radius=6, fill=(254, 242, 242), outline=(239, 68, 68), width=2)
        draw.text((480, 95), "Ciphertext (C):", font=font_sub, fill=(185, 28, 28))
        draw.rectangle([(480, 120), (600, 160)], fill=(255, 255, 255), outline=(252, 165, 165))
        draw.text((486, 132), "0x44 0x1f 0x0a...", font=font_mono, fill=(185, 28, 28))
        draw.text((480, 175), "Insecure Channel", font=font_small, fill=(220, 38, 38))

        # Arrow to Decryption
        draw.line([(612, 140), (668, 140)], fill=(239, 68, 68), width=2)
        draw.polygon([(666, 136), (666, 144), (672, 140)], fill=(239, 68, 68))

        # 4. Decryption Engine
        draw.rounded_rectangle([(670, 70), (830, 210)], radius=6, fill=(240, 253, 244), outline=(34, 197, 94), width=2)
        draw.rectangle([(670, 70), (830, 100)], fill=(34, 197, 94))
        draw.text((695, 76), "DECRYPTION (D)", font=font_sub, fill=(255, 255, 255))
        draw.text((685, 115), "Shared Secret Key (K)", font=font_mono, fill=(20, 83, 45))
        draw.text((685, 140), f"Key: '{sample_key}'", font=font_small, fill=(22, 163, 74))
        draw.text((685, 175), "P = D_K(C) = C ⊕ K", font=font_mono, fill=(20, 83, 45))

        # Restored Plaintext Box below
        draw.rounded_rectangle([(250, 240), (610, 340)], radius=6, fill=(240, 253, 244), outline=(74, 222, 128), width=2)
        draw.text((265, 255), "Decrypted Plaintext Output:", font=font_sub, fill=(22, 101, 52))
        draw.text((265, 285), f'Recovered Text: "{sample_msg}"', font=font_mono, fill=(21, 128, 61))
        draw.text((265, 312), "Verification Status: SUCCESS (Matches Original Plaintext Bit-for-Bit)", font=font_small, fill=(22, 101, 52))

        # Arrow from Decryption to Recovered
        draw.line([(750, 212), (750, 290), (612, 290)], fill=(34, 197, 94), width=2)
        draw.polygon([(614, 286), (614, 294), (608, 290)], fill=(34, 197, 94))

        # Bottom summary pill
        draw.rectangle([(30, height - 36), (width - 30, height - 10)], fill=(248, 250, 252), outline=(226, 232, 240))
        draw.text((45, height - 28), "Mathematical Property: Involutory XOR operation satisfies (P ⊕ K) ⊕ K = P. Same key is required for confidentiality.", font=font_small, fill=(71, 85, 105))

        img.save(dest_path, "PNG", optimize=True)
        return dest_path
