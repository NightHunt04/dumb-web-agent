import os
import asyncio
import json
from dotenv import load_dotenv
from src.browser import Browser
from src.models.gemini import GeminiProvider
from src.models.groq import GroqProvider
from src.agent.agent import Agent
load_dotenv()

async def main():
    gemini_model = GeminiProvider(api_key=os.getenv('GOOGLE_API_KEY'))
    # groq_model = GroqProvider(api_key=os.getenv('GROQ_API_KEY'))

    schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "name of the model or tool"
            },
            "rate_limit": {
                "type": "string",
                "description": "rate limit of the model or tool"
            },
            "description": {
                "type": "string",
                "description": "description of the model or tool"
            },
            "parameters": {
                "type": "array",
                "description": "parameters of the model or tool",
                "items": {
                    "type": "string",
                    "description": "name of the parameter"
                }
            },
            "method": {
                "type": "string",
                "description": "method of the model or tool"
            }
        },
        "required": ["name", "rate_limit", "description", "parameters", "method"]
    }

    ws_endpoint = "wss://dumb-cdp.onrender.com/dumb-cdp"
    browser = Browser(headless=False)
    agent = Agent(browser=browser, model=gemini_model, scraper_response_json_format=schema)
    # prompt = """go to https://www.glassdoor.co.in/Job/india-ai-engineer-jobs-SRCH_IL.0,5_IN115_KO6,17.htm,
    # scrape title, comapny name, location, description of the job, handle unlimited scrolling to load more jobs,
    # scroll and scrape until you see load more jobs button
    # """
    prompt = """go to https://api.kastg.xyz/ai,
    scrape name, rate limit, description, parameters, method of the models,
    click on Search button, then scrape that page,
    finally click on Tools button, then scrape that page
    """
    # prompt = """go to https://summerofcode.withgoogle.com/programs/2025/projects,
    # scrape title, contributor, mentors, organization, title, description of the project,
    # handle pagination by clicking on the Next Page button, handle upto 3 pages of scraping
    # """

    # memory = agent.get_memory()
    # print(memory)

    # response = await agent.replay_session(
    #     "08345dad-4893-4956-985e-303d4738bf24", 
    #     verbose=True, 
    #     wait_between_actions=0,
    #     screenshot_each_step=True
    # )

    response = await agent.arun(
        query=prompt, 
        verbose=True,
        wait_between_actions=0,
    )
    print(response)

    with open('browserless-kastg-test-groq.json', 'w', encoding='utf-8') as f:
        json.dump(response, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())








 # response = await agent.arun(
        #     "go to https://api.kastg.xyz/ai, and then from the table of data, give me those models which are for text generation or llm", 
        # )
        # response = await agent.arun("go to https://www.ycombinator.com/companies, select the batch of Summer 2025 and Winter 2025, scroll down 2 times to load more companies, then scrape those company details including the company name, location, description, logo url, and tags, the output should be in json format", verbose=True)
        # response = await agent.arun("go to https://playwright.dev/python/docs/intro, then click on Pages section, and give me summary of it")
        # response = await agent.arun("go to https://www.glassdoor.co.in/Job/index.htm, in job search, write software engineer, in city enter India and then press 'Enter' key from keyboard, then scrape all the jobs details including the job title, company name, location, salary, the output should be in json format, also scroll down upto end for loading more jobs, scroll maximum down height for loading more jobs or there might be a button to load more jobs, scroll until no new jobs are loaded, this will be getting dynamic content", verbose=True)
        # response = await agent.arun("go to https://www.linkedin.com/jobs/search?position=1&pageNum=0, in jobs search AI Engineer, and in location write India (erase any previous location by first clicking on x button in location as it is already filled), then search, then scroll down to load more jobs, then scrape all the jobs details including the job title, company name, location, salary, job role, there will be lots of jobs, scrape all of them, the output should be in json format, at the end if you see load more jobs button then click on it (click only one time if you see, and dont click again), and continue to scrape once more")
        # response = await agent.arun("go to amazon and search for 'laptop under the price rupees 50000' directly into the search bar and scroll down to load more laptops, then scrape all the laptop details including the laptop name, price, rating, number of reviews, and image url, the output should be in json format, also handle the pagination buttons, scrape about 3 pages by clicking on the pagination buttons down below")
        # response = await agent.arun("go to https://en.wikipedia.org/wiki/Elon_Musk, then tell me when was elon musk born and what was the the name of his younger sister")
        # response = await agent.arun("go to perplexity.ai and search for 'what is the best way to learn python', wait for a while until it generates response, then scrape the output it generates")
        # response = await agent.arun("go to https://www.google.com/recaptcha/api2/demo, the fields are already filled, click on I'm not a robot checkbox and then click submit button")
       
        # response = await agent.arun("""go to https://www.coursera.org/professional-certificates/meta-data-analyst, 
        # scrape the title of the course, description, also scrape the number of course series, the rating, the level, 
        # time to complete it, what will learn, then click on the Courses button you will find down, which will scroll 
        # you down to the Courses section, there you will see the course series, it will be like accordian, click on each 
        # caret like to open it and scrape and scroll down to scrape below ones as well""", verbose=True)

        # batch = [
        #     'https://www.coursera.org/learn/data-literacy-what-is-it-and-why-does-it-matter',
        #     'https://www.coursera.org/learn/data-science-ethics',
        #     'https://www.coursera.org/learn/google-drive',
        #     'https://www.coursera.org/learn/digital-transformation-google-cloud',
        #     'https://www.coursera.org/learn/process-mining'
        # ]
        # response = await agent.arun(f"""go to these given batches of url:\n {'\n'.join(batch)} and scrape as per given json schema""", verbose=True)

        # response = await agent.arun("go to https://www.glassdoor.co.in/Job/index.htm, in job search, write software engineer, in city enter India and then press 'Enter' key from keyboard, then keep scrolling to the bottom until you see load more jobs button and click on it, while scrolling if you see same informative elements then know that you need to scroll down again until the show more jobs button appears, scrape all the jobs details including the job title, company name, location", verbose=True)
        # try:
        #     print(json.dumps(response, indent=4))
        # except Exception as e:
        #     print(response)

        # response = await agent.arun("go to chatgpt.com, then in write 'write a poem' in ask anything input, then press enter key, then wait for some time to let it answer, then scrape the answer it gives", verbose=True)


        # response = await agent.arun("go to  https://www.glassdoor.co.in/Job/index.htm, in jobs write 'ai engineer' and in location write 'india' and then press 'Enter' key from keyboard, keep on scroling down bit by bit until you see load more jobs button, then click on it, make sure if any pop ups appear then close it, once loading more jobs, scroll down again until you see load more jobs button again, click on it and then scrape all the jobs details", verbose=True)
        
        
        # response = await agent.arun("go to https://playtictactoe.org/, first play your turn as x, then the bot will do its own turn, before each move get the html and observe and then play, play until the game ends", verbose=True)