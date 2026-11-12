# Database Optimizer (database-optimizer)

**Source :** `/home/fatsio/.config/opencode/skills/database-optimizer/SKILL.md`  \n**Domaine :** Base de données — Performance  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Optimizes database queries and improves performance across PostgreSQL and MySQL systems. Creates indexes, analyzes execution plans, optimizes schemas, prevents N+1 queries. Essential for any project with a relational database.

## Main capabilities

- **Query optimization**: Analyzes and optimizes SQL queries for performance
- **Index creation**: Recommends and creates appropriate indexes for query patterns
- **Execution plan analysis**: Uses EXPLAIN/ANALYZE to understand query performance
- **Schema optimization**: Optimizes database schema for better performance
- **N+1 query prevention**: Identifies and eliminates N+1 query patterns in ORM usage
- **Performance monitoring**: Tracks query latency and throughput metrics

## What it can do

- Analyze SQL query execution plans with EXPLAIN/ANALYZE
- Create and manage indexes (B-tree, GiN, GiS, hash) for PostgreSQL and MySQL
- Optimize schema design including denormalization and proper data types
- Identify and fix N+1 query patterns in Eloquent, SQLAlchemy, or Django ORM
- Set up query performance monitoring and alerting
- Generate index recommendations based on query patterns

## When it is useful

- Performance tuning of existing database-driven applications
- Designing new database schemas with performance in mind
- Debugging slow queries in production
- Optimizing ORM-generated queries
- Planning database migrations or upgrades
- Setting up query performance metrics and thresholds

## Practical examples

### EXPLAIN ANALYZE usage

```sql
-- Analyze query execution plan
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at > NOW() - INTERVAL '30 days'
GROUP BY u.name
ORDER BY order_count DESC;
```

### N+1 query detection

```python
# Before (N+1 problem)
for user in users:
    print(user.posts.count)  # Triggers N separate queries

# After (fix N+1)
# Option 1: Eager loading
from django.db.models import Prefetch
users = User.objects.prefetch_related('posts').all()

# Option 2: Annotate in single query
from django.db.models import Count
users = User.objects.annotate(post_count=Count('posts')).all()
```

### Index recommendation

```sql
-- Create index for frequently queried column
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Create composite index for combined filter
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);
```

## Original source path

`/home/fatsio/.config/opencode/skills/database-optimizer/SKILL.md`

## Classification

- **Domaines :** base de données, PostgreSQL, MySQL, performance, ORM
- **Statut :** Indispensable (Niveau A)
- **Références :** `python-pro`, `monitoring-expert`, `change-impact`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis
