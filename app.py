from flask import Flask, render_template, request, send_file
import sqlite3
import qrcode
from reportlab.pdfgen import canvas
import os

import os

# Ensure the directories exist at the start of the app
os.makedirs("qrcodes", exist_ok=True)
os.makedirs("hall_tickets", exist_ok=True)

# Initialize Flask app
app = Flask(__name__)

# Database setup
DATABASE = "students.db"

def init_db():
    os.makedirs("qrcodes", exist_ok=True)
    os.makedirs("hall_tickets", exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            exam_date TEXT NOT NULL,
            hall_no TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Generate QR Code
def generate_qr(data, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save(filename)

# Generate Hall Ticket PDF
def create_hall_ticket(student, qr_code_path, hall_ticket_path):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    # Add student image (top-right corner)
    if os.path.exists(student["student_image"]):
        pdf.image(student["student_image"], x=160, y=10, w=40, h=40)

    # Add student details
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Name: {student['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Student ID: {student['student_id']}", ln=True)
    pdf.cell(200, 10, txt=f"Hall Number: {student['hall_no']}", ln=True)

    # Add subjects and exam dates
    pdf.cell(200, 10, txt="Subjects and Exam Dates:", ln=True)
    for subject, date in zip(student['subjects'], student['exam_dates']):
        pdf.cell(200, 10, txt=f"{subject}: {date}", ln=True)

    # Add QR code (below the hall ticket)
    pdf.image(qr_code_path, x=80, y=200, w=50, h=50)

    # Output PDF
    pdf.output(hall_ticket_path)




# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    student_id = request.form['student_id']
    hall_no = request.form['hall_no']

    # Ensure exactly 5 subjects and exam dates
    subjects = request.form.getlist('subjects')
    exam_dates = request.form.getlist('exam_dates')

    if len(subjects) != 5 or len(exam_dates) != 5:
        return "Please provide exactly 5 subjects and corresponding exam dates.", 400

    # Handle image upload
    student_image = request.files['student_image']
    image_path = os.path.join('student_images', f"{student_id}.jpeg")
    os.makedirs('student_images', exist_ok=True)
    student_image.save(image_path)

    # Create the hall ticket with updated data
    student_data = {
        "name": name,
        "student_id": student_id,
        "hall_no": hall_no,
        "subjects": subjects,
        "exam_dates": exam_dates,
        "student_image": image_path,
    }

    qr_code_path = os.path.join("qrcodes", f"{student_id}.png")
    hall_ticket_path = os.path.join("hall_tickets", f"{student_id}.pdf")

    generate_qr(f"ID: {student_id}, Name: {name}, Hall: {hall_no}", qr_code_path)
    create_hall_ticket(student_data, qr_code_path, hall_ticket_path)

    return send_file(hall_ticket_path, as_attachment=True)



# Start Flask app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
