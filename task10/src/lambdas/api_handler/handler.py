import os

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
import re
import boto3
import os
import re

_LOG = get_logger('ApiHandler-handler')


def get_user_pool_id(client, user_pool_name: str) -> str:
    user_pools = client.list_user_pools(MaxResults=60)
    for user_pool in user_pools["UserPools"]:
        _LOG.info(f"User pool: {user_pool}")
        if user_pool["Name"] == user_pool_name:
            return user_pool["Id"]


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass

    def validate_email(self, email):
        pattern = r'^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$'
        return re.match(pattern, email)

    def signup(self, data: dict):

        client = boto3.client('cognito-idp')
        user_pool_name = os.environ.get("USER_POOL")
        _LOG.info(f"Looking for user pool id for: {user_pool_name}")

        user_pool_id = get_user_pool_id(client, user_pool_name)
        _LOG.info(f"User pool id: {user_pool_id}")

        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        email = data.get("email", "")
        password = data.get("password", "")

        try:
            resp = client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
                    {
                        "Name": "given_name",
                        "Value": first_name
                    },
                    {
                        "Name": "family_name",
                        "Value": last_name
                    }
                ],
                TemporaryPassword=password
            )
            _LOG.info(f"User create response: {resp}")
        except Exception as e:
            _LOG.error(f"Exception during create user: {e}")
            return {
                "statusCode": 400
            }

        try:
            resp = client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=password,
                Permanent=True
            )
            _LOG.info(f'set_user_password permanent response: {resp}')
        except Exception as e:
            _LOG.error(f"Exception during setting password: {e}")
            return {
                "statusCode": 400
            }
        return {
            "statusCode": 200
        }

    def signin(self):
        ...


    def tables(self):
        ...


    def reservations(self):
        ...


    def handle_request(self, event, context):
        """
        Explain incoming event here
        """

        path = event.get("path", None)
        method = event.get("methodHttp", "")
        _LOG.info(f"Event: {event}")
        _LOG.info(f"Context: {context}")
        body = json.loads(event['body'])
        if path:
            if path == "/signup":
                return self.signup(body)
            elif path == "/signin":
                pass
            elif path == "/tables":
                if method == "GET":
                    pass
                elif method == "POST":
                    pass
            elif path == "reservations":
                if method == "GET":
                    pass
                elif method == "POST":
                    pass

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
