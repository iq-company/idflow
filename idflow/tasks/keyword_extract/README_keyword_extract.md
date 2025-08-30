# Keyword Extraction Task

This task provides keyword extraction functionality using the [KeyBERT](https://github.com/MaartenGr/KeyBERT) library, which leverages BERT embeddings for intelligent keyword and keyphrase extraction from text.

## Features

- **BERT-based keyword extraction**: Uses state-of-the-art transformer models for accurate keyword identification
- **Flexible n-gram support**: Extract single words, phrases, or combinations
- **Multiple algorithms**: Support for MaxSum and Maximal Marginal Relevance (MMR) for diverse results
- **Multilingual support**: Works with various languages using appropriate models
- **Configurable parameters**: Customize extraction behavior based on your needs

## Installation

The KeyBERT dependency has been added to `pyproject.toml`. Install it with:

```bash
pip install -e .
```

## Usage

### Basic Keyword Extraction

```python
from tasks.keyword_extract import keyword_extract

# Simple keyword extraction
keywords = keyword_extract(
    text="Your text here...",
    top_n=10
)
```

### Advanced Configuration

```python
# Extract keyphrases with diversity
keyphrases = keyword_extract(
    text="Your article text...",
    model="all-MiniLM-L6-v2",
    keyphrase_ngram_range=(1, 3),  # 1-3 word phrases
    top_n=15,
    use_mmr=True,                   # Use MMR for diversity
    diversity=0.8,                  # High diversity
    stop_words="english"
)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | - | **Required**: Input text/article to extract keywords from |
| `model` | str | "all-MiniLM-L6-v2" | BERT model for embeddings |
| `keyphrase_ngram_range` | Tuple[int, int] | (1, 2) | Range of n-grams (e.g., (1,1) for words, (1,2) for phrases) |
| `top_n` | int | 10 | Number of top keywords to return |
| `stop_words` | Optional[str] | "english" | Language for stop words removal |
| `use_maxsum` | bool | False | Use MaxSum algorithm for diversity |
| `use_mmr` | bool | False | Use Maximal Marginal Relevance for diversity |
| `diversity` | float | 0.7 | Diversity parameter for MMR (0.0-1.0) |
| `nr_candidates` | int | 20 | Number of candidates for MaxSum algorithm |
| `highlight` | bool | False | Return highlighted text instead of keywords |

## Model Recommendations

### English Text
- **Default**: `"all-MiniLM-L6-v2"` - Fast and accurate for English
- **High Quality**: `"all-mpnet-base-v2"` - Better quality, slower

### Multilingual Text
- **Multilingual**: `"paraphrase-multilingual-MiniLM-L12-v2"` - Good for multiple languages
- **German**: `"paraphrase-multilingual-MiniLM-L12-v2"` - Works well with German text

## Examples

### Single Word Keywords
```python
keywords = keyword_extract(
    text="Your text...",
    keyphrase_ngram_range=(1, 1),
    top_n=5
)
# Returns: [('keyword1', 0.85), ('keyword2', 0.78), ...]
```

### Keyphrases
```python
keyphrases = keyword_extract(
    text="Your text...",
    keyphrase_ngram_range=(1, 3),
    top_n=10
)
# Returns: [('key phrase one', 0.92), ('another key phrase', 0.87), ...]
```

### Diverse Results with MMR
```python
diverse_keywords = keyword_extract(
    text="Your text...",
    use_mmr=True,
    diversity=0.9,  # High diversity
    top_n=8
)
```

### German Text Processing
```python
german_keywords = keyword_extract(
    text="Deutscher Text...",
    model="paraphrase-multilingual-MiniLM-L12-v2",
    stop_words="german",
    top_n=10
)
```

## Return Format

The function returns a list of tuples, each containing:
- **Keyword/Keyphrase**: The extracted text
- **Score**: Confidence score (0.0-1.0, higher is better)

```python
[
    ('machine learning', 0.9234),
    ('artificial intelligence', 0.8912),
    ('neural networks', 0.8567),
    # ... more keywords
]
```

## Error Handling

The task includes comprehensive error handling:
- Invalid model names
- Text processing errors
- BERT model loading issues
- Parameter validation

Errors are wrapped in `RuntimeError` with descriptive messages.

## Testing

Run the test script to verify functionality:

```bash
python tests/test_keyword_extract.py
```

This will test:
- Basic keyword extraction
- Keyphrase extraction
- Diversity algorithms
- German text processing

## Performance Notes

- **First run**: May take longer due to model downloading
- **Model size**: Larger models provide better quality but slower performance
- **Text length**: Processing time scales with input text length
- **Memory**: BERT models require significant RAM (2-4GB recommended)

## Dependencies

- `keybert>=0.9.0` - Core keyword extraction library
- `sentence-transformers` - BERT model support (auto-installed)
- `torch` - PyTorch backend (auto-installed)
- `scikit-learn` - Algorithm implementations (auto-installed)
