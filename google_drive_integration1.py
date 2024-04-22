
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
import io
from io import BytesIO
import dicttoxml
import datetime

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
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    return items


def save_to_xml(service, analysis_response, xml_file_id):
    try:
        # Convert the combined data to XML
        xml_content = dicttoxml.dicttoxml(analysis_response)

        # Read the existing content of the XML file from Google Drive
        existing_xml_content = service.files().get_media(fileId=xml_file_id).execute()

        # Merge the new XML content with the existing one if there is any
        if existing_xml_content:
            merged_content = existing_xml_content + b'\n' + xml_content
        else:
            merged_content = xml_content

        # Upload the merged XML content back to the Google Drive file
        media_body = MediaIoBaseUpload(BytesIO(merged_content), mimetype='application/xml')
        updated_file = service.files().update(
            fileId=xml_file_id,
            media_body=media_body
        ).execute()

        print(f'Updated File ID: {updated_file.get("id")}')

    except Exception as e:
        print(f'An error occurred: {e}')
        
def save_to_txt(service, content, file_name, txt_file_id):
    try:
        # Add filename and timestamp to the content
        content_with_metadata = f"******* File: {file_name}, Timestamp: {datetime.datetime.now()}\n{content}"

        # Read the existing content of the text file from Google Drive
        existing_txt_content = service.files().get_media(fileId=txt_file_id).execute()

        # Merge the new text content with the existing one if there is any
        if existing_txt_content:
            merged_content = existing_txt_content + b'\n\n' + content_with_metadata.encode('utf-8')
        else:
            merged_content = content_with_metadata.encode('utf-8')

        # Upload the merged text content back to the Google Drive file
        media_body = MediaIoBaseUpload(BytesIO(merged_content), mimetype='text/plain')
        updated_file = service.files().update(
            fileId=txt_file_id,
            media_body=media_body
        ).execute()

        print(f'Updated File ID: {updated_file.get("id")}')

    except Exception as e:
        print(f'An error occurred: {e}')
                 
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
        print(f"Uploaded file with id: {file.get('id')}")
    except Exception as e:
        print(f"An error occurred: {e}")

def download_file(file_id, file_name):
    service = authenticate()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()

    # Create a downloader object to fetch the data
    downloader = MediaIoBaseDownload(fh, request)

    try:
        # Download the data in chunks
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        # Flush and prepare the stream for reading
        fh.seek(0)

        # Write the content of the BytesIO stream to the file
        with open(file_name, 'wb') as f:
            f.write(fh.read())
            # Ensure all internal buffers associated with the file are written to disk
            f.flush()
        os.fsync(f.fileno())

        print(f"{file_name} has been downloaded successfully.")
    except Exception as e:
        print(f"An error occurred during the download: {e}")

def delete_file(file_id):
    service = authenticate()
    try:
        service.files().delete(fileId=file_id).execute()
        print(f"File with id {file_id} was deleted successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
# Update a custom property or move the file to a different folder
def mark_file_as_processed(file_id, processed_folder_id):
    service = authenticate()
    # Move the file to the "processed" folder
    file = service.files().get(fileId=file_id,
                               fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    # Move the file to the new folder
    file = service.files().update(fileId=file_id,
                                  addParents=processed_folder_id,
                                  removeParents=previous_parents,
                                  fields='id, parents').execute()
