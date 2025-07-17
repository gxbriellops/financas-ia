from agno.agent import Agent, RunResponse  # noqa
from agno.models.groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
groq_api = os.getenv('GROQ_API_KEY')


agent = Agent(model=Groq(id="llama-3.3-70b-versatile"), markdown=True)

# Get the response in a variable
# run: RunResponse = agent.run("Share a 2 sentence horror story")
# print(run.content)

# Print the response on the terminal
agent.print_response("Quem foi o pior presidente do Brasil?")