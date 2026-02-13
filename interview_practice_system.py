from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel, Field

groq_llm = LLM(
    model="groq/llama-3.1-8b-instant",
    temperature=0.2,
    max_tokens=300
)

class QuestionAnswerPair(BaseModel):
    question: str = Field(...)
    correct_answer: str = Field(...)

company_researcher = Agent(
    role="Company Researcher",
    goal="Create interview topic",
    backstory="Expert interviewer.",
    llm=groq_llm,
    verbose=False,
)

question_creator = Agent(
    role="Question Creator",
    goal="Create one technical question with answer",
    backstory="Senior interviewer.",
    llm=groq_llm,
    verbose=False,
)

answer_evaluator = Agent(
    role="Answer Evaluator",
    goal="Evaluate if answer is correct",
    backstory="Technical reviewer.",
    llm=groq_llm,
    verbose=False,
)

followup_creator = Agent(
    role="Follow-up Creator",
    goal="Create one follow-up question",
    backstory="Interview expert.",
    llm=groq_llm,
    verbose=False,
)

def company_task(company, role, difficulty):
    return Task(
        description=f"Create one {difficulty} interview topic for {role} at {company}.",
        expected_output="Short topic",
        agent=company_researcher,
    )

def question_task(difficulty):
    return Task(
        description=f"Create ONE {difficulty} technical question with a short correct answer.",
        expected_output="Question and answer",
        output_pydantic=QuestionAnswerPair,
        agent=question_creator,
    )

def evaluation_task(question, user_answer, correct_answer):
    return Task(
        description=f"""
Question: {question}
User Answer: {user_answer}
Correct Answer: {correct_answer}

Reply ONLY:
Correct: Yes/No
Missing: short
""",
        expected_output="Short evaluation",
        agent=answer_evaluator,
    )

def followup_task(question, role, difficulty):
    return Task(
        description=f"Create ONE follow-up {difficulty} question for {role} based on: {question}",
        expected_output="Follow-up Q&A",
        output_pydantic=QuestionAnswerPair,
        agent=followup_creator,
    )

def preparation_crew(company, role, difficulty):
    return Crew(
        agents=[company_researcher, question_creator],
        tasks=[
            company_task(company, role, difficulty),
            question_task(difficulty),
        ],
        process=Process.sequential,
        verbose=False,
    )

def evaluation_crew(question, user_answer, correct_answer):
    return Crew(
        agents=[answer_evaluator],
        tasks=[evaluation_task(question, user_answer, correct_answer)],
        process=Process.sequential,
        verbose=False,
    )

def followup_crew(question, role, difficulty):
    return Crew(
        agents=[followup_creator],
        tasks=[followup_task(question, role, difficulty)],
        process=Process.sequential,
        verbose=False,
    )

def run_cli():
    company = "Google"
    role = "Data Scientist"
    difficulty = "easy"

    prep = preparation_crew(company, role, difficulty).kickoff()
    qa = prep.pydantic

    print("\nQuestion:")
    print(qa.question)

    user_answer = input("\nYour answer: ")

    eval_result = evaluation_crew(
        qa.question, user_answer, qa.correct_answer
    ).kickoff()

    print("\nEvaluation:")
    print(eval_result)

    followup = followup_crew(qa.question, role, difficulty).kickoff()
    fqa = followup.pydantic

    print("\nFollow-up Question:")
    print(fqa.question)

    user_answer_2 = input("\nYour answer: ")

    followup_eval = evaluation_crew(
        fqa.question, user_answer_2, fqa.correct_answer
    ).kickoff()

    print("\nFollow-up Evaluation:")
    print(followup_eval)

def initialize_preparation_crew(company, role, difficulty):
    return preparation_crew(company, role, difficulty)

def evaluate_answer(question, user_answer, correct_answer):
    return evaluation_crew(question, user_answer, correct_answer).kickoff()

if __name__ == "__main__":
    run_cli()
