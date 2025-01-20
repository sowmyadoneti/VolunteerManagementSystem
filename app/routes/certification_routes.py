from flask import request, redirect, url_for, flash, session, render_template
from app.models.certification import Certification
from app.models.volunteer import Volunteer
from app.models.transaction import Transaction
from app.models.event import Event
from app.models.organization import Organization
from .decorating_item import login_required
from app import app
from app.models.volunteer import Volunteer
from app.models.event import Event
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import send_file, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime



@app.route('/admin_logs', methods=['GET'])
@login_required
def admin_logs():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Fetch volunteer logs and certificates
    volunteer_logs = []
    logs = Transaction.collection.find()  # Fetch all transaction logs
    for log in logs:
        volunteer = Volunteer.find_by_id(log['user_id'])
        event = Event.find_by_id(log['event_id'])

        # Fetch organization name
        organization_name = "Unknown Organization"
        if "organization_id" in event:
            organization = Organization.find_by_id(event["organization_id"])
            if organization:
                organization_name = organization.get("org_name", "Unknown Organization")

        # Check if a certificate has already been issued for this volunteer-event
        certificate = Certification.find_one({
            "volunteer_id": log['user_id'],
            "event_id": log['event_id']
        })
        print(certificate)

        # Calculate total hours worked by summing up `hours_worked` in the `logs` array
        total_hours_worked = sum(entry.get('hours_worked', 0) for entry in log.get('logs', []))

        volunteer_logs.append({
            "volunteer_id": log['user_id'],
            "volunteer_name": volunteer['firstname'],  # Use volunteer name
            "event_name": event['name'],  # Use event name
            "organization_name": organization_name,  # Use organization name
            "event_id": str(event['_id']),  # Add event_id
            "date": log.get('date', 'N/A'),
            "hours_worked": total_hours_worked,
            "certificate_issued": certificate is not None  # True if a certificate exists
        })

    return render_template('admin/admin_logs.html', volunteer_logs=volunteer_logs)



@app.route('/issue_certificate', methods=['POST'])
@login_required
def issue_certificate():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    volunteer_id = request.form.get('volunteer_id')
    event_id = request.form.get('event_id')
    reason = request.form.get('reason')
    
    try:
        # Validate Volunteer and Event
        volunteer = Volunteer.find_by_id(volunteer_id)
        event = Event.find_by_id(ObjectId(event_id))
        
        if not volunteer:
            flash("Volunteer not found.", "error")
            return redirect(url_for('admin_logs'))
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for('admin_logs'))

        # Check if certificate is already issued
        certificate = Certification.collection.find_one({
            "volunteer_id": volunteer_id,
            "event_id": event_id
        })
        if certificate:
            flash("Certificate already issued for this event.", "warning")
            return redirect(url_for('admin_logs'))

        # Issue Certificate
        Certification.create({
            "volunteer_id": ObjectId(volunteer_id),
            "event_id": ObjectId(event_id),
            "organization_id": ObjectId(event["organization_id"]),
            "reason": reason,
            "issued_by": ObjectId(session["user_id"]),
            "status": "issued",
            "issued_on": datetime.now()
        })

        flash(f"Certificate successfully issued to {volunteer['firstname']} for event {event['name']}!", "success")
    except Exception as e:
        flash(f"An error occurred while issuing the certificate: {e}", "error")

    return redirect(url_for('admin_logs'))


@app.route('/view_my_certificates', methods=['GET', 'POST'])
@login_required
def view_my_certificates():
    if session["user_type"] != "volunteer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    volunteer_id = session["user_id"]
    certificates = Transaction.find_by_volunteer_id(volunteer_id)
    return render_template('volunteer/view_my_certificates.html', certificates=certificates)





@app.route('/download_certificate/<event_id>')
@login_required
def download_certificate(event_id):
    if session["user_type"] != "volunteer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Fetch the certificate data
    certificate = Certification.find_one({
        "volunteer_id": ObjectId(session["user_id"]),
        "event_id": ObjectId(event_id),
        "status": "issued"
    })

    if not certificate:
        flash("No certificate available for this event.", "error")
        return redirect(url_for('volunteer_dashboard'))

    # Fetch the associated event and volunteer information
    event = Event.find_by_id(ObjectId(event_id))
    print(event)
    volunteer = Volunteer.find_by_id(session["user_id"])
    organization_id = event["organizer_id"]
    print(organization_id)
    organization = Organization.find_by_id(organization_id)

    # Create a PDF in memory
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    pdf.setTitle("Certificate of Participation")

    # Set styles and content
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(300, 750, "Certificate of Participation")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(300, 700, f"Presented to {volunteer['firstname']} {volunteer['lastname']}")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        300, 650, f"For participating in the event: {event['name']}"
    )
    # set hours worked
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        300, 625, f"Hours Worked: {certificate['hours_worked']}"
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        300, 600, f"Organization: {organization['org_name']}"
    )

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        300, 550, f"Date of Issue: {datetime.now().strftime('%Y-%m-%d')}"
    )

    # Optional: Add a signature or seal area
    pdf.drawString(100, 450, "_______Volunteer Management________")
    pdf.drawString(100, 430, "Authorized Signature")

    # Save the PDF
    pdf.save()
    pdf_buffer.seek(0)

    # Return the PDF as a downloadable file
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"certificate_{event_id}.pdf",
        mimetype='application/pdf'
    )
