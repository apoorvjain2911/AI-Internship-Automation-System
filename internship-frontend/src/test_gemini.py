from google import genai

client = genai.Client(api_key="AIzaSyDyA23XLmXsJjaI5eScU0cDDB-t6cgbwqg")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Write one professional sentence."
)

print(response.text)