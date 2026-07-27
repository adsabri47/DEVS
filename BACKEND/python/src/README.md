# ⚖️ Digital Evidence Verification System (DEVS)

### **What is DEVS?**
DEVS is a secure backend system designed for law firms (like AF Mpanga) to 
manage digital evidence. Its main job is to ensure that files (images, 
videos, PDFs) are not tampered with or changed once they are uploaded.

### **🚀 How to Start the System**
1. **Activate Environment:** `.\venv\Scripts\activate`
2. **Install Libraries:** `pip install -r requirements.txt`
3. **Set up Database:** `python manage.py migrate`
4. **Collect CSS/JS:** `python manage.py collectstatic`
5. **Start Production Engine:** `waitress-serve --port=8000 DEVS_PROJECT.wsgi:application`

### **🛡️ Security Protocols**
* **SHA-256 Hashing:** Every file gets a "Digital Fingerprint." If even one 
    pixel in a photo changes, the system detects it.
* **MIME Validation:** The system checks the "Magic Numbers" of a file to 
    make sure no one uploads a virus disguised as a document.
* **Audit Logging:** Every action (Upload, Verify, Download) is recorded in 
    a permanent log to maintain the "Chain of Custody."
* **Size Limit:** A 500MB cap is enforced to prevent server crashes.

### **🧪 The Integrity Test (Demo Steps)**
1.  **Upload:** Add a text file to the system.
2.  **Verify:** Run the integrity check; it should say "MATCH."
3.  **Tamper:** Open the file in the `media/exhibits` folder and change a word.
4.  **Result:** Run the check again; the system will flag it as "FAILED/TAMPERED."


<!-- waitress-serve --port=8000 DEVS_PROJECT.wsgi:application -->