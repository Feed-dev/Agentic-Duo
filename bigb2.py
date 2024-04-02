import anthropic
import os
from dotenv import load_dotenv
import requests
import pyaudio
from pydub import AudioSegment
from pydub.playback import play
import openai
from openai import OpenAI

# Load environment variables from a .env file
load_dotenv()

# Define a dictionary to store API keys
api_keys = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "elevenlabs": os.getenv("ELEVEN_LABS_API_KEY")
}

# Create a dictionary to store API clients
client = {
    "openai": openai.OpenAI(api_key=api_keys["openai"]),
    "anthropic": anthropic.Anthropic(api_key=api_keys["anthropic"])
}

# Define voice IDs for text-to-speech
voice_id1 = "dyLJ4nCukg4AOgAVlUR7"
voice_id2 = "qGEJwA7CnR65FUkVZZV3"

# Define color constants for console output
NEON_GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET_COLOR = '\033[0m'


# Function to open and read a file
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def text_to_speech(text, voice_id, xi_api_key, filename="output.mp3"):
    output_file_path = os.getenv("OUTPUT_FILE_PATH")
    
    # Ensure the directory exists
    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)
    
    # Complete file path
    full_file_path = os.path.join(output_file_path, filename)
    
    # URL and headers for the ElevenLabs API request
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": xi_api_key
    }
    
    # Data payload for the API request
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    # Making a POST request to the API
    response = requests.post(url, json=data, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Writing the received audio content to the specified file
        with open(full_file_path, 'wb') as f:
            f.write(response.content)
        return {"success": True, "message": "Audio generated successfully.", "file_path": full_file_path}
    else:
        return {"success": False, "message": "Failed to generate audio."}


def play_audio(file_path):
    # Load the audio file
    audio = AudioSegment.from_mp3(file_path)
    # Play the audio
    play(audio) 


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
    # topic1 = input("Enter the topic Mike wants to talk about: ")
    # topic2 = input("Enter the topic Annie wants to talk about: ")
    max_range = int(input("Enter the maximum number of messages in the conversation: "))
    
    # Load system messages for Mike and Annie from text files
    mike_system_message = open_file("mike.txt")  # .replace("<<TPC1>>", topic1)
    annie_system_message = open_file("annie.txt")  # .replace("<<TPC2>>", topic2)
    
    # Initialize memory for Mike and Annie
    mike_memory = []
    annie_memory = []
    
    # Get the output file path from the environment variable
    output_file_path = os.getenv("OUTPUT_FILE_PATH")
    
    # Start the conversation with a friendly "Hello" from Mike
    user_input = "Hello Annie, I'm Mike, lets start working on improving the code"
    annie_response = annie_chat(user_input, annie_system_message, annie_memory)
    print(YELLOW + annie_response + RESET_COLOR)
    
    # Convert Annie's response to speech and play it
    text_to_speech(annie_response, voice_id=voice_id2, xi_api_key=api_keys["elevenlabs"], filename=f"annie_response_0.mp3")
    play_audio(os.path.join(output_file_path, "annie_response_0.mp3"))
    
    # Start the conversation loop
    for i in range(1, max_range):
        # Mike's turn to respond
        mike_response = mike_chat(annie_response, mike_system_message, mike_memory)
        # print(NEON_GREEN + mike_response + RESET_COLOR)
        
        # Convert Mike's response to speech and play it
        text_to_speech(mike_response, voice_id=voice_id1, xi_api_key=api_keys["elevenlabs"], filename=f"mike_response_{i}.mp3")
        play_audio(os.path.join(output_file_path, f"mike_response_{i}.mp3"))
        
        # Annie's turn to respond
        annie_response = annie_chat(mike_response, annie_system_message, annie_memory)
        print(YELLOW + annie_response + RESET_COLOR)
        
        # Convert Annie's response to speech and play it
        text_to_speech(annie_response, voice_id=voice_id2, xi_api_key=api_keys["elevenlabs"], filename=f"annie_response_{i}.mp3")
        play_audio(os.path.join(output_file_path, f"annie_response_{i}.mp3"))


# run the main function if the script is executed directly
if __name__ == "__main__":
    main()
