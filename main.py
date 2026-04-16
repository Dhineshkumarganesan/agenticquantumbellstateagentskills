import argparse

from agent_runtime.agent import AgentRuntime


def parse_args():
    parser = argparse.ArgumentParser(description="Agentic Quantum Lab")
    parser.add_argument(
        "--run-agent",
        dest="run_agent_instruction",
        help="Run the agent exactly once with the given instruction, then exit.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    runtime = AgentRuntime()

    if args.run_agent_instruction:
        runtime.run_agent(args.run_agent_instruction)
        return

    print("Agentic Quantum Lab")
    print("Type /help for commands.")

    while True:
        user_input = input("\n> ").strip()
        if not user_input:
            continue

        if user_input in ("/quit", "/exit"):
            print("Bye.")
            return

        if user_input == "/help":
            print(runtime.help_text())
            continue

        if user_input.startswith("/run-agent "):
            instruction = user_input[len("/run-agent ") :].strip()
            runtime.run_agent(instruction)
            continue

        if user_input == "/run-traditional":
            import traditional

            traditional.run_traditional()
            continue

        if user_input == "/draw-last":
            runtime.draw_last()
            continue

        if user_input == "/analyze-last":
            runtime.analyze_last()
            continue

        print("Unknown command. Use /help.")


if __name__ == "__main__":
    main()
