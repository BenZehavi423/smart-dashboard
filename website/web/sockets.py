from flask import session
from flask_socketio import emit, join_room, leave_room
from . import socketio

# A simple dictionary to keep track of which business is being edited by which user
editing_locks = {}


@socketio.on('start_editing')
def handle_start_editing(data):
    """
    Called when a user enters the 'Edit Plots' page for a business.
    """
    business_name = data['business_name']
    username = session.get('username')

    # Join a 'room' for this specific business, so we can send messages to everyone on this page
    join_room(business_name)

    if business_name not in editing_locks:
        # If no one is editing, grant the lock to the current user
        editing_locks[business_name] = username
        # Notify everyone in the room that the business is now locked
        emit('business_locked', {'username': username}, room=business_name)
    elif editing_locks[business_name] != username:
        # If someone else is editing, notify the current user
        emit('lock_failed', {'username': editing_locks[business_name]})


@socketio.on('stop_editing')
def handle_stop_editing(data):
    """
    Called when a user leaves the 'Edit Plots' page.
    """
    business_name = data['business_name']
    username = session.get('username')

    # Leave the room for this business
    leave_room(business_name)

    if editing_locks.get(business_name) == username:
        # If the current user holds the lock, release it
        del editing_locks[business_name]
        # Notify everyone in the room that the business is now unlocked
        emit('business_unlocked', room=business_name)