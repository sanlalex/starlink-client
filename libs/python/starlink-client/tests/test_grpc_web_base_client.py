import json
import tempfile
import unittest
from unittest.mock import patch

from spacex.api.device.device_pb2 import Request, Response
from starlink_client.account import Account
from starlink_client.dto import ServiceAddress, ServiceLine
from starlink_client.grpc_web_base_client import GrpcWebBaseClient


ACCOUNT_PAYLOAD = json.dumps(
    {
        "email": "test@example.com",
        "emailVerified": True,
        "familyName": "Test",
        "givenName": "Account",
        "locale": "en",
        "name": "Test Account",
        "subjectId": "subject",
        "accountId": "ACC-1",
        "updatedAt": 0,
        "isSupportAgent": False,
        "isSpacexEmployee": False,
        "enabled": True,
        "canManageClients": False,
        "roles": [],
        "employeeAccountPermissions": [],
        "permissions": [],
    }
)


class FakeCookies:
    def keys(self):
        return []

    @property
    def jar(self):
        return []


class FakeResponse:
    def __init__(self, *, status_code=200, text=ACCOUNT_PAYLOAD, content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content
        self.cookies = FakeCookies()
        self.headers = {}
        self.reason_phrase = "OK"


class FakeHttpClient:
    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.get_calls = []
        self.post_calls = []
        self.closed = False

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return FakeResponse()

    def post(self, url, **kwargs):
        self.post_calls.append((url, kwargs))
        payload = Response().SerializeToString(deterministic=True)
        frame = bytes([0]) + len(payload).to_bytes(4, "big") + payload
        return FakeResponse(content=frame)

    def close(self):
        self.closed = True


class GrpcWebBaseClientTests(unittest.TestCase):
    def make_client(self, **kwargs):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        patcher = patch(
            "starlink_client.grpc_web_base_client.httpx.Client",
            FakeHttpClient,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return GrpcWebBaseClient(
            "Starlink.Com.Access.V1=secret; Starlink.Com.Sso=session",
            temporary_directory.name,
            **kwargs,
        )

    def test_current_starlink_endpoints_are_defaults(self):
        client = self.make_client()

        self.assertEqual(
            client._url,
            "https://starlink.com/api/SpaceX.API.Device.Device/Handle",
        )
        self.assertEqual(
            client._auth_url,
            "https://api.starlink.com/auth-rp/auth/user",
        )
        _, auth_kwargs = client._client.get_calls[0]
        self.assertNotIn("x-xsrf-token", auth_kwargs["headers"])

    def test_endpoint_origin_and_timeout_can_be_overridden(self):
        client = self.make_client(
            grpc_web_api_url="https://gateway.example/grpc",
            auth_url="https://gateway.example/auth",
            web_origin="https://console.example",
            timeout=12,
        )

        client.call(Request())

        url, post_kwargs = client._client.post_calls[0]
        self.assertEqual(url, "https://gateway.example/grpc")
        self.assertEqual(post_kwargs["headers"]["Origin"], "https://console.example")
        self.assertEqual(post_kwargs["timeout"], 12)
        self.assertEqual(client._client.init_kwargs["timeout"], 12)

    def test_client_can_be_used_as_a_context_manager(self):
        client = self.make_client()

        with client as entered_client:
            self.assertIs(entered_client, client)

        self.assertTrue(client._client.closed)

    def test_non_positive_timeout_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.make_client(timeout=0)

    def test_account_without_can_manage_clients_defaults_to_false(self):
        payload = json.loads(ACCOUNT_PAYLOAD)
        del payload["canManageClients"]

        account = Account.model_validate(payload)

        self.assertFalse(account.canManageClients)

    def test_service_line_accepts_nullable_optional_fields(self):
        service_line = ServiceLine.model_validate(
            {
                "serviceLineNumber": "SL-1",
                "nickname": None,
                "displayName": None,
                "serviceAddress": ServiceAddress.model_construct(),
                "userTerminals": [],
                "gateways": [],
                "subscription": None,
                "isDepositCancelled": False,
                "canPauseService": False,
            }
        )

        self.assertIsNone(service_line.nickname)
        self.assertIsNone(service_line.displayName)
        self.assertIsNone(service_line.subscription)


if __name__ == "__main__":
    unittest.main()

