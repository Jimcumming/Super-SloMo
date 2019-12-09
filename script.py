import boto3
import os
import numpy as np
import os
import subprocess
from botocore.exceptions import ClientError

def getFramerate(video):
    con = 'ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=noprint_wrappers=1:nokey=1 "' + video + '"'
    proc = subprocess.Popen(con, stdout=subprocess.PIPE, shell=True)
    framerateString = str(proc.stdout.read())[2:-3]
    a = int(framerateString.split('/')[int(0)])
    b = int(framerateString.split('/')[int(1)])
    return int(np.round(np.divide(a,b)))

def processVideo(args):
    con = 'python video_to_slomo.py --ffmpeg ' + args["ffmpeg"] + ' --video ' + args["video"] + ' --sf ' + args["sf"] + \
          ' --checkpoint ' + args["checkpoint"] + ' --fps ' + args["fps"]  + ' --output ' + args["output"]
    print(con)
    proc = subprocess.Popen(con, stdout=subprocess.PIPE, shell=True)
    print(proc.stdout.read())

def create_presigned_url(bucket_name, object_name, expiration=3600):
    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'), region_name='eu-west-2')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def sendEmail(email, downloadbucket, video):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "Slomotatron <slomo@jcws.co.uk>"
    
    download_link = create_presigned_url(downloadbucket, video)

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = email

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "eu-west-1"

    # The subject line for the email.
    SUBJECT = "Your super slomo video"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Slomotatron has processed your video\r\n" +
                "donwload your video from the link below\r\n" + download_link
                )
                
    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Slomotatron</h1>
    <p>Slomotatron has processed your video, download it using the following link
        <a href='"""+ download_link +"""'>"""+ video[video.rfind("/")+1:] + """</a></p>
    </body>
    </html>
    """
    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


# Create SQS client
sqs = boto3.client('sqs', region_name='eu-west-2')
s3 = boto3.client('s3', region_name='eu-west-2')


queue_url = 'https://sqs.eu-west-2.amazonaws.com/839229338431/dev-slomo.fifo'
s3attachmentsBucket = 'slomo-app-api-dev-uploadsbucket-ko2jzrics82r'
s3downloadBucket = 'slomo-app-api-dev-downloadsbucket-t4wypnf2t36r'
videoInputFolder = os.path.join('..', 'input')


while 1:
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
        VisibilityTimeout=3600,
        WaitTimeSeconds=10
    )

    if 'Messages' in response:
        message = response['Messages'][0]
        messageAttrbibutes = message['MessageAttributes']
        uploadAttachment = messageAttrbibutes['uploadAttachment']['StringValue']
        savePath = os.path.join(videoInputFolder, uploadAttachment)
        userId = messageAttrbibutes['userId']['StringValue']
        email = messageAttrbibutes['email']['StringValue']
        slomoFactor = messageAttrbibutes['slomoFactor']['StringValue']
        receipt_handle = message['ReceiptHandle']
        #download attachment
        attachmentPath = "private/" + userId + "/" + uploadAttachment
        s3.download_file(s3attachmentsBucket, attachmentPath, savePath)
        #get fps of file using ffmpeg
    
        framerate = getFramerate(savePath)
        #process file to slow motion
        outputFile = os.path.join("..", "output", uploadAttachment)
        args = {
            "ffmpeg": "/usr/bin",
            "video": '"' + savePath + '"',
            "sf": str(slomoFactor),
            "checkpoint": "../checkpoints/default.ckpt",
            "fps": str(framerate),
            "output": '"' + outputFile + '"',
        }

        result = processVideo(args)

        #copy file to download folder
        s3.upload_file(outputFile, s3downloadBucket, attachmentPath)
        #generate email to client
        sendEmail(email, s3downloadBucket, attachmentPath)

        # Delete received message from queue
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print('Received and deleted message: %s' % message)
    else:
        print('no messages')
