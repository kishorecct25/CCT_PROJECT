"""
Web routes for the CCT Web Application.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app

web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@web_bp.route('/login')
def login():
    """Render the login page."""
    return render_template('login.html')

@web_bp.route('/register')
def register():
    """Render the registration page."""
    return render_template('register.html')

@web_bp.route('/dashboard')
def dashboard():
    """Render the dashboard page."""
    return render_template('dashboard.html')

@web_bp.route('/devices')
def devices():
    """Render the devices page."""
    return render_template('devices.html')

@web_bp.route('/device/<device_id>')
def device_detail(device_id):
    """Render the device detail page."""
    return render_template('device_detail.html', device_id=device_id)

@web_bp.route('/profile')
def profile():
    """Render the user profile page."""
    return render_template('profile.html')

@web_bp.route('/notifications')
def notifications():
    """Render the notifications page."""
    return render_template('notifications.html')

@web_bp.route('/settings')
def settings():
    """Render the settings page."""
    return render_template('settings.html')
