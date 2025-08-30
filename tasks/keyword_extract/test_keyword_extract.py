#!/usr/bin/env python3
"""
Test script for the keyword extraction task.
This demonstrates how to use the keyword_extract function.
"""

import pytest
from tasks.keyword_extract.keyword_extract import keyword_extract


def test_basic_keyword_extraction():
    """Test basic keyword extraction functionality."""

    # Sample text for testing
    sample_text = """
    Supervised learning is the machine learning task of learning a function that
    maps an input to an output based on example input-output pairs. It infers a
    function from labeled training data consisting of a set of training examples.
    In supervised learning, each example is a pair consisting of an input object
    (typically a vector) and a desired output value (also called the supervisory signal).
    A supervised learning algorithm analyzes the training data and produces an inferred function,
    which can be used for mapping new examples. An optimal scenario will allow for the
    algorithm to correctly determine the class labels for unseen instances. This requires
    the learning algorithm to generalize from the training data to unseen situations in a
    'reasonable' way (see inductive bias).
    """

    # Extract basic keywords
    keywords = keyword_extract(
        text=sample_text,
        top_n=5,
        keyphrase_ngram_range=(1, 1)
    )

    # Assertions for pytest
    assert len(keywords) == 5
    assert all(isinstance(kw, tuple) for kw in keywords)
    assert all(len(kw) == 2 for kw in keywords)
    assert all(isinstance(kw[0], str) for kw in keywords)
    assert all(isinstance(kw[1], (int, float)) for kw in keywords)

    # Check that we get some expected keywords - be more flexible
    keyword_texts = [kw[0].lower() for kw in keywords]
    # At least one of these common ML terms should appear
    expected_terms = ['learning', 'function', 'data', 'training', 'algorithm', 'supervised']
    assert any(term in ' '.join(keyword_texts) for term in expected_terms), f"Expected at least one of {expected_terms} in keywords: {keyword_texts}"


def test_keyphrase_extraction():
    """Test keyphrase extraction functionality."""

    sample_text = """
    Machine learning algorithms can be categorized into supervised learning,
    unsupervised learning, and reinforcement learning. Each approach has its
    own strengths and applications in artificial intelligence.
    """

    # Extract keyphrases
    keyphrases = keyword_extract(
        text=sample_text,
        top_n=5,
        keyphrase_ngram_range=(1, 2)
    )

    # Assertions
    assert len(keyphrases) == 5
    assert all(isinstance(kp, tuple) for kp in keyphrases)

    # Check for multi-word phrases
    multi_word_phrases = [kp[0] for kp in keyphrases if ' ' in kp[0]]
    assert len(multi_word_phrases) > 0


def test_mmr_diversity():
    """Test Maximal Marginal Relevance for diversity."""

    sample_text = """
    Artificial intelligence encompasses machine learning, deep learning, neural networks,
    natural language processing, computer vision, and robotics. These technologies
    are transforming industries and creating new opportunities.
    """

    # Test with MMR for diversity
    diverse_keywords = keyword_extract(
        text=sample_text,
        top_n=5,
        keyphrase_ngram_range=(1, 2),
        use_mmr=True,
        diversity=0.7
    )

    # Assertions
    assert len(diverse_keywords) == 5
    assert all(isinstance(kw, tuple) for kw in diverse_keywords)


@pytest.mark.slow
def test_german_text():
    """Test keyword extraction with German text."""

    german_text = """
    Künstliche Intelligenz (KI) ist ein Teilgebiet der Informatik, das sich mit der Automatisierung
    intelligenten Verhaltens und dem maschinellen Lernen befasst. KI-Systeme können Aufgaben lösen,
    die normalerweise menschliche Intelligenz erfordern, wie das Erkennen von Mustern, das Treffen
    von Entscheidungen und das Verstehen natürlicher Sprache. Maschinelles Lernen ist eine wichtige
    Technik der KI, bei der Algorithmen aus Daten lernen und Vorhersagen treffen können.
    """

    # Use multilingual model for German text
    keywords = keyword_extract(
        text=german_text,
        model="paraphrase-multilingual-MiniLM-L12-v2",
        top_n=5,
        keyphrase_ngram_range=(1, 2)
    )

    # Assertions
    assert len(keywords) == 5
    assert all(isinstance(kw, tuple) for kw in keywords)


def test_error_handling():
    """Test error handling with invalid input."""

    # Test with invalid model name that should cause an error
    with pytest.raises(RuntimeError):
        keyword_extract(
            text="This is a test text",
            model="invalid-model-name-that-does-not-exist",
            top_n=5
        )


if __name__ == "__main__":
    # This allows running the file directly for debugging
    # But pytest will run it as a module
    pytest.main([__file__, "-v"])
