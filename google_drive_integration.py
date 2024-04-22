import io
import os
import dicttoxml
import datetime
from io import BytesIO
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload

LOG_FILE_PATH = './log.txt'  # Define the path for the log file

def log_message(message, log_file_path=LOG_FILE_PATH):
    with open(log_file_path, 'a') as log_file:  # Open the log file in append mode
        log_file.write(f"{message}\n")  # Add the message to the log file
    print(message)
    
# Initialize the Google Drive API client
def authenticate():
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('drive', 'v3', credentials=creds)
    return service

# List all files within the specified folder
def list_files(folder_id):
    service = authenticate()
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        pageSize=10, 
        fields="nextPageToken, files(id, name, createdTime)").execute()
    items = results.get('files', [])
    if not items:
        log_message('No files found.')
    else:
        log_message('Files:')
        for item in items:
            log_message(u'{0} ({1})'.format(item['name'], item['id']))
    return items

def create_subfolder(service, folder_name, parent_folder_id):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    log_message(f"Folder '{folder_name}' created with id: {folder.get('id')} inside parent folder with id: {parent_folder_id}")
    return folder.get('id')

def find_or_create_folder(service, folder_name, parent_id):

    # Define the Google Drive folder MIME type
    folder_mime_type = 'application/vnd.google-apps.folder'
    
    # First try to find the folder
    try:
        query = f"mimeType='{folder_mime_type}' and name='{folder_name}' and '{parent_id}' in parents and trashed=false"
        response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = response.get('files', [])
        
        if files:
            # Folder exists, so return the existing folder's ID
            return files[0]['id']
        else:
            # Folder does not exist, so create it
            file_metadata = {
                'name': folder_name,
                'mimeType': folder_mime_type,
                'parents': [parent_id]
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')
            
    except HttpError as error:
        log_message(f'An error occurred: {error}')
        # Add any custom error handling here.
        raise error
    
def save_to_xml(service, analysis_response, resume_file_name, folder_id):
    try:
        # Convert the combined data to XML formatted string
        xml_content = dicttoxml.dicttoxml(analysis_response, custom_root='analysis', attr_type=False).decode()

        # Query if the specified XML file exists in the given folder
        query = f"name = 'result.xml' and '{folder_id}' in parents"
        response = service.files().list(q=query).execute()

        files = response.get('files', [])
        
        if files:
            # File exists, get the existing content and append new content
            file_id = files[0].get('id')
            request = service.files().get_media(fileId=file_id)
            file_io = BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
            file_io.seek(0)

            existing_xml_content = file_io.read().decode('utf-8')
            merged_content = existing_xml_content + '\n' + xml_content
        else:
            # File does not exist, create a new one with given content
            file_metadata = {
                'name': 'result.xml',
                'parents': [folder_id],
                'mimeType': 'application/xml'
            }
            file = service.files().create(body=file_metadata, fields='id').execute()
            file_id = file.get('id')
            merged_content = xml_content

        # Convert merged content into bytes for uploading
        merged_content_bytes = merged_content.encode('utf-8')
        media_body = MediaIoBaseUpload(BytesIO(merged_content_bytes), mimetype='application/xml')

        # Update the file with the new content or create a new one
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media_body
        ).execute()

        log_message(f"Recorded content to XML file for {resume_file_name}")

    except Exception as e:
        log_message(f'An error occurred: {e}')
              
def save_to_txt(service, content, resume_file_name, folder_id):
    try:
        # Query if "output.txt" is present in the specified folder
        query = f"name = 'output.txt' and '{folder_id}' in parents"
        response = service.files().list(q=query).execute()

        timestamp = datetime.datetime.now().isoformat()
        #content_with_metadata = f"\n******* File: {resume_file_name}, Timestamp: {timestamp}\n{content}\n"
        content_with_metadata = content + "\n"

        # Get the files from the response
        files = response.get('files', [])
        
        if files:
            # If file exists, get the existing content and append new content
            file_id = files[0].get('id')
            request = service.files().get_media(fileId=file_id)
            file_io = BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
            file_io.seek(0)

            existing_txt_content = file_io.read().decode('utf-8')
            merged_content = existing_txt_content + content_with_metadata
        else:
            # If file does not exist, create a new one
            file_metadata = {
                'name': 'output.txt',
                'parents': [folder_id],
                'mimeType': 'text/plain'
            }
            file = service.files().create(body=file_metadata, fields='id').execute()
            file_id = file.get('id')
            merged_content = content_with_metadata

        # Convert merged content into bytes
        merged_content_bytes = merged_content.encode('utf-8')
        media_body = MediaIoBaseUpload(BytesIO(merged_content_bytes), mimetype='text/plain')

        # Update the file with the new content
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media_body
        ).execute()

        log_message(f"Recorded content to text file for {resume_file_name}")

    except Exception as e:
        log_message(f'An error occurred: {e}')
        
def save_to_csv(service, file_name, candidate_name, folder_id):
    try:
        query = f"name = 'review.csv' and '{folder_id}' in parents"
        response = service.files().list(q=query).execute()
        
        timestamp = datetime.datetime.now().isoformat()
        metadata=f"{file_name}, {candidate_name}, {timestamp}\n"
        
        files = response.get('files', [])
        if files:
            file_id = files[0].get('id')
            request = service.files().get_media(fileId=file_id)
            file_io = BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            file_io.seek(0)
            
            existing_csv_content = file_io.read().decode('utf-8')
            merged_content = existing_csv_content + metadata
            
        else:
            file_metadata = {
                'name': 'review.csv',
                'parents': [folder_id],
                'mimeType': 'text/csv'
            }    
            file = service.files().create(body=file_metadata, fields='id').execute()
            file_id = file.get('id')
            merged_content = metadata
            
        merged_content_bytes = merged_content.encode('utf-8')
        media_body = MediaIoBaseUpload(BytesIO(merged_content_bytes), mimetype='text/csv')
        
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media_body
        ).execute()
        
        log_message(f"Recorded metadata to review file for {candidate_name}'s resume")

    except Exception as e:
        log_message(f'An error occurred: {e}')
                         
def upload_file(file_path, folder_id):
    service = authenticate()
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
        log_message(f"Uploaded file with id: {file.get('id')}")
    except Exception as e:
        log_message(f"An error occurred: {e}")

def download_file(file_id, file_name):
    service = authenticate()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()

    downloader = MediaIoBaseDownload(fh, request)

    try:
        done = False
        while not done:
            status, done = downloader.next_chunk()
            log_message(f"Download {int(status.progress() * 100)}%.")

        fh.seek(0)

        with open(file_name, 'wb') as f:
            f.write(fh.read())

        log_message(f"{file_name} has been downloaded successfully.")
        
    except Exception as e:
        log_message(f"An error occurred during the download: {e}")

def download_files_in_folder(service, folder_id, download_folder):
    results = service.files().list(q=f"'{folder_id}' in parents").execute()
    items = results.get('files', [])

    if not items:
        log_message("No files found.")
    else:
        for item in items:
            file_id = item['id']
            file_name = item['name']
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()

            # Download the file
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            # Write the content to local file
            filepath = os.path.join(download_folder, file_name)
            with open(filepath, 'wb') as f:
                fh.seek(0)
                f.write(fh.read())

            log_message(f"Downloaded '{file_name}' to '{download_folder}'")

def clear_files_in_folder(service, folder_id):
    results = service.files().list(q=f"'{folder_id}' in parents").execute()
    items = results.get('files', [])

    if not items:
        log_message("No files found.")
    else:
        for item in items:
            file_id = item['id']
            service.files().delete(fileId=file_id).execute()
            log_message(f"File with id: {file_id} has been deleted.")
                      
def delete_file(file_id):
    service = authenticate()
    try:
        service.files().delete(fileId=file_id).execute()
        log_message(f"File with id {file_id} was deleted successfully.")
    except Exception as e:
        log_message(f"An error occurred: {e}")
        
# Update a custom property or move the file to a different folder
def move_file_to_reviewed_folder(service, file_id, processed_folder_id):
    # Move the file to the "processed" folder
    file = service.files().get(fileId=file_id,
                               fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    # Move the file to the new folder
    file = service.files().update(fileId=file_id,
                                  addParents=processed_folder_id,
                                  removeParents=previous_parents,
                                  fields='id, parents').execute()
