import os
import sys
import asyncio

import argparse
import uvicorn
import pytest
from dotenv            import load_dotenv
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore    import QTimer
from qasync            import QEventLoop

from src.webui         import app
from src.qt            import MainWindow, API_BASE
from src.qt.styles     import STYLESHEET
from src.rest_client   import AsyncApiClient


__version__ = "1.0"
__author__ = "Wiered"

def run_qt():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    client = AsyncApiClient(base_url=API_BASE)
    window = MainWindow(client)
    window.show()

    with loop:
        loop.run_forever()

        loop.run_until_complete(client.close())

def run_webui():
    load_dotenv()

    if __name__ == "__main__":
        try:
            port = 8083
        except:
            port = 8080
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

def run_tests():
    # point pytest at your tests directory
    return pytest.main(["-q", "tests/"])

def run_pytest():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="run the pytest suite and exit",
    )
    args = parser.parse_args()

    if args.test:
        # invoke pytest and exit with its return code
        sys.exit(run_tests())

    # … your normal application startup here …
    print("Starting the app…")
    # e.g. uvicorn, click CLI, whatever your app does

def main():
    """"""
    run_qt()
    # run_webui()
    # run_pytest()

if __name__ == '__main__':
    main()
