# Product Data Enrichment Tool

A web-based tool for enriching product data from Excel files and PDF manuals.

## Features

- Upload Excel files and PDF manuals
- Automatically enrich missing product data
- Flag potentially incorrect data
- Generate detailed enrichment reports
- Download enriched data in Excel format

## Running the Application

### Using Docker (Recommended)

1. Install Docker and Docker Compose on your system
2. Clone this repository
3. Run the following command in the project directory:
   ```bash
   docker-compose up
   ```
4. Open your web browser and navigate to `http://localhost:5000`

### Manual Setup

1. Install Python 3.9 or later
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```bash
   python -m flask run
   ```
4. Open your web browser and navigate to `http://localhost:5000`

## Usage

1. Upload your Excel file or PDF manual using the web interface
2. The application will process the file and enrich the data
3. View the enrichment report and download the enriched data
4. The enriched data will be available as an Excel file

## File Formats

- Excel files (.xlsx)
- PDF manuals (.pdf)

## Notes

- Maximum file size: 16MB
- The application will automatically create an 'uploads' directory for temporary file storage
- Enriched data and reports are saved in the 'uploads' directory
