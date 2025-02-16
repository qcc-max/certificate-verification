import hashlib
import PyPDF2

def generate_text_hash(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "".join([page.extract_text() or "" for page in reader.pages])  # Extract text from all pages
        text_hash = hashlib.sha256(text.encode()).hexdigest()  # Generate SHA-256 hash
    return text_hash

pdf_path = "oxford.pdf"  # Path to certificate PDF
hash_value = generate_text_hash(pdf_path)
print("Text-Based Hash:", hash_value)
