SYSTEM_PROMPT = """You are SmartWiki2, a deterministic wiki maintenance assistant.
Use vault content as source of truth, preserve structure, and produce precise outputs."""


def query_prompt(question: str, context: str) -> str:
    return (
        "Answer the question from the provided vault excerpts. Cite file paths. "
        "If uncertain, state uncertainty.\n\n"
        f"Question:\n{question}\n\nContext:\n{context}\n"
    )
