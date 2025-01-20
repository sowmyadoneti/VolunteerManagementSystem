from flask import render_template, request, redirect, url_for, session, flash
from app import app
from .decorating_item import login_required
import logging
from datetime import datetime
from bson.objectid import ObjectId
from app.models.event import Event
from app.models.organization import Organization
from app.models.transaction import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from bson import ObjectId  # Import ObjectId for proper querying

@app.route('/manage_admin_events', methods=['GET', 'POST'])
@login_required
def manage_admin_events():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Handle form submission for adding a new event
    if request.method == 'POST':
        try:
            name = request.form.get('name').strip()
            description = request.form.get('description').strip()
            organization_id = request.form.get('organization').strip()
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            capacity = int(request.form.get('capacity'))
            reg_deadline = datetime.strptime(request.form.get('reg_deadline'), '%Y-%m-%d')

            # Add event data
            event_data = {
                "name": name,
                "description": description,
                "organization_id": ObjectId(organization_id),
                "start_date": start_date,
                "end_date": end_date,
                "capacity": capacity,
                "assigned_volunteers": [],
                "reg_deadline": reg_deadline
            }
            Event.create(event_data)  # Assuming `Event.create` adds the event to the database
            flash('Event added successfully!', 'success')
        except Exception as e:
            logger.error(f"Error adding event: {e}", exc_info=True)
            flash("An unexpected error occurred while adding the event.", "error")

    # Retrieve all events and organizations for display
    events = Event.find_all()
    organizations = Organization.find_all()
    for event in events:
        try:
            # Convert `organization_id` to ObjectId before querying
            organization = Organization.find_by_id(ObjectId(event["organization_id"]))
            if organization:
                event["organization_name"] = organization["org_name"]
            else:
                event["organization_name"] = "Unknown Organization"
        except Exception as e:
            logger.error(f"Error fetching organization for event: {e}", exc_info=True)
            event["organization_name"] = "Unknown Organization"

    return render_template('admin/manage_admin_events.html', events=events, organizations=list(organizations))


@app.route('/edit_event/<event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    # Fetch event details by ID
    event = Event.find_by_id(ObjectId(event_id))
    organizations = Organization.find_all()  # Fetch all organizations for the dropdown

    if not event:
        flash("Event not found.", "error")
        return redirect(url_for('manage_admin_events'))

    if request.method == 'POST':
        try:
            # Get updated data from the form
            updated_data = {
                "name": request.form.get('name').strip(),
                "description": request.form.get('description').strip(),
                "organization_id": request.form.get('organization').strip(),
                "start_date": datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
                "end_date": datetime.strptime(request.form.get('end_date'), '%Y-%m-%d'),
                "capacity": int(request.form.get('capacity')),
                "reg_deadline": datetime.strptime(request.form.get('reg_deadline'), '%Y-%m-%d')
            }
            # Update the event in the database
            Event.update(event_id, updated_data)
            flash('Event updated successfully!', 'success')
            return redirect(url_for('manage_admin_events'))
        except Exception as e:
            logger.error(f"Error updating event: {e}", exc_info=True)
            flash("An unexpected error occurred while updating the event.", "error")

    # Pass the event and organizations to the template
    return render_template('admin/edit_event.html', event=event, organizations=list(organizations))


@app.route('/delete_event/<event_id>', methods=['POST', 'GET'])
@login_required
def delete_event(event_id):
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        Event.delete_by_id(ObjectId(event_id))
        flash('Event deleted successfully.', 'success')
    except Exception as e:
        logger.error(f"Error deleting event: {e}", exc_info=True)
        flash("An unexpected error occurred while deleting the event.", "error")

    return redirect(url_for('manage_admin_events'))

from datetime import datetime
from bson.objectid import ObjectId

@app.route('/register_event/<event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    if session["user_type"] != "volunteer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        # Fetch the event
        event = Event.get_by_id(ObjectId(event_id))
        if not event:
            flash("Event not found.", "error")
            return redirect(url_for('volunteer_dashboard'))

        # Ensure assigned_volunteers field exists
        assigned_volunteers = event.get("assigned_volunteers", [])

        # Check capacity
        if len(assigned_volunteers) >= event["capacity"]:
            flash("This event has reached its maximum capacity.", "warning")
            return redirect(url_for('volunteer_dashboard'))

        # Prevent duplicate registrations
        if session["user_id"] in assigned_volunteers:
            flash("You are already registered for this event!", "warning")
            return redirect(url_for('volunteer_dashboard'))

        # Check for conflicting events
        volunteer_id = session["user_id"]
        volunteer_events = Event.find_all({"assigned_volunteers": volunteer_id})
        event_start = datetime.strptime(event["start_date"], '%Y-%m-%d')
        event_end = datetime.strptime(event["end_date"], '%Y-%m-%d')

        for v_event in volunteer_events:
            v_start = datetime.strptime(v_event["start_date"], '%Y-%m-%d')
            v_end = datetime.strptime(v_event["end_date"], '%Y-%m-%d')
            # Check if event dates overlap
            if max(event_start, v_start) <= min(event_end, v_end):
                flash(f"Conflict with '{v_event['name']}' from {v_start.date()} to {v_end.date()}.", "warning")
                return redirect(url_for('volunteer_dashboard'))

        # Add the volunteer to the event's assigned volunteers
        Event.update(
            ObjectId(event_id),
            {"$push": {"assigned_volunteers": volunteer_id}}
        )

        # Create a new transaction record
        transaction_data = {
            "event_id": ObjectId(event_id),
            "user_id": ObjectId(volunteer_id),
            "hours_worked": 0,
            "date": datetime.now(),
            "logs": []  # Initialize with an empty list
        }
        Transaction.create(transaction_data)  # Assuming Transaction.create adds a record to the database

        flash("Successfully registered for the event!", "success")
    except Exception as e:
        logger.error(f"Error registering for event: {e}", exc_info=True)
        flash("An error occurred while registering for the event.", "error")

    return redirect(url_for('volunteer_dashboard'))
