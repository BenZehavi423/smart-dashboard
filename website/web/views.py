from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, flash
import os
from .auth import login_required
from .csv_processor import process_file
from .models import Plot, Business
from .logger import logger
import requests
from .llm_client import generate_insights_for_file
from .plot_generator import generate_plot_image

# Blueprint lets us organize routes into different files
# we don't have to put all routes in the "views.py" module
views = Blueprint('views', __name__)

def can_edit_business(user, business):
    return user._id in business.editors

# Define the routes for the views blueprint
@views.route('/')
def home():
    # Return a simple HTML response for the home page
    # 200 is the "OK" HTTP status code

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

@views.route('/upload_files/<business_name>', methods=['GET', 'POST'])
@login_required
def upload_files(business_name):
    # Check if user is logged in
    # If not, redirect to login page
    if 'username' not in session:
        logger.warning("Unauthorized access to upload_files")
        return redirect(url_for('auth.login'))
    
    user = current_app.db.get_user_by_username(session['username'])
    logger.info(f"Upload files page accessed by user: {user.username}",
                extra_fields={'user_id': user._id, 'action': 'upload_files_access'})
    
    # Handle file upload via AJAX post request
    # POST: process uploaded files
    if request.method == 'POST':
        files = request.files.getlist('file')
        logger.info(f"User {user.username} uploading {len(files)} files")
        failed_files = []

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                logger.debug(f"Processing file: {file.filename}")
                try:
                    # Get business for this business_name to get the business_id
                    business = current_app.db.get_business_by_name(business_name)
                    if not business:
                        # Create a default business if it doesn't exist
                        business = current_app.db.create_business(user._id, business_name)
                    
                    #Process the file and attach business_id + preview
                    processed_file = process_file(file, business._id)
                    current_app.db.create_file(processed_file)
                    logger.info(f"File {file.filename} uploaded successfully for user {user.username}")

                except Exception as e:
                    # If processing fails, log the error
                    logger.error(f"Failed to process file {file.filename} for user {user.username}: {e}")
                    failed_files.append(f"{file.filename}: {str(e)}")

            # If file is not valid, log the error
            else:
                logger.warning(f"Invalid file upload attempt by user {user.username}: {getattr(file, 'filename', 'unknown')}")
                failed_files.append(f"Invalid file: {getattr(file, 'filename', 'unknown')}")

        # Return JSON response to the frontend
        return jsonify({
            'success': len(failed_files) == 0,
            'failed_files': failed_files,
            'files': [f.filename for f in current_app.db.get_files_for_user(user)]
        })

    #GET: render the upload page with current user's files
    user_files = current_app.db.get_files_for_user(user)
    return render_template('upload_files.html', files=user_files, business_name=business_name)

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

@views.route('/edit_plots/<business_name>', methods=['GET', 'POST'])
@login_required
def edit_plots(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    business = current_app.db.get_business_by_name(business_name)

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

        # Update plot order in business page
        order_success = current_app.db.update_plot_presentation_order(business._id, plot_order)

        success = plot_success and order_success

        if success:
            logger.info(f"Plot changes saved successfully for user {username}",
                        extra_fields={'user_id': user._id, 'presented_plots': len(plot_order)})
        else:
            logger.error(f"Failed to save plot changes for user {username}",
                         extra_fields={'user_id': user._id, 'plot_success': plot_success, 'order_success': order_success})

        return jsonify({'success': success})

    # GET: render the edit plots page
    all_plots = current_app.db.get_plots_for_business(business_name)
    presented_plots = [p for p in all_plots if p.is_presented]

    # Get business to determine presented plot order
    business = current_app.db.get_business_by_name(business_name)

    # Sort presented plots according to business order
    plots_dict = {plot._id: plot for plot in presented_plots}
    ordered_presented_plots = []
    for plot_id in business.presented_plot_order:
        if plot_id in plots_dict:
            ordered_presented_plots.append(plots_dict[plot_id])

    # Add any plots that are presented but not in the order list
    for plot in presented_plots:
        if plot._id not in business.presented_plot_order:
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
                         presented_plots=presented_plots_data,
                         business_name=business_name)

@views.route('/analyze_data/<business_name>', methods=['GET', 'POST'])
@login_required
def analyze_data(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    business = current_app.db.get_business_by_id(user._id)

    if request.method == 'POST':
        # This now handles the plot generation request from the new frontend
        data = request.get_json()
        file_id = data.get('file_id')
        prompt = data.get('prompt')

        if not file_id or not prompt:
            return jsonify({'success': False, 'error': 'File ID and prompt are required.'}), 400

        try:
            # Call our new plot generation function
            plot_image_b64 = generate_plot_image(file_id, prompt)
            return jsonify({'success': True, 'plot_image': plot_image_b64})

        except Exception as e:
            logger.error(f"Failed to generate plot for user {username}: {e}",
                         extra_fields={'user_id': user._id, 'file_id': file_id})
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('analyze_data.html', user=user)

@views.route('/save_generated_plot', methods=['POST'])
@login_required
def save_generated_plot():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    data = request.get_json()

    image_name = data.get('image_name')
    image_data = data.get('image_data')
    based_on_file = data.get('based_on_file')

    if not all([image_name, image_data, based_on_file]):
        return jsonify({'success': False, 'error': 'Missing required data to save plot.'}), 400

    try:
        # Create a new Plot object and save it to the database
        new_plot = Plot(
            image_name=image_name,
            image=image_data,
            files=[based_on_file],
            user_id=user._id,
            is_presented=True # New plots are presented by default
        )
        plot_id = current_app.db.create_plot(new_plot)

        # Add the new plot to the user's presentation order
        profile = current_app.db.get_or_create_user_profile(user._id)
        profile.presented_plot_order.append(plot_id)
        current_app.db.update_user_profile(user._id, {"presented_plot_order": profile.presented_plot_order})

        logger.info(f"User {username} saved a new plot: {image_name}", extra_fields={'user_id': user._id, 'plot_id': plot_id})
        return jsonify({'success': True, 'plot_id': plot_id})

    except Exception as e:
        logger.error(f"Failed to save plot for user {username}: {e}", extra_fields={'user_id': user._id})
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

@views.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)

    logger.info(f"Dashboard page accessed by user: {username}",
                extra_fields={'user_id': user._id, 'action': 'dashboard_access'})
    
    dashboard_doc = current_app.db.get_dashboard_for_user(user._id)

    return render_template('dashboard.html', user=user, dashboard=dashboard_doc), 200




@views.route('/dashboard/files', methods=['GET'])
@login_required
def list_user_files():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    user_files = current_app.db.get_files_for_user(user)

    logger.info(f"User {username} requested file list",
                extra_fields={'user_id': user._id, 'files_count': len(user_files)})

    files_payload = [
        {
            "_id": f._id,
            "filename": f.filename,
            "upload_date": f.upload_date.isoformat() if f.upload_date else None,
        }
        for f in user_files
    ]
    return jsonify({'files': files_payload}), 200





@views.route('/dashboard/create', methods=['POST'])
@login_required
def create_dashboard():
    # Identify current user
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)

    payload = request.get_json(silent=True) or {}
    logger.info(f"User {username} initiated dashboard creation",
                extra_fields={'user_id': user._id, 'payload': payload})
    
    file_id = payload.get('file_id') or request.form.get('file_id')
    if not file_id:
        logger.warning(f"User {username} tried to create dashboard without selecting file",
                       extra_fields={'user_id': user._id})
        return jsonify({"success": False, "error": "Please select a file to generate a dashboard."}), 400

    f = current_app.db.get_file(file_id)
    if not f or f.user_id != user._id:
        logger.warning(f"Unauthorized dashboard creation attempt by {username}",
                       extra_fields={'user_id': user._id, 'file_id': file_id})
        return jsonify({"success": False, "error": "You are not authorized to use the selected file."}), 403

    try:
        # Generate insights from available file (preview-based prompt to LLM)
        file_id, insights = generate_insights_for_file(file_id) 

        # Persist a new dashboard entry (we keep history by creating a new doc each time)
        current_app.db.create_dashboard(user_id=user._id, file_id=file_id, insights=insights)

        logger.info("Dashboard created", extra_fields={'user_id': user._id, 'file_id': file_id})
        flash("Dashboard created successfully", "success")

        return jsonify({"success": True, "redirect": url_for('views.dashboard')}), 200
    
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}", extra_fields={'user_id': user._id, 'file_id': file_id})
        return jsonify({"success": False, "error": "An unexpected error occurred while creating the dashboard."}), 500


@views.route('/business_page/<business_name>')
@login_required
def business_page(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    
    # Get business by name
    business = current_app.db.get_business_by_name(business_name)
    if not business:
        return render_template('error.html', error='Business not found'), 404
    
    # Get owner information
    owner = current_app.db.get_user_by_id(business.owner)
    owner_name = owner.username if owner else 'Unknown User'

    # Get files for this business
    files = current_app.db.get_files_for_business(business)
    files_data = []
    for file in files:
        files_data.append({
            '_id': file._id,
            'filename': file.filename,
            'upload_date': file.upload_date.isoformat() if file.upload_date else None,
        })

    # Get presented plots for this business
    presented_plots = current_app.db.get_presented_plots_for_business_ordered(business_name)
    # Convert plots to a format suitable for JSON serialization
    plots_data = []
    for plot in presented_plots:
        plots_data.append({
            '_id': plot._id,
            'image_name': plot.image_name,
            'image': plot.image,
            'created_time': plot.created_time.isoformat() if plot.created_time else None,
            'is_presented': plot.is_presented
        })
    
    # Create a helper function for the template to get editor user info
    def get_editor_user(editor_id):
        return current_app.db.get_user_by_id(editor_id)
    
    return render_template('business_page.html', 
                         user=user, 
                         business=business, 
                         owner=owner_name,
                         plots=plots_data,
                         files=files_data,
                         get_editor_user=get_editor_user), 200


@views.route('/add_editor/<business_name>', methods=['POST'])
@login_required
def add_editor(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    
    # Get business by name
    business = current_app.db.get_business_by_name(business_name)
    if not business:
        return render_template('error.html', error='Business not found'), 404
    
    # Check if user is the owner
    if user._id != business.owner:
        return render_template('error.html', error='Only the business owner can add editors'), 403
    
    # Get the username to add as editor
    editor_username = request.form.get('username', '').strip()
    if not editor_username:
        return redirect(url_for('views.business_page', business_name=business_name))
    
    # Find the user by username
    editor_user = current_app.db.get_user_by_username(editor_username)
    if not editor_user:
        # Could add a flash message here for better UX
        return redirect(url_for('views.business_page', business_name=business_name))
    
    # Ensure editors is a set
    if not hasattr(business, 'editors') or not isinstance(business.editors, set):
        business.editors = set([business.owner])
    
    # Check if user is already an editor
    if editor_user._id in business.editors:
        # Could add a flash message here for better UX
        return redirect(url_for('views.business_page', business_name=business_name))
    
    # Add user to editors
    business.editors.add(editor_user._id)
    
    # Update business in database
    current_app.db.update_business(business._id, {'editors': list(business.editors)})
    
    logger.info(f"User {username} added {editor_username} as editor to business {business_name}",
               extra_fields={'owner_id': user._id, 'editor_id': editor_user._id, 'business_name': business_name})
    
    return redirect(url_for('views.business_page', business_name=business_name))


@views.route('/remove_editor/<business_name>', methods=['POST'])
@login_required
def remove_editor(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    
    # Get business by name
    business = current_app.db.get_business_by_name(business_name)
    if not business:
        return render_template('error.html', error='Business not found'), 404
    
    # Check if user is the owner
    if user._id != business.owner:
        return render_template('error.html', error='Only the business owner can remove editors'), 403
    
    # Get the editor ID to remove
    editor_id = request.form.get('editor_id')
    if not editor_id:
        return redirect(url_for('views.business_page', business_name=business_name))
    
    # Check if trying to remove the owner
    if editor_id == business.owner:
        return redirect(url_for('views.business_page', business_name=business_name))
    
    # Ensure editors is a set
    if not hasattr(business, 'editors') or not isinstance(business.editors, set):
        business.editors = set([business.owner])
    
    # Remove user from editors
    if editor_id in business.editors:
        business.editors.remove(editor_id)
        
        # Update business in database
        current_app.db.update_business(business._id, {'editors': list(business.editors)})
        
        # Get editor username for logging
        editor_user = current_app.db.get_user_by_id(editor_id)
        editor_username = editor_user.username if editor_user else 'Unknown User'
        
        logger.info(f"User {username} removed {editor_username} as editor from business {business_name}",
                   extra_fields={'owner_id': user._id, 'editor_id': editor_id, 'business_name': business_name})
    
    return redirect(url_for('views.business_page', business_name=business_name))

@views.route('/businesses_search')
@login_required
def businesses_search():
    return render_template('generic_page.html', title='Businesses Search', content='Coming soon'), 200

@views.route('/new_business', methods=['GET', 'POST'])
@login_required
def new_business():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validate mandatory fields
        if not name:
            return render_template('new_business.html', 
                                 error='Business name is required',
                                 form_data={'name': name, 'address': address, 'phone': phone, 'email': email})
        
        # Check if business name already exists
        existing_business = current_app.db.get_business_by_name(name)
        if existing_business:
            return render_template('new_business.html', 
                                 error=f'A business with the name "{name}" already exists. Please choose a different name.',
                                 form_data={'name': name, 'address': address, 'phone': phone, 'email': email})
        
        try:
            # Create new business
            new_business = Business(
                owner=user._id,
                name=name,
                address=address if address else None,
                phone=phone if phone else None,
                email=email if email else None
            )
            
            # Save to database
            business_id = current_app.db.create_business(new_business)
            
            logger.info(f"User {username} created new business: {name}",
                       extra_fields={'user_id': user._id, 'business_id': business_id, 'business_name': name})
            
            # Redirect to the new business page
            return redirect(url_for('views.business_page', business_name=name))
            
        except Exception as e:
            logger.error(f"Failed to create business for user {username}: {e}",
                        extra_fields={'user_id': user._id, 'business_name': name})
            return render_template('new_business.html', 
                                 error='An error occurred while creating the business. Please try again.',
                                 form_data={'name': name, 'address': address, 'phone': phone, 'email': email})
    
    # GET request - show the form
    return render_template('new_business.html')
