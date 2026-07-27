import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.http import HttpResponse
from django.utils import timezone
import datetime

def generate_verification_certificate(evidence):
    """
    ULTIMATE FORENSIC REPORT ENGINE:
    Fixed spacing, local Kampala time, and collision-free layout.
    """
    # 1. TIMEZONE CORRECTION (Kampala UTC+3)
    local_time = timezone.localtime(timezone.now())
    time_str = local_time.strftime('%Y-%m-%d %H:%M:%S %p')

    # 2. INITIALIZE RESPONSE
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Forensic_Report_{evidence.title}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # --- BRAND COLORS ---
    DARK_NAVY = colors.HexColor("#1B2631")
    FORENSIC_GREEN = colors.HexColor("#27AE60")
    CRITICAL_RED = colors.HexColor("#C0392B")
    SOFT_GREY = colors.HexColor("#F8F9F9")

    # --- HEADER BLOCK (Fixed at top) ---
    p.setFillColor(DARK_NAVY)
    p.rect(0, 730, width, 70, fill=1) # Dark top bar
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(40, 765, "FORENSIC AUTHENTICITY REPORT")
    
    p.setFont("Helvetica", 9)
    p.drawRightString(width - 40, 775, "AF Mpanga DEVS Protocol v3.0")
    p.drawRightString(width - 40, 760, f"Report Generated: {time_str}")

    # --- INTEGRITY VERDICT STAMP (High Visibility) ---
    status = getattr(evidence, 'integrity_status', 'PENDING').upper()
    if "INTACT" in status or "VERIFIED" in status:
        p.setFillColor(FORENSIC_GREEN)
        stamp_text = "EVIDENCE STATUS: VERIFIED INTACT"
    elif "FAILED" in status or "TAMPERED" in status:
        p.setFillColor(CRITICAL_RED)
        stamp_text = "EVIDENCE STATUS: TAMPERED / INVALID"
    else:
        p.setFillColor(colors.orange)
        stamp_text = "EVIDENCE STATUS: PENDING ANALYSIS"

    p.rect(40, 680, width - 80, 35, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, 692, stamp_text)

    # --- SECTION I: EVIDENCE DATA (Spaced to avoid overlap) ---
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 650, "I. EVIDENCE IDENTIFICATION")
    p.setStrokeColor(DARK_NAVY)
    p.setLineWidth(1)
    p.line(40, 645, 230, 645)

    p.setFont("Helvetica", 10)
    # Defining a specific Y-start and step to prevent "confusion"
    data_y = 625
    data_points = [
        ("Exhibit UUID:", str(evidence.id)),
        ("Evidence Title:", evidence.title),
        ("Original MIME:", evidence.mime_type or "Unknown"),
        ("Custodian:", evidence.uploaded_by.username if evidence.uploaded_by else "System Admin"),
        ("Vault Entry:", evidence.uploaded_at.strftime('%Y-%m-%d %H:%M')),
    ]

    for label, value in data_points:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, data_y, label)
        p.setFont("Helvetica", 10)
        p.drawString(160, data_y, value)
        data_y -= 18  # Consistent downward step

    # --- SHA-256 FINGERPRINT BOX (Isolated for clarity) ---
    p.setFillColor(SOFT_GREY)
    p.setStrokeColor(colors.lightgrey)
    p.rect(40, 520, width - 80, 45, fill=1)
    
    p.setFillColor(DARK_NAVY)
    p.setFont("Courier-Bold", 10)
    p.drawString(50, 545, "DIGITAL FINGERPRINT (SHA-256):")
    p.setFont("Courier", 9)
    p.drawString(50, 532, str(evidence.original_hash))

    # --- SECTION II: CHAIN OF CUSTODY (Audit Trail) ---
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, 485, "II. CHAIN OF CUSTODY LOGS")
    p.line(40, 480, 230, 480)
    
    log_y = 460
    logs = evidence.audit_logs.all().order_by('-timestamp')[:6] # Show last 6 events
    
    # Table Header for Logs
    p.setFont("Helvetica-Bold", 9)
    p.drawString(50, log_y, "TIMESTAMP (LST)")
    p.drawString(160, log_y, "ACTION PERFORMED")
    p.drawString(400, log_y, "OPERATOR")
    p.line(40, log_y - 4, width - 40, log_y - 4)
    
    log_y -= 18
    p.setFont("Helvetica", 9)
    for log in logs:
        # Convert audit log time to local Kampala time
        log_time = timezone.localtime(log.timestamp).strftime('%Y-%m-%d %H:%M')
        p.drawString(50, log_y, log_time)
        p.drawString(160, log_y, log.action[:45])
        p.drawString(400, log_y, log.user.username if log.user else "System")
        log_y -= 15

    # --- SECTION III: FORENSIC ALERT (Only shows if tampered) ---
    if "FAILED" in status or "TAMPERED" in status:
        p.setFillColor(colors.HexColor("#FDEDEC"))
        p.rect(40, log_y - 40, width - 80, 30, fill=1)
        p.setFillColor(CRITICAL_RED)
        p.setFont("Helvetica-Bold", 10)
        details = getattr(evidence, 'tamper_details', 'Binary mismatch detected during routine scan.')
        p.drawString(50, log_y - 30, f"ALERT: {details}")

    # --- QR CODE & FOOTER ---
    # The URL links directly to the verification page in your dashboard
    qr_data = f"DEVS-VERIFY-{evidence.id}-{evidence.original_hash[:10]}"
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="#1B2631", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_buffer.seek(0)
    
    p.drawImage(ImageReader(qr_buffer), width - 130, 40, width=90, height=90)
    
    p.setFillColor(colors.grey)
    p.setFont("Helvetica-Bold", 8)
    p.drawRightString(width - 40, 35, "SECURE DIGITAL VERIFICATION")
    
    p.setFont("Helvetica-Oblique", 7)
    p.drawCentredString(width / 2, 20, "This certificate is a legally admissible forensic document generated by DEVS. Hashing algorithm: SHA-256.")

    # --- FINALIZE ---
    p.showPage()
    p.save()
    return response