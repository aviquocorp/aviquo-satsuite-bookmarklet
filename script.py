from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

import time
import json
from typing import Final
import sqlite3
import sys

SAT: Final = "99"
PSAT11_10: Final = "100"
PSAT8_9: Final = "102"
debug = True
headless = False

class Main:
    def __init__(self):
        """
        Sets up options for the Firefox driver
        Opens the Firefox driver
        Initializes the database object
        """
        self.options = webdriver.FirefoxOptions()
        if headless:
            self.options.add_argument("--headless")
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
        self.headers = ""
        self.waiter = WebDriverWait(self.driver, 10)
        self.currentTest = ""
        self.currentCategory = ""
        self.database = Database()

    def goToQuestionBankSite(self):
        """
        Navigates to the SAT Question Bank website, clicks on the "Find Questions" button, and waits for the assessment type dropdown to appear.
        """
        self.driver.get("https://satsuitequestionbank.collegeboard.org/")
        button = self.driver.find_element(By.CLASS_NAME, "cb-btn")
        button.click()
        self.waiter.until(EC.presence_of_element_located((By.ID, "selectAssessmentType")))

    def getQuestionsForTest(self, test: str):
        """
        Selects the given assessment type from the dropdown and then calls
        getQuestionsForCategory for both reading and writing and math.

        Args:
            test (str): The assessment type to select.

        Returns:
            None
        """
        assessmentButton = Select(self.driver.find_element(By.ID, "selectAssessmentType"))
        assessmentButton.select_by_value(test)
        self.currentTest = test
        self.getQuestionsForCategory('2')
        self.getQuestionsForCategory('1')

    def getQuestionsForCategory(self, category: str):
        """
        Retrieves and processes questions for the specified category.

        Args:
            category (str): The category of questions to retrieve.

        Returns:
            None
        """
        testButton = Select(self.driver.find_element(By.ID, "selectTestType"))
        testButton.select_by_value(category)
        self.currentCategory = "Reading and Writing" if category == '1' else "Math"

        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for checkbox in checkboxes[:4]:
            checkbox.click()
        button = self.driver.find_element(By.CLASS_NAME, "cb-btn-primary")
        button.click()

        request = self.driver.wait_for_request("get-questions", 10)
        # when the table is loaded, the request already has a response
        self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, "view-question-button")))

        response = json.loads(request.response.body)
        self.headers = request.headers.as_string()
        del self.driver.requests

        for question in response:
            external_id = question['external_id']
            if debug:
                print(f"Getting {external_id} ({question['questionId']}) from {self.currentTest} {category}")
            self._getQuestionData(question)
            time.sleep(2)

        # must go back to main page before scraping next category/test
        self.goToQuestionBankSite()


    def _getQuestionData(self, questionResponse: dict):
        """
        Gets the data for a single question and inserts it into the database.

        Args:
            questionResponse (dict): The response from the get-questions request.

        Returns:
            None
        """
        script = f"""
            let xhr = new XMLHttpRequest();
            xhr.open('POST', 'https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-question', false);
            xhr.send('{{"external_id": "{questionResponse['external_id']}"}}');
        """
        if debug:
            print(script)
        self.driver.execute_script(script)

        request = self.driver.wait_for_request("get-question", 10)
        response = json.loads(request.response.body)
        question = Question(questionResponse['external_id'], questionResponse['questionId'], self.currentCategory, questionResponse['primary_class_cd_desc'], questionResponse['skill_desc'], Main.convertDifficulty(questionResponse['difficulty']), response['stimulus'], response['stem'], response['answerOptions'], response['correct_answer'][0], response['rationale'])

        self.questions.append(question)
        self.database.insert(question)

        with open('questions.txt', 'a') as f:
            json.dump(response, f)
            f.write(',\n')

        del self.driver.requests

    def convertDifficulty(difficulty: str):
        if difficulty == "H":
            return "Hard"
        elif difficulty == "M":
            return "Medium"
        elif difficulty == "E":
            return "Easy"


class Question:
    def __init__(self, external_id: str, id: str, category: str, domain: str, skill: str, difficulty: str, details: str, question: str, answer_choices: dict, answer: str, rationale: str):
        """
        Initializes a new Question object.

        Args:
            external_id (str): The external id of the question.
            id (str): The id of the question.
            category (str): The category of the question.
            domain (str): The domain of the question.
            skill (str): The skill of the question.
            difficulty (str): The difficulty of the question.
            details (str): The extra details given with the question.
            question (str): The text of the question.
            answer_choices (dict): The answer choices.
            answer (str): The correct answer.
            rationale (str): The explanation for the answer.
        """
        self.external_id = external_id
        self.id = id
        self.category = category
        self.domain = domain
        self.skill = skill
        self.difficulty = difficulty
        self.details = details
        self.question = question
        self.answer_choices = answer_choices
        self.answer = answer
        self.rationale = rationale

class Database:
    def __init__(self):
        """
        Initializes a new Database object.

        This will create a new SQLite database file if it doesn't exist, and
        connect to it. The database will have a single table, `sat_questions`,
        with the following columns:
        - `id`: A unique identifier for the question.
        - `category`: The category of the question (reading, writing, math).
        - `domain`: The domain of the question.
        - `skill`: The skill of the question.
        - `difficulty`: The difficulty of the question.
        - `details`: The extra details given with the question.
        - `question`: The text of the question.
        - `answer_choices`: The answer choices.
        - `answer`: The correct answer.
        - `rationale`: The explanation for the answer.
        """
        self.connection = sqlite3.connect('questions.db')
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sat_questions (
                id TEXT PRIMARY KEY NOT NULL UNIQUE,
                category TEXT NOT NULL,
                domain TEXT,
                skill TEXT,
                difficulty TEXT,
                details TEXT,
                question TEXT,
                answer_choices TEXT,
                answer TEXT,
                rationale TEXT
            );
        """)

    def insert(self, question: Question):
        """
        Inserts a single question into the database.

        Args:
            question (Question): The question to insert.
        """
        self.cursor.execute("""
            INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            question.id,
            question.category,
            question.domain,
            question.skill,
            question.difficulty,
            question.details,
            question.question,
            json.dumps(question.answer_choices),
            question.answer,
            question.rationale
        ))
        self.connection.commit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in range(1, len(sys.argv)):
            if sys.argv[arg] == "--debug" or sys.argv[arg] == "-d":
                debug = True
            elif sys.argv[arg] == "--headless" or sys.argv[arg] == "-H":
                headless = True
            elif sys.argv[arg] == "--help" or sys.argv[arg] == "-h":
                print("Usage: python script.py [--debug | -d] [--headless | -H]")
                sys.exit(0)

    runner = Main()
    elem = runner.goToQuestionBankSite()

    for test in (SAT, PSAT11_10, PSAT8_9):
        runner.getQuestionsForTest(test)

    print("Done!")