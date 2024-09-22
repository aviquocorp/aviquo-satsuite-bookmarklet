var id = [];
var assessment = [];
var test = [];
var domain = [];
var skill = [];
var difficulty = [];
var question = [];
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
    
} 


console.log("ID,Assessment,Test,Domain,Skill,Difficulty," + 
    "QuestionParagraph,QuestionStatement,A,B,C,D,Answer,Explanation")
