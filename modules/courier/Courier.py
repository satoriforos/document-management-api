import sendgrid
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import Content
import json
import requests


class Courier:

    settings = None

    def __init__(self, settings):
        self.settings = settings

    def send_template_email(
        self,
        to_email,
        from_email,
        subject,
        template_id,
        substitutions
    ):
        # https://sendgrid.com/docs/API_Reference/SMTP_API/how_to_use_a_transactional_template_with_smtp.html
        # https://sendgrid.com/docs/ui/sending-email/how-to-send-an-email-with-dynamic-transactional-templates/
        # https://sendgrid.com/docs/API_Reference/api_v3.html
        #subs = {}
        #for key, value in substitutions.items():
        #    subs[":{}".format(key)] = [value]

        personalizations = {
            "from":{
                "email": "noreply@fromdatawithlove.com",
                "name": "FromDataWithLove"
            },
            "personalizations": [{
                "to": [{"email": to_email}],
                "dynamic_template_data": substitutions
            }],
            "template_id": template_id
        }

        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            'Authorization': "Bearer {}".format(self.settings["key"]),
            'Content-Type': "application/json"
        }
        response = requests.post(url, json=personalizations, headers=headers)
        return response

    def send_email(self, to_email, from_email, subject, message):
        sg = sendgrid.SendGridAPIClient(apikey=self.settings["key"])
        # msg_from = Email(from_email)
        # msg_to = Email(to_email)
        content = Content("text/plain", message)
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        # response.status_code == 202 is good
        return response
