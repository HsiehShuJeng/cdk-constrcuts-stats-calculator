import csv
import os
import time

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Load environment variables from .env file
load_dotenv()

# Accessing the username and password from .env
SONATYPE_USERNAME = os.getenv("user")
SONATYPE_PASSWORD = os.getenv("password")


def automate_sonatype_csv_download():
    # Initialize the WebDriver (Ensure you have the ChromeDriver installed and set up)
    driver = webdriver.Chrome()

    # Navigate to the Sonatype login page
    driver.get("https://s01.oss.sonatype.org/#welcome")

    # Wait for the page to fully load
    WebDriverWait(driver, 120).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

    try:
        # Navigate to the Sonatype login page
        driver.get("https://s01.oss.sonatype.org/#welcome")

        # Use JavaScript to trigger the click event for 'Log In'
        # Find the 'Log In' button
        print(f"Targeting the login spen element...")
        login_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.ID, "head-link-r"))
        )

        # Try to click the button using WebDriver click
        try:
            print("Clicking using WebDriver")
            login_button.click()
        except ElementNotInteractableException:
            print("Element not interactable, using JavaScript click")
            driver.execute_script("arguments[0].click();", login_button)

        # Wait for the login modal to be visible
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, "login-window"))
        )

        # Wait for the input fields to be ready
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "usernamefield"))
        )

        # Enter username and password
        username_field = driver.find_element(By.ID, "usernamefield")
        username_field.send_keys(SONATYPE_USERNAME)

        password_field = driver.find_element(By.ID, "passwordfield")
        password_field.send_keys(SONATYPE_PASSWORD)

        # Click the "Log In" button within the modal
        login_submit_button = driver.find_element(By.ID, "ext-gen224")
        try:
            print("Clicking submit button using WebDriver")
            login_submit_button.click()
        except ElementNotInteractableException:
            print("Submit button not interactable, using JavaScript click")
            driver.execute_script("arguments[0].click();", login_submit_button)

        # Wait for the page to redirect after login
        WebDriverWait(driver, 15).until(EC.url_contains("#welcome"))

        # Navigate to the Central Statistics page
        driver.get("https://s01.oss.sonatype.org/#central-stat")

        # Wait for the Central Statistics page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "centralStatGxtPanel"))
        )

        # Fill in GroupId and ArtifactId fields
        group_id_field = driver.find_element(By.ID, "x-auto-14-input")
        group_id_field.clear()
        group_id_field.send_keys("io.github.hsiehshujeng")

        artifact_id_field = driver.find_element(By.ID, "x-auto-17-input")
        artifact_id_field.clear()
        artifact_id_field.send_keys("cdk-comprehend-s3olap-go")

        # Click the "Export CSV" button to download the statistics
        export_button = driver.find_element(
            By.XPATH, "//button[contains(text(),'Export CSV')]"
        )
        export_button.click()

        # Wait for the download to complete (adjust timing based on network speed)
        time.sleep(10)  # Adjust this wait time as needed

    except TimeoutException as e:
        print(f"Timeout occurred: {e}")
    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser even if there is an error
        driver.quit()


# Call the function to automate the CSV download
automate_sonatype_csv_download()
