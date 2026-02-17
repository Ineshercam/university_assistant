from openai import OpenAI
from dotenv import load_dotenv 
import os

load_dotenv()
OPEN_AI_KEY =os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPEN_AI_KEY)


def generate_qa_from_transcript(file_path):
    # Load the transcription text
    with open(file_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # Send to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You extract clear questions and answers from transcripts."
            },
            {
                "role": "user",
                "content": f"""
                Here is a transcription of a Q&A video.
                Please generate a clean list of questions and answers based on the content.
                give the output in JSON fotmat {{"question": "", "answer":""\}}

                TRANSCRIPT:
                {transcript}
                """
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    file_path = ""
    qa_output = generate_qa_from_transcript(file_path)
    print("\n=== GENERATED Q&A ===\n")
    print(qa_output)
