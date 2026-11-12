# Prompt Engineer (prompt-engineer)

**Source :** `/home/fatsio/.config/opencode/skills/prompt-engineer/SKILL.md`  \n**Domaine :** IA — Prompt  \n**Type :** Skill technique  \n**Niveau :** Expérimental (Niveau C)  \n

## Description

Writes, refactors, and evaluates prompts for LLMs — generates optimized prompt templates, structured output schemas (JSON mode, function calling), evaluation rubrics, and test suites. Design patterns (zero-shot, few-shot, CoT, ReAct).

## Main capabilities

- **Prompt optimization**: Generates optimized prompt templates for specific LLM tasks
- **Structured output schemas**: Implements JSON mode and function calling for deterministic outputs
- **Evaluation rubrics**: Creates rubrics for evaluating LLM prompt quality and effectiveness
- **Test suites**: Generates test suites for prompt validation and regression
- **Pattern library**: Maintains library of proven prompt patterns (zero-shot, few-shot, CoT, ReAct)
- **Few-shot example generation**: Creates few-shot examples for LLM prompting

## What it can do

- Design optimized prompt templates for specific tasks (classification, extraction, reasoning)
- Implement JSON mode for structured LLM outputs
- Create function calling schemas for tool use by LLMs
- Develop evaluation rubrics to measure prompt quality
- Generate test suites for prompt regression testing
- Apply few-shot, zero-shot, CoT (Chain-of-Thought), and ReAct patterns

## When it is useful

- Designing prompts for new LLM tasks or capabilities
- Refactoring existing prompts for better accuracy or token efficiency
- Implementing structured outputs for LLM tool use
- Building prompt evaluation frameworks
- Creating few-shot prompts for few-shot learning
- Optimizing prompt token usage for cost reduction

## Practical examples

### Few-shot prompt template

```markdown
# Few-shot: Text Classification

Classify the following text into one of: {positive, negative, neutral}.

Examples:
1. "I love this movie!" -> positive
2. "This is terrible." -> negative
3. "It was okay." -> neutral

Now classify: "{text}"
```

### JSON mode for structured output

```python
import json
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Extract the name and price from: 'iPhone 15 Pro $999'"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "product_info",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"}
                },
                "required": ["name", "price"],
                "additionalProperties": False
            }
        }
    }
)

print(json.parse(response.choices[0].message.content))
```

### Chain-of-Thought prompt

```markdown
# CoT: Math Reasoning

Solve the following math problem step by step:

{question}

Let's think step by step.
```
