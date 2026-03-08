# Rate Limiter

## Problem

Build a rate limiter that controls how many operations a given caller can perform within a time window.

Rate limiters are ubiquitous in production systems: API gateways, login endpoints, message brokers, billing systems. They protect services from abuse, ensure fair usage, and prevent cascading failures under load.

## Requirements

### Functional

- Callers are identified by a string key (e.g. user ID, IP address, API key).
- The limiter decides whether a given call should be **allowed** or **rejected**.

---

*This is a seed description. Further functional and non-functional requirements will emerge during the brainstorming phase with the AI.*
