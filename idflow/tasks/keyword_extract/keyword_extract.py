# TYPE: KEYWORD_EXTRACT

from conductor.client.worker.worker_task import worker_task
from keybert import KeyBERT
from typing import List, Tuple, Optional


@worker_task(task_definition_name='keyword_extract')
def keyword_extract(
    text: str,
    model: str = "all-MiniLM-L6-v2",
    keyphrase_ngram_range: Tuple[int, int] = (1, 2),
    top_n: int = 10,
    stop_words: Optional[str] = "english",
    use_maxsum: bool = False,
    use_mmr: bool = False,
    diversity: float = 0.7,
    nr_candidates: int = 20,
    highlight: bool = False
) -> List[Tuple[str, float]]:
    """
    Extract keywords from the given text using KeyBERT.

    Args:
        text: The input text/article to extract keywords from
        model: The BERT model to use for embeddings (default: "all-MiniLM-L6-v2")
        keyphrase_ngram_range: Range of n-grams for keyphrase extraction (default: (1, 2))
        top_n: Number of top keywords to return (default: 10)
        stop_words: Language for stop words removal (default: "english")
        use_maxsum: Whether to use MaxSum algorithm for diversity (default: False)
        use_mmr: Whether to use Maximal Marginal Relevance for diversity (default: False)
        diversity: Diversity parameter for MMR (default: 0.7)
        nr_candidates: Number of candidates for MaxSum algorithm (default: 20)
        highlight: Whether to highlight keywords in the text (default: False)

    Returns:
        List of tuples containing (keyword, score) pairs
    """

    try:
        # Initialize KeyBERT with the specified model
        kw_model = KeyBERT(model=model)

        # Extract keywords based on the parameters
        if use_maxsum:
            keywords = kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_ngram_range,
                stop_words=stop_words,
                use_maxsum=True,
                nr_candidates=nr_candidates,
                top_n=top_n
            )
        elif use_mmr:
            keywords = kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_ngram_range,
                stop_words=stop_words,
                use_mmr=True,
                diversity=diversity,
                top_n=top_n
            )
        else:
            keywords = kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=keyphrase_ngram_range,
                stop_words=stop_words,
                top_n=top_n
            )

        # If highlight is requested, return the highlighted text instead
        if highlight:
            highlighted_text = kw_model.extract_keywords(text, highlight=True)
            return highlighted_text

        return keywords

    except Exception as e:
        raise RuntimeError(f"Keyword extraction failed: {str(e)}")
