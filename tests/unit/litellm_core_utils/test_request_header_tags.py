import litellm
from starlette.datastructures import Headers

from litellm.litellm_core_utils.litellm_logging import StandardLoggingPayloadSetup


def test_request_tags_support_starlette_headers(monkeypatch):
    monkeypatch.setattr(litellm, "disable_add_user_agent_to_request_tags", False)
    monkeypatch.setattr(litellm, "extra_spend_tag_headers", ["x-custom-header"])

    proxy_server_request = {
        "headers": Headers(
            {
                "user-agent": "curl/8.7.1",
                "x-custom-header": "abc",
            }
        )
    }

    assert StandardLoggingPayloadSetup._get_request_tags(
        litellm_params={},
        proxy_server_request=proxy_server_request,
    ) == [
        "User-Agent: curl",
        "User-Agent: curl/8.7.1",
        "x-custom-header: abc",
    ]
