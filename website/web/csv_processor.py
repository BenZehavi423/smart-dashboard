from flask import current_app, session
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from .models import File
from .logger import logger

def process_file(file, business_id):
    # Secure the filename (removes special characters)
    filename = secure_filename(file.filename)

    # Try to read the CSV file with pandas - another protaction for file kind
    try:
        df = pd.read_csv(file)
        logger.info(f"File {filename} successfully read as CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to parse CSV file {filename}: {e}")
        raise ValueError(f"Failed to parse CSV: {e}")

    # Create a preview: first 5 rows as list of dictionaries
    preview = df.head(100).to_dict(orient="records")
    logger.info(f"Preview created for file {filename} with {len(preview)} rows")
    # Create File object with preview
    new_file = File(
        business_id=business_id,
        filename=filename,
        upload_date=datetime.now(timezone.utc)
    )

    # Attach preview manually (not part of original constructor)
    new_file.preview = preview
    logger.info(f"File object created for {filename} with business_id={business_id}")

    return new_file
