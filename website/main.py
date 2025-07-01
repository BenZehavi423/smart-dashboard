import argparse
from web import create_app
import sys
# Ensure the web package is in the Python path
sys.path.append("/app")

app = create_app()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask server.')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    app.run(debug=True, host='0.0.0.0', port=args.port)