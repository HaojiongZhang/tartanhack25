import logging
import ollama
import re
from config import OLLAMA_MODEL, OLLAMA_SERVER_URL
from json_repair import json_repair
import json

def remove_think_tags(text):
    """
    Remove any content enclosed within <think>...</think> tags.

    Args:
        text (str): The input text containing <think> tags.

    Returns:
        str: The cleaned text without <think> tag content.
    """
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def summarize_text(text):
    """
    Summarize the provided text using the Ollama server.

    Args:
        text (str): The text to summarize.

    Returns:
        str or None: The summarized text, or None if an error occurs.
    """
    try:
        # Remove <think> tag content
        
        
        # Create an Ollama client with the specified server URL
        client = ollama.Client(host=OLLAMA_SERVER_URL)
        
        # Define the prompt for summarizing
        prompt = f"""Please analyze this 10K filing and extract all the useful info into easy to read nuance points, highlight significant numbers. The input: {text}"""
        
        # Generate a response using the specified model
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)

        # Ensure the response contains 'response' key
        if 'response' not in response:
            logging.error("Error: Missing 'response' key in Ollama response")
            return None
        
        # Extract the generated text from the response
        summary = response['response']
        summary = remove_think_tags(summary)
        return summary.strip()
    except Exception as e:
        logging.error("Error calling the Ollama server: %s", e)
        return None

def summarize_dispute(text):
    """
    Summarize the provided text using the Ollama server.

    Args:
        text (str): The text to summarize.

    Returns:
        str or None: The summarized text, or None if an error occurs.
    """
    try:
        # Remove <think> tag content
        
        
        # Create an Ollama client with the specified server URL
        client = ollama.Client(host=OLLAMA_SERVER_URL)
        
        # Define the prompt for summarizing
        prompt = f"""Given the following analysis report of a company's employment-related legal matters,
provide a summary of the company's employment dipute and relevant suggestion on a job hunter's
applicant towards the company.
Note that the total cases is based on 2 year history and the recent case range is one year. {text}"""
        
        # Generate a response using the specified model
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)

        # Ensure the response contains 'response' key
        if 'response' not in response:
            logging.error("Error: Missing 'response' key in Ollama response")
            return None
        
        # Extract the generated text from the response
        summary = response['response']
        summary = remove_think_tags(summary)
        return summary.strip()
    except Exception as e:
        logging.error("Error calling the Ollama server: %s", e)
        return None
    
def generate_structured_output(prompt):
    """
    Generate structured JSON output using the Ollama server and repair the JSON if necessary.

    Args:
        prompt (str): The prompt for generating structured output.

    Returns:
        dict or None: The structured output as a Python dictionary, or None if an error occurs.
    """
    try:
        # Remove <think> tag content
        prompt = remove_think_tags(prompt)
        
        # Create an Ollama client with the specified server URL
        client = ollama.Client(host=OLLAMA_SERVER_URL)
        
        # Generate a response using the specified model
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)
        
        # Ensure the response contains 'response' key
        if 'response' not in response:
            logging.error("Error: Missing 'response' key in Ollama response")
            return None
        
        # Extract the generated output from the response
        output = response['response']
        
        # Repair the JSON output in case it's malformed
        repaired_json = json_repair(output)
        
        # Parse the repaired JSON string into a Python dictionary
        structured_output = json.loads(repaired_json)
        
        return structured_output
    except Exception as e:
        logging.error("Error generating structured output: %s", e)
        return None