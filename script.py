import boto3
import os
import numpy as np
import os
import subprocess
#import video_to_slomo


def getFramerate(video):
    con = 'ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=noprint_wrappers=1:nokey=1 "' + video + '"'
    proc = subprocess.Popen(con, stdout=subprocess.PIPE, shell=True)
    framerateString = str(proc.stdout.read())[2:-5]
    a = int(framerateString.split('/')[0])
    b = int(framerateString.split('/')[1])
    return int(np.round(np.divide(a,b)))

# Create SQS client
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

queue_url = 'https://sqs.eu-west-2.amazonaws.com/839229338431/dev-slomo.fifo'
s3attachmentsBucket = 'slomo-app-api-dev-attachmentsbucket-kq6u576cwyz3'
videoInputFolder = '../input/'

# Receive message from SQS queue
response = sqs.receive_message(
    QueueUrl=queue_url,
    AttributeNames=[
        'SentTimestamp'
    ],
    MaxNumberOfMessages=1,
    MessageAttributeNames=[
        'All'
    ],
    VisibilityTimeout=10,
    WaitTimeSeconds=10
)

if 'Messages' in response:
    message = response['Messages'][0]
    messageAttrbibutes = message['MessageAttributes']
    uploadAttachment = messageAttrbibutes['uploadAttachment']['StringValue']
    savePath = os.path.join(videoInputFolder, uploadAttachment)
    userId = messageAttrbibutes['userId']['StringValue']
    receipt_handle = message['ReceiptHandle']
    #download attachment
    attachmentPath = "private/" + userId + "/" + uploadAttachment
    s3.download_file(s3attachmentsBucket, attachmentPath, savePath)
    #get fps of file using ffmpeg
    framerate = getFramerate(savePath)
    #process file to slow motion

    #copy file to download folder

    #generate email to client
    

    # Delete received message from queue
    # sqs.delete_message(
    #     QueueUrl=queue_url,
    #     ReceiptHandle=receipt_handle
    # )
    # print('Received and deleted message: %s' % message)
else:
    print('no messages')
