#This file contains examples for the most common tasks involving ETL on Google Cloud storage and Big Query using Python
#Check the BigQuery Python Setup Steps.txt for setup steps

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from bigquery import get_client

from googleapiclient import http
from bigquery.errors import BigQueryTimeoutException
from bigquery import JOB_SOURCE_FORMAT_CSV

credentials = GoogleCredentials.get_application_default()

project_id = 'YOUR PROJECTID'
dataset = 'YOUR DATASET'
service = discovery.build('storage', 'v1', credentials=credentials)
client = get_client(project_id, credentials=credentials)


#Step 1: Upload local file to google cloud storage (GCS)
filename = 'YOUR FILE PATH'
bucket = 'YOUR GCS Bucket' #Note: This should not contain gs:// part

destination_file_path='Destination file path inside the bucket'
body = {'name': destination_file_path}
req = service.objects().insert(bucket=bucket, body=body, media_body=filename)
resp = req.execute()


#Step 2: Load file in GCS to a table in big query

#Drop table if exists
table_name = 'YOUR_TABLE_NAME'
if(client.check_table(dataset, table_name)):
    client.delete_table(dataset, table_name)

gs_file_path = 'gs://' + bucket + '/' + destination_file_path

schema = [
    {'name': 'Col1', 'type': 'STRING'},
    {'name': 'Col2', 'type': 'STRING'},
	..
    {'name': 'Coln', 'type': 'INTEGER'},
]

job = client.import_data_from_uris(gs_file_path, dataset, table_name, schema, 
                                   source_format=JOB_SOURCE_FORMAT_CSV, field_delimiter='\t')

job_resource = client.wait_for_job(job, timeout=60)


#Step 3 : Write results of a query to a new table

#Drop table if exists
tmp_table_name='TMP_TABLE_NAME'
if(client.check_table(dataset, tmp_table_name)):
    client.delete_table(dataset, tmp_table_name)
    
querystr = querystr = 'SELECT col1, col2, .., coln FROM ' + dataset + '.' + table_name 

job = client.write_to_table(querystr, dataset, tmp_table_name)

try:
    job_resource = client.wait_for_job(job, timeout=60)
except BigQueryTimeoutException:
    quit()


#Step 4: Export table in big query to google cloud storage. Here we are exporting the new table created above

destination_file_path_new = 'Destination file path inside the bucket.' #Give a new name so the existing file isn't updated

gs_filepath_new = 'gs://' + bucket + '/' + destination_file_path_new

job = client.export_data_to_uris(gs_filepath_new, dataset, tmp_table_name)

try:
    job_resource = client.wait_for_job(job, timeout=60)
except BigQueryTimeoutException:
    quit()


#Step 5: Export the above exported file in GCS to local directory
src_filename = destination_file_path_new
dest_local_filepath = 'YOUR LOCAL FILEPATH TO EXPORT FILE'
dest_fh = open(dest_local_filepath, 'w+')

req = service.objects().get_media(bucket=bucket, object=src_filename)
downloader = http.MediaIoBaseDownload(dest_fh, req)

try:
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download {}%.".format(int(status.progress() * 100)))
    dest_fh.close()
except IOError:
    print 'IOException'