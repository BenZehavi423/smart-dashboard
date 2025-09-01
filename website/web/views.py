from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, flash
import os
from .auth import login_required
from .csv_processor import process_file
from .models import Plot, Business
from .validation import Validator
from .logger import logger
import requests
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
    owned_businesses = current_app.db.get_businesses_for_owner(user._id)
    shared_businesses = current_app.db.get_businesses_as_editor(user._id)
    logger.info(
        f"Profile page accessed by user: {username}, found {len(owned_businesses)} owned and {len(shared_businesses)} shared businesses.",
        extra_fields={'user_id': user._id})

    return render_template('profile.html',
                           user=user,
                           owned_businesses=owned_businesses,
                           shared_businesses=shared_businesses), 200

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
    
    business = current_app.db.get_business_by_name(business_name)
    if not business:
        return jsonify({'success': False, 'error': 'Business not found'}), 404
    
    # Handle file upload via AJAX post request
    # POST: process uploaded files
    if request.method == 'POST':
        files = request.files.getlist('file')
        logger.info(f"User {user.username} uploading {len(files)} files")
        failed_files = []

        for file in files:
            try:
                # Validate file using the Validator class
                file_valid, file_error = Validator.validate_file(file)
                
                if file_valid:
                    logger.debug(f"Processing file: {file.filename}")
                    try:              
                        #Process the file and attach business_id + preview
                        processed_file = process_file(file, business._id)
                        current_app.db.create_file(processed_file)
                        logger.info(f"File {file.filename} uploaded successfully for user {user.username}")

                    except Exception as e:
                        # If processing fails, log the error
                        logger.error(f"Failed to process file {file.filename} for user {user.username}: {e}")
                        failed_files.append(f"{file.filename}: {str(e)}")
                else:
                    logger.warning(f"Invalid file upload attempt by user {user.username}: {getattr(file, 'filename', 'unknown')} - {file_error}")
                    failed_files.append(f"{getattr(file, 'filename', 'unknown')}: {file_error}")
            except Exception as e:
                # Handle any unexpected errors during validation
                logger.error(f"Unexpected error during file validation for user {user.username}: {e}")
                failed_files.append(f"{getattr(file, 'filename', 'unknown')}: Unexpected error during validation")

        # Return JSON response to the frontend
        return jsonify({
            'success': len(failed_files) == 0,
            'failed_files': failed_files,
            'files': [f.filename for f in current_app.db.get_files_for_business(business)]
        })

    #GET: render the upload page with current user's files
    user_files = current_app.db.get_files_for_business(business)
    return render_template('upload_files.html', files=user_files, business_name=business_name)


@views.route('/edit_plots/<business_name>', methods=['GET', 'POST'])
@login_required
def edit_plots(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    business = current_app.db.get_business_by_name(business_name)

    if not business:
        return render_template('error.html',
                               error='Business not found'), 404

    if user._id not in business.editors:
        return render_template('error.html',
                               error='You do not have permission to access this business.'), 403
    
    logger.info(f"Edit plots page accessed by user: {username}",
                extra_fields={'user_id': user._id, 'action': 'edit_plots_access'})

    if request.method == 'POST':
        # Handle AJAX request for saving plot changes
        try:
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
            
        plot_updates = data.get('plot_updates', [])
        plot_order = data.get('plot_order', [])

        logger.info(f"User {username} saving plot changes: {len(plot_updates)} updates, {len(plot_order)} plots in order",
                    extra_fields={'user_id': user._id, 'updates_count': len(plot_updates),
                                  'order_length': len(plot_order)})

        success = current_app.db.save_plot_changes_for_business(business._id, plot_updates, plot_order)

        if success:
            logger.info(f"Plot changes saved successfully for user {username}",
                        extra_fields={'user_id': user._id, 'presented_plots': len(plot_order)})
        else:
            logger.error(f"Failed to save plot changes for user {username}")

        # Convert MagicMock to boolean for JSON serialization
        success_bool = bool(success) if hasattr(success, '__bool__') else bool(success)
        return jsonify({'success': success_bool})

    # GET: render the edit plots page
    all_plots = current_app.db.get_plots_for_business(business._id)
    ordered_presented_plots = []
    plots_dict = {plot._id: plot for plot in all_plots if plot.is_presented}

    for plot_id in business.presented_plot_order:
        if plot_id in plots_dict:
            ordered_presented_plots.append(plots_dict[plot_id])

    for plot in all_plots:
        if plot.is_presented and plot._id not in business.presented_plot_order:
            ordered_presented_plots.append(plot)

    all_plots_data = [{
        '_id': p._id, 'image_name': p.image_name, 'image': p.image,
        'created_time': p.created_time.isoformat() if p.created_time else None,
        'is_presented': p.is_presented
    } for p in all_plots]

    presented_plots_data = [{
        '_id': p._id, 'image_name': p.image_name, 'image': p.image,
        'created_time': p.created_time.isoformat() if p.created_time else None,
        'is_presented': p.is_presented
    } for p in ordered_presented_plots]

    # Log the page render with plot statistics
    presented_count = len([p for p in all_plots if p.is_presented])
    logger.info(f"Edit plots page rendered for user {username}: {len(all_plots)} total plots, {presented_count} presented",
                extra_fields={'user_id': user._id, 'total_plots': len(all_plots), 'presented_plots': presented_count})

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
    business = current_app.db.get_business_by_name(business_name)

    if not business:
        return jsonify({'success': False, 'error': 'business not found'}), 404

    if request.method == 'POST':
        # This now handles the plot generation request from the new frontend
        try:
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
            
        file_id = data.get('file_id')
        prompt = data.get('prompt', '').strip()
        
        # Sanitize inputs
        file_id = Validator.sanitize_input(str(file_id))
        prompt = Validator.sanitize_input(prompt)

        if not file_id:
            return jsonify({'success': False, 'error': 'File ID is required.'}), 400
        
        # Validate prompt
        prompt_valid, prompt_error = Validator.validate_analysis_prompt(prompt)
        if not prompt_valid:
            return jsonify({'success': False, 'error': prompt_error}), 400

        try:
            # Call our new plot generation function
            plot_image_b64 = generate_plot_image(file_id, prompt)
            return jsonify({'success': True, 'plot_image': plot_image_b64})

        except Exception as e:
            logger.error(f"Failed to generate plot for user {username}: {e}",
                         extra_fields={'user_id': user._id, 'file_id': file_id})
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('analyze_data.html', user=user, business_name=business_name)

@views.route('/save_generated_plot/<business_name>', methods=['POST'])
@login_required
def save_generated_plot(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    business = current_app.db.get_business_by_name(business_name)

    if not business or user._id not in business.editors:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        if data is None:
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400

    image_name = data.get('image_name', '').strip()
    image_data = data.get('image_data')
    based_on_file = data.get('based_on_file')
    
    # Sanitize inputs
    image_name = Validator.sanitize_input(image_name)
    based_on_file = Validator.sanitize_input(str(based_on_file))

    if not image_data or not based_on_file:
        return jsonify({'success': False, 'error': 'Missing required data to save plot.'}), 400
    
    # Validate plot name
    name_valid, name_error = Validator.validate_plot_name(image_name)
    if not name_valid:
        return jsonify({'success': False, 'error': name_error}), 400

    try:
        # Create a new Plot object and save it to the database
        new_plot = Plot(
            image_name=image_name,
            image=image_data,
            files=[based_on_file],
            business_id=business._id
        )
        plot_id = current_app.db.create_plot(new_plot)

        # Update the business's plot order (not the user's old profile).
        business.presented_plot_order.append(plot_id)
        current_app.db.update_business(business._id, {"presented_plot_order": business.presented_plot_order})

        logger.info(f"User {username} saved a new plot: {image_name}", extra_fields={'user_id': user._id, 'plot_id': plot_id})
        return jsonify({'success': True, 'plot_id': plot_id})

    except Exception as e:
        logger.error(f"Failed to save plot for user {username}: {e}", extra_fields={'user_id': user._id})
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500



@views.route('/dashboard/files', methods=['GET'])
@login_required
def list_user_files():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)

    # Get all businesses the user has access to (as owner or editor)
    user_businesses = current_app.db.get_businesses_for_editor(user._id)

    # Get files from all businesses
    all_files = []
    for business in user_businesses:
        business_files = current_app.db.get_files_for_business(business)
        all_files.extend(business_files)

    logger.info(f"User {username} requested file list",
                extra_fields={'user_id': user._id, 'files_count': len(all_files)})

    files_payload = [
        {
            "_id": f._id,
            "filename": f.filename,
            "upload_date": f.upload_date.isoformat() if f.upload_date else None,
        }
        for f in all_files
    ]
    return jsonify({'files': files_payload}), 200

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
    
    # Validate username
    username_valid, username_error = Validator.validate_username(editor_username)
    if not username_valid:
        flash(username_error, 'error')
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
    editor_id = request.form.get('editor_id', '').strip()
    if not editor_id:
        flash('Editor ID is required', 'error')
        return redirect(url_for('views.business_page', business_name=business_name))
    
    # Sanitize and validate editor_id
    editor_id = Validator.sanitize_input(editor_id)
    
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
        
        # Sanitize inputs
        name = Validator.sanitize_input(name)
        address = Validator.sanitize_input(address)
        phone = Validator.sanitize_input(phone)
        email = Validator.sanitize_input(email)
        
        # Validate all fields
        validation_rules = {
            'name': {'type': 'business_name', 'required': True, 'label': 'Business name'},
            'address': {'type': 'address', 'required': False, 'label': 'Address'},
            'phone': {'type': 'phone', 'required': False, 'label': 'Phone'},
            'email': {'type': 'email', 'required': False, 'label': 'Email'}
        }
        
        errors = Validator.validate_form_data({
            'name': name,
            'address': address,
            'phone': phone,
            'email': email
        }, validation_rules)
        
        if errors:
            error_message = list(errors.values())[0]  # Show first error
            return render_template('new_business.html', 
                                 error=error_message,
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

@views.route('/edit_business_details/<business_name>', methods=['GET', 'POST'])
@login_required
def edit_business_details(business_name):
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    
    # Get business by name
    business = current_app.db.get_business_by_name(business_name)
    if not business:
        return render_template('error.html', error='Business not found'), 404
    
    # Check if user is an editor
    if user._id not in business.editors:
        return render_template('error.html', error='You do not have permission to edit this business'), 403
    
    if request.method == 'POST':
        # Update business details
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        # Sanitize inputs
        address = Validator.sanitize_input(address)
        phone = Validator.sanitize_input(phone)
        email = Validator.sanitize_input(email)
        
        # Validate fields
        validation_rules = {
            'address': {'type': 'address', 'required': False, 'label': 'Address'},
            'phone': {'type': 'phone', 'required': False, 'label': 'Phone'},
            'email': {'type': 'email', 'required': False, 'label': 'Email'}
        }
        
        errors = Validator.validate_form_data({
            'address': address,
            'phone': phone,
            'email': email
        }, validation_rules)
        
        if errors:
            error_message = list(errors.values())[0]
            flash(error_message, 'error')
            return redirect(url_for('views.edit_business_details', business_name=business_name))
        
        # Update business in database
        update_data = {}
        if address != business.address:
            update_data['address'] = address if address else None
        if phone != business.phone:
            update_data['phone'] = phone if phone else None
        if email != business.email:
            update_data['email'] = email if email else None
        
        if update_data:
            current_app.db.update_business(business._id, update_data)
            logger.info(f"User {username} updated business {business_name} details",
                       extra_fields={'user_id': user._id, 'business_name': business_name, 'updates': update_data})
        
        return redirect(url_for('views.business_page', business_name=business_name))
    
    return render_template('edit_business_details.html', business=business, business_name=business_name)

@views.route('/edit_profile_details', methods=['GET', 'POST'])
@login_required
def edit_profile_details():
    username = session.get('username')
    user = current_app.db.get_user_by_username(username)
    
    if request.method == 'POST':
        # Update user details
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Sanitize inputs
        email = Validator.sanitize_input(email)
        phone = Validator.sanitize_input(phone)
        
        # Validate fields
        validation_rules = {
            'email': {'type': 'email', 'required': False, 'label': 'Email'},
            'phone': {'type': 'phone', 'required': False, 'label': 'Phone'}
        }
        
        errors = Validator.validate_form_data({
            'email': email,
            'phone': phone
        }, validation_rules)
        
        if errors:
            error_message = list(errors.values())[0]
            flash(error_message, 'error')
            return redirect(url_for('views.edit_profile_details'))
        
        # Update user in database
        update_data = {}
        if email != user.email:
            update_data['email'] = email if email else None
        if phone != user.phone:
            update_data['phone'] = phone if phone else None
        
        if update_data:
            current_app.db.update_user(user._id, update_data)
            logger.info(f"User {username} updated their profile",
                       extra_fields={'user_id': user._id, 'updates': update_data})
        
        return redirect(url_for('views.profile'))
    
    return render_template('edit_profile_details.html', user=user)
