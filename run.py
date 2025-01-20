from app import app
from app.routes import admin_routes, volunteer_routes, certification_routes, transaction_routes
from app.routes import home_routes, organization_routes, event_routes
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
