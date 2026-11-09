"""`python -m npsr_admin` — start the local admin and open it in the browser."""

import os
import time
import webbrowser

from .server import make_server


def main() -> None:
    srv = make_server()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"Админка дашборда: {url}  (закройте это окно, чтобы остановить)")
    if not os.environ.get("NPSR_NO_BROWSER"):
        webbrowser.open(url)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
