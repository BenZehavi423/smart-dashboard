from flask import session, request
from flask_socketio import emit, join_room, leave_room
from . import socketio

# A simple dictionary to keep track of which business is being edited by which user
editing_locks = {}


@socketio.on('start_editing')
def handle_start_editing(data):
    """
    Called when a user enters any editing page for a business (plots or details).
    """
    business_name = data['business_name']
    username = session.get('username')

    # Associate the user's session ID with the business they are editing
    session['editing_business'] = business_name

    join_room(business_name)

    if business_name not in editing_locks:
        editing_locks[business_name] = username
        emit('business_locked', {'username': username}, room=business_name)
    elif editing_locks[business_name] != username:
        emit('lock_failed', {'username': editing_locks[business_name]})


@socketio.on('stop_editing')
def handle_stop_editing(data):
    """
    Called when a user leaves any editing page for a business.
    """
    business_name = data['business_name']
    username = session.get('username')

    leave_room(business_name)

    if editing_locks.get(business_name) == username:
        del editing_locks[business_name]
        emit('business_unlocked', room=business_name)


@socketio.on('disconnect')
def handle_disconnect():
    """
    Called when a user disconnects from the WebSocket.
    """
    # Check if the user was editing a business
    business_name = session.get('editing_business')
    username = session.get('username')

    if business_name and editing_locks.get(business_name) == username:
        # If the disconnected user was the one editing, release the lock
        del editing_locks[business_name]
        # Notify the other users that the business is now unlocked
        emit('business_unlocked', room=business_name)