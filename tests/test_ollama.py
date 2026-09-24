from ollama import chat


MODEL = "oamazonasgabriel/lfm2.5-230m:bf16-8gbRAM"


def main():
    print("Testing Ollama connection...")
    print(f"Model: {MODEL}")
    print()

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Say hello and tell me you are ready "
                    "to act as an insurance claims assistant."
                )
            }
        ],
    )

    print("MODEL RESPONSE:")
    print(response.message.content)


if __name__ == "__main__":
    main()
