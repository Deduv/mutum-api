import boto3
import logging
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_content: str) -> None:
    """
    Sends an HTML email using AWS SES.
    If SES is not configured (e.g. locally or in testing), falls back to logging the email to stdout.
    """
    if not settings.EMAILS_FROM_EMAIL:
        logger.warning(
            f"[EMAIL MOCK] Missing EMAILS_FROM_EMAIL configuration. Email details:\n"
            f"  To: {to_email}\n"
            f"  Subject: {subject}\n"
            f"  Body: {html_content}\n"
        )
        return

    # Use explicit credentials if configured, otherwise fall back to environment/IAM role settings
    aws_kwargs = {}
    if settings.AWS_ACCESS_KEY_ID:
        aws_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
    if settings.AWS_SECRET_ACCESS_KEY:
        aws_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    if settings.AWS_REGION:
        aws_kwargs["region_name"] = settings.AWS_REGION

    # If no credentials configured, we also fall back to MOCK unless it's production
    # In test/dev settings, write to logs if no keys are defined.
    # Note: AWS CLI/boto3 might still search default credentials.
    # We will log a trace if we don't have explicit credentials.
    if not settings.AWS_ACCESS_KEY_ID and not settings.AWS_SECRET_ACCESS_KEY:
        logger.info(
            f"[EMAIL MOCK] No AWS credentials configured. Email details:\n"
            f"  From: {settings.EMAILS_FROM_EMAIL}\n"
            f"  To: {to_email}\n"
            f"  Subject: {subject}\n"
            f"  Body: {html_content}\n"
        )
        return

    try:
        client = boto3.client("ses", **aws_kwargs)
        response = client.send_email(
            Source=settings.EMAILS_FROM_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Html": {"Data": html_content, "Charset": "UTF-8"}},
            },
        )
        logger.info(f"Email sent successfully via AWS SES to {to_email}. MessageId: {response.get('MessageId')}")
    except ClientError as e:
        logger.error(f"AWS SES ClientError sending email to {to_email}: {e.response['Error']['Message']}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error sending email via AWS SES to {to_email}: {e}")
        raise e
