import base64
import boto3
from botocore.exceptions import ClientError
from decouple import config
import logging
import json

logger = logging.getLogger("aws-helpers")

if config("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=config("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"),
    )
else:
    s3 = boto3.client("s3")


def get_bucket(test):
    return "badger-staging-merkle-proofs" if test else "badger-merkle-proofs"


def get_secret(
    secret_name: str,
    secret_key: str,
    region_name: str = "us-west-1",
    assume_role_arn: str = None,
    test: bool = False,
) -> str:
    """Retrieves secret from AWS secretsmanager.
    Args:
        secret_name (str): secret name in secretsmanager
        secret_key (str): Dict key value to use to access secret value
        region_name (str, optional): AWS region name for secret. Defaults to "us-west-1".
    Raises:
        e: DecryptionFailureException - Secrets Manager can't decrypt the protected secret text using the provided KMS key.
        e: InternalServiceErrorException - An error occurred on the server side.
        e: InvalidParameterException - You provided an invalid value for a parameter.
        e: InvalidRequestException - You provided a parameter value that is not valid for the current state of the resource.
        e: ResourceNotFoundException - We can't find the resource that you asked for.
    Returns:
        str: secret value
    """
    if test:
        return config(secret_key, "")

    # Create a Secrets Manager client
    if assume_role_arn:
        credentials = get_assume_role_credentials(assume_role_arn)
        # Use the temporary credentials that AssumeRole returns to create session
        session = boto3.session.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
        )
        client = session.client(
            service_name="secretsmanager",
            region_name=region_name,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
        )
    else:
        session = boto3.session.Session()
        client = session.client(
            service_name="secretsmanager",
            region_name=region_name,
        )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        logger.info("get secret value response no error")
    except ClientError as e:
        logger.error(f"get secret value response error: {e}")
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if "SecretString" in get_secret_value_response:
            return json.loads(get_secret_value_response["SecretString"]).get(secret_key)
        else:
            return base64.b64decode(get_secret_value_response["SecretBinary"]).get(
                secret_key
            )

    return None


def get_assume_role_credentials(assume_role_arn: str):
    sts_client = boto3.client("sts")

    # Call the assume_role method of the STSConnection object and pass the role
    # ARN and a role session name.
    assumed_role_object = sts_client.assume_role(
        RoleArn=assume_role_arn, RoleSessionName="AssumeRoleSession1"
    )
    logger.info(f"assumed role: {assumed_role_object}")

    # From the response that contains the assumed role, get the temporary
    # credentials that can be used to make subsequent API calls
    credentials = assumed_role_object["Credentials"]

    return credentials
