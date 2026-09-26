# Draft reply to the SwiftSci maintainer

Status: proposed wording from this chat, not posted by this chat. Date: September 26, 2026.

I'm learning as I go too. I'm a nuclear engineer rather than a software engineer, and I generally write code because I need it to solve a particular problem. Frustration with parts of my Python workflow is what led me to your library.

I do a lot of numerical work in Python and R. What I need is a combination I haven't found yet: fast, memory-efficient data structures and operations that make good use of Apple Silicon, with APIs familiar enough that moving existing numerical workflows doesn't require redesigning everything.

The API similarity matters to me because it reduces the amount of higher-level code I have to rethink. Underneath that, I want control over memory use, copying, and parallel execution. The dataframe work in this PR is one part of that.

I'm also implementing local AI for my company. I've chosen Apple Silicon for that work, and I'm paying for the hardware myself, so memory efficiency and throughput directly affect what I can afford to run. Tools like MLX already provide useful building blocks, but I still need an efficient path from loading and transforming data through numerical analysis and model execution.

That's why SwiftSci caught my attention. It brings together enough of the operations I need that contributing to it makes more sense than starting everything from scratch. Your project is useful for a real engineering problem, and I appreciate you making it available.
