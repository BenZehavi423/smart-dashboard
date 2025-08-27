from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, flash
import os
from .auth import login_required
from .csv_processor import process_file
from .models import Plot
from .logger import logger
import requests

# Blueprint lets us organize routes into different files
# we don't have to put all routes in the "views.py" module
views = Blueprint('views', __name__)

# Define the routes for the views blueprint
@views.route('/')
def home():
    # Return a simple HTML response for the home page
    # 200 is the "OK" HTTP status code

    #files = list(current_app.db.db.files.find({})) add later
    return render_template('home.html'), 200

@views.route('/profile')
@login_required
def profile():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    businesses = current_app.db.get_businesses_for_owner(user._id)

    logger.info(f"Profile page accessed by user: {username} with {len(businesses)} businesses",
                extra_fields={'user_id': user._id, 'businesses_count': len(businesses)})

    return render_template('profile.html', user=user, businesses=businesses), 200

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@views.route('/upload_files', methods=['GET', 'POST'])
@login_required
def upload_files():
    # Check if user is logged in
    # If not, redirect to login page
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    user = current_app.db.get_user_by_username(session['username'])

    # Handle file upload via AJAX post request
    # POST: process uploaded files
    if request.method == 'POST':
        files = request.files.getlist('file')
        failed_files = []

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                try:
                    #Process the file and attach user_id + preview
                    processed_file = process_file(file, user._id)
                    current_app.db.create_file(processed_file)

                except Exception as e:
                    # If processing fails, log the error
                    failed_files.append(f"{file.filename}: {str(e)}")

            # If file is not valid, log the error
            else:
                failed_files.append(f"Invalid file: {getattr(file, 'filename', 'unknown')}")

        # Return JSON response to the frontend
        return jsonify({
            'success': len(failed_files) == 0,
            'failed_files': failed_files,
            'files': [f.filename for f in current_app.db.get_files_for_user(user)]
        })

    #GET: render the upload page with current user's files
    user_files = current_app.db.get_files_for_user(user)
    return render_template('upload_files.html', files=user_files)

@views.route('/ask_llm', methods=['POST'])
@login_required
def ask_llm():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # The service name 'llm_service' is used as the hostname
        llm_api_url = 'http://llm_service:5001/predict'
        response = requests.post(llm_api_url, json={'query': query})
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        # Log the error e
        return jsonify({'error': 'The LLM service is currently unavailable.'}), 503

@views.route('/edit_plots', methods=['GET', 'POST'])
@login_required
def edit_plots():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)

    logger.info(f"Edit plots page accessed by user: {username}",
                extra_fields={'user_id': user._id, 'action': 'edit_plots_access'})

    if request.method == 'POST':
        # Handle AJAX request for saving plot changes
        data = request.get_json()
        plot_updates = data.get('plot_updates', [])
        plot_order = data.get('plot_order', [])

        logger.info(f"User {username} saving plot changes: {len(plot_updates)} updates, {len(plot_order)} plots in order",
                    extra_fields={'user_id': user._id, 'updates_count': len(plot_updates), 'order_length': len(plot_order)})

        # Update plot presentation status
        plot_success = current_app.db.update_multiple_plots(plot_updates)

        # Update plot order in user profile
        order_success = current_app.db.update_plot_presentation_order(user._id, plot_order)

        success = plot_success and order_success

        if success:
            logger.info(f"Plot changes saved successfully for user {username}",
                        extra_fields={'user_id': user._id, 'presented_plots': len(plot_order)})
        else:
            logger.error(f"Failed to save plot changes for user {username}",
                         extra_fields={'user_id': user._id, 'plot_success': plot_success, 'order_success': order_success})

        return jsonify({'success': success})

    # GET: render the edit plots page
    all_plots = current_app.db.get_plots_for_user(user._id)
    presented_plots = [p for p in all_plots if p.is_presented]

    # Get user profile to determine presented plot order
    profile = current_app.db.get_or_create_user_profile(user._id)

    # Sort presented plots according to profile order
    plots_dict = {plot._id: plot for plot in presented_plots}
    ordered_presented_plots = []
    for plot_id in profile.presented_plot_order:
        if plot_id in plots_dict:
            ordered_presented_plots.append(plots_dict[plot_id])

    # Add any plots that are presented but not in the order list
    for plot in presented_plots:
        if plot._id not in profile.presented_plot_order:
            ordered_presented_plots.append(plot)

    # Convert plots to a format suitable for JSON serialization
    all_plots_data = []
    for plot in all_plots:
        all_plots_data.append({
            '_id': plot._id,
            'image_name': plot.image_name,
            'image': plot.image,
            'created_time': plot.created_time.isoformat() if plot.created_time else None,
            'is_presented': plot.is_presented
        })

    presented_plots_data = []
    for plot in ordered_presented_plots:
        presented_plots_data.append({
            '_id': plot._id,
            'image_name': plot.image_name,
            'image': plot.image,
            'created_time': plot.created_time.isoformat() if plot.created_time else None,
            'is_presented': plot.is_presented
        })

    logger.info(f"Edit plots page rendered for user {username}: {len(all_plots)} total plots, {len(presented_plots)} presented",
                extra_fields={'user_id': user._id, 'total_plots': len(all_plots), 'presented_plots': len(presented_plots)})

    return render_template('edit_plots.html',
                         user=user,
                         all_plots=all_plots_data,
                         presented_plots=presented_plots_data)

@views.route('/analyze_data', methods=['GET', 'POST'])
@login_required
def analyze_data(): # TODO: analyze_data
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)

    logger.info(f"Analyze data page accessed by user: {username}",
                extra_fields={'user_id': user._id, 'action': 'analyze_data_access'})

    if request.method == 'POST':
        # Handle AJAX request for saving new plots
        data = request.get_json()
        new_plots = data.get('new_plots', [])

        logger.info(f"User {username} attempting to save {len(new_plots)} new plots",
                    extra_fields={'user_id': user._id, 'plots_count': len(new_plots)})
        try:
            # Get user profile to determine the next order numbers
            profile = current_app.db.get_or_create_user_profile(user._id)
            current_order = len(profile.presented_plot_order)

            saved_plot_ids = []
            for i, plot_data in enumerate(new_plots):
                if plot_data.get('save_to_business', False):
                    # Create new Plot object
                    new_plot = Plot(
                        image_name=plot_data['image_name'],
                        image=plot_data['image'],
                        files=plot_data.get('files', []),
                        user_id=user._id,
                        is_presented=True
                    )
                    # Save to database
                    plot_id = current_app.db.create_plot(new_plot)
                    saved_plot_ids.append(plot_id)
                    logger.info(f"Plot saved successfully: {plot_data['image_name']}",
                                extra_fields={'user_id': user._id, 'plot_id': plot_id, 'plot_name': plot_data['image_name']})
                    # Add to user profile order (at the end)
                    profile.presented_plot_order.append(plot_id)
            # Update user profile with new order
            if saved_plot_ids:
                current_app.db.update_user_profile(user._id, {
                    "presented_plot_order": profile.presented_plot_order
                })
                logger.info(f"User profile updated with {len(saved_plot_ids)} new plots",
                            extra_fields={'user_id': user._id, 'saved_count': len(saved_plot_ids)})
            return jsonify({
                'success': True,
                'saved_count': len(saved_plot_ids)
            })
        except Exception as e:
            logger.error(f"Failed to save plots: {e}", extra_fields={'user_id': user._id})
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET: render the analyze data page
    user_files = current_app.db.get_files_for_user(user)
    logger.info(f"Analyze data page rendered for user {username} with {len(user_files)} files",
                extra_fields={'user_id': user._id, 'files_count': len(user_files)})

    return render_template('analyze_data.html', user=user, files=user_files)

# ---- Simple placeholder pages to satisfy navbar links ----
@views.route('/user_profile')
@login_required
def user_profile():
    return render_template('generic_page.html', title='User Profile', content='Coming soon'), 200

@views.route('/businesses_search')
@login_required
def businesses_search():
    return render_template('generic_page.html', title='Businesses Search', content='Coming soon'), 200

@views.route('/new_business')
@login_required
def new_business():
    return render_template('generic_page.html', title='New Business', content='Coming soon'), 200
