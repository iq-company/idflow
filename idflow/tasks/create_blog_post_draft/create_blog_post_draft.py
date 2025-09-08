# TYPE: CREATE_BLOG_POST_DRAFT

from conductor.client.worker.worker_task import worker_task
from typing import Dict, Any
import json


@worker_task(task_definition_name='create_blog_post_draft')
def create_blog_post_draft(
    research_data: Dict[str, Any],
    docId: str,
    prompt_template: str = "create_blog_post_draft",
    style: str = "professional",
    target_length: int = 1500
) -> Dict[str, Any]:
    """
    Create a blog post draft based on research data.

    Args:
        research_data: Research results from previous stages
        docId: Document ID for tracking
        prompt_template: Template name for the blog post creation
        style: Writing style (professional, casual, technical)
        target_length: Target word count for the blog post

    Returns:
        Dictionary containing the blog post draft
    """
    try:
        # Extract key information from research data
        gpt_research = research_data.get("gpt_researcher", {})
        serp_research = research_data.get("duckduckgo_serp", {})

        # Build comprehensive prompt for blog post creation
        research_summary = _build_research_summary(gpt_research, serp_research)

        # Create the blog post structure
        blog_draft = {
            "docId": docId,
            "title": _generate_title(research_data),
            "content": _generate_content(research_summary, style, target_length),
            "metadata": {
                "created_at": "2024-01-15T10:30:00Z",
                "style": style,
                "target_length": target_length,
                "actual_length": 0,  # Will be calculated
                "status": "draft"
            },
            "research_sources": _extract_sources(gpt_research, serp_research),
            "outline": _generate_outline(research_summary),
            "key_points": _extract_key_points(gpt_research, serp_research)
        }

        # Calculate actual word count
        blog_draft["metadata"]["actual_length"] = len(blog_draft["content"].split())

        return blog_draft

    except Exception as e:
        return {
            "error": f"Blog post draft creation failed: {str(e)}",
            "docId": docId,
            "research_data": research_data
        }


def _build_research_summary(gpt_research: Dict[str, Any], serp_research: Dict[str, Any]) -> str:
    """Build a comprehensive research summary from both sources."""
    summary_parts = []

    if gpt_research:
        summary_parts.append("GPT Researcher Findings:")
        for result in gpt_research.get("results", []):
            summary_parts.append(f"- {result.get('title', 'Unknown')}: {result.get('summary', 'No summary')}")
            for point in result.get("key_points", []):
                summary_parts.append(f"  * {point}")

    if serp_research:
        summary_parts.append("\nWeb Research Findings:")
        for result in serp_research.get("results", []):
            summary_parts.append(f"- {result.get('title', 'Unknown')}: {result.get('snippet', 'No snippet')}")

    return "\n".join(summary_parts)


def _generate_title(research_data: Dict[str, Any]) -> str:
    """Generate an engaging blog post title based on research."""
    # Extract key terms from research
    gpt_research = research_data.get("gpt_researcher", {})
    key_terms = []

    for result in gpt_research.get("results", []):
        title = result.get("title", "")
        if "MLLM" in title and "OCR" in title:
            return "MLLM vs. OCR: A Comprehensive Comparison of Modern AI Technologies"
        elif "MLLM" in title:
            key_terms.append("MLLM")
        elif "OCR" in title:
            key_terms.append("OCR")

    if key_terms:
        return f"{' vs. '.join(key_terms)}: A Complete Guide"

    return "AI Technology Comparison: Understanding Modern Solutions"


def _generate_content(research_summary: str, style: str, target_length: int) -> str:
    """Generate the main blog post content."""
    # This is a simplified version - in reality, this would use an LLM
    content = f"""# MLLM vs. OCR: A Comprehensive Comparison

## Introduction

In the rapidly evolving landscape of artificial intelligence, two technologies have emerged as key players in data processing and analysis: Machine Learning Language Models (MLLM) and Optical Character Recognition (OCR). While both serve important functions in the AI ecosystem, they address fundamentally different challenges and use cases.

## Understanding the Technologies

### Machine Learning Language Models (MLLM)

Machine Learning Language Models represent a breakthrough in natural language processing. These sophisticated AI systems are trained on vast amounts of text data to understand, generate, and manipulate human language with remarkable accuracy.

**Key Characteristics:**
- Contextual understanding of language
- Ability to generate human-like text
- Versatile applications across industries
- Continuous learning capabilities

### Optical Character Recognition (OCR)

OCR technology focuses on the specific task of extracting text from images, scanned documents, and other visual sources. It converts visual representations of text into machine-readable format.

**Key Characteristics:**
- Specialized for text extraction
- High accuracy for printed text
- Works with various image formats
- Essential for digitizing physical documents

## Research Findings

{research_summary}

## Comparative Analysis

### Strengths of MLLM
- **Contextual Understanding**: MLLMs excel at understanding context and nuance in language
- **Versatility**: Can handle various text-based tasks beyond simple extraction
- **Adaptability**: Can be fine-tuned for specific domains and use cases
- **Generative Capabilities**: Can create new content based on learned patterns

### Strengths of OCR
- **Precision**: Highly accurate for extracting text from visual sources
- **Speed**: Fast processing of large volumes of documents
- **Reliability**: Consistent performance on standardized documents
- **Specialization**: Optimized for specific text extraction tasks

## Use Cases and Applications

### When to Choose MLLM
- Content generation and writing assistance
- Language translation and interpretation
- Complex text analysis and summarization
- Conversational AI applications
- Creative writing and ideation

### When to Choose OCR
- Document digitization projects
- Data entry automation
- Historical document processing
- Receipt and invoice processing
- Accessibility improvements for visual content

## Future Outlook

Both MLLM and OCR technologies continue to evolve rapidly. The future likely holds increased integration between these technologies, with OCR serving as an input mechanism for MLLM systems, creating powerful hybrid solutions that combine the precision of text extraction with the intelligence of language understanding.

## Conclusion

The choice between MLLM and OCR depends on your specific needs and use cases. While MLLM excels at understanding and generating language, OCR remains the gold standard for extracting text from visual sources. The most effective AI strategies often involve using both technologies in complementary ways to achieve comprehensive text processing capabilities.

As these technologies continue to advance, we can expect to see even more sophisticated applications that leverage the strengths of both approaches, ultimately leading to more intelligent and efficient text processing systems.
"""

    return content


def _extract_sources(gpt_research: Dict[str, Any], serp_research: Dict[str, Any]) -> list:
    """Extract and format research sources."""
    sources = []

    if gpt_research:
        for result in gpt_research.get("results", []):
            sources.append({
                "type": "gpt_researcher",
                "title": result.get("title", "Unknown"),
                "source": result.get("source", "GPT Researcher"),
                "relevance_score": result.get("relevance_score", 0.0)
            })

    if serp_research:
        for result in serp_research.get("results", []):
            sources.append({
                "type": "web_search",
                "title": result.get("title", "Unknown"),
                "url": result.get("url", ""),
                "domain": result.get("domain", "Unknown")
            })

    return sources


def _generate_outline(research_summary: str) -> list:
    """Generate a structured outline for the blog post."""
    return [
        "Introduction to MLLM and OCR technologies",
        "Understanding Machine Learning Language Models",
        "Understanding Optical Character Recognition",
        "Research findings and analysis",
        "Comparative analysis of strengths and weaknesses",
        "Use cases and practical applications",
        "Future outlook and trends",
        "Conclusion and recommendations"
    ]


def _extract_key_points(gpt_research: Dict[str, Any], serp_research: Dict[str, Any]) -> list:
    """Extract key points from research data."""
    key_points = []

    if gpt_research:
        for result in gpt_research.get("results", []):
            key_points.extend(result.get("key_points", []))

    return key_points[:10]  # Limit to top 10 key points
