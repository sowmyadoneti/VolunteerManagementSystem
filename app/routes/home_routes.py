#  hi index route
from flask import render_template
from app import app 
from flask import redirect, url_for, session
from flask import request
from .decorating_item import login_required
from flask import flash
from flask import render_template_string
from werkzeug.security import generate_password_hash
from app.models.admin import Admin
from app.models.volunteer import Volunteer
from app.models.organization import Organization
from app.models.transaction import Transaction
from app.models.event import Event
from app.models.certification import Certification
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash
import logging
from flask import send_file, jsonify
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from flask import request, render_template, jsonify

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/validate_certificate', methods=['GET', 'POST'])
def validate_certificate():
    if request.method == 'POST':
        certificate_id = request.form.get('certificate_id')
        certificate = Certification.find_one({"_id": ObjectId(certificate_id), "status": "issued"})
        if certificate:
            return render_template('certificate_verified.html', certificate=certificate,
                                   volunteer=Volunteer.find_by_id(certificate['volunteer_id']),
                                   event=Event.find_by_id(certificate['event_id']),
                                   organization=Organization.find_by_id(certificate['organization_id']))
        flash("Certificate not found or not issued.", "error")
        return redirect(url_for('validate_certificate'))
    return render_template('validate_certificate.html')


@app.route('/download_certificate_public/<certificate_id>', methods=['GET'])
def download_certificate_public(certificate_id):
    certificate = Certification.find_one({"_id": ObjectId(certificate_id), "status": "issued"})
    if not certificate:
        return jsonify({"error": "Certificate not found or not issued"}), 404

    volunteer = Volunteer.find_by_id(certificate['volunteer_id'])
    event = Event.find_by_id(certificate['event_id'])
    organization = Organization.find_by_id(certificate['organization_id'])

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    pdf.setTitle("Certificate of Participation")

    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(300, 750, "Certificate of Participation")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(300, 700, f"Presented to {volunteer['firstname']}")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(300, 650, f"For participating in the event: {event['name']}")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(300, 600, f"Organization: {organization['org_name']}")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(300, 550, f"Issued On: {certificate['issued_on'].strftime('%Y-%m-%d')}")

    pdf.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name=f"certificate_{certificate_id}.pdf", mimetype='application/pdf')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': 
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        # Check if the email belongs to a Volunteer
        if Volunteer.exists_by_email(email):
            volunteer = Volunteer.get_by_email(email)
            if volunteer['password'] == password:
                session["user_id"] = str(volunteer['_id'])
                session["user_type"] = "volunteer"
                return redirect(url_for('volunteer_dashboard'))
            else:
                flash("Invalid credentials.", "error")
                return redirect(url_for('login'))

        # Check if the email belongs to an Admin
        elif Admin.exists_by_email(email):
            admin = Admin.get_by_email(email)
            if check_password_hash(admin['password'], password):
                session["user_id"] = str(admin['_id'])
                session["user_type"] = "admin"
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid credentials.", "error")
                return redirect(url_for('login'))

        # Check if the email belongs to an Organization
        elif Organization.exists_by_email(email):
            organization = Organization.get_by_email(email)
            print(organization)
            if check_password_hash(organization['password'], password):
                
                session["user_id"] = str(organization['_id'])
                session["user_type"] = "organizer"
                return redirect(url_for('organizer_dashboard'))
            else:
                flash("Invalid credentials.", "error")
                return redirect(url_for('login'))

        # If the email doesn't belong to any, return an error
        else:
            flash("Email not found.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/adminregister', methods=['GET', 'POST'])
def adminregister():
    try:
        if request.method == 'POST':
            email = request.form.get("email").strip()
            if Admin.exists_by_email(email): 
                flash("Email already registered", "error")
                return redirect(url_for('adminregister'))

            password = request.form.get("password").strip()
            confirm_password = request.form.get("confirm_password").strip()

            if password != confirm_password:
                flash("Passwords do not match", "error")
                return redirect(url_for('adminregister'))

            data = {
                "username": request.form.get("username").strip(),
                "email": email,
                "password": generate_password_hash(password),
            }
            Admin.create(data)  # Assuming Admin has a 'create' method similar to Organizer
            flash("Admin registered successfully!", "success")
            return redirect(url_for('admin_dashboard'))

        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error during admin registration: {e}", exc_info=True)
        flash("Internal Server Error", "error")
        return redirect(url_for('adminregister'))





@app.route('/logout')
def logout():
    try:
        session.pop('user_id', None)
        session.pop('user_type', None)
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return "Internal Server Error", 500
