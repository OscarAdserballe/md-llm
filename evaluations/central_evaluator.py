from pathlib import Path
from typing import Dict
import click
from termcolor import colored

from config import SUPPORTED_MODELS
from src.llm import LLM
from config_logger import logger

# Define evaluation prompts
EVALUATION_PROMPTS: Dict[str, Dict[str, str]] = {
    "coding": {
        "description": "Generate a Python function to reverse a string.",
        "prompt": "Write a Python function named `reverse_string` that takes a single string argument and returns the string reversed."
    },
    "writing": {
        "description": "Compose a short story opening.",
        "prompt": "Write the opening paragraph of a mystery novel set in Victorian London."
    },
    "math": {
        "description": "Solve a calculus problem.",
        "prompt": "Evaluate the integral of x squared from 0 to 3."
    },
    "summarization": {
        "description": "Summarize a paragraph.",
        "prompt": "Summarize the following paragraph in two sentences: [Insert paragraph here]."
    },
    "general_knowledge": {
        "description": "Explain the Theory of Relativity.",
        "prompt": "Explain the Theory of Relativity in simple terms."
    },
}

# Define the Evaluations directory
EVALUATIONS_DIR = Path("evaluations")

def ensure_evaluations_dir():
    if not EVALUATIONS_DIR.exists():
        EVALUATIONS_DIR.mkdir(parents=True)
        logger.info(f"Created evaluations directory at {EVALUATIONS_DIR.resolve()}")

def ensure_model_dirs():
    for model_name in SUPPORTED_MODELS.keys():
        model_dir = EVALUATIONS_DIR / model_name
        if not model_dir.exists():
            model_dir.mkdir(parents=True)
            logger.info(f"Created directory for model '{model_name}' at {model_dir.resolve()}")

def save_response(model_name: str, prompt_name: str, response: str):
    model_dir = EVALUATIONS_DIR / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    response_file = model_dir / f"{prompt_name}.txt"
    with open(response_file, "w", encoding="utf-8") as f:
        f.write(response)
    logger.info(f"Saved response for prompt '{prompt_name}' under model '{model_name}'.")

@click.command()
@click.option('--models', '-m', multiple=True, help='Specify models to evaluate. If not provided, all supported models are evaluated.')
@click.option('--re-run', is_flag=True, help='Re-run evaluations even if responses already exist.')
def evaluate(models: tuple, re_run: bool):
    """
    Runs evaluation prompts across specified LLM models and saves the responses.
    """
    ensure_evaluations_dir()
    ensure_model_dirs()

    models_to_evaluate = models if models else SUPPORTED_MODELS.keys()

    for model_name in models_to_evaluate:
        if model_name not in SUPPORTED_MODELS:
            print(colored(f"Model '{model_name}' is not supported. Skipping.", "red"))
            logger.warning(f"Model '{model_name}' is not supported. Skipping.")
            continue

        print(colored(f"\nEvaluating model: {model_name}", "cyan", attrs=["bold"]))
        llm_config = SUPPORTED_MODELS[model_name]
        llm = LLM(llm_config=llm_config)
        
        for prompt_key, prompt_detail in EVALUATION_PROMPTS.items():
            prompt_description = prompt_detail["description"]
            prompt_text = prompt_detail["prompt"]

            response_path = EVALUATIONS_DIR / model_name / f"{prompt_key}.txt"
            if response_path.exists() and not re_run:
                print(colored(f"  Skipping '{prompt_key}' (response already exists). Use --re-run to overwrite.", "yellow"))
                logger.info(f"Skipped prompt '{prompt_key}' for model '{model_name}' as response already exists.")
                continue

            print(colored(f"  Running prompt '{prompt_key}': {prompt_description}", "green"))
            messages = [{"role": "user", "content": prompt_text}]
            try:
                response = llm.query(messages=messages)
                save_response(model_name, prompt_key, response)
                print(colored(f"    ✔ Completed '{prompt_key}'.", "green"))
            except Exception as e:
                print(colored(f"    ✖ Error running '{prompt_key}': {e}", "red"))
                logger.error(f"Error running prompt '{prompt_key}' for model '{model_name}': {e}")

    print(colored("\nEvaluation completed.", "green", attrs=["bold"]))
    logger.info("Completed evaluations.")

if __name__ == "__main__":
    evaluate()
