from flask import jsonify, session, redirect
from datetime import datetime
from bson.objectid import ObjectId
from app import app
from app.models.transaction import Transaction
import pymongo

@app.route('/clock_in/<event_id>', methods=['POST'])
def clock_in(event_id):
    print("clock_in")
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')

    result = Transaction.collection.update_one(
        {'user_id': ObjectId(user_id), 'event_id': ObjectId(event_id), 'date': today_str},
        {
            '$push': {'logs': {'clock_in_time': now, 'clock_out_time': None}},
            '$setOnInsert': {'hours_worked': 0}
        },
        upsert=True
    )

    if result.matched_count > 0 or result.upserted_id:
        return jsonify({'success': True, 'message': 'Clock-in time recorded!'}), 200
    else:
        return jsonify({'error': 'Failed to record clock-in time.'}), 500


@app.route('/clock_out/<event_id>', methods=['POST'])
def clock_out(event_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')

    logs_document = Transaction.collection.find_one({
        'user_id': ObjectId(user_id),
        'event_id': ObjectId(event_id),
        'date': today_str
    })

    if not logs_document or 'logs' not in logs_document or not logs_document['logs']:
        return jsonify({'error': 'No clock-in record found to clock out.'}), 400

    last_log_index = len(logs_document['logs']) - 1
    last_log = logs_document['logs'][last_log_index]

    if last_log.get('clock_out_time') is None:
        last_log['clock_out_time'] = now
        hours_worked_this_session = (now - last_log['clock_in_time']).total_seconds() / 3600.0
        last_log['hours_worked'] = hours_worked_this_session

        Transaction.collection.update_one(
            {'_id': logs_document['_id']},
            {'$set': {f'logs.{last_log_index}': last_log}}
        )

        total_hours_worked = logs_document.get('hours_worked', 0) + hours_worked_this_session
        Transaction.collection.update_one(
            {'_id': logs_document['_id']},
            {'$set': {'hours_worked': total_hours_worked}}
        )
        return jsonify({'success': True, 'message': 'Clock-out time recorded!', 'hours_worked': hours_worked_this_session}), 200
    else:
        return jsonify({'error': 'Already clocked out.'}), 400
