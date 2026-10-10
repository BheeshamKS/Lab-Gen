import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

out_dir = Path("/mnt/SSD_Storage/Coding/Lab-Gen/assignments/Database_Systems_Assignment_01/images")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Diagram for Q1: University Information System Database Architecture
def create_uis_diagram():
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Title
    ax.text(5, 5.6, "University Information System (UIS) Database Architecture", 
            ha='center', va='center', fontsize=12, fontweight='bold', color='#111827', fontfamily='sans-serif')
    
    # Central Database Node (Cylinder-like shape representation)
    center_box = patches.FancyBboxPatch((3.7, 2.1), 2.6, 1.6, boxstyle="round,pad=0.15", 
                                       facecolor='#EEF2F6', edgecolor='#1E3A8A', linewidth=2)
    ax.add_patch(center_box)
    ax.text(5, 3.1, "CENTRAL UNIVERSITY\nDATABASE (DBMS)", 
            ha='center', va='center', fontsize=10, fontweight='bold', color='#1E3A8A', fontfamily='sans-serif')
    ax.text(5, 2.45, "• Student Records  • Faculty Info\n• Course Catalog   • Fee Transactions", 
            ha='center', va='center', fontsize=8, color='#374151', fontfamily='sans-serif')
    
    # Surrounding user nodes
    nodes = [
        {"name": "Students Portal", "desc": "• Course Registration\n• View Grades & CGPA\n• Fee Challans", 
         "pos": (0.4, 3.4), "box_w": 2.5, "box_h": 1.4, "color": "#F0FDF4", "edge": "#16A34A", "line_from": (2.9, 4.1), "line_to": (3.7, 3.4)},
        {"name": "Faculty / Lecturers", "desc": "• Attendance Records\n• Grade Submission\n• Course Rosters", 
         "pos": (7.1, 3.4), "box_w": 2.5, "box_h": 1.4, "color": "#EFF6FF", "edge": "#2563EB", "line_from": (7.1, 4.1), "line_to": (6.3, 3.4)},
        {"name": "Examination Cell", "desc": "• Result Verification\n• Official Transcripts\n• Grade Curve Audit", 
         "pos": (0.4, 0.5), "box_w": 2.5, "box_h": 1.4, "color": "#FEF3C7", "edge": "#D97706", "line_from": (2.9, 1.2), "line_to": (3.7, 2.4)},
        {"name": "Finance & Accounts", "desc": "• Fee Reconciliation\n• Admit Card Clearance\n• Staff Payroll", 
         "pos": (7.1, 0.5), "box_w": 2.5, "box_h": 1.4, "color": "#FDF2F8", "edge": "#DB2777", "line_from": (7.1, 1.2), "line_to": (6.3, 2.4)}
    ]
    
    for n in nodes:
        box = patches.FancyBboxPatch(n["pos"], n["box_w"], n["box_h"], boxstyle="round,pad=0.1", 
                                     facecolor=n["color"], edgecolor=n["edge"], linewidth=1.5)
        ax.add_patch(box)
        cx = n["pos"][0] + n["box_w"] / 2
        ax.text(cx, n["pos"][1] + n["box_h"] - 0.28, n["name"], 
                ha='center', va='center', fontsize=9.5, fontweight='bold', color='#111827', fontfamily='sans-serif')
        ax.text(cx, n["pos"][1] + 0.45, n["desc"], 
                ha='center', va='center', fontsize=8, color='#374151', fontfamily='sans-serif')
        
        # Bidirectional arrows
        ax.annotate("", xy=n["line_to"], xytext=n["line_from"],
                    arrowprops=dict(arrowstyle="<->", color=n["edge"], lw=1.5, shrinkA=5, shrinkB=5))
    
    plt.tight_layout()
    diagram_path = out_dir / "uis_architecture.png"
    plt.savefig(diagram_path, bbox_inches='tight', dpi=200)
    plt.close()
    print("Saved:", diagram_path)

# 2. Diagram for Q2 & Q4: Multi-Layer Database Security Architecture
def create_security_diagram():
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')
    
    ax.text(5, 4.6, "Multi-Layer University Database Security Architecture", 
            ha='center', va='center', fontsize=12, fontweight='bold', color='#111827', fontfamily='sans-serif')
    
    layers = [
        {"title": "1. User Access Layer", "desc": "Role-Based Access Control (RBAC), Strong Authentication (MFA, Salted Hashing)", 
         "y": 3.4, "color": "#EFF6FF", "edge": "#2563EB"},
        {"title": "2. Network / In-Transit Layer", "desc": "TLS 1.3 / HTTPS Encryption, Secure Sockets, Firewall & MITM Protection", 
         "y": 2.3, "color": "#F0FDF4", "edge": "#16A34A"},
        {"title": "3. DBMS & Row-Level Layer", "desc": "Row-Level Security (RLS: CURRENT_USER()), DCL Privilege Revocation, Secure Views", 
         "y": 1.2, "color": "#FEF3C7", "edge": "#D97706"},
        {"title": "4. Storage & Audit Layer", "desc": "Transparent Data Encryption (AES-256 TDE), Immutable Audit Logs & Triggers", 
         "y": 0.1, "color": "#FDF2F8", "edge": "#DB2777"}
    ]
    
    for l in layers:
        box = patches.FancyBboxPatch((0.8, l["y"]), 8.4, 0.85, boxstyle="round,pad=0.08", 
                                     facecolor=l["color"], edgecolor=l["edge"], linewidth=1.5)
        ax.add_patch(box)
        ax.text(1.1, l["y"] + 0.55, l["title"], fontsize=9.5, fontweight='bold', color='#111827', fontfamily='sans-serif')
        ax.text(1.1, l["y"] + 0.22, l["desc"], fontsize=8.5, color='#374151', fontfamily='sans-serif')
    
    plt.tight_layout()
    diagram_path = out_dir / "database_security_layers.png"
    plt.savefig(diagram_path, bbox_inches='tight', dpi=200)
    plt.close()
    print("Saved:", diagram_path)

create_uis_diagram()
create_security_diagram()
