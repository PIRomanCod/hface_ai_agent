from typing import List, Dict, Any, Optional

import re

from langchain_experimental.tools.python.tool import PythonREPLTool

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
import google.generativeai as genai
from langchain.tools import BaseTool
from tools import (
    audio_transcriber,
    extract_text_from_image,
    read_csv_file,
    read_excel_file,
    analyze_youtube_video,
    search_web,
    search_wikipedia,
    fix_reversed_text,
    chess_board_recognition,
    arvix_search,
    read_file,
)
from langchain.agents import initialize_agent, AgentType
from google.api_core.exceptions import ResourceExhausted
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type


class EnhancedGAIAAgent:
    def __init__(
        self,
        api_key: str,
        temperature: float = 0.1,
        additional_tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        verbose: bool = True
    ):
        self.verbose = verbose
        self._setup_models(api_key, temperature)
        self._setup_tools(additional_tools)
        self._setup_system_prompt(system_prompt)
        self._setup_memory()


    def answer_question(self, question: str, task_file_path: Optional[str] = None) -> str:
        """
        Answer a question using the Gemini model and available tools.
        
        Args:
            question: The question to answer
            task_file_path: Optional path to a task file
            
        Returns:
            The answer to the question
        """
        try:
            context_info = ""
            if task_file_path:
                context_info = f"\nAttached file path: {task_file_path}\n"

            prompt = question + context_info
            
            agent_kwargs = {"system_message": self.system_prompt} if self.system_prompt else {}
            agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
                verbose=self.verbose,
                memory=self.memory,
                agent_kwargs={"system_message": self.system_prompt} 
            )
            
            response = self._run_agent_with_retry(agent, prompt)
            return self._clean_answer(response)
            
        except Exception as e:
            if self.verbose:
                print(f"Error answering question: {str(e)}")
            return f"Error: {str(e)}"

    def _setup_models(self, api_key: str, temperature: float):
        """Set up the Gemini model."""
        genai.configure(api_key=api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  #  "gemini-1.5-pro-002"  "gemini-2.0-flash"
            temperature=temperature,
        )

        # === Retry with delay ===
    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_fixed(20),  # Wait 20 seconds
        stop=stop_after_attempt(5)  # 5 try
    )
    def _run_agent_with_retry(self, agent, prompt: str) -> str:
        return agent.run(prompt)
        

    def _setup_tools(self, additional_tools: Optional[List[BaseTool]]):
        """Set up the available tools."""
        self.tools = [
            PythonREPLTool(),
            analyze_youtube_video,
            extract_text_from_image,
            read_csv_file,
            read_excel_file,
            search_web,
            search_wikipedia,
            fix_reversed_text,
            arvix_search,
            read_file,
            chess_board_recognition,
            audio_transcriber,
        ]
        if additional_tools:
            self.tools.extend(additional_tools)

    def _setup_system_prompt(self, system_prompt: Optional[str]):
        """Set up the system prompt."""
        self.system_prompt = system_prompt or """
            You are a general AI assistant.
            
            You MUST ONLY reply in the following format:
            FINAL ANSWER: [your final answer]
            
            Do NOT explain, do NOT describe your reasoning or tool usage.
            Use tools silently if needed.
            
            ---
            
            FORMAT RULES ONLY:
            - For numbers: 1234 (no commas, no units unless explicitly asked)
            - For currency: $1234 (use dollar sign only if asked)
            - For strings: paris (no articles, no abbreviations, lowercase)
            - For lists: 1234,paris,5678,london (follow rules above for each item)
            - For cities: Saint Petersburg
            
            If you do NOT know the answer or cannot solve the task using the tools:
            FINAL ANSWER: I have no tools for this task
            
            ---
            
            TOOLS USAGE ORDER:
            
            1. TABLE FILES
               - Use `read_csv_file` for .csv
               - Use `read_excel_file` for .xls or .xlsx
               
            2. Use 'analyze_youtube_video' for youtube tasks

            3. SEARCH
               - Use `search_wikipedia` for:
                   • Named entities
                   • Historical facts, definitions, biographical data
                   • Concise and structured knowledge
               - Use `search_web` only if Wikipedia fails:
                   • For recent events, niche topics, public discourse
               - Use `arxiv_search` for:
                   • Academic/scientific topics (AI, math, physics, etc.)
                   • Peer-reviewed papers, technical analysis
            
            4. CODE
               - Use `PythonInterpreterTool()` to execute or analyze code
            
            5. AUDIO
               - Use 'audio_transcriber' for .mp3 or other sound files
            
            6. IMAGES
               - Use `extract_text_from_image` for .jpg, .jpeg, or .png
            
            7. CHESS
               - Use `chess_board_recognition`
               - Each given picture is an 8*8 field with chess
               - Return the position ONLY in algebraic notation
            
            8. OTHER TOOLS
               - Use silently when clearly appropriate
                        
            GENERAL INSTRUCTIONS:
            - Prefer tool use over assumptions.
            - If the answer is obvious/common knowledge, reply directly using FINAL ANSWER.
            - After using tools, summarize the result as the final answer (concise format).
            - For lists, select only the objects specified in the task, do not add any speculation.
            - Avoid quotations in your answers, only answer the question directly asked.
            """

    def _prepare_prompt(self, question: str) -> str:
        """
        Prepare the prompt for the model.
        
        Args:
            question: The question to answer
            
        Returns:
            The prepared prompt
        """
        prompt = self.system_prompt + "\n\n"
        prompt += f"Question: {question}\n\n"
        
        return prompt

    def _setup_memory(self):
        """Set up the conversation memory."""
        self.memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        input_key="input",
        output_key="output"
    ) 

    def _clean_answer(self, answer: any) -> str:
        """
        Clean up the answer to match the required format.
        Extracts the final answer from the model's response.
        
        Args:
            answer: The raw answer from the model
            
        Returns:
            The cleaned final answer as a string
        """
        # Handle different response formats
        if hasattr(answer, 'content'):
            answer = answer.content
        elif isinstance(answer, dict):
            if 'content' in answer:
                answer = answer['content']
            else:
                answer = str(answer)
        elif not isinstance(answer, str):
            answer = str(answer)
            
        # Remove any metadata or additional kwargs
        answer = re.sub(r'additional_kwargs={.*?}', '', answer)
        answer = re.sub(r'response_metadata={.*?}', '', answer)
        answer = re.sub(r'id=\'.*?\'', '', answer)
        answer = re.sub(r'usage_metadata={.*?}', '', answer)
        
        # Extract the FINAL ANSWER if present
        final_answer_match = re.search(r'FINAL ANSWER:\s*(.*?)(?:\n|$)', answer, re.IGNORECASE)
        if final_answer_match:
            answer = final_answer_match.group(1).strip()
        else:
            # If no FINAL ANSWER found, try to extract the last line that looks like an answer
            lines = answer.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith(('The answer is', 'Answer:', 'Final answer:', 'The result is')):
                    answer = line
                    break

        # Remove any remaining prefixes or formatting
        prefixes_to_remove = [
            "The answer is ",
            "Answer: ",
            "Final answer: ",
            "The result is ",
            "To answer this question: ",
            "Based on the information provided, ",
            "According to the information: ",
        ]

        for prefix in prefixes_to_remove:
            if answer.startswith(prefix):
                answer = answer[len(prefix):].strip()

        # Remove quotes if they wrap the entire answer
        if (answer.startswith('"') and answer.endswith('"')) or (answer.startswith("'") and answer.endswith("'")):
            answer = answer[1:-1].strip()

        # Final cleanup
        answer = answer.strip()
        
        return answer

    