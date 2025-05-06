class LLMModel:
    def __init__(self, api_key=None):
        # init openai or other client
        pass

    def select_best(self, candidates: list[str]) -> str:
        # stub: returns longest
        return max(candidates, key=len)
        # later: call LLM to rank or merge
