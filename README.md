# AEPIL1-Assignment
Andela GenAI First Assignment
This repo provides the a simple way for an ecommerce service to utilize AI to query their customer service for complaints and get answers.
The purpose is to reduce the time spent attending to customer complaint and improve customer experience.

Project Setup Instructions
1. Open your command terminal
2. Clone the repo in your directory of choice by running the git command `git clone https://github.com/nwubni/AEPIL1-Assignment.git`
3. Next, run `cd AEPIL1-Assignment` to change into the project's root directory.
4. Next, create a virtual environment to isolate the project's dependencies by running `python3 -m venv .venv`. After creating the virtual evironment, activate it with the following command `source .venv/bin/activate`
4. Next, run `pip install -r requirements.txt` to install the dependencies. The dependencies include openai to use OpenAI models to process user prompts.

Running the application
Here is the format for running the application:
`python3 app/endpoint.py query`
Example `python3 app/endpoint.py "What payment options do you have?"`


Setup, environment variables, run commands, how to reproduce metrics, known limitations.


Testing
- Uses Pytest