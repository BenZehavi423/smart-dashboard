from flask import current_app, session
from werkzeug.utils import secure_filename

def process_file(file):
    # Secure the filename (removes special characters)
    filename = secure_filename(file.filename)
    # Here you would parse/validate the file content as needed
    # For now, just save the file (implement your own save logic)
    return file

import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from .models import File

def process_file(file, business_id):
    # Secure the filename (removes special characters)
    filename = secure_filename(file.filename)

    # Try to read the CSV file with pandas - another protaction for file kind
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")

    # Create a preview: first 5 rows as list of dictionaries
    preview = df.head().to_dict(orient="records")

    # Create File object with preview
    new_file = File(
        business_id=business_id,
        filename=filename,
        upload_date=datetime.now(timezone.utc)
    )

    # Attach preview manually (not part of original constructor)
    new_file.preview = preview

    return new_file
