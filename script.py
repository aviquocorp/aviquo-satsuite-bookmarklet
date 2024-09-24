from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select


import json
from typing import Final

SAT: Final = "99"
PSAT11_10: Final = "100"
PSAT8_9: Final = "102"

class Main:
    def __init__(self):
        self.options = webdriver.FirefoxOptions()
        #self.options.add_argument("--headless")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--disable-notifications")
        self.options.add_argument("window-size=1920,1080")
        self.options.set_preference("dom.webdriver.enabled", False)
        self.options.set_preference("dom.webnotifications.enabled", False)
        self.options.set_preference("dom.disable_open_during_load", False)
        self.options.set_preference("general.useragent.override", "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0")
        self.options.set_preference("permissions.default.image", 2)
        self.options.set_preference("permissions.default.desktop-notification", 2)
        self.options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
        self.options.set_preference("media.autoplay.default", 0)
        self.options.set_preference("media.autoplay.enabled.user-gestures-needed", 0)
        self.options.set_preference("media.autoplay.enabled", 0)
        self.options.set_preference("browser.privatebrowsing.autostart", 1)

        self.driver = webdriver.Firefox(options=self.options)
        self.questions = []
        self.waiter = WebDriverWait(self.driver, 10)

    def goToQuestionBankSite(self):
        """
        Navigates to the SAT Question Bank website, clicks on the "Find Questions" button, and waits for the assessment type dropdown to appear.
        """
        self.driver.get("https://satsuitequestionbank.collegeboard.org/")
        button = self.driver.find_element(By.CLASS_NAME, "cb-btn")
        button.click()
        self.waiter.until(EC.presence_of_element_located((By.ID, "selectAssessmentType")))

    def getToQuestionsPage(self, test: str):
        assessmentButton = Select(self.driver.find_element(By.ID, "selectAssessmentType"))
        assessmentButton.select_by_value(test)
        testButton = Select(self.driver.find_element(By.ID, "selectTestType"))
        testButton.select_by_value('1')

        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for checkbox in checkboxes[:4]:
            checkbox.click()
        button = self.driver.find_element(By.CLASS_NAME, "cb-btn-primary")
        button.click()

        request = self.driver.wait_for_request("get-questions", 10)
        # when the table is loaded, the request already has a response
        self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, "view-question-button")))

        response = json.loads(request.response.body)
        with open('data.txt', 'w') as f:
            json.dump(response, f)

        exit(0)

    def getReadingTestQuestions(self):
        checkboxes = self.driver.find_elements(By.TAG_NAME, "input")
        for checkbox in checkboxes:
            checkbox.click()



class Question:
    def __init(self, externalId: str, id: str, category: str, domain: str, skill: str, difficulty: str, active: bool, question: str, answerChoices: str, answer: str, rationale: str):
        self.externalId = externalId
        self.id = id
        self.category = category
        self.domain = domain
        self.skill = skill
        self.difficulty = difficulty
        self.active = active
        self.question = question
        self.answerChoices = answerChoices
        self.answer = answer
        self.rationale = rationale

if __name__ == "__main__":
    runner = Main()
    elem = runner.goToQuestionBankSite()

    for test in (SAT, PSAT11_10, PSAT8_9):
        runner.getToQuestionsPage(test)
    input()