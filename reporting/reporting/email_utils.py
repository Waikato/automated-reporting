from . import settings
from django.core.mail import send_mail
import traceback
import logging

logger = logging.getLogger(__name__)


def send_email(to, subject, body):
    """
    Sends an email.

    :param to: the email recipient
    :type to: str
    :param subject: the email subject
    :type subject: str
    :param body: the email message
    :type body: str
    :return: None if successful otherwise error message
    :rtype: str
    """

    try:
        send_mail(
            subject,
            body,
            settings.ADMIN_EMAIL,
            [to],
            fail_silently=False,
        )
    except Exception as ex:
        msg = traceback.format_exc()
        logger.error(msg=msg)
        return msg

    return None
