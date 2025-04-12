"""
Controllers package initialization
"""
from flask import redirect, url_for

def init_app(app):
    # Import blueprints
    from controllers.appointment_controller import appointment_bp
    from controllers.customer_controller import customer_bp
    from controllers.whatsapp_controller import whatsapp_bp
    from controllers.admin_controller import admin_bp
    
    # Register blueprints with the app
    app.register_blueprint(appointment_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(admin_bp)
    
    # Add root route
    @app.route('/')
    def index():
        """Redirect to admin login page"""
        return redirect(url_for('admin.login'))