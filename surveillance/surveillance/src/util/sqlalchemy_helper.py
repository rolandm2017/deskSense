"""
Both Chat and Claude agree that there are
"differences in how SQLAlchemy handles coroutines in different contexts 
(e.g., production vs. test environments) and possibly even version mismatches." - GPT
https://chatgpt.com/c/67bd1000-163c-8010-a809-85a8dab27c67

And "in some versions or contexts, scalars().all() can behave differently. 
It might be returning a coroutine in your test environment that needs to be awaited." - Claude
https://claude.ai/chat/64f5028f-1365-43d2-a11d-8ff83dc4f7df

So the answer, per GPT, is to contextually await, or not await. So cool.
"""

# This function exists because SQLAlchemy's async API can be inconsistent.
# In some cases, scalars().all() must be awaited, while in others it should not be.
# This function dynamically determines the correct behavior.


async def await_if_needed(scalars_result):
    return await scalars_result.all() if hasattr(scalars_result, "__await__") else scalars_result.all()
