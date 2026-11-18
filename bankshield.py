from guardrails.input_guardrail import check_input
from guardrails.output_guardrail import check_output
from guardrails.human_review import submit_for_review

from pathlib import Path
import os
from llama_cpp import Llama

MODEL_PATH = Path(os.environ.get(
    "BANKSHIELD_MODEL_PATH",
    str(Path(__file__).resolve().parent / "models" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),
)).expanduser()

if not MODEL_PATH.is_file():
    raise SystemExit(
        f"Model not found: {MODEL_PATH}\n"
        "Place the GGUF file in models/ or set BANKSHIELD_MODEL_PATH. "
        "See README.md for setup instructions."
    )

print("Loading quantized TinyLlama locally...")

llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=1024,
    n_gpu_layers=0,
    chat_format="zephyr",
    verbose=False
)

def generator(messages, max_new_tokens=100, do_sample=False):

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_new_tokens,
        temperature=0.0
    )

    answer = response["choices"][0]["message"]["content"] or ""

    return [
        {
            "generated_text": [
                *messages,
                {"role": "assistant", "content": answer}
            ]
        }
    ]



def generate_answer(prompt):
    input_result = check_input(prompt)
    print("\nInput guardrail:", input_result)

    if input_result["decision"] == "BLOCK":
        return "Request blocked by BankShield AI."

    if input_result["decision"] == "HUMAN_REVIEW":
        case = submit_for_review(
            prompt,
            input_result["reason"],
        )
        print(f"Review case created: {case['case_id']}")
        return "Request referred for human security review."

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    result = generator(
    messages,
    max_new_tokens=100,
    do_sample=False,
)

    generated = result[0]["generated_text"]

    if isinstance(generated, list):
        answer = next(
            (
                item["content"]
                for item in reversed(generated)
                if item.get("role") == "assistant"
            ),
            "",
        )
    else:
        answer = str(generated)

    output_result = check_output(answer)
    print("Output guardrail:", output_result)

    if output_result["decision"] == "BLOCK":
        return "Response blocked by BankShield AI."

    if output_result["decision"] == "HUMAN_REVIEW":
        case = submit_for_review(
            prompt,
            output_result["reason"],
        )
        print(f"Review case created: {case['case_id']}")
        return "Response held for human security review."

    return answer

if __name__ == "__main__":
    print("\nBankShield AI is ready.")
    print("Type 'exit' to quit.")

    while True:
        prompt = input("\nYou: ").strip()

        if prompt.lower() == "exit":
            print("BankShield AI closed.")
            break

        if not prompt:
            print("Please enter a prompt.")
            continue

        try:
            answer = generate_answer(prompt)
            print("\nBankShield AI:", answer)
        except Exception as error:
            print("\nAn error occurred:", error)
