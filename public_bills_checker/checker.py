"""Package module defining RPA/Scraper logic."""

from __future__ import annotations

# import sys
import os
from dataclasses import dataclass
import logging
import json
import time
import re
import winsound
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


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
class WebBillData:
    """Holds data associated to a service bill."""

    service: str
    provider: str
    url: str
    account_reference: str


def read_json_bill_params(
    params_file_path="./res/params.json",
) -> list[WebBillData]:
    """Convert JSON file to a list of WebBillData objects.

    Args:
        params_file_path. JSON file with parameters.

    Returns:
        list[WebBillData]

    Examples:
        params = read_json_bill_params()
        print(params[0].url)
    """
    with open(params_file_path, "r", encoding="UTF-8") as file:
        data = json.load(file)

    bills = data["services"]
    service_params_list = []
    for bill in bills:
        # p is a dict, get its values expanded to instantiate the dataclass
        service_params_list.append(WebBillData(*bill.values()))

    return service_params_list


def route_service_to_handler(
    driver_wrapper: FirefoxDriverWrapper, bill: WebBillData
):
    """Route to the right bill handler.

    Args:
        driver_wrapper (FirefoxDriverWrapper)
        bill (WebBillData)
    """
    if bill.provider == "enel":
        enel_handler(driver_wrapper, bill)
    elif bill.provider == "EAAB ESP":
        eab_handler(driver_wrapper, bill)
    elif bill.provider == "Vanti S.A. E.S.P.":
        vanti_handler(driver_wrapper, bill)
    elif bill.provider == "D":
        print("routing to D")


def enel_handler(driver_wrapper: FirefoxDriverWrapper, bill: WebBillData):
    """Handle data collection for Enel bill.

    Args:
        driver_wrapper (FirefoxDriverWrapper)
        bill (WebBillData)
    """

    # TODO Add better wrapping so errors in a handler allow logged exits

    driver_wrapper.driver.get(bill.url)

    elem: WebElement

    # Accept cookies button. If not shown, then keep going normally.
    try:
        driver_wrapper.driver.find_element(
            By.XPATH, '//*[@id="truste-consent-button"]'
        ).click()
    except NoSuchElementException:
        logger.info("No ENEL captcha required.")

    driver_wrapper.driver.get(bill.url)

    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="numero_cuenta"]'))
    )
    elem.send_keys(bill.account_reference.split("-")[0])

    elem = driver_wrapper.driver.find_element(By.XPATH, '//*[@id="dv"]')
    elem.send_keys(bill.account_reference.split("-")[1])

    elem = driver_wrapper.driver.find_element(By.XPATH, '//*[@id="solicitar"]')
    elem.send_keys(Keys.ENTER)

    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="DataTables_Table_0"]/tbody/tr[1]')
        )
    )

    timestr = time.strftime("%Y%m%d-%H%M")
    driver_wrapper.driver.get_screenshot_as_file(
        "./images/enel-" + timestr + ".png"
    )
    pttern = re.compile(r"[\n\t]")
    text_data = tuple(pttern.split(elem.get_attribute("innerText")))
    logger.info(str(("Enel",) + text_data))
    # _, date_issued, pay_amount, payment_source, status, _ = text_data
    # if status == "Emitida":
    #     status = "Payment not registered."


def eab_handler(driver_wrapper: FirefoxDriverWrapper, bill: WebBillData):
    """Handle data collection for EAB bill.

    Args:
        driver_wrapper (FirefoxDriverWrapper)
        bill (WebBillData)
    """
    # TODO Add better wrapping so errors in a handler allow logged exits

    driver_wrapper.driver.get(bill.url)

    elem: WebElement

    driver_wrapper.driver.get(bill.url)

    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="MainContent_tbxContractAccount"]')
        )
    )
    elem.send_keys(bill.account_reference)
    elem.send_keys(Keys.ENTER)

    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="MainContent_pnlBills"]')
        )
    )

    timestr = time.strftime("%Y%m%d-%H%M")
    driver_wrapper.driver.get_screenshot_as_file(
        "./images/eab-" + timestr + ".png"
    )
    text = elem.get_attribute("innerText")
    status = "Aprobada" if "aprobada" in text.lower() else "No paga"
    logger.info(str(("EAB", "Ultima factura", status)))


def vanti_handler(driver_wrapper: FirefoxDriverWrapper, bill: WebBillData):
    """Handle data collection for Vanti bill.

    Args:
        driver_wrapper (FirefoxDriverWrapper)
        bill (WebBillData)
    """
    # TODO Add better wrapping so errors in a handler allow logged exits

    driver_wrapper.driver.get(bill.url)

    elem: WebElement

    driver_wrapper.driver.get(bill.url)

    elem = driver_wrapper.driver.find_element(By.XPATH, '//*[@id="queryID"]')
    elem.send_keys(bill.account_reference)
    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="select2-projectId-container"]')
        )
    )
    elem.click()
    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, '(//*[@id="select2-projectId-results"]//li)[2]')
        )
    )
    elem.click()

    duration = 500  # milliseconds
    freq = 700  # Hz
    winsound.Beep(freq, duration)
    input("Paused. Waiting for user to type captcha. Press ENTER to resume.")

    elem = WebDriverWait(driver_wrapper.driver, 20).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/div[1]/div[3]/div/form/div[2]/table[1]")
        )
    )

    #     "Pagar	No. Pago	Cuenta Contrato	Valor Total a Pagar
    # Pagar	62685426280822	62685426	$ 15.000"

    timestr = time.strftime("%Y%m%d-%H%M")
    driver_wrapper.driver.get_screenshot_as_file(
        "./images/vanti-" + timestr + ".png"
    )

    try:
        text = elem.get_attribute("innerText")
        text = text.splitlines()[1]
        text = tuple(text.split("\t")[2:4]) + ("Pendiente",)
    except:
        text = ("No encontrada (Paga?)",)

    logger.info(str(("Vanti",) + text))
