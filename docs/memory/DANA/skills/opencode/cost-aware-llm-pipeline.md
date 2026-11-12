# Cost-Aware LLM Pipeline (cost-aware-llm-pipeline)

**Source :** `/home/fatsio/.config/opencode/skills/cost-aware-llm-pipeline/SKILL.md`  \n**Domaine :** IA Coût — LLM  \n**Type :** Skill technique  \n**Niveau :** Spécialisé (Niveau B)  \n

## Description

Cost optimization patterns for LLM API usage — model routing by task complexity, budget tracking (immutable dataclasses), retry logic, and prompt caching. Model selection based on text length/item count (sonnet/haiku routing).

## Main capabilities

- **Model routing**: Routes requests to appropriate models based on task complexity (sonnet for complex, haiku for simple)
- **Budget tracking**: Tracks LLM spending with immutable dataclass budgets and alerts
- **Retry logic**: Implements exponential backoff and retry patterns for API calls
- **Prompt caching**: Leverages prompt caching for repeated requests to reduce costs
- **Token optimization**: Optimizes prompts by removing redundant content and using efficient formatting
- **Cost analytics**: Provides cost breakdown by model, request type, and time period

## What it can do

- Route LLM requests to cost-appropriate models based on complexity analysis
- Track and alert on budget thresholds and spending limits
- Implement retry with exponential backoff for transient API failures
- Cache repeated prompts to reduce API token usage
- Analyze cost per token and per request type
- Generate cost optimization reports

## When it is useful

- Multi-provider LLM applications needing cost optimization
- Production LLM systems with predictable budget requirements
- Applications with varying complexity levels in LLM requests
- Reducing LLM API costs without sacrificing quality
- Setting up spending limits and alerts for LLM usage

## Practical examples

### Model routing based on query complexity

```python
def route_llm_request(query: str, budget: Budget) -> str:
    """Route LLM request to appropriate model based on complexity."""
    if len(query.split()) > 100 or "complex" in query.lower():
        # Use sonnet for complex queries
        return "claude-3-5-sonnet-20240620"
    else:
        # Use haiku for simple queries
        return "claude-3-haiku-20240307"
```

### Prompt caching implementation

```python
# Cache key based on prompt hash
prompt_hash = hash(prompt)
cache_key = f"llm_cache:{prompt_hash}"

# Check cache before API call
if cache_key in cache:
    return cache[cache_key]

# Make API call and cache result
result = call_llm_api(prompt)
cache[cache_key] = result
return result
```

### Budget tracking dataclass

```python
@dataclass(frozen=True)
class LLMMonthlyBudget:
    """Immutable monthly budget for LLM usage."""
    limit_usd: float
    spent_usd: float
    remaining_usd: float
    
    def can_afford(self, estimated_cost: float) -> bool:
        return self.spent_usd + estimated_cost <= self.limit_usd
    
    @property
    def progress_percent(self) -> float:
        return (self.spent_usd / self.limit_usd) * 100
```

## Original source path

`/home/fatsio/.config/opencode/skills/cost-aware-llm-pipeline/SKILL.md`

## Classification

- **Domaines :** IA, LLM, coût, optimisation, budget
- **Statut :** Spécialisé (Niveau B)
- **Références :** `monitoring-expert`, `api-design`, `rag-architect`
- **Validé :** Oui (rapport d'analyse stratégique Niveau B)
- **Auteur :** OpenCode Analysis
