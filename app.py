import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Railway's assigned port
    app.run(host="0.0.0.0", port=port, debug=True)
import hashlib
from flask import Flask, render_template, request
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
import pytesseract
from web3 import Web3

# ✅ Blockchain Setup
INFURA_URL = "https://sepolia.infura.io/v3/67988122a30f4f0086693063eeacbb1e"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

CONTRACT_ADDRESS = "0x9B6bfAB5a79551ed423A83466002082bb3CE9227"
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "documentHash", "type": "string"}],
        "name": "verifyCertificate",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"},
            {"internalType": "string", "name": "", "type": "string"},
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# ✅ Flask Setup
app = Flask(__name__, static_folder="static")
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ✅ Generate Hash from PDF (Text + OCR)
def generate_text_hash(pdf_path):
    try:
        # Extract text from PDF
        text = extract_text(pdf_path).strip()

        # If no text, use OCR
        if not text or len(text) < 50:
            print("🔍 No text found. Running OCR...")
            images = convert_from_path(pdf_path)
            ocr_text = " ".join([pytesseract.image_to_string(img) for img in images])
            text += "\n" + ocr_text  # Combine extracted text

        if not text.strip():
            return None  # No valid text found

        return hashlib.sha256(text.encode()).hexdigest()

    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        return None


# ✅ Verify Certificate on Blockchain
def verify_certificate(document_hash):
    try:
        is_valid, issuer, timestamp = contract.functions.verifyCertificate(document_hash).call()
        return is_valid, issuer, timestamp
    except Exception as e:
        print(f"❌ Blockchain Query Failed: {e}")
        return False, "", 0


# ✅ Flask Routes
@app.route("/", methods=["GET", "POST"])
def index():
    debug_info = []
    message = "Upload a certificate PDF to verify."

    if request.method == "POST":
        if "pdf_file" not in request.files:
            return render_template("index.html", message="❌ No file uploaded.", debug=debug_info)

        file = request.files["pdf_file"]
        if file.filename == "":
            return render_template("index.html", message="❌ No selected file.", debug=debug_info)

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        debug_info.append("✅ File uploaded successfully.")

        # Generate PDF Hash
        doc_hash = generate_text_hash(file_path)
        if not doc_hash:
            return render_template("index.html", message="❌ Could not extract text.", debug=debug_info)

        debug_info.append(f"🔍 Computed Hash: {doc_hash}")

        # Verify on Blockchain
        is_valid, issuer, timestamp = verify_certificate(doc_hash)
        debug_info.append(f"🔍 Blockchain Query: is_valid={is_valid}, issuer={issuer}, timestamp={timestamp}")

        if is_valid:
            message = f"✅ Certificate Verified! Issued by: {issuer} on {timestamp}"
        else:
            message = "❌ Certificate is NOT valid!"

        return render_template("index.html", message=message, debug=debug_info)

    return render_template("index.html", message=message, debug=debug_info)


if __name__ == "__main__":
    app.run(debug=True)
