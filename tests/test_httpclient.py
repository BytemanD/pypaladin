from pypaladin import httpclient


def test_httpclient():
    client = httpclient.default_client(timeout=10, raise_for_status=True)
    client.get("https://www.baidu.com/")
