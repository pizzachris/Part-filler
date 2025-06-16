#!/usr/bin/env python3
"""
Product Data Enrichment Flask Application
A modern web app for enriching product data from Excel files and PDF manuals.
"""

import os
import pandas as pd
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import re
from typing import Dict, List, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'pdf'}

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_specs_from_part_number(part_number: str) -> Dict[str, str]:
    """Extract specifications from part number patterns."""
    specs = {}
    
    if not part_number or not isinstance(part_number, str):
        return specs
    
    # Common patterns for extracting specs from part numbers
    patterns = {
        'voltage': r'(\d+)V',
        'amperage': r'(\d+)A(?![\w])',
        'horsepower': r'(\d+(?:\.\d+)?)HP',
        'phase': r'(\d)PH',
        'rpm': r'(\d+)RPM',
    }
    
    for spec_type, pattern in patterns.items():
        match = re.search(pattern, part_number.upper())
        if match:
            specs[spec_type] = match.group(1)
    
    return specs

def enrich_product_data(df: pd.DataFrame) -> Dict:
    """Enrich product data by extracting information from part numbers and existing data."""
    enrichment_stats = {
        'total_products': len(df),
        'enriched_products': 0,
        'new_fields_added': 0,
        'errors': []
    }
    
    # Ensure required columns exist
    required_columns = ['part_number', 'description', 'manufacturer']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Add enrichment columns if they don't exist
    enrichment_columns = ['voltage', 'amperage', 'horsepower', 'phase', 'rpm', 'category', 'enrichment_status']
    for col in enrichment_columns:
        if col not in df.columns:
            df[col] = ''
            enrichment_stats['new_fields_added'] += 1
    
    # Process each row
    for idx, row in df.iterrows():
        part_number = str(row.get('part_number', ''))
        description = str(row.get('description', ''))
        
        if part_number and part_number != 'nan':
            # Extract specs from part number
            specs = extract_specs_from_part_number(part_number)
            
            enriched = False
            for spec_type, value in specs.items():
                if spec_type in df.columns and (not row[spec_type] or str(row[spec_type]) == ''):
                    df.at[idx, spec_type] = value
                    enriched = True
            
            # Categorize based on description or part number
            category = categorize_product(part_number, description)
            if category and (not row.get('category') or str(row['category']) == ''):
                df.at[idx, 'category'] = category
                enriched = True
            
            if enriched:
                df.at[idx, 'enrichment_status'] = f'Enriched on {datetime.now().strftime("%Y-%m-%d")}'
                enrichment_stats['enriched_products'] += 1
            else:
                df.at[idx, 'enrichment_status'] = 'No enrichment needed'
    
    return {
        'enriched_df': df,
        'stats': enrichment_stats
    }

def categorize_product(part_number: str, description: str) -> str:
    """Categorize product based on part number and description."""
    text = f"{part_number} {description}".upper()
    
    categories = {
        'Motor': ['MOTOR', 'MOT', 'HP'],
        'Valve': ['VALVE', 'VLV', 'BALL', 'GATE'],
        'Pump': ['PUMP', 'PMP'],
        'Bearing': ['BEARING', 'BRG'],
        'Belt': ['BELT', 'BLT'],
        'Sensor': ['SENSOR', 'SNS', 'TEMP', 'PRESSURE'],
        'Switch': ['SWITCH', 'SW'],
        'Relay': ['RELAY', 'RLY'],
        'Connector': ['CONNECTOR', 'CONN', 'PLUG'],
        'Filter': ['FILTER', 'FLT'],
    }
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return 'Uncategorized'

@app.route('/')
def index():
    """Main upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Please upload Excel (.xlsx, .xls) or PDF files.'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file
        if filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
            result = enrich_product_data(df)
            
            # Save enriched data
            output_filename = f"enriched_{filename}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            result['enriched_df'].to_excel(output_path, index=False)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'stats': result['stats'],
                'download_url': url_for('download_file', filename=output_filename),
                'preview_data': result['enriched_df'].head(10).to_dict('records')
            })
        
        elif filename.lower().endswith('.pdf'):
            # For now, return a placeholder response for PDF files
            os.remove(filepath)
            return jsonify({
                'success': True,
                'message': 'PDF processing feature coming soon!',
                'stats': {'total_products': 0, 'enriched_products': 0}
            })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed file."""
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError:
        flash('File not found')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
