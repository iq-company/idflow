# TYPE: LLM_TEXT_COMPLETE

from conductor.client.worker.worker_task import worker_task
from litellm import completion


@worker_task(task_definition_name='llm_text_complete')
def llm_text_complete(
    llmProvider: str,
    model: str,
    # promptName: str,
    prompt: str,
    promptVariables: dict | None = None,
    temperature: float | None = None,
    stopWords: list[str] | str | dict | None = None,
    topP: float | None = None,
    maxTokens: int | None = None,
) -> str:
    # Prepare the prompt with variables if provided
    final_prompt = prompt
    if promptVariables:
        try:
            final_prompt = prompt.format(**promptVariables)
        except KeyError as e:
            raise ValueError(f"Missing prompt variable: {e}")

    # Prepare completion parameters
    completion_params = {
        "model": model,
        "messages": [{"role": "user", "content": final_prompt}]
    }

    # Add optional parameters if provided
    if temperature is not None:
        completion_params["temperature"] = temperature
    if topP is not None:
        completion_params["top_p"] = topP
    if maxTokens is not None:
        completion_params["max_tokens"] = maxTokens
    if stopWords is not None:
        if isinstance(stopWords, str):
            completion_params["stop"] = [stopWords]
        elif isinstance(stopWords, list):
            completion_params["stop"] = stopWords
        elif isinstance(stopWords, dict):
            completion_params["stop"] = list(stopWords.values())

    try:
        # Call the LLM using litellm
        response = completion(**completion_params)
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"LLM completion failed: {str(e)}")
