from flask import render_template, request, redirect, url_for, session, flash
from app import app
from .decorating_item import login_required
import logging
from datetime import datetime, timedelta, timezone
from bson.objectid import ObjectId 
from flask import jsonify 
from app.models.volunteer import Volunteer
from app.models.organization import Organization
from app.models.certification import Certification
from app.models.event import Event
from app.models.transaction import Transaction
from app.models.admin import Admin
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/register_volunteer', methods=['GET', 'POST'])
def register_volunteer():
    if request.method == 'POST':
        try:
            # Extract form data
            firstname = request.form.get('firstname').strip()
            lastname = request.form.get('lastname').strip()
            dob = request.form.get('dob').strip()
            email = request.form.get('email').strip()
            phone = request.form.get('phone').strip()
            city = request.form.get('city').strip()
            zip_code = request.form.get('zip').strip()
            password = request.form.get('password').strip()
            confirm_password = request.form.get('confirm_password').strip()

            # Validate password
            if password != confirm_password:
                flash('Password and Confirm Password do not match.', 'error')
                return redirect(url_for('register_volunteer'))

            # Create new volunteer data
            volunteer_data = {
                "firstname": firstname,
                "lastname": lastname,
                "dob": dob,
                "email": email,
                "phone": phone,
                "city": city,
                "zip_code": zip_code,
                "status": "active",
                "password": password  # Storing plain text password (not recommended)
            }

            # Assuming `Volunteer.create` adds the volunteer to the database
            Volunteer.create(volunteer_data)
            flash('Volunteer registered successfully!', 'success')
            return redirect(url_for('view_volunteers'))
        except Exception as e:
            logger.error(f"Error registering volunteer: {e}", exc_info=True)
            flash("An error occurred while registering the volunteer.", "error")
            return redirect(url_for('register_volunteer'))

    return render_template('volunteer/register_volunteer.html')

from datetime import datetime
from bson.objectid import ObjectId
@app.route('/volunteer_dashboard')
@login_required
def volunteer_dashboard():
    if session["user_type"] != "volunteer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    volunteer = Volunteer.find_by_id(session["user_id"])
    if volunteer['status'] != 'active':
        return render_template('volunteer/volunteer.html', volunteer=volunteer, events=[])

    current_date = datetime.now()

    # Fetch all events
    events_cursor = Event.find_all({})

    events = []
    # Fetch events the volunteer is already registered for
    volunteer_events = Event.find_all({"assigned_volunteers": session["user_id"]})
    registered_events = [
        {
            "start_date": datetime.strptime(v["start_date"], '%Y-%m-%d'),
            "end_date": datetime.strptime(v["end_date"], '%Y-%m-%d'),
            "name": v["name"]
        }
        for v in volunteer_events
    ]

    for event in events_cursor:
        # Parse date strings into datetime objects
        event['registration_deadline'] = datetime.strptime(event['registration_deadline'], '%Y-%m-%d')
        event['start_date'] = datetime.strptime(event['start_date'], '%Y-%m-%d')
        event['end_date'] = datetime.strptime(event['end_date'], '%Y-%m-%d')

        # Include only events with valid registration deadlines
        if event['registration_deadline'] >= current_date:
            event["current_capacity"] = event["capacity"] - len(event.get("assigned_volunteers", []))

            if session["user_id"] in event.get("assigned_volunteers", []):
                # Skip conflict logic for already registered events
                event["conflict"] = False
                event["conflict_event"] = None

                # Fetch certification status
                certificate = Certification.find_one({
                    "volunteer_id": ObjectId(session["user_id"]),
                    "event_id": event["_id"]
                })
                event["certificate_status"] = certificate["status"] if certificate else None

                # Determine clock status
                log = Transaction.find_one({
                    "user_id": ObjectId(session["user_id"]),
                    "event_id": event["_id"]
                })

                if log and "logs" in log:
                    if any(l.get("clock_out_time") is None for l in log["logs"]):
                        event["clock_status"] = "Clock Out"
                    else:
                        event["clock_status"] = "Clock In"
                else:
                    event["clock_status"] = "Clock In"
            else:
                # Check for conflicts
                conflict = False
                conflict_event_name = None
                event_start = event["start_date"]
                event_end = event["end_date"]

                for reg_event in registered_events:
                    if max(event_start, reg_event["start_date"]) <= min(event_end, reg_event["end_date"]):
                        conflict = True
                        conflict_event_name = reg_event["name"]
                        break

                event["conflict"] = conflict
                event["conflict_event"] = conflict_event_name

                event["certificate_status"] = None
                event["clock_status"] = None

            events.append(event)

    return render_template('volunteer/volunteer.html', volunteer=volunteer, events=events)




@app.route('/add_volunteer', methods=['GET', 'POST'])
@login_required
def add_volunteer():

    if not (session.get("user_type") == "admin"):
        flash("Unauthorized access. Admins and Superadmins only.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:  
            volunteer_data = {
                "volunteer_code": request.form.get('volunteer_code').strip(),
                "position": request.form.get('position').strip(),
                "department_id": request.form.get('department_id').strip(),
                "name": "", 
                "email":  "",
                "password":  "",
                "phone_number":  "",
                "status": request.form.get('status').strip(),

            }

            # Assuming Employee.create returns the new volunteer object, including its ID
            new_volunteer_result = Volunteer.create(volunteer_data)
            new_volunteer_id = new_volunteer_result.inserted_id 


            contract_data = {
                "volunteer_id": new_volunteer_id,
                "volunteer_type": request.form.get('volunteer_type').strip(),
                "allocated_leaves": request.form.get('allocated_leaves').strip(),
                "start_date": request.form.get('start_date').strip(),
                "end_date": request.form.get('end_date').strip(), 
                "hourly_wage": request.form.get('hourly_wage').strip(),
            }


            
            flash('Employee and contract details added successfully!', 'success')
            return redirect(url_for('view_volunteers'))

        except Exception as e:
            logger.error(f"Error adding volunteer: {e}", exc_info=True)
            flash("An unexpected error occurred while adding the volunteer.", "error")
            return redirect(url_for('add_volunteer'))

    departments = Organization.find_all()
    return render_template('volunteer/add_volunteer.html', departments=list(departments))





@app.route('/manage_volunteers', methods=['GET', 'POST'])
@login_required
def manage_volunteers():
    if session.get("user_type") != "admin":
        flash("Unauthorized access. Admins only.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            volunteer_id = request.form.get('volunteer_id')
            new_status = request.form.get('status')

            # Update the status of the volunteer
            Volunteer.update(
                ObjectId(volunteer_id),
                {"status": new_status}
            )
            flash("Volunteer status updated successfully!", "success")
        except Exception as e:
            logger.error(f"Error updating volunteer status: {e}", exc_info=True)
            flash("An error occurred while updating the volunteer status.", "error")

    # Fetch all volunteers for display
    volunteers = Volunteer.find_all()
    return render_template('admin/manage_volunteers.html', volunteers=volunteers)



@app.route('/event_details/<event_id>', methods=['GET', 'POST'])
@login_required
def event_details(event_id):
    if session["user_type"] != "volunteer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Fetch the event details
    event = Event.get_by_id(ObjectId(event_id))
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('volunteer_dashboard'))

    # Convert date strings to datetime objects
    for key in ['start_date', 'end_date', 'registration_deadline']:
        if key in event and isinstance(event[key], str):
            event[key] = datetime.strptime(event[key], '%Y-%m-%d')

    # Check if the volunteer is registered for the event
    if session["user_id"] not in event.get("assigned_volunteers", []):
        flash("You are not registered for this event.", "error")
        return redirect(url_for('volunteer_dashboard'))

    # Fetch certification status
    certificate = Certification.find_one({
        "volunteer_id": ObjectId(session["user_id"]),
        "event_id": event["_id"]
    })
    certificate_status = certificate["status"] if certificate else None

    # Fetch all transactions for the user and event
    transactions = Transaction.find({
        "user_id": ObjectId(session["user_id"]),
        "event_id": event["_id"]
    })

    logs = []
    clock_status = "Clock In"

    if transactions:
        for transaction in transactions:
            if "logs" in transaction:
                for log in transaction["logs"]:
                    # Check for pending clock-out and update if necessary
                    if log.get("clock_out_time") is None:
                        clock_in_time = log["clock_in_time"]
                        # Set clock-out time to 11:59 PM
                        clock_out_time = datetime.now().replace(hour=23, minute=30, second=0, microsecond=0)
                        hours_worked = (clock_out_time - clock_in_time).total_seconds() / 3600.0

                        # Update the log
                        log["clock_out_time"] = clock_out_time
                        log["hours_worked"] = hours_worked

                        # Update the database for the current transaction
                        Transaction.update_one(
                            {"_id": transaction["_id"]},
                            {"$set": {"logs": transaction["logs"]}}
                        )
                    
                    logs.append(log)

        # Determine clock status based on logs
        if any(log.get("clock_out_time") is None for log in logs):
            clock_status = "Clock Out"

    # Sort logs by clock-in time for display
    logs.sort(key=lambda x: x["clock_in_time"])

    return render_template(
        'volunteer/event_details.html',
        event=event,
        certificate_status=certificate_status,
        clock_status=clock_status,
        logs=logs
    )