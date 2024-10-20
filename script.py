from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

import gzip
import time
import json
from typing import Final
import asqlite
import sys
import re
import asyncio

SAT: Final = "99"
PSAT11_10: Final = "100"
PSAT8_9: Final = "102"
debug = False
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
        self.headers = ""
        self.waiter = WebDriverWait(self.driver, 10)
        self.currentTest = ""
        self.currentCategory = ""
        self.newQuestions = 0

    def goToQuestionBankSite(self):
        """
        Navigates to the SAT Question Bank website, clicks on the "Find Questions" button, and waits for the assessment type dropdown to appear.
        """
        self.driver.get("https://satsuitequestionbank.collegeboard.org/")
        self.waiter.until(EC.presence_of_element_located((By.CLASS_NAME, "cb-btn")))
        button = self.driver.find_element(By.CLASS_NAME, "cb-btn")
        button.click()
        self.waiter.until(EC.presence_of_element_located((By.ID, "selectAssessmentType")))

    async def getQuestionsForTest(self, test: str):
        """
        Selects the given assessment type from the dropdown and then calls
        getQuestionsForCategory for both reading and writing and math.

        Args:
            test (str): The assessment type to select.

        Returns:
            None
        """
        self.newQuestions = 0
        for category in ('1', '2'):
            assessmentButton = Select(self.driver.find_element(By.ID, "selectAssessmentType"))
            assessmentButton.select_by_value(test)
            self.currentTest = test
            await self.getQuestionsForCategory(category)

        print(f"Got {self.newQuestions} new questions for {self.currentTest}")

    async def getQuestionsForCategory(self, category: str):
        """
        Retrieves and processes questions for the specified category.

        Args:
            category (str): The category of questions to retrieve.

        Returns:
            None
        """
        self.waiter.until(EC.presence_of_element_located((By.ID, "selectTestType")))
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

        response = json.loads(request.response.body.decode('utf-8'))
        self.headers = request.headers.as_string()
        del self.driver.requests

        for question in response:
            external_id = question['external_id']
            if debug:
                print(f"Getting {external_id if external_id else question['ibn']} ({question['questionId']}) from {self.currentTest} {category}")

            # if the question is already in the database, skip it
            isDupe = await databaseIsDuplicate(question['questionId'])
            if isDupe:
                if debug:
                    print(f"{external_id if external_id else question['ibn']} is already in table")
                continue
            await self._getQuestionData(question)
            self.newQuestions+=1
            await asyncio.sleep(0.5)

        # must go back to main page before scraping next category/test
        self.goToQuestionBankSite()


    async def _getQuestionData(self, questionResponse: dict):
        """
        Gets the data for a single question and inserts it into the database.

        Args:
            questionResponse (dict): The response from the get-questions request.

        Returns:
            None
        """
        if 'external_id' not in questionResponse or questionResponse['external_id'] is None:
            await self._getQuestionDataMath(questionResponse)
            return

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
        question = Question(
            questionResponse['questionId'],
            questionResponse['external_id'],
            self.testToString(self.currentTest),
            self.currentCategory,
            questionResponse['primary_class_cd_desc'],
            questionResponse['skill_desc'],
            Main.convertDifficulty(questionResponse['difficulty']),
            response['stimulus'] if 'stimulus' in response else "",
            response['stem'],
            response['answerOptions'],
            response['correct_answer'][0],
            response['rationale']
        )

        if debug:
            print(f"Got {question.id} from {self.currentTest} {self.currentCategory}")

        await databaseInsert(question)

        # with open('questions.txt', 'a') as f:
        #     json.dump(response, f)
        #     f.write(',\n')

        del self.driver.requests

    async def _getQuestionDataMath(self, questionResponse: dict):
        script = f"""
            let xhr = new XMLHttpRequest();
            xhr.open('GET', 'https://saic.collegeboard.org/disclosed/{questionResponse['ibn']}.json', false);
            xhr.send();
        """
        if debug:
            print(script)
        self.driver.execute_script(script)

        request = self.driver.wait_for_request(f"{questionResponse['ibn']}.json")
        data = request.response.body
        if request.response.headers['Content-Encoding'] == 'gzip':
            data = gzip.decompress(request.response.body)
        response = json.loads(data.decode('utf-8'))[0]

        answer = ""
        answer_choices = ""
        if response['answer']['style'] == "Multiple Choice":
            answer = response['answer']['correct_choice'] if 'correct_choice' in response['answer'] else re.search(r"Choice (.) is correct\.", response['answer']['rationale'])[0]
            answer_choices = response['answer']['choices']
        else:
            ans = re.search(r"([1-9]*)\.", response['answer']['rationale'])
            if ans:
                answer = ans[0]

        question = Question(
            questionResponse['questionId'],
            questionResponse['ibn'],
            self.testToString(self.currentTest),
            self.currentCategory,
            questionResponse['primary_class_cd_desc'],
            questionResponse['skill_desc'],
            Main.convertDifficulty(questionResponse['difficulty']),
            response['body'] if 'body' in response else "",
            response['prompt'] if 'prompt' in response else "",
            answer_choices,
            answer,
            response['answer']['rationale']
        )

        await databaseInsert(question)

        # with open('questions.txt', 'a') as f:
        #     json.dump(response, f)
        #     f.write(',\n')

        del self.driver.requests

    def convertDifficulty(difficulty: str):
        if difficulty == "H":
            return "Hard"
        elif difficulty == "M":
            return "Medium"
        elif difficulty == "E":
            return "Easy"

    def testToString(self, test: str):
        if test == "99":
            return "SAT"
        elif test == "100":
            return "PSAT 10/11"
        elif test == "102":
            return "PSAT 8/9"


class Question:
    def __init__(self,
        question_id: str,
        external_id: str,
        test: str,
        category: str,
        domain: str,
        skill: str,
        difficulty: str,
        details: str,
        question: str,
        answer_choices: dict,
        answer: str,
        rationale: str
    ):
        """
        Initializes a new Question object.

        Args:
            id (str): The id of the question.
            external_id (str): The external id or ibn number of the question.
            test (str): The test the question belongs to.
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
        self.question_id = question_id
        self.id = external_id
        self.test = test
        self.category = category
        self.domain = domain
        self.skill = skill
        self.difficulty = difficulty
        self.details = details
        self.question = question
        self.answer_choices = answer_choices
        self.answer = answer
        self.rationale = rationale


async def connectToDatabase():
    """
    Initializes the database connection and creates the table if it doesn't exist.

    This creates a connection to the SQLite database file `questions.db` and
    creates a table `sat_questions` if it doesn't exist. The table has the
    following columns:
    - `questionId`: A unique identifier for the question.
    - `id`: The external id or ibn number of the question.
    - `test`: The test the question belongs to.
    - `category`: The category of the question (reading, writing, math).
    - `domain`: The domain of the question.
    - `skill`: The skill of the question.
    - `difficulty`: The difficulty of the question.
    - `details`: The extra details given with the question.
    - `question`: The text of the question.
    - `answer_choices`: The answer choices.
    - `answer`: The correct answer.
    - `rationale`: The explanation for the answer.

    A unique index is created on the `id` column to ensure that each question
    has a unique identifier.
    """
    global connection, cursor
    connection = await asqlite.connect('questions.db')
    cursor = await connection.cursor()

    await cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sat_questions (
            questionId TEXT PRIMARY KEY NOT NULL UNIQUE,
            id TEXT NOT NULL,
            test TEXT NOT NULL,
            category TEXT NOT NULL,
            domain TEXT NOT NULL,
            skill TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            details TEXT,
            question TEXT NOT NULL,
            answer_choices TEXT,
            answer TEXT NOT NULL,
            rationale TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS dupeCheckIndex ON sat_questions (questionId);
    """)

async def databaseInsert(question: Question):
    """
    Inserts a single question into the database.

    Args:
        question (Question): The question to insert.
    """
    try:
        await cursor.execute("""
            INSERT INTO sat_questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            question.question_id,
            question.id,
            question.test,
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
        await connection.commit()
    except Exception as e:
        print(e)

async def databaseIsDuplicate(questionId: str):
    res = await cursor.execute("""
        SELECT COUNT(*) FROM sat_questions WHERE questionId = ?;
    """, (questionId,))

    count = await res.fetchone()
    return count[0] > 0

async def main():
    runner = Main()
    runner.goToQuestionBankSite()
    for test in (SAT, PSAT11_10, PSAT8_9):
        await runner.getQuestionsForTest(test)
    await connection.close()

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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(connectToDatabase())
    loop.run_until_complete(main())

    print("Done!")