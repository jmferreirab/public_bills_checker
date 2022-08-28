"""Package module defining RPA/Scraper logic."""

# import sys
import os
from inspect import getsourcefile
from os.path import abspath
from dataclasses import dataclass
import logging
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

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
logger.info("Running from: " + abspath(getsourcefile(lambda: 0)))
logger.info("Running from: " + PROJECT_ROOT)


class FirefoxDriverWrapper:
    """Class to centralize custom properties associated to the driver"""

    def __init__(
        self,
        executable_path="./res/geckodriver.exe",
        original_profile_path="./rust_mozprofile",
    ):
        self.setup_browser(executable_path, original_profile_path)

    def setup_browser(self, executable_path, sample_profile_path):
        """Setup a firefox browser using specified geckodriver path
        and (optionally), a pre-existing firefox profile.

        Args:
            m_executable_path (str, optional): [description].
            browser_profile_path (str, optional): [description].
        """

        m_options = Options()
        service = Service(executable_path)

        if os.path.exists(sample_profile_path):
            logging.info("Attempting to use cached profile")
            m_options.add_argument("-profile")
            # this will still copy to temp the sample profile but with cache.
            m_options.add_argument(sample_profile_path)
            # m_options.set_preference("profile", PROJECT_ROOT + "\\rust_mozprofile")
            self.cached_browser = True
        else:
            logging.info("Running with blank profile")
            self.cached_browser = False

        self.driver = webdriver.Firefox(
            service=service,
            options=m_options,
            # , firefox_binary=binary)
        )


@dataclass
class PublicService:
    service: str
    provider: str
    url: str
    account_reference: str


def parse_bill_parameters(
    params_file_path="./res/params.json",
) -> list("PublicServiceParams"):
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

    params = params["services"]
    service_params_list = []
    for p in params:
        # p is a dict, get its values expanded to instantiate the dataclass
        service_params_list.append(PublicService(*p.values()))

    return service_params_list


def route_service_to_handler(
    driverWrapper: FirefoxDriverWrapper, service: PublicService
):
    if service.provider == "enel":
        enel_handler(driverWrapper, service)
    elif service.provider == "EAAB ESP":
        print("routing to EAAB ESP")
        pass
    elif service.provider == "C":
        print("routing to C")
        pass  # raise NotImplementedError()
    elif service.provider == "D":
        print("routing to D")
        pass  # raise NotImplementedError()


def enel_handler(driverWrapper: FirefoxDriverWrapper, service: PublicService):
    driverWrapper.driver.get(service.url)

    el: WebElement

    try:
        driverWrapper.driver.find_element(
            By.XPATH, '//*[@id="truste-consent-button"]'
        ).click()
    except:
        pass

    driverWrapper.driver.get(service.url)

    el = WebDriverWait(driverWrapper.driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="numero_cuenta"]'))
    )
    el.send_keys(service.account_reference.split("-")[0])

    el = driverWrapper.driver.find_element(By.XPATH, '//*[@id="dv"]')
    el.send_keys(service.account_reference.split("-")[1])

    el = driverWrapper.driver.find_element(By.XPATH, '//*[@id="solicitar"]')
    el.send_keys(Keys.ENTER)

    el = WebDriverWait(driverWrapper.driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="DataTables_Table_0"]/tbody/tr[1]')
        )
    )

    import re

    pttern = re.compile(r"[\n\t]")
    x = tuple(pttern.split(el.get_attribute("innerText")))
    logger.info(str(("Enel",) + x))
    _, date_issued, pay_amount, payment_source, status, _ = x
    if status == "Emitida":
        status = "Payment not registered."


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

    driver_wrapper = FirefoxDriverWrapper()
    driver = driver_wrapper.driver
    service_list = parse_bill_parameters()

    service: PublicService
    for service in service_list:
        route_service_to_handler(driver_wrapper, service)
        break

    driver.quit()


main()
