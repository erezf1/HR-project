import datetime
import google_drive_integration as gdi
import document_processing as dp
import openai_integration as openai
import data_storage_reporting_gdrive as dsr
import error_handling_notifications as ehn

# Configuration parameters (to be replaced with actual values)
GOOGLE_DRIVE_FOLDER_ID = "1_1PHDeB2pKSed28hFzP726wC9s38ggHg"
OPENAI_API_KEY = "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"
CSV_STORAGE_PATH = "csv_storage.csv"
EMAIL_RECIPIENTS = ["erez@mvp-house.com"]  # Notification recipients

LOG_FILE_PATH = './log.txt'  # Define the path for the log file

def log_message(message, log_file_path=LOG_FILE_PATH):
    with open(log_file_path, 'a') as log_file:  # Open the log file in append mode
        log_file.write(f"{message}\n")  # Add the message to the log file
    print(message)

def main():
    try:
        # Authenticate with Google Drive and OpenAI API
        service = gdi.authenticate()
        openai.initialize_api(OPENAI_API_KEY)
        
        # Find 'New Resumes' folder within the folder
        folders = gdi.list_files(GOOGLE_DRIVE_FOLDER_ID)
        
        # Find if 'New Resumes' folder exists and get its ID
        new_resumes_folder_id = None
        new_resume_list = [] 
        for folder in folders:
            if folder.get('name') == 'New Resumes':
                new_resumes_folder_id = folder.get('id')
        
        if new_resumes_folder_id is None:
            log_message("New Resumes folder does not exist.")
            return
        
        gdi.clear_files_in_folder(service, new_resumes_folder_id)
        gdi.upload_file('./Resume/Resume2.pdf', new_resumes_folder_id)
        
        # List files in "New Resumes" folder
        new_resumes = gdi.list_files(new_resumes_folder_id)
        
        # Find or create 'Review Results' folder
        review_results_folder_id = gdi.find_or_create_folder(service, 'Review Results', GOOGLE_DRIVE_FOLDER_ID)
        # Find or create 'Reviewed Resumes' folder
        reviewed_resumes_folder_id = gdi.find_or_create_folder(service, 'Reviewed Resumes', GOOGLE_DRIVE_FOLDER_ID)

        # Read the prompt from a text file within the folder
        with open('./utils/prompt.txt', 'r', encoding='utf-8') as file:
            prompt = file.read()

        # Process each resume in "New Resumes" folder
        for resume in new_resumes:
            file_name = resume['name']
            file_extension = file_name.split(".")[-1].lower()  # Get the file extension in lowercase
            if file_extension in ["pdf", "doc", "docx"]:                
                # Download the resume file
                local_file_path = f"./downloads/{file_name}"
                gdi.download_file(resume['id'], local_file_path)
                
                # Extract and normalize text from the resume
                extracted_text = dp.extract_text(local_file_path)
                normalized_text = dp.normalize_text(extracted_text)                
                
                timestamp = datetime.datetime.now().isoformat()
                
                # Combine the prompt and normalized text
                combined_string = prompt + "\n" + normalized_text + f"Current data and time is {timestamp}"                 
                additional_prompt = "Extract only name of candiate from following resume data.\n"
                
                # Send analysis request to OpenAI and parse the response
                analysis_response = openai.send_analysis_request(combined_string)
                candiate_name = openai.send_analysis_request(additional_prompt + normalized_text)
                
                # Save extracted data in different formats to 'Review Results'
                gdi.save_to_xml(service, analysis_response, resume['name'], review_results_folder_id)
                gdi.save_to_txt(service, analysis_response, resume['name'], review_results_folder_id)
                gdi.save_to_csv(service, resume['name'], candiate_name, review_results_folder_id)                 
                
                # Move reviewed file to 'Reviewed Resumes' folder in Google Drive
                gdi.move_file_to_reviewed_folder(service, resume['id'], reviewed_resumes_folder_id)

            else:
                log_message(f"Ignoring file '{file_name}' as it is not a compatible file type.")
            new_resume_list.append(file_name)
        
        # After processing all resumes, write the list of processed resumes to the log file    
        log_message("Processed the following new resumes:")
        log_message("\n".join(new_resume_list))
        
        # Downloads files in reviewed result folder to local
        gdi.download_files_in_folder(service, review_results_folder_id, './Review Results')
    except Exception as e:
        # Log the error and notify administrators
        ehn.log_error({'message': str(e)})
        ehn.notify_administrators(EMAIL_RECIPIENTS, str(e))

if __name__ == "__main__":
    main()