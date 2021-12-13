import boto3
import base64

from flask import Blueprint, request, abort, jsonify

from config import Config

blueprint = Blueprint('views', __name__)

# Initialize AWS Clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

@blueprint.route('/')
def hello_world():
    return {
        'message': 'App is working'
    }

@blueprint.route('/upload', methods=['POST'])
def parse_rekognition():
    """
        Validate HTTP Request
    """
    def validate(request) -> bool:
        if 'image' not in request:
            return False
        if 'name' not in request:
            return False
        return True

    """
        Upload to S3 Bucket Function
        @child
            -> _has_s3_bucket()
    """
    def upload_to_s3(file_name: str) -> bool:
        """
            Checks if S3 Bucket Exists in env
        """
        def _has_s3_bucket() -> bool:
            return Config.S3_BUCKET is not False

        if _has_s3_bucket():
            try:
                s3.upload_file(
                    '/tmp/' + file_name,
                    Config.S3_BUCKET,
                    file_name
                )
                return True;
            except:
                return False
        else:
            return False

    if not request.json:
        abort(400, "Request has to be in JSON Format.")
    if not validate(request.json):
        abort(400, "One or more fields not satisfied.")

    file_name = request.json['name']
    image = request.json['image']

    # 1. Write to file
    with open('/tmp/' + file_name, 'wb') as new_image:
        new_image.write(
            base64.b64decode(
                str(image).replace("data:image/jpeg;base64,", "")
            )
        )

    # 2. Upload to Amazon S3
    if not upload_to_s3(file_name):
        abort(500, "Unable to upload to S3.")
    
    # 3. Perform Rekognition
    rekognition_response = rekognition.detect_faces(
        Image={
            'S3Object': {
                'Bucket': Config.S3_BUCKET,
                'Name': file_name
            }
        },
        Attributes=[
            "ALL",
            "DEFAULT"
        ]
    )

    # 5. Delete from S3 Bucket
    s3.delete_object(
        Bucket=Config.S3_BUCKET,
        Key=file_name
    )

    # 4. Return response. Pluck 'FaceDetails'.
    return jsonify(
        rekognition_response['FaceDetails']
    ), 201
