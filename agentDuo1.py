import anthropic
import os
from dotenv import load_dotenv
import requests
import openai
from openai import OpenAI

# Load environment variables from a .env file
load_dotenv()

# Define a dictionary to store API keys
api_keys = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY")
}

# Create a dictionary to store API clients
client = {
    "openai": openai.OpenAI(api_key=api_keys["openai"]),
    "anthropic": anthropic.Anthropic(api_key=api_keys["anthropic"])
}


# Define color constants for console output
NEON_GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET_COLOR = '\033[0m'


# Function to open and read a file
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


# Function for Mike's chat using the Anthropic API
def mike_chat(user_input, system_message, memory):
    messages = [
        *memory,
        {
            "role": "user",
            "content": user_input
        }
    ]

    response_text = ""

    with client["anthropic"].messages.stream(
            model="claude-3-opus-20240229",
            max_tokens=300,
            temperature=0.7,
            messages=messages,
            system=system_message,
    ) as stream:
        for text in stream.text_stream:
            response_text += text
            print(NEON_GREEN + text + RESET_COLOR, end="", flush=True)

    response_text = response_text.replace('\\n', '\n')

    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": response_text})

    return response_text


# Function for Annie's chat using the OpenAI API
def annie_chat(user_input, system_message, memory):
    messages = [
        {"role": "system", "content": system_message},
        *memory,
        {"role": "user", "content": user_input}
    ]

    chat_completion = client["openai"].chat.completions.create(
        model="gpt-4-0125-preview",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )

    response_content = chat_completion.choices[0].message.content

    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": response_content})

    return response_content


def main():
    # Get user input for topics and maximum number of messages
    topic1 = input("Enter the topic Mike wants to talk about: ")
    topic2 = input("Enter the topic Annie wants to talk about: ")
    max_range = int(input("Enter the maximum number of messages in the conversation: "))

    # Load system messages for Mike and Annie from text files
    mike_system_message = open_file("mike.txt").replace("<<TPC1>>", topic1)
    annie_system_message = open_file("annie.txt").replace("<<TPC2>>", topic2)

    # Initialize memory for Mike and Annie
    mike_memory = []
    annie_memory = []

    # Get the output file path from the environment variable
    output_file_path = os.getenv("OUTPUT_FILE_PATH")

    # Start the conversation with a friendly "Hello" from Mike
    user_input = "Hello Annie, I'm Mike, lets talk about the freemasons"
    annie_response = annie_chat(user_input, annie_system_message, annie_memory)
    print(YELLOW + annie_response + RESET_COLOR)


    # Start the conversation loop
    for i in range(1, max_range):
        # Mike's turn to respond
        mike_response = mike_chat(annie_response, mike_system_message, mike_memory)
        print(NEON_GREEN + mike_response + RESET_COLOR)


        # Annie's turn to respond
        annie_response = annie_chat(mike_response, annie_system_message, annie_memory)
        print(YELLOW + annie_response + RESET_COLOR)


# run the main function if the script is executed directly
if __name__ == "__main__":
    main()
