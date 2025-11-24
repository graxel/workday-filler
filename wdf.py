
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException


def refresh_on_error(max_attempts=3):
    def decorator(risky_thing):
        def wrapper(self, *args, attempts=0, **kwargs):
            if attempts > max_attempts:
                print(f"Tried {attempts} times. Giving up.")
                return
            try:
                return risky_thing(self, *args, **kwargs)
            except (NoSuchElementException, TimeoutException) as e:
                try:
                    self.driver.find_element(By.XPATH, "//h1[text()='Something went wrong']")
                except NoSuchElementException:
                    raise e from None
                print(f"Attempt {attempts + 1} failed, refreshing and retrying...")
                self.driver.refresh()
                return wrapper(self, *args, attempts=attempts+1, **kwargs)
            except (StaleElementReferenceException) as e:
                print(f"Attempt {attempts + 1} failed (stale element), refreshing and retrying...")
                self.driver.refresh()
                return wrapper(self, *args, attempts=attempts+1, **kwargs)
        return wrapper
    return decorator

class FormFiller:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)
        self.wait_longer = WebDriverWait(driver, 15)

    def fill_out_text_box(self, element_id, text, css_selector=False):
        if css_selector:
            locator_tuple = (By.CSS_SELECTOR, element_id)
        else:
            locator_tuple = (By.ID, element_id)
        input_box = self.wait.until(EC.presence_of_element_located(locator_tuple))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", input_box)
        input_box.clear()
        input_box = self.wait.until(EC.presence_of_element_located(locator_tuple)) # is this really necessary?
        input_box.send_keys(text)
    
    def select_custom_dropdown(self, button_id, options, multiselect=False, parent=0):
        # dropdown_button = self.wait.until(EC.element_to_be_clickable((By.ID, button_id)))
        dropdown_button = self.wait.until(EC.presence_of_element_located((By.ID, button_id)))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_button)
        self.click_button(button_id, parent=parent, css_selector=False)

        if isinstance(options, str):
            options = [options]

        if multiselect:
            # cycle through options passed
            for option_text in options:
                # type in an option
                dropdown_button.send_keys(option_text)
                dropdown_button.send_keys(Keys.ENTER)
                # # expand code to see if list still open
                # data-automation-id="activeListContainer"
                
        else:
            # see choices
            list_choices = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[visibility='opened'] ul[role='listbox'] li")))
            
            # cycle through options passed
            for option_text in options:
                # if option offered in choices, select it
                if option_text in [list_choice.text for list_choice in list_choices]:
                    dropdown_button.send_keys(option_text)
                    dropdown_button.send_keys(Keys.ENTER)
                    break
            else:
                dropdown_button.send_keys(Keys.ESCAPE)


    def click_button(self, button_id, parent=0, css_selector=True):
        time.sleep(0.2)
        if css_selector:
            # button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, button_id)))
            button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_id)))
        else:
            # button = self.wait.until(EC.presence_of_element_located((By.ID, button_id)))
            button = self.wait.until(EC.element_to_be_clickable((By.ID, button_id)))
        for _ in range(parent):
            button = button.find_element(By.XPATH, "./..")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
        button.click()

    def click_checkbox(self, element_id, check=True, css_selector=False):
        if css_selector:
            checkbox = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, element_id)))
        else:
            checkbox = self.wait.until(EC.presence_of_element_located((By.ID, element_id)))
        self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
        if checkbox.is_selected() != check:
            checkbox.click()

    def add_work_experience(self, exp_data):
        """Adds a work experience panel and fills it out."""
        # Click 'add' button to add a work experience panel
        self.click_button("div[aria-labelledby='Work-Experience-section'] button[data-automation-id='add-button']")

        # Find last added work experience panel
        null_container = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[aria-labelledby='Work-Experience-section'] div[data-fkit-id$='--null']")))[-1]
        panel_prefix = null_container.get_attribute("data-fkit-id").replace("--null", "")
        
        # Fill out work experience data
        self.fill_out_text_box(f"{panel_prefix}--jobTitle", exp_data["jobTitle"])
        self.fill_out_text_box(f"{panel_prefix}--companyName", exp_data["companyName"])
        self.fill_out_text_box(f"{panel_prefix}--location", exp_data.get("location", ""))
        self.fill_out_text_box(f"{panel_prefix}--startDate-dateSectionMonth-input", exp_data["startMonth"])
        self.fill_out_text_box(f"{panel_prefix}--startDate-dateSectionYear-input", exp_data["startYear"])
        if exp_data.get("currentlyWorkHere", False) == True:
            self.click_checkbox(f"{panel_prefix}--currentlyWorkHere")
        else:
            self.fill_out_text_box(f"{panel_prefix}--endDate-dateSectionMonth-input", exp_data["endMonth"])
            self.fill_out_text_box(f"{panel_prefix}--endDate-dateSectionYear-input", exp_data["endYear"])
        self.fill_out_text_box(f"{panel_prefix}--roleDescription", exp_data.get("roleDescription", ""))

    def add_education(self):
        """Adds an education panel and fills it out."""

        school = os.getenv("SCHOOL")
        degree = os.getenv("DEGREE")
        degree_backup = os.getenv("DEGREE_BACKUP")
        major = os.getenv("MAJOR")
        # Click 'add' button to add an education panel
        self.click_button("div[aria-labelledby='Education-section'] button[data-automation-id='add-button']")

        # Find last added education panel
        null_container = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[aria-labelledby='Education-section'] div[data-fkit-id$='--null']")))[-1]
        panel_prefix = null_container.get_attribute("data-fkit-id").replace("--null", "")
        
        # Fill out education data
        school_fields = [f"{panel_prefix}--schoolName", f"{panel_prefix}--school"]
        for field_id in school_fields:
            try:
                self.select_custom_dropdown(field_id, school, multiselect=True, parent=2)
                break
            except:
                pass
        else:
            print("Couldn't fill school name")

        degrees = [degree, degree_backup]
        for deg in degrees:
            try:
                self.select_custom_dropdown(f"{panel_prefix}--degree", deg)
                break
            except:
                pass
        else:
            print("Couldn't fill degree")

        try:
            self.select_custom_dropdown(f"{panel_prefix}--fieldOfStudy", "Chemical Engineering", multiselect=True, parent=2)
        except:
            print("Couldn't fill field of study")

            
    def upload_resume_file(self, file_path="resume.pdf"):
        file_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][data-automation-id='file-upload-input-ref']")))
        file_string = os.path.abspath(file_path)
        file_input.send_keys(file_string)


    def create_acct_or_log_in(self, email, password):
        page_title = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2[id='authViewTitle']")))
        if page_title.text == "Create Account":
            self.fill_out_text_box("input[data-automation-id='email']", email, css_selector=True)
            self.fill_out_text_box("input[data-automation-id='password']", password, css_selector=True)
            self.fill_out_text_box("input[data-automation-id='verifyPassword']", password, css_selector=True)
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-automation-id='createAccountCheckbox']")))
                self.click_checkbox("input[data-automation-id='createAccountCheckbox']", check=True, css_selector=True)
            except TimeoutException:
                pass
            self.click_button("button[data-automation-id='createAccountSubmitButton']", parent=1)
        time.sleep(5)
        page_title = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2[id='authViewTitle']")))
        if page_title.text == "Sign In":
            self.fill_out_text_box("input[data-automation-id='email']", email, css_selector=True)
            self.fill_out_text_box("input[data-automation-id='password']", password, css_selector=True)
            self.click_button("button[data-automation-id='signInSubmitButton']", parent=1)

    @refresh_on_error(max_attempts=1)
    def fill_out_information_page(self):
        country = os.getenv("COUNTRY")
        first_name = os.getenv("FIRST_NAME")
        last_name = os.getenv("LAST_NAME")
        address_line1 = os.getenv("ADDRESS_LINE1")
        city = os.getenv("CITY")
        state_abbr = os.getenv("STATE_ABBR")
        state_full = os.getenv("STATE_FULL")
        postal_code = os.getenv("POSTAL_CODE")
        phone_type = os.getenv("PHONE_TYPE")
        phone_country_code = os.getenv("PHONE_COUNTRY_CODE")
        phone_number = os.getenv("PHONE_NUMBER")

        # Select "How Did You Hear About Us?" dropdown value
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "source--source")))
            self.select_custom_dropdown("source--source", "LinkedIn")
        except TimeoutException:
            pass
        # Select radio button
        # self.click_button("input#hssh3", parent=1)  # go to label/container and click
        self.select_custom_dropdown("country--country", country)
        self.fill_out_text_box("name--legalName--firstName", first_name)
        self.fill_out_text_box("name--legalName--lastName", last_name)
        self.fill_out_text_box("address--addressLine1", address_line1)
        self.fill_out_text_box("address--city", city)
        self.select_custom_dropdown("address--countryRegion", [state_abbr, state_full])  # State dropdown
        self.fill_out_text_box("address--postalCode", postal_code)
        self.select_custom_dropdown("phoneNumber--phoneType", phone_type)
        self.select_custom_dropdown("phoneNumber--countryPhoneCode", phone_country_code, multiselect=True, parent=2)
        self.fill_out_text_box("phoneNumber--phoneNumber", phone_number)

    @refresh_on_error(max_attempts=3)
    def fill_out_experience_page(self, experience_data):
        # Work
        for company in experience_data.keys():
            self.add_work_experience(experience_data[company])
        
        # Education
        self.add_education()

        # Resume Upload
        self.upload_resume_file()

        # Websites