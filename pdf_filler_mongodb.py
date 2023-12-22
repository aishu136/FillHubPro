import streamlit as st
import cv2
from PyPDF2 import PdfFileReader, PdfFileWriter
from pymongo import MongoClient
from io import BytesIO
from flask import Flask, request, jsonify

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["pdf_database"]
collection = db["filled_pdfs"]

app = Flask(__name__)

def fill_pdf(input_pdf_path, data):
    pdf_writer = PdfFileWriter()

    with open(input_pdf_path, 'rb') as input_file:
        pdf_reader = PdfFileReader(input_file)

        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            filled_page = fill_data(page, data)
            pdf_writer.addPage(filled_page)

    output_pdf_bytes = BytesIO()
    pdf_writer.write(output_pdf_bytes)
    return output_pdf_bytes.getvalue()

def fill_data(page, data):
    # Custom model logic to fill data into the PDF page
    # For simplicity, we're using OpenCV to overlay text on the PDF as an image
    img = page.to_pil()
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # Example: Overlay text on the image using OpenCV
    cv2.putText(cv_img, data, (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Convert the image back to PIL format and update the PDF page
    img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    page = pdf.PdfImage(img, width=img.width, height=img.height)
    
    return page

def save_to_mongodb(pdf_data):
    document = {"pdf_data": pdf_data}
    collection.insert_one(document)
    return document["_id"]

@app.route('/fill-pdf', methods=['POST'])
def fill_pdf_api():
    data = request.json
    input_pdf_path = data.get('input_pdf_path')
    field_data = data.get('field_data')

    filled_pdf_data = fill_pdf(input_pdf_path, field_data)
    document_id = save_to_mongodb(filled_pdf_data)

    return jsonify({"status": "success", "document_id": document_id})

def main():
    st.title("PDF Filler")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file is not None:
        st.write("File Uploaded!")

        data = st.text_input("Enter data to fill in the PDF:")

        if st.button("Fill PDF"):
            # Prepare data for API request
            api_data = {"input_pdf_path": uploaded_file.name, "field_data": data}

            # Send API request to Flask server
            response = requests.post("http://127.0.0.1:5000/fill-pdf", json=api_data)
            
            if response.status_code == 200:
                st.success(f"PDF filled and saved to MongoDB with ID: {response.json()['document_id']}")
            else:
                st.error("Error filling PDF and saving to MongoDB.")

if __name__ == "__main__":
    main()

