from pypaladin import conf, httpclient

CONF = conf.BaseAppConfig()


def main():
    CONF.setup()

    client = httpclient.default_client(timeout=10)
    client.get("https://www.baidu.com/")


if __name__ == "__main__":
    main()
