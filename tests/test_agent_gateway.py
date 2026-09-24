from ollama import chat

from src.protected_tools import execute_protected_tool


MODEL = "lfm2.5-thinking:1.2b"


# ------------------------------------------------------------
# Agent identity
# ------------------------------------------------------------

AGENT_ID = "claims-agent-01"
USER_ID = 2
USER_ROLE = "CLAIMS_ASSISTANT"


# ------------------------------------------------------------
# Tool definition exposed to the LLM
# ------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_claim",
            "description": (
                "Retrieve information about an insurance claim. "
                "The claim must be accessible to the current user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_id": {
                        "type": "integer",
                        "description": "The claim ID."
                    }
                },
                "required": ["claim_id"],
            },
        },
    }
]


def main():

    print()
    print("=" * 60)
    print("AURELIA PROTECTED CLAIMS AGENT")
    print("=" * 60)

    print(f"Model: {MODEL}")
    print(f"User ID: {USER_ID}")
    print(f"Role: {USER_ROLE}")

    # --------------------------------------------------------
    # 1. User request
    # --------------------------------------------------------

    messages = [
        {
            "role": "user",
            "content": (
                "Retrieve claim 1 and tell me what happened."
            ),
        }
    ]

    # --------------------------------------------------------
    # 2. Ask the LLM
    # --------------------------------------------------------

    response = chat(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )

    print()
    print("=" * 60)
    print("MODEL RESPONSE")
    print("=" * 60)

    print(response.message)

    # --------------------------------------------------------
    # 3. Check whether the model requested a tool
    # --------------------------------------------------------

    if not response.message.tool_calls:

        print()
        print("The model did not request a tool.")

        if response.message.content:
            print(response.message.content)

        return

    # --------------------------------------------------------
    # 4. Process tool calls
    # --------------------------------------------------------

    messages.append(response.message)

    for tool_call in response.message.tool_calls:

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        print()
        print("=" * 60)
        print("MODEL TOOL REQUEST")
        print("=" * 60)

        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # The LLM does NOT execute the tool directly.
        #
        # It goes through our security gateway.
        # ----------------------------------------------------

        result = execute_protected_tool(
            agent_id=AGENT_ID,
            user_id=USER_ID,
            user_role=USER_ROLE,
            tool_name=tool_name,
            arguments=arguments,
        )

        print()
        print("=" * 60)
        print("PROTECTED TOOL RESULT")
        print("=" * 60)

        print(result)

        # ----------------------------------------------------
        # Send gateway result back to the model
        # ----------------------------------------------------

        messages.append(
            {
                "role": "tool",
                "tool_name": tool_name,
                "content": str(result),
            }
        )

    # --------------------------------------------------------
    # 5. Ask the model for final response
    # --------------------------------------------------------

    final_response = chat(
        model=MODEL,
        messages=messages,
    )

    print()
    print("=" * 60)
    print("FINAL AGENT RESPONSE")
    print("=" * 60)

    print(final_response.message.content)


if __name__ == "__main__":
    main()
