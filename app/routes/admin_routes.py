import logging
from flask import Blueprint, request, render_template, redirect, url_for, jsonify ,flash
from app.models import User
from app.services.admin_service import AdminService
from app.utils.decorators import role_required
from flask_login import login_user, logout_user, current_user


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure logs are sent to stdout for CloudWatch
    ]
)
logger = logging.getLogger(__name__)

error_template = "error.html"
not_implemented = NotImplementedError("Implement this logic")

# Define Blueprint
admin_bp = Blueprint('admin', __name__)
admin_service = AdminService()

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Handle admin login page and form submission."""
    # For GET requests, just show the login page
    if request.method == 'GET':
        print("Admin Login page")
        return render_template("AdminLogin.html")

    # For POST requests, process the login form
    email = request.form.get('email')
    password = request.form.get('password')

    # Validate form inputs
    if not email or not password:
        logger.warning("Login attempt with missing email or password.")
        return render_template("AdminLogin.html", error="Email and password are required.")

    try:
        # Query the database for an admin user
        admin = User.query.filter_by(email=email, role='admin').first()

        # Validate password
        if admin and admin.check_password(password):
            # Important: This is where you need to log the user in with Flask-Login
            login_user(admin)
            logger.info(f"Admin login successful for email: {email}")
            return redirect(url_for('admin.admin_home'))
        else:
            logger.warning(f"Login attempt failed for email: {email}")
            return render_template("AdminLogin.html", error="Invalid email or password.")
    except Exception as e:
        logger.error(f"Error during login process: {e}", exc_info=True)
        return render_template(error_template, error_message="Unexpected error occurred during login.")

@admin_bp.route('/admin/home', methods=['GET'])
@role_required('admin')
def admin_home():
    """Render the admin home page."""
    logger.info("Rendering admin home page.")
    return render_template("AdminHome.html")


@admin_bp.route('/admin/bookings', methods=['GET'])
@role_required('admin')
def admin_bookings():
    """Fetch and render all course bookings."""
    try:
        # Get course ID from query parameters
        course_id = request.args.get('course_id', type=int)
        
        if course_id:
            # Fetch bookings for the specific course ID
            logger.info(f"Fetching bookings for Course ID: {course_id}")
            bookings = admin_service.get_bookings_by_course(course_id)
        else:
            # Fetch all bookings
            logger.info("Fetching all bookings.")
            bookings = admin_service.get_all_bookings()
        
        if not bookings:
            logger.warning(f"No bookings found{' for Course ID: ' + str(course_id) if course_id else ''}.")
            return render_template("AdminBookings.html", bookings=[])
        
        logger.info(f"Successfully fetched {len(bookings)} bookings{' for Course ID: ' + str(course_id) if course_id else ''}.")
        return render_template("AdminBookings.html", bookings=bookings)
    
    except Exception as e:
        logger.error(f"Error fetching bookings: {e}", exc_info=True)
        return render_template("error.html", error_message="Failed to load bookings.")


@admin_bp.route('/admin/users', methods=['GET'])
@role_required('admin')
def admin_users():
    """Fetch and render all users."""
    try:
        # admin_service = AdminService()
        users = admin_service.get_all_users()
        if not users:
            logger.warning("No users found.")
            return render_template("AdminUsers.html", users=[])
        logger.info(f"Successfully fetched {len(users)} users.")
        return render_template("AdminUsers.html", users=users)
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to load users.")


@admin_bp.route('/admin/courses', methods=['GET'])
@role_required('admin')
def list_courses():
    """Fetch and render all courses."""
    try:
        courses = admin_service.get_all_course_details()
        if not courses:
            logger.warning("No courses found.")
            return render_template("AdminCourseList.html", courses=[])
        logger.info(f"Successfully fetched {len(courses)} courses.")
        return render_template("AdminCourseList.html", courses=courses)
    except Exception as e:
        logger.error(f"Error fetching courses: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to load courses.")


@admin_bp.route('/admin/bookings/<int:booking_id>/status', methods=['POST'])
@role_required('admin')
def update_booking_status(booking_id):
    """Update the status of a booking."""
    try:
        new_status = request.form.get('status')
        logger.info(f"Updating booking status for ID: {booking_id} to {new_status}")
        admin_service.update_booking_status(booking_id, new_status=new_status)
        return f"Booking status updated for ID {booking_id}."
    except Exception as e:
        logger.error(f"Failed to update booking status for ID {booking_id}: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to update booking status.")

@admin_bp.route('/admin/bookings/<int:booking_id>', methods=['PATCH'])
@role_required('admin')
def update_booking(booking_id):
    """Update a booking by its ID."""
    try:
        logger.info(f"Updating booking with ID: {booking_id}")
        updated_booking = request.form.get('booking')
        admin_service.update_booking(booking_id, updated_booking)
        # Add logic to update the booking
        return f"Booking {booking_id} updated successfully."
    except Exception as e:
        logger.error(f"Failed to update booking with ID {booking_id}: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to load bookings"), 500

@admin_bp.route('/admin/update-subscription/<int:booking_id>', methods=['POST'])
@role_required('admin')
def update_subscription(booking_id):
    form_data = request.form
    updated_subscription = admin_service.update_booking(booking_id, **form_data)
    if updated_subscription:
        return redirect(url_for('admin.admin_bookings'))
    else:
        return "Subscription not found", 404

@admin_bp.route('/admin/bookings/<int:booking_id>', methods=['DELETE'])
@role_required('admin')
def delete_booking(booking_id):
    """
    Route to delete a subscription (booking).
    """
    try:
        # Call the delete_booking method in the service
        
        # Redirect to the admin bookings page on success
        return redirect(url_for('admin.admin_bookings'))
    except ValueError as e:
        # Handle case where booking is not found
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"success": False, "message": "An error occurred."}), 500


# Create a new course
@admin_bp.route('/admin/courses', methods=['POST'])
@role_required('admin')
def create_course():
    try:
        data = request.form
        name = data.get("name")
        description = data.get("description")
        price = float(data.get("price"))

        course_id = admin_service.create_course(name, description, price)

        raise not_implemented
        return f"Course created with ID {course_id}", 201

    except Exception as e:
        logger.error(f"Failed to create course: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to create course"), 500


@admin_bp.route('/admin/courses/<int:course_id>', methods=['PATCH'])
@role_required('admin')
def update_course(course_id):
    try:
        data = request.form
        name = data.get("name")
        description = data.get("description")
        price = data.get("price")

        result = admin_service.update_course(course_id, name, description, float(price) if price else None)

        if result:
            raise not_implemented
            return f"Course {course_id} updated successfully", 200
        else:
            logger.error(f"Course {course_id} not found")
            return render_template(error_template, error_message="Course not found"), 404

    except Exception as e:
        logger.error(f"Failed to update course {course_id}: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to update course"), 500

# Delete course
@admin_bp.route('/admin/courses/<int:course_id>', methods=['DELETE'])
@role_required('admin')
def delete_course(course_id):
    try:
        result = admin_service.delete_course(course_id)
        if result:
            raise not_implemented
            return f"Course {course_id} deleted successfully", 200
        else:
            logger.error(f"Course {course_id} not found")
            return render_template(error_template, error_message="Course not found"), 404

    except Exception as e:
        logger.error(f"Failed to delete course {course_id}: {e}", exc_info=True)
        return render_template(error_template, error_message="Failed to delete course"), 500


@admin_bp.route('/admin/add-course', methods=['POST'])
@role_required('admin')
def add_course():
    """
    Route to add a new course.
    """
    # Collect course data
    course_name = request.form.get('name')
    course_description = request.form.get('description')
    course_price = request.form.get('price')

    # Validation: Ensure course details are valid
    if not course_name:
        flash("Course name is required!", "error")
        return redirect(url_for('admin.create_course'))

    # Prepare course data
    course_data = {
        'name': course_name,
        'description': course_description,
        'price': float(course_price) if course_price else 0.0
    }

    # Save the course in the database
    course_id = admin_service.add_course(course_data)

    if course_id:
        flash("Course added successfully! Now you can add modules to the course.", "success")
        # Redirect to the module addition page with the newly created course ID
        return redirect(url_for('admin.create_course', course_id=course_id))
    else:
        flash("An error occurred while adding the course. Please try again.", "error")
        return redirect(url_for('admin.create_course'))
    
    
@admin_bp.route('/admin/add-modules', methods=['POST'])
@role_required('admin')
def add_modules():
    """
    Route to add modules to an existing course.
    """
    # Collect course ID and module data
    course_id = request.form.get('course_id')
    module_titles = request.form.getlist('module_titles[]')
    module_descriptions = request.form.getlist('module_descriptions[]')

    # Validation: Ensure course ID and modules are valid
    if not course_id:
        flash("You must select a course before adding modules!", "error")
        return redirect(url_for('admin.create_course'))

    if not module_titles or len(module_titles) == 0 or all(title.strip() == "" for title in module_titles):
        flash("At least one module is required with a valid title!", "error")
        return redirect(url_for('admin.reate_course', course_id=course_id))

    # Prepare module data
    module_data = [
        {'title': title.strip(), 'description': description.strip()}
        for title, description in zip(module_titles, module_descriptions)
        if title.strip()
    ]

    # Add modules to the course
    success = admin_service.add_modules_to_course(course_id, module_data)

    if success:
        flash("Modules added successfully!", "success")
        return redirect(url_for('admin.list_courses'))
    else:
        flash("An error occurred while adding the modules. Please try again.", "error")
        return redirect(url_for('admin.create_course', course_id=course_id))
 


@admin_bp.route('/admin/get-courses', methods=['GET'])
@role_required('admin')
def get_courses():
    """
    Fetch all courses as JSON to populate the dropdown.
    """
    # Fetch all courses
    courses = admin_service.get_all_courses()

    # Return courses as JSON
    if courses:
        return jsonify({'courses': courses})
    else:
        return jsonify({'courses': []}), 404

@admin_bp.route('/admin/logout')
def admin_logout():
    """Handle admin logout."""
    if current_user.is_authenticated:
        logger.info(f"Admin logged out: {current_user.email}")
        logout_user()
        flash("You have been logged out successfully.", "success")
    return redirect(url_for('admin.admin_login'))
