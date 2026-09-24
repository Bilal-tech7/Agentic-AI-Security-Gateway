import json

from ollama import chat

from src.tools import get_claim


MODEL = "lfm2.5-thinking:1.2b"


def main():
    print("=" * 60)
    print("STAGE B.2 - COMPLETE AI CLAIMS AGENT")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Define the conversation
    # ---------------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI insurance claims assistant for "
                "Aurelia Insurance.\n\n"
                "You have access to tools that retrieve claims "
                "information.\n"
                "When the user asks about a claim, use the "
                "appropriate tool.\n"
                "Never invent claim information.\n"
                "After receiving the tool result, provide a short "
                "clear summary to the user."
            ),
        },
        {
            "role": "user",
            "content": (
                "Retrieve claim 1 and give me a short "
                "summary of what happened."
            ),
        },
    ]

    # ---------------------------------------------------------
    # 2. Define the available tool
    # ---------------------------------------------------------

    tool = {
        "type": "function",
        "function": {
            "name": "get_claim",
            "description": (
                "Retrieve an insurance claim from the "
                "Aurelia Insurance claims database using "
                "its claim ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_id": {
                        "type": "string",
                        "description": (
                            "The numeric claim ID, for example 1."
                        ),
                    }
                },
                "required": ["claim_id"],
            },
        },
    }

    # ---------------------------------------------------------
    # 3. Ask the LLM what it wants to do
    # ---------------------------------------------------------

    print("\nUSER REQUEST:")
    print(messages[-1]["content"])
    print()

    print("Sending request to AI agent...")
    print()

    response = chat(
        model=MODEL,
        messages=messages,
        tools=[tool],
        options={
            "temperature": 0.05,
        },
    )

    # ---------------------------------------------------------
    # 4. Check for tool call
    # ---------------------------------------------------------

    if not response.message.tool_calls:
        print("ERROR: Agent did not request a tool.")
        print()
        print("Model response:")
        print(response.message.content)
        return

    # Add the assistant's tool request to the conversation
    messages.append(response.message)

    print("AGENT REQUESTED TOOL:")
    print("-" * 60)

    for call in response.message.tool_calls:

        tool_name = call.function.name
        arguments = call.function.arguments

        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")
        print()

        # -----------------------------------------------------
        # 5. Execute the tool
        # -----------------------------------------------------

        if tool_name == "get_claim":

            claim_id = arguments.get("claim_id")

            print(f"Executing database tool for {claim_id}...")
            print()

            result = get_claim(claim_id)

            print("DATABASE RESULT:")
            print("-" * 60)
            print(json.dumps(result, indent=2, default=str))
            print()

            # -------------------------------------------------
            # 6. Return the tool result to the LLM
            # -------------------------------------------------

            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(
                        result,
                        default=str
                    ),
                }
            )

        else:

            print(f"ERROR: Unknown tool requested: {tool_name}")
            return

    # ---------------------------------------------------------
    # 7. Ask the LLM to produce the final answer
    # ---------------------------------------------------------

    print("=" * 60)
    print("GENERATING FINAL AGENT RESPONSE")
    print("=" * 60)

    final_response = chat(
        model=MODEL,
        messages=messages,
        tools=[tool],
        options={
            "temperature": 0.05,
        },
    )

    print()
    print("FINAL AGENT RESPONSE:")
    print("-" * 60)
    print(final_response.message.content)
    print()


if __name__ == "__main__":
    main()