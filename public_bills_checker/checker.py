"""Package module defining RPA/Scraper logic."""

# import sys
import os
from os.path import abspath
from dataclasses import dataclass
import logging
from inspect import getsourcefile
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(module)-18s | %(levelname)s | %(funcName)s -- l"
        "%(lineno)d | %(message)s"
    ),
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger(__name__)
fh = logging.FileHandler("log.log", mode="a")  # append
fm = logging.Formatter(
    fmt=(
        "%(asctime)s | %(module)-18s | %(levelname)s | %(funcName)s -- l"
        " %(lineno)d | %(message)s"
    ),
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
fh.setLevel(logging.INFO)
fh.setFormatter(fm)
logger.addHandler(fh)


PROJECT_ROOT = os.path.abspath(".")
logger.info(abspath(getsourcefile(lambda: 0)))
logger.info(PROJECT_ROOT)


@dataclass
class FirefoxDriverWrapper:
    """Class to centralize custom properties associated to the driver"""

    driver: webdriver.Firefox = None
    cached_browser: bool = False
    original_profile_path: str = ""


def setup_browser(
    m_executable_path="./res/geckodriver.exe",
    browser_profile_path="./rust_mozprofile",
) -> FirefoxDriverWrapper:
    """Setup a firefox browser using specified geckodriver path
    and (optionally), a pre-existing firefox profile.

    Args:
        m_executable_path (str, optional): [description].
        browser_profile_path (str, optional): [description].

    Returns:
        FirefoxDriverWrapper
    """

    if os.path.exists(browser_profile_path):
        logging.info("Attempting to use cached profile")
        m_options = Options()
        m_options.add_argument("-profile")
        # this will still copy to temp the sample profile but with cache.
        m_options.add_argument(browser_profile_path)

        # m_options.set_preference("profile", PROJECT_ROOT + "\\rust_mozprofile")
        driver = webdriver.Firefox(
            options=m_options,
            executable_path=m_executable_path
            # , firefox_binary=binary)
        )
        cached_browser = True
    else:
        logging.info("Running with blank profile")
        driver = webdriver.Firefox(executable_path=m_executable_path)

        cached_browser = False

    # return a ref of the driver
    return FirefoxDriverWrapper(driver, cached_browser, browser_profile_path)


def get_bill_parameters(params_file_path="./res/params.json") -> dict:
    """Get url, service name and account number from a JSON file

    Args:
        params_file_path. JSON file with parameters.

    Returns:
        Parameters dictionary

    Examples:
        params = get_bill_parameters()
        print(params['services']['water'])
    """
    with open(params_file_path, "r", encoding="UTF-8") as file:
        params = json.load(file)

    print(params)
    return params


def main():
    """Entry point"""

    # Setup browser
    # For every bill/service url passed in params.json (command line specified file)
    #   Go to page with public bill
    #   Find out the price and enddate or take screenshot for specified account number
    # End For
    # Show results like via stdout
    # Bill A: NameA, Due X, amount Y
    # Bill B: NameB, Due X, amount Y

    os.chdir("./public_bills_checker")

    driver_wrapper = setup_browser()
    driver = driver_wrapper.driver
    params = get_bill_parameters()
    params = params["services"]

    for _, value in params.items():
        driver.get(value["nav_url"])


main()
