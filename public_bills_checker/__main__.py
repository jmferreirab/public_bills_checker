import os
import logging
from public_bills_checker import checker

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


def main():
    """Package demo entry point"""

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
        driver_wrapper = checker.FirefoxDriverWrapper()
        driver = driver_wrapper.driver
        bill_list = checker.read_json_bill_params()

        skip_unavailable_service = ["electricity"]

        bill: checker.WebBillData
        for bill in bill_list:
            if bill.service in skip_unavailable_service:
                logger.info(
                    f"Skipping {}. Reason: flagged unavailable.", bill.service
                )
                continue
            checker.route_service_to_handler(driver_wrapper, bill)
            # break
    except Exception as exc:
        logger.exception(exc)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
