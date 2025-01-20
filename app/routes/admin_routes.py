from flask import render_template, request, redirect, url_for, session, flash
from app import app
from .decorating_item import login_required
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId 
from flask import jsonify 
from app.models.transaction import Transaction
from app.models.volunteer import Volunteer
from app.models.event import Event
from app.models.certification import Certification
from app.models.organization import Organization
from dateutil.parser import parse  # Make sure to install python-dateutil if not already
import json



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    # get total empoyees nd total departments
    total_certifications = Certification.count_all()
    total_organizations = Organization.count_all()
    total_volunteers = Volunteer.count_all()
    return render_template('admin/admin.html', total_certifications=total_certifications, 
                           total_organizations=total_organizations, total_volunteers=total_volunteers)




