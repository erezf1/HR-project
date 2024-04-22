
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import csv

def initialize_storage(service, folder_id, file_name='Resume_Review_Results.csv'):
    # Check if the CSV file exists in the specified Google Drive folder. If not, create it.
    response = service.files().list(q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
                                    spaces='drive',
                                    fields='files(id, name)').execute()
    files = response.get('files', [])
    
    if not files:
        # If the file does not exist, create it
        file_metadata = {
            'name': file_name,
            'parents': [folder_id],
            'mimeType': 'text/csv'
        }
        file = service.files().create(body=file_metadata, fields='id').execute()
        file_id = file.get('id')
        # Initialize the file with headers
        fh = io.StringIO()
        writer = csv.writer(fh)
        writer.writerow(['File Name', 'Submission Date', 'Responses'])
        fh.seek(0)
        media = MediaIoBaseUpload(io.BytesIO(fh.getvalue().encode()), mimetype='text/csv')
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        file_id = files[0].get('id')
    
    return file_id

def write_to_csv1(service, file_id, data):
    # Download the existing CSV content
    print("in scv write::", service)

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    # Append the new data
    fh.seek(0)
    content = fh.getvalue().decode()
    content += "\n" + ','.join([str(data['file_name']), str(data['submission_date']), str(data['responses'])])
    print(content)
    # Upload the updated content
    fh = io.BytesIO(content.encode())
    media = MediaIoBaseUpload(fh, mimetype='text/csv', resumable=True)
    service.files().update(fileId=file_id, media_body=media).execute()


def write_to_csv(service, file_id, data):
    # Download the existing CSV content
    print("in csv write::", service)
    
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        
    # Append the new data
    fh.seek(0)
    content = fh.getvalue().decode()
    
    if content.strip():  # check if the csv is not empty
        content += "\n"
    
    content += ','.join(['"'+str(data.get('file_name', '')).replace('"', '""')+'"', 
                         '"'+str(data.get('submission_date', '')).replace('"', '""')+'"', 
                         '"'+str(data.get('gpt_analytics', '')).replace('"', '""')+'"'])
    print(content)
    
    # Upload the updated content
    fh = io.BytesIO(content.encode())
    media = MediaIoBaseUpload(fh, mimetype='text/csv', resumable=True)
    service.files().update(fileId=file_id, media_body=media).execute()
    
def generate_report(service, file_id, start_date, end_date):
    # Placeholder for report generation logic
    print(f"Generating report from {start_date} to {end_date} for file {file_id}.")
