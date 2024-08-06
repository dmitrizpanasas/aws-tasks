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
        # _LOG.info(f"User pool: {user_pool}")
        if user_pool["Name"] == user_pool_name:
            return user_pool["Id"]


class ApiHandler(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass

    def validate_email(self, email):
        pattern = r'^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$'
        return re.match(pattern, email)

    def signup(self, data: dict):

        _LOG.info(f"Sign up with data: {data}")
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

    def signin(self, data: dict):
        _LOG.info(f"Signing in: {data}")
        client = boto3.client('cognito-idp')
        user_pool_name = os.environ.get("USER_POOL")
        _LOG.info(f"Looking for user pool id for (pool name): {user_pool_name}")

        user_pool_id = get_user_pool_id(client, user_pool_name)
        _LOG.info(f"User pool id: {user_pool_id}")

        email = data.get("email", "")
        password = data.get("password", "")

        response = client.list_user_pool_clients(
            UserPoolId=user_pool_id
        )
        _LOG.info(f"List user pool clients: {response}")

        client_id = None
        for user_pool_item in response["UserPoolClients"]:
            if user_pool_item["ClientName"] == "clientapp":
                client_id = user_pool_item['ClientId']
                _LOG.info(f"Found client id {client_id}")
                break
        if not client_id:
            _LOG.info("Client id is not found")
            return {
                "statusCode": 400
            }
        try:
            response = client.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )

            _LOG.info(f"Client initiate_auth response: {response}")
            return {
                'statusCode': 200,
                'body': json.dumps({'accessToken': response['AuthenticationResult']['IdToken']})
            }

        except Exception as e:
            _LOG.error(f"Exception during initiate_auth: {e}")
            return {
                "statusCode": 400
            }

    def post_tables(self, data: dict):
        _LOG.info('POST tables')
        db = boto3.resource('dynamodb')
        table_name = os.environ['TABLES_TABLE']
        _LOG.info(f'POST tables: {table_name}')
        table = db.Table(table_name)

        try:
            item = {
                "id": data["id"],
                "number": data["number"],
                "places": data["places"],
                "isVip": data["isVip"],
                "minOrder": data["minOrder"]
            }
            table.put_item(Item=item)
            return {
                'statusCode': 200,
                'body': json.dumps({'id': item['id']})
            }
        except Exception as e:
            _LOG.error(f"Exception during post_tables: {e}")
            return {
                'statusCode': 400
            }

    def get_table_by_id(self, table_id: int):
        _LOG.info(f'GET table by id: {table_id}')
        db = boto3.resource('dynamodb')
        table_name = os.environ['TABLES_TABLE']
        table = db.Table(table_name)

        try:
            item = table.get_item(Key={'id': table_id})
            return {
                'statusCode': 200,
                'body': json.dumps({"id": int(item["id"]),
                    "number": int(item["number"]),
                    "places": int(item["places"]),
                    "isVip": item["isVip"],
                    "minOrder": int(item["minOrder"])})
            }
        except Exception as e:
            return {
                'statusCode': 400
            }

    def get_tables(self):
        _LOG.info('GET tables')

        db = boto3.resource('dynamodb')
        table_name = os.environ['TABLES_TABLE']
        _LOG.info(f'GET tables. table name: {table_name}')
        table = db.Table(table_name)
        try:
            result = []
            response = table.scan()
            _LOG.info(f"Item from Tables: {response}")
            for item in response["Items"]:
                result.append({
                    "id": int(item["id"]),
                    "number": int(item["number"]),
                    "places": int(item["places"]),
                    "isVip": item["isVip"],
                    "minOrder": int(item["minOrder"])
                })
            _LOG.info(f"List tables: {result}")
            return {
                'statusCode': 200,
                'body': {"tables": result}
            }
        except Exception as e:
            _LOG.error(f"Error while getting tables: {e}")
            return {
                "statusCode": 400
            }

    def post_reservation(self, data: dict):
        pass

    def get_reservations(self):
        pass


    def handle_request(self, event, context):
        """
        Explain incoming event here
        """

        path = event.get("path", None)
        method = event.get("httpMethod", "")
        _LOG.info(f"Event: {event}")
        _LOG.info(f"Context: {context}")
        if path:
            if path == "/signup":
                return self.signup(json.loads(event['body']))
            elif path == "/signin":
                return self.signin(json.loads(event['body']))
            elif path == "/tables":
                if method == "GET":
                    return self.get_tables()
                elif method == "POST":
                    return self.post_tables(json.loads(event['body']))
            elif event["resource"] == "/tables/{tablesId}":
                table_id = int(event['path'].split('/')[-1])
                return self.get_table_by_id(table_id)
            elif path == "reservations":
                if method == "GET":
                    return self.get_reservations()
                elif method == "POST":
                    return self.post_reservation(json.loads(event['body'])
)

HANDLER = ApiHandler()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
