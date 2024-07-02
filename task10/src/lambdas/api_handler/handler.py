import os

from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda
import json
import re
import boto3
import os

_LOG = get_logger('ApiHandler-handler')


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass

    @staticmethod
    def get_user_pool_id(client, user_pool_name: str) -> str:
        user_pools = client.list_user_pools(MaxResults=60)
        for user_pool in user_pools:
            if user_pool["Name"] == user_pool_name:
                return user_pool["Id"]

    def signup(self, data: dict):

        client = boto3.client('cognito-idp')
        user_pool_name = os.environ.get("USER_POOL")
        _LOG.info(f"Looking for user pool id for: {user_pool_name}")
        user_pool_id = client.get_user_pool_id(client, user_pool_name)
        _LOG.info(f"User pool id: {user_pool_id}")

        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        email = data.get("email", "")
        password = data.get("password", "")

        resp = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    "Name": "firstName",
                    "Value": first_name
                },
                {
                    "Name": "lastName",
                    "Value": last_name
                }
            ],
            TemporaryPassword=password
        )

        _LOG.info(f"User create response: {resp}")
        resp = client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )

        _LOG.info(f'set_user_password permanent response: {resp}')
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
                ...
            elif path == "/tables":
                if method == "GET":
                    ...
                elif method == "POST":
                    ...
            elif path == "reservations":
                if method == "GET":
                    ...
                elif method == "POST":
                    ...

        return 200


HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
