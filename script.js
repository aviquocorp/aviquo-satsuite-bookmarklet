let questions = [];

var id = [];
var assessment = [];
var test = [];
var domain = [];
var skill = [];
var difficulty = [];
var questionParagraph = [];
var questionStatement = [];
var a = [];
var b = [];
var c = [];
var d = [];
var answer = [];
var explanation = [];

// First we need to get the ID of the Table
const table = document.getElementById('apricot_table_6').children;
const questionBanner =
  document.getElementsByClassName('question-banner')[0].children;

// Now we get the table off of the current page using the for loop
for (var i = 0; i < table.length; i++) {
  var button = table[i].cells[1].children[0];

  id.push(button.textContent);
  button.click();

  // now that we have the modal open, scrape everything

  /* assessment, test, domain, skill */
  assessment.push(questionBanner[0].children[1].textContent);
  test.push(questionBanner[1].children[1].textContent);
  domain.push(questionBanner[2].children[1].textContent);
  skill.push(questionBanner[3].children[1].textContent);

  // difficulty
  difficulty.push(
    document.getElementsByClassName('question-difficulty')[0].children[1]
      .textContent
  );

  /* question */
  questionParagraph.push(
    document.getElementsByClassName('prompt cb-margin-top-32')[0].textContent
  );

  questionStatement.push(
    document.getElementsByClassName('question cb-margin-top-16')[0].textContent
  );

  /* A B C D */
  const answers = document.getElementsByClassName(
    'answer-choices cb-margin-top-16'
  )[0].children[0].children;

  a.push(answers[0].textContent);
  b.push(answers[1].textContent);
  c.push(answers[2].textContent);
  d.push(answers[3].textContent);

  let q = {
    id: '',
    assessment: '',
    test: '',
    domain: '',
    skill: '',
    difficulty: '',
    question: '',
    answer: '',
    explanation: '',
  };
  let button = table[i].cells[1].children[0];
  q.id = button.textContent;
  button.click();

  // now that we have the modal open, scrape everything
  const questionTable =
    document.getElementsByClassName('question-banner')[0].children;

  for (let j = 0; j < questionTable.length; j++) {
    const column = questionTable[j].children;
    const header = column[0].textContent;
    const val = column[1].textContent;

    switch (header) {
      case 'Assessment':
        q.assessment = val;
        break;
      case 'Test':
        q.test = val;
        break;
      case 'Domain':
        q.domain = val;
        break;
      case 'Skill':
        q.skill = val;
        break;
      case 'Difficulty':
        // difficulty shown here is an svg image
        break;
    }
  }

  const questionText =
    document.getElementsByClassName('question')[0].children[0].children[0];
  q.question = questionText.textContent;

  questions.push(q);
}

console.log(
  'ID,Assessment,Test,Domain,Skill,Difficulty,' +
    'QuestionParagraph,QuestionStatement,A,B,C,D,Answer,Explanation'
);
