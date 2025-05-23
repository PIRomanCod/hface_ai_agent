import os
import uuid
import gradio as gr
import requests
import pandas as pd
import time
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Tuple

from dotenv import load_dotenv
from agents.gemini_agent import EnhancedGAIAAgent
from agents.openai_agent import EnhancedOpenAIAgent

load_dotenv()

# --- Constants ---
DEFAULT_API_URL = "https://agents-course-unit4-scoring.hf.space"

# --- Agent Loader ---
AGENT_CLASSES = {
    "Gemini Agent": EnhancedGAIAAgent,
    "OpenAI Agent": EnhancedOpenAIAgent,
}

OPEN_API_KEY = os.getenv("OPEN_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_KEY = os.getenv("HF_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")



def load_questions_from_file(file_path: str = "questions.json") -> Tuple[str, List[Dict]]:
    """
    Load questions from a local JSON file in the root of the project.

    Args:
        file_path (str): Path to the JSON file with questions.

    Returns:
        Tuple[str, List[Dict]]: Message and a list of question dictionaries.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' not found.", []

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return "Error: JSON format is invalid. Expected a list of question objects.", []

        # Validate expected keys in at least one item
        required_keys = {"task_id", "question", "file_name"}
        if not all(required_keys.issubset(q) for q in data):
            return "Error: Some questions are missing required fields.", []

        print(f"Loaded {len(data)} questions from file.")
        return data

    except json.JSONDecodeError as e:
        return f"Error decoding JSON: {e}", []
    except Exception as e:
        return f"Unexpected error: {e}", []

        
# --- Evaluation Runner ---
def run_and_submit_all(selected_agent_name: str, profile: gr.OAuthProfile | None):
    if selected_agent_name == "Gemini Agent":
        agent = EnhancedGAIAAgent(api_key=GOOGLE_API_KEY)
    elif selected_agent_name == "OpenAI Agent":
        agent = EnhancedOpenAIAgent(api_key=OPEN_API_KEY)
   
    else:
        raise ValueError(f"Unknown agent: {selected_agent_name}")


    username = profile.username
    print(f"User logged in: {username}")

    api_url = DEFAULT_API_URL
    questions_url = f"{api_url}/questions"
    submit_url = f"{api_url}/submit"
    file_download_url = f"{api_url}/files"
    
    space_id = os.getenv("SPACE_ID")
    agent_code = f"https://huggingface.co/spaces/{space_id}/tree/main" if space_id else "N/A"

    # Fetch Questions
    print(f"Fetching questions from: {questions_url}")
    try:
        response = requests.get(questions_url, timeout=35)
        if response.status_code == 429:
            print("Received 429 Too Many Requests. Falling back to local file.")
            questions_data = load_questions_from_file()
        else:
            response.raise_for_status()
            questions_data = response.json()

        if not questions_data:
            return "Fetched questions list is empty or invalid format.", None
        print(f"Fetched {len(questions_data)} questions.")
    except Exception as e:
        print(f"Error fetching questions: {e}")
        return f"Error fetching questions: {e}", None

    # Run Agent
    results_log = []
    answers_payload = []
    print(f"Running agent on {len(questions_data)} questions...")

    for item in questions_data:
        task_id = item.get("task_id")
        question_text = item.get("question")
        file_name = item.get("file_name")
        file_path = None
    
        if not task_id or question_text is None:
            print(f"Skipping item with missing task_id or question: {item}")
            continue
    
        if file_name:
            file_url = f"{file_download_url}/{task_id}"
            try:
                print(f"Downloading associated file for task {task_id}...")
                file_response = requests.get(file_url, timeout=30)
                file_response.raise_for_status()
    
                file_content = file_response.content
                # Unique new file name generator
                ext = os.path.splitext(file_name)[-1] or ".dat"
                unique_name = f"{task_id}_{uuid.uuid4().hex}{ext}"
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, unique_name)
    
                with open(file_path, "wb") as f:
                    f.write(file_content)
    
                print(f"File for task {task_id} saved to {file_path}")
    
            except Exception as e:
                print(f"Failed to download file for task {task_id}: {e}")
                file_path = None

        try:
            submitted_answer = agent.answer_question(question_text, task_file_path=file_path)
            answers_payload.append({"task_id": task_id, "submitted_answer": submitted_answer})
            results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": submitted_answer})
            time.sleep(10)
    
        except Exception as e:
            print(f"Error running agent on task {task_id}: {e}")
            results_log.append({"Task ID": task_id, "Question": question_text, "Submitted Answer": f"AGENT ERROR: {e}"})
            time.sleep(10)


    if not answers_payload:
        return "Agent did not produce any answers to submit.", pd.DataFrame(results_log)

    # Prepare Submission
    submission_data = {"username": username.strip(), "agent_code": agent_code, "answers": answers_payload}
    print(f"Submitting {len(answers_payload)} answers...")

    # Submit
    try:
        response = requests.post(submit_url, json=submission_data, timeout=60)
        response.raise_for_status()
        result_data = response.json()
        final_status = (
            f"Submission Successful!\n"
            f"User: {result_data.get('username')}\n"
            f"Overall Score: {result_data.get('score', 'N/A')}% "
            f"({result_data.get('correct_count', '?')}/{result_data.get('total_attempted', '?')} correct)\n"
            f"Message: {result_data.get('message', 'No message received.')}"
        )
        print("Submission successful.")
        results_df = pd.DataFrame(results_log)
        return final_status, results_df
    except Exception as e:
        print(f"Error during submission: {e}")
        return f"Submission failed: {e}", pd.DataFrame(results_log)


# --- Build Gradio Interface ---
with gr.Blocks() as demo:
    gr.Markdown("# Basic Agent Evaluation Runner")

    agent_selector = gr.Dropdown(
        choices=["Gemini Agent", "OpenAI Agent"],             
        label="Choose Agent to Run",
        value="OpenAI Agent"
    )
  
    gr.LoginButton()

    run_button = gr.Button("Run Evaluation & Submit All Answers")

    status_output = gr.Textbox(label="Run Status / Submission Result", lines=5, interactive=False)
    results_table = gr.DataFrame(label="Questions and Agent Answers", wrap=True)

    run_button.click(
        fn=run_and_submit_all,
        inputs=[agent_selector],
        outputs=[status_output, results_table]
    )

if __name__ == "__main__":
    print("\nLaunching Gradio Interface...")
    demo.launch(debug=True, share=False)