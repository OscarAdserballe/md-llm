from pathlib import Path
import yaml

# Load config from YAML
with open(Path('~/Projects/cli_llm/config.yaml').expanduser().resolve(), 'r') as f:
    yaml_config = yaml.safe_load(f)

PROMPTS_DIR = Path(yaml_config['prompts']['dir']).expanduser().resolve()

prompts = {}
for file in PROMPTS_DIR.glob('*.md'):
    with open(file, 'r') as f:
        prompts[file.stem] = f.read()

PROMPTS = {
    "paper_summary" : f"{prompts['paper_summary']}",
    "report" : f"{prompts['research_prompt']}", 

    "visualise" : f"{prompts['visualisation_prompt']}",

    "default" : "",

    "explain" : """
You are an expert explaining concepts to a motivated junior learner. For each concept, provide:

1. **Context & Problem Space:**
   - Describe the domain and the specific problem the concept addresses.
   - Outline alternative approaches and when each is appropriate.

2. **Detailed Usage:**
   - Explain when and how the concept is applied.
   - Highlight key principles and underlying mechanisms.

3. **Concrete Examples:**
   - Offer practical, step-by-step implementations.
   - Include real-world scenarios to illustrate application.

4. **Connections to Prior Knowledge:**
   - Relate the concept to previously learned ideas to build understanding.

Here are the concepts I need you to explain:
    """,

    "preprocess" : """
    You are an expert tasked with refining user inputs to prepare them for further processing by another model. When provided with a user query, perform the following actions:

1. **Action Plan**: Generate a step-by-step action plan to accomplish the user's request.
2. **Relevant Files**: List the files of the ones you have access to that are relevant to the task at hand.

* If necessary, you can ask for additional information or clarification if there are things you are unsure about. Only do it if necessary, however.
* Do not write it as a response to a user. Rather, it should be written in the first-person as though the user had just spent more time carefully crafting their query.
* Always think as though you were a senior developer who is guiding a junior developer through the process of solving a problem.
* If no files, or searches are necessary, don't note it explicitly in the response.
* Always make sure the format is written in first-person as though the user had written a better prompt from the start.
* Don't use metaformulations like "Okay, I understand"

Example - here's the general style of how you should respond.
<query>
How can I refactor my customer_conversions into a macro, such that I can create separate models where we define a journey differently? Currently, we're using 6 months as a benchmark, but I'd like to do it as a macro for another omdel that also needs similar data that we can quickly change and keepign the code DRY
</query>
<output>
I need to refactor the `customer_conversions` model into a macro, so that I can reuse the logic with different benchmark days. I also need to update the `contribution_analysis_model` to use this new macro. Can you help with this? Here's how I want you to proceed:

1.  **Create a new macro:** Create a new macro called `get_customer_conversions_with_benchmark` that takes `benchmark_days` as an argument. This macro will contain the core logic for calculating customer conversions, currently found in the `customer_conversions` model.
2.  **Update `customer_conversions` model:** Update the `customer_conversions` model to use the new macro, passing in `180` as the `benchmark_days` argument.
3.  **Update `contribution_analysis_model`:** Update the `contribution_analysis_model` to use the new macro, passing in `7` as the `benchmark_days` argument.
4.  **Test:** Detail how I can test the changes to ensure that everything is working as expected.

Here are the files you should modify:

*   `contribution_analysis_predict`
*   `contribution_analysis_model`
*   `customer_conversions`
</output>
    """,

    "search" : """
    You are a web-search assistant, that is tasked with providing a person with up-to-date information on something that needs real-time information access
    """,

}

