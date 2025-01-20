from flask import render_template, request, redirect, url_for, session, flash
from app import app
from .decorating_item import login_required
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId 
from flask import jsonify 
from app.models.volunteer import Volunteer
from app.models.organization import Organization
from app.models.event import Event
from app.models.transaction import Transaction
from app.models.admin import Admin


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from werkzeug.security import generate_password_hash



@app.route('/organizer_dashboard')
@login_required
def organizer_dashboard():
    if session["user_type"] != "organizer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Fetch events created by the organizer
    events = Event.find_by_organizer_id(session["user_id"])

    # Convert date fields to datetime objects
    for event in events:
        if isinstance(event['start_date'], str):
            event['start_date'] = datetime.strptime(event['start_date'], '%Y-%m-%d')
        if isinstance(event['end_date'], str):
            event['end_date'] = datetime.strptime(event['end_date'], '%Y-%m-%d')

    return render_template('organizer/dashboard.html', events=events)



@app.route('/organizer_create_event', methods=['GET', 'POST'])
@login_required
def organizer_create_event():
    if session["user_type"] != "organizer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            event_data = {
                "name": request.form.get("name").strip(),
                "description": request.form.get("description").strip(),
                "organizer_id": session["user_id"],
                "start_date": request.form.get("start_date"),
                "end_date": request.form.get("end_date"),
                "capacity": int(request.form.get("capacity")),
                "registration_deadline": request.form.get("reg_deadline")
            }
            Event.create(event_data)
            flash("Event created successfully!", "success")
            return redirect(url_for('organizer_dashboard'))
        except Exception as e:
            logger.error(f"Error creating event: {e}", exc_info=True)
            flash("An error occurred while creating the event.", "error")
            return redirect(url_for('create_event'))

    return render_template('organizer/create_event.html')

@app.route('/organizer_edit_event/<event_id>', methods=['GET', 'POST'])
@login_required
def organizer_edit_event(event_id):
    if session["user_type"] != "organizer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    event = Event.get_by_id(event_id)
    print(event)
    if not event or event['organizer_id'] != session["user_id"]:
        flash("Unauthorized or event not found.", "error")
        return redirect(url_for('organizer_dashboard'))

    # Convert dates to datetime objects if needed
    if isinstance(event['start_date'], str):
        event['start_date'] = datetime.strptime(event['start_date'], '%Y-%m-%d')
    if isinstance(event['end_date'], str):
        event['end_date'] = datetime.strptime(event['end_date'], '%Y-%m-%d')
    if isinstance(event['registration_deadline'], str):
        event['registration_deadline'] = datetime.strptime(event['registration_deadline'], '%Y-%m-%d')

    if request.method == 'POST':
        print(request.form)
        try:
            data = {
                "name": request.form.get("name").strip(),
                "description": request.form.get("description").strip(),
                "start_date": request.form.get("start_date"),
                "end_date": request.form.get("end_date"),
                "capacity": int(request.form.get("capacity")),
                "registration_deadline": request.form.get("reg_deadline")
            }
            print(data)
            Event.update(event_id, data)
            flash("Event updated successfully!", "success")
            return redirect(url_for('organizer_dashboard'))
        except Exception as e:
            logger.error(f"Error updating event: {e}", exc_info=True)
            flash("An error occurred while updating the event.", "error")

    return render_template('organizer/edit_event.html', event=event)


@app.route('/organizer_delete_event/<event_id>', methods=['POST'])
@login_required
def organizer_delete_event(event_id):
    if session["user_type"] != "organizer":
        flash("Unauthorized access.", "error")  
        return redirect(url_for('login'))
    
    event = Event.get_by_id(event_id)
    if not event or event['organizer_id'] != session["user_id"]:
        flash("Unauthorized or event not found.", "error")
        return redirect(url_for('organizer_dashboard'))
    
    Event.delete(event_id)
    flash("Event deleted successfully!", "success")
    return redirect(url_for('organizer_dashboard'))





@app.route('/manage_organizations', methods=['GET', 'POST'])
@login_required
def manage_organizations():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            org_name = request.form.get('org_name').strip()
            org_email = request.form.get('org_email').strip()
            first_name = request.form.get('first_name').strip()
            last_name = request.form.get('last_name').strip()
            contact_email = request.form.get('contact_email').strip()
            contact_phone = request.form.get('contact_phone').strip()
            city = request.form.get('city').strip()
            zip_code = request.form.get('zip_code').strip()
            password = request.form.get('password').strip()

            # Hash the password for security
            hashed_password = generate_password_hash(password)

            # Check for duplicate organization email
            if Organization.exists_by_email(org_email):  # Assuming this method exists
                flash('Organization email already exists.', 'error')
            else:
                organization_data = {
                    "org_name": org_name,
                    "org_email": org_email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "city": city,
                    "zip_code": zip_code,
                    "password": hashed_password,  # Save hashed password
                    "events": []
                }
                Organization.create(organization_data)
                flash('Organization added successfully!', 'success')
        except Exception as e:
            logger.error(f"Error adding organization: {e}", exc_info=True)
            flash("An unexpected error occurred while adding the organization.", "error")

    organizations = Organization.find_all()
    return render_template('admin/manage_organizations.html', organizations=organizations)


@app.route('/edit_organization/<org_id>', methods=['GET', 'POST'])
@login_required
def edit_organization(org_id):
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    organization = Organization.find_by_id(org_id)
    if request.method == 'POST':
        updated_data = {
            'org_name': request.form.get('org_name').strip(),
            'org_email': request.form.get('org_email').strip(),
            'contact_person': request.form.get('contact_person').strip(),
            'contact_email': request.form.get('contact_email').strip(),
            'contact_phone': request.form.get('contact_phone').strip()
        }
        Organization.update(org_id, updated_data)
        flash('Organization updated successfully.', 'success')
        return redirect(url_for('manage_organizations'))

    return render_template('admin/edit_organization.html', organization=organization)


@app.route('/delete_organization/<org_id>', methods=['POST', 'GET'])
@login_required
def delete_organization(org_id):
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    Organization.delete(org_id)
    flash('Organization deleted successfully.', 'success')
    return redirect(url_for('manage_organizations'))


from app.models.certification import Certification

@app.route('/organizer_event_logs/<event_id>', methods=['GET'])
@login_required
def organizer_event_logs(event_id):
    if session["user_type"] != "organizer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    event = Event.find_by_id(ObjectId(event_id))

    # Check if the event exists and belongs to the organizer
    if not event or event['organizer_id'] != session["user_id"]:
        flash("Unauthorized access or event not found.", "error")
        return redirect(url_for('organizer_dashboard'))

    # Fetch volunteer logs for the event
    volunteer_logs = []
    logs = Transaction.collection.find({"event_id": ObjectId(event_id)})  # Logs specific to the event
    for log in logs:
        volunteer = Volunteer.find_by_id(log['user_id'])

        # Check if a certificate has already been issued for this volunteer-event
        certificate = Certification.find_one({
            "volunteer_id": log['user_id'],
            "event_id": log['event_id']
        })

        # Calculate total hours worked by summing up `hours_worked` in the `logs` array
        total_hours_worked = sum(entry.get('hours_worked', 0) for entry in log.get('logs', []))

        volunteer_logs.append({
            "volunteer_id": str(log['user_id']),
            "volunteer_name": volunteer.get('firstname', 'Unknown Volunteer') + " " + volunteer.get('lastname', ''),
            "hours_worked": total_hours_worked,
            "certificate_issued": certificate is not None  # True if a certificate exists
        })

    return render_template('organizer/event_logs.html', event=event, volunteer_logs=volunteer_logs)


@app.route('/organizer_issue_certificate', methods=['POST'])
@login_required
def organizer_issue_certificate():
    if session["user_type"] != "organizer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    volunteer_id = request.form.get('volunteer_id')
    event_id = request.form.get('event_id')
    reason = request.form.get('reason')
    print(volunteer_id)
    print(event_id)
    print(reason)

    # Get organization id based on the event id
    event = Event.find_by_id(ObjectId(event_id))
    print(event)
    organization_id = event['organizer_id']
    print(organization_id)
    
    try:
        # Validate Volunteer and Event
        volunteer = Volunteer.find_by_id(volunteer_id)
        print(volunteer)
        event = Event.find_by_id(ObjectId(event_id))
        print(event)
        
        if not volunteer:
            flash("Volunteer not found.", "error")
            return redirect(url_for('organizer_event_logs', event_id=event_id))
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for('organizer_dashboard'))

        # Check if the event belongs to the logged-in organizer
        if event['organizer_id'] != session["user_id"]:
            flash("Unauthorized access to this event.", "error")
            return redirect(url_for('organizer_dashboard'))

        # Check if certificate is already issued
        certificate = Certification.collection.find_one({
            "volunteer_id": ObjectId(volunteer_id),
            "event_id": ObjectId(event_id)
        })
        if certificate:
            flash("Certificate already issued for this event.", "warning")
            return redirect(url_for('organizer_event_logs', event_id=event_id))

        # Fetch total hours worked from the transaction logs
        transaction = Transaction.collection.find_one({
            "user_id": ObjectId(volunteer_id),
            "event_id": ObjectId(event_id)
        })
        if not transaction:
            flash("No transaction data found for the volunteer in this event.", "error")
            return redirect(url_for('organizer_event_logs', event_id=event_id))

        total_hours_worked = sum(entry.get('hours_worked', 0) for entry in transaction.get('logs', []))
        print(f"Total Hours Worked: {total_hours_worked}")

        # Issue Certificate
        data = {
            "volunteer_id": ObjectId(volunteer_id),
            "event_id": ObjectId(event_id),
            "reason": reason,
            "organization_id": ObjectId(organization_id),
            "issued_by": ObjectId(session["user_id"]),
            "status": "issued",
            "issued_on": datetime.now(),
            "hours_worked": round(total_hours_worked, 2)  # Include total hours worked in the certificate
        }
        print(data)
        Certification.create(data)

        flash(f"Certificate successfully issued to {volunteer['firstname']} for event {event['name']}!", "success")
    except Exception as e:
        flash(f"An error occurred while issuing the certificate: {e}", "error")

    return redirect(url_for('organizer_event_logs', event_id=event_id))
