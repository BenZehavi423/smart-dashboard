import argparse
from web import create_app, socketio
from web.logger import logger
import sys
# Ensure the web package is in the Python path
sys.path.append("/app")

app = create_app()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask server.')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    logger.info(f"Starting Smart Dashboard server on port {args.port}")
    if args.debug:
        logger.info("Debug mode enabled")
    
    try:
        socketio.run(app, debug=args.debug, host='0.0.0.0', port=args.port, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)