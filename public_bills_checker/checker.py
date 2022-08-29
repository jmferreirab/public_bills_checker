"""Package module defining RPA/Scraper logic."""

# import sys
import os
from dataclasses import dataclass
import logging
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
import winsound

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(module)-10s | %(levelname)-5s | %(funcName)15s -- l"
        "%(lineno)4d | %(message)s"
    ),
    datefmt="%Y-%m-%dT%H:%M",
)
logger = logging.getLogger(__name__)
fh = logging.FileHandler("log.log", mode="a")  # append
fm = logging.Formatter(
    fmt=(
        "%(asctime)s | %(module)-10s | %(levelname)-5s | %(funcName)15s -- l"
        "%(lineno)4d | %(message)s"
    ),
    datefmt="%Y-%m-%dT%H:%M",
)
fh.setLevel(logging.INFO)
fh.setFormatter(fm)
logger.addHandler(fh)


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
            logger.info("Attempting to use cached profile")
            m_options.add_argument("-profile")
            m_options.add_argument(sample_profile_path)
            self.cached_browser = True
        else:
            logger.info("Running with blank profile")
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
        eab_handler(driverWrapper, service)
        pass
    elif service.provider == "Vanti S.A. E.S.P.":
        vanti_handler(driverWrapper, service)
        pass  # raise NotImplementedError()
    elif service.provider == "D":
        print("routing to D")
        pass  # raise NotImplementedError()


def enel_handler(driverWrapper: FirefoxDriverWrapper, service: PublicService):

    # TODO Add better wrapping so errors in a handler allow logged exits

    driverWrapper.driver.get(service.url)

    el: WebElement

    # Accept cookies button. If not shown, then keep going normally.
    try:
        driverWrapper.driver.find_element(
            By.XPATH, '//*[@id="truste-consent-button"]'
        ).click()
    except:
        logger.info("No ENEL captcha required.")

    driverWrapper.driver.get(service.url)

    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="numero_cuenta"]'))
    )
    el.send_keys(service.account_reference.split("-")[0])

    el = driverWrapper.driver.find_element(By.XPATH, '//*[@id="dv"]')
    el.send_keys(service.account_reference.split("-")[1])

    el = driverWrapper.driver.find_element(By.XPATH, '//*[@id="solicitar"]')
    el.send_keys(Keys.ENTER)

    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="DataTables_Table_0"]/tbody/tr[1]')
        )
    )

    import re

    timestr = time.strftime("%Y%m%d-%H%M")
    driverWrapper.driver.get_screenshot_as_file(
        "./images/enel-" + timestr + ".png"
    )
    pttern = re.compile(r"[\n\t]")
    x = tuple(pttern.split(el.get_attribute("innerText")))
    logger.info(str(("Enel",) + x))
    _, date_issued, pay_amount, payment_source, status, _ = x
    if status == "Emitida":
        status = "Payment not registered."


def eab_handler(driverWrapper: FirefoxDriverWrapper, service: PublicService):

    # TODO Add better wrapping so errors in a handler allow logged exits

    driverWrapper.driver.get(service.url)

    el: WebElement

    driverWrapper.driver.get(service.url)

    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="MainContent_tbxContractAccount"]')
        )
    )
    el.send_keys(service.account_reference)
    el.send_keys(Keys.ENTER)

    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="MainContent_pnlBills"]')
        )
    )

    timestr = time.strftime("%Y%m%d-%H%M")
    driverWrapper.driver.get_screenshot_as_file(
        "./images/eab-" + timestr + ".png"
    )
    text = el.get_attribute("innerText")
    status = "Aprobada" if "aprobada" in text.lower() else "No paga"
    logger.info(str(("EAB", "Ultima factura", status)))


def vanti_handler(driverWrapper: FirefoxDriverWrapper, service: PublicService):

    # TODO Add better wrapping so errors in a handler allow logged exits

    driverWrapper.driver.get(service.url)

    el: WebElement

    driverWrapper.driver.get(service.url)

    el = driverWrapper.driver.find_element(By.XPATH, '//*[@id="queryID"]')
    el.send_keys(service.account_reference)
    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="select2-projectId-container"]')
        )
    )
    el.click()
    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '(//*[@id="select2-projectId-results"]//li)[2]')
        )
    )
    el.click()

    duration = 1000  # milliseconds
    freq = 440  # Hz
    winsound.Beep(freq, duration)
    input("Paused. Waiting for user to type captcha. Press ENTER to resume.")

    el = WebDriverWait(driverWrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div[1]/div[3]/div/form/div[2]/table[1]")
        )
    )

    #     "Pagar	No. Pago	Cuenta Contrato	Valor Total a Pagar
    # Pagar	62685426280822	62685426	$ 15.000"

    timestr = time.strftime("%Y%m%d-%H%M")
    driverWrapper.driver.get_screenshot_as_file(
        "./images/vanti-" + timestr + ".png"
    )

    try:
        text = el.get_attribute("innerText")
        text = text.splitlines()[1]
        text = tuple(text.split("\t")[2:4]) + ("Pendiente",)
    except:
        text = ("No encontrada (Paga?)",)

    logger.info(str(("Vanti",) + text))


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

    try:
        os.mkdir("images")
    except:
        pass

    try:
        driver_wrapper = FirefoxDriverWrapper()
        driver = driver_wrapper.driver
        service_list = parse_bill_parameters()

        service: PublicService
        for service in service_list:
            route_service_to_handler(driver_wrapper, service)
            # break
    except Exception as e:
        logger.exception(e)
    finally:
        driver.quit()


main()
