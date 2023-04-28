import requests
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import datetime as dt
import io



def get_secret():
    secret_name = 'apiKey'
    region_name = 'ap-southeast-2'

    #create a secret manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',region_name=region_name)

    try:
        get_secret_value_response  = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    secret = secret.split(':')[1].replace('}','')
    
    return secret.replace('"','')
    
 
def file_exists(bucketName,path):
    s3_client = boto3.client('s3')
    result = s3_client.list_objects_v2(Bucket=bucketName, Prefix=path)
    if 'Contents' in result:
        return True
    else:
        return False
    

def ingest(x,y):
    
    bucket_name = 'staging-bucket-foundary'
    today = dt.date.today()
    year = today.year
    month = today.month
    day=today.day
    file_name = f'weather/{year}/{month}/{day}/data.csv'
    url = "https://weatherapi-com.p.rapidapi.com/current.json"

    querystring = {"q":"-37.82,144.97"}

    headers = {
        "content-type": "application/octet-stream",
        "X-RapidAPI-Key": get_secret(),
        "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    data = pd.json_normalize(response.json())
    #print(data)
    
    
    #create s3 client
    s3 = boto3.client("s3")

    
    #check if the file exists and append new data if the file already exists
    if file_exists(bucket_name,file_name)==True:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        csv_bytes = response['Body'].read()
        dfOld = pd.read_csv(io.BytesIO(csv_bytes))
        data = pd.concat([dfOld,data],axis=0)
    else:
        print('File dosent exists hence creating a new one')
    
    
    csv_buffer = data.to_csv(index=False)

    
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=csv_buffer)


   