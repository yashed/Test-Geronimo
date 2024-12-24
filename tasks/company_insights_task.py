from crewai import Task
from agents.company_insights_agent import company_insights_agent

company_insights_task = Task(
    description="Generate company overview, competitors, and news summary.",
    agent=company_insights_agent,
    input_data={
        "company_data": "{web_scrape_task.output}",
        "competitor_data": "{fetch_google_results_task.output}",
    },
    expected_output="A detailed company overview, including information on competitors and recent news."  # Add expected output
)
