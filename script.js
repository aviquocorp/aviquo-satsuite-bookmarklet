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
const table = document.getElementById("apricot_table_6").children;
const questionBanner = document.getElementsByClassName("question-banner")[0].children;

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
        document.getElementsByClassName("question-difficulty")[0]
        .children[1].textContent);

    /* question */
    questionParagraph.push(
        document.getElementsByClassName("prompt cb-margin-top-32")[0].textContent);

    questionStatement.push(
        document.getElementsByClassName("question cb-margin-top-16")[0].textContent);

    /* A B C D */
    const answers = document.getElementsByClassName("answer-choices cb-margin-top-16")
            [0].children[0].children;

    a.push(answers[0].textContent);
    b.push(answers[1].textContent);
    c.push(answers[2].textContent);
    d.push(answers[3].textContent);

    /* answer */
    answer.push(document.getElementsByClassName("correct-answer")
        [0].children[1].textContent);

    explanation.push(document.getElementsByClassName("rationale")
        [0].children[1].textContent);


    // we got all the info, close the modal
    document.getElementsByClassName("cb-btn cb-btn-square cb-btn-close")[0].click();
} 


console.log("ID,Assessment,Test,Domain,Skill,Difficulty," + 
    "QuestionParagraph,QuestionStatement,A,B,C,D,Answer,Explanation")
