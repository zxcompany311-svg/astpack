# 🚀 AstPack 全球宣发武器库 (Launch Kit)

本文件汇总了面向 **Hacker News**、**Twitter (X)**、**Reddit** 以及 **国内技术社区（V2EX / 掘金 / 即刻）** 的全套爆款宣发文案与发布节奏。

---

## 1. Hacker News (Show HN)

* **提交页面**: https://news.ycombinator.com/submit
* **最佳发布时间**: 美东时间上午 8:00 - 10:00 (北京时间晚上 20:00 - 22:00)
* **Title**:
  ```text
  Show HN: AstPack – AST-aware semantic context pruning for AI coding agents
  ```
* **URL**: `https://github.com/zxcompany311-svg/astpack`
* **Text (首楼评论或直接提交)**:
  ```markdown
  Hey HN,

  I built AstPack (https://github.com/zxcompany311-svg/astpack) to solve a personal pain point: feeding huge repos to Claude Code, Cursor, and ChatGPT burns too many tokens and causes hallucination.

  Existing tools like Repomix and gitingest concatenate raw text files verbatim. If you want an agent to fix a payment function, they send 50,000 lines of unrelated internal loops, SQL queries, and logging helpers.

  AstPack takes a compiler-level approach:
  1. It parses code into Abstract Syntax Trees (Python AST + JS/TS syntax).
  2. With `--focus <function>`, it preserves the full implementation of your target logic, while collapsing all auxiliary functions and methods into PEP 484-compliant type stubs (`def helper(...) -> ReturnType: ...`) and docstrings.
  3. It cuts token consumption by 70%~85% while keeping 100% of the type signatures and syntax validity.
  4. It includes a built-in Model Context Protocol (MCP) server so agents can autonomously prune context on the fly.

  Benchmark on sample projects:
  - Raw pack: ~85,000 tokens
  - AstPack stubs: ~18,200 tokens (-78.6%)

  Zero external runtime dependencies. Would love your feedback and thoughts!
  ```

---

## 2. X (Twitter) 爆款推文串 (Thread)

* **Tweet 1 (Hook)**:
  ```text
  Stop burning 80% of your LLM context window on irrelevant function bodies. 💸

  Coding agents don't need 50,000 lines of internal CRUD loops to understand your codebase. They need clean type signatures and targeted call closures.

  Introducing AstPack: AST-Aware Semantic Context Pruning for AI Agents. 🌳👇
  ```

* **Tweet 2 (The Problem)**:
  ```text
  Tools like Repomix dump raw code files into prompts. 

  When you ask Claude/Cursor to refactor checkout(), you pay for hundreds of lines of XML formatting and logging helpers. 

  Result: Astronomical token bills + context dilution (LLM attention decay).
  ```

* **Tweet 3 (The Solution)**:
  ```text
  AstPack parses ASTs and prunes code losslessly:

  🎯 Focus Mode: Keeps target functions 100% intact
  ✂️ Semantic Stubs: Elides auxiliary methods into PEP 484 stubs (`...`) with full type annotations
  🔌 Native MCP Server: Claude Desktop and Cursor can prune autonomously!

  Token reduction: -78.6% on average.
  ```

* **Tweet 4 (Call to Action)**:
  ```text
  Zero required dependencies. Works with Python and TypeScript.

  📦 Run instantly: `uvx astpack --help`
  ⭐ Open Source on GitHub: https://github.com/zxcompany311-svg/astpack

  RT if your LLM bills are getting out of hand! 🔄
  ```

---

## 3. Reddit (r/LocalLLaMA & r/ChatGPTCoding)

* **Title**:
  ```text
  I made an AST-aware semantic context pruner that cuts Coding Agent token usage by 80%
  ```
* **Post Content**:
  ```markdown
  Hey everyone,

  Like many of you, I've been using Claude 3.7 / Cursor / Aider heavily for daily coding. The biggest bottleneck isn't context window size—it's context noise. When you dump an entire repository into an agent, 80% of the tokens are just function implementations the model never needs to see.

  I built **AstPack** (https://github.com/zxcompany311-svg/astpack) to fix this using AST analysis:

  - It replaces non-target function bodies with `...` (Ellipsis) while preserving complete type signatures, parameters, and docstrings.
  - If you pass `--focus <function>`, it automatically preserves that function's implementation while stubbing the rest.
  - Generates AI-optimized Markdown context packs with repository directory trees and token compression reports.
  - Comes with a native MCP server (`astpack mcp`) for agent integration.

  In our benchmarks, a 85k token repo shrinks to 18k tokens with zero loss in type awareness.

  It's fully open source (MIT): https://github.com/zxcompany311-svg/astpack
  Let me know what you think!
  ```

---

## 4. 中文社区（V2EX / 即刻 / 掘金）

* **标题**:
  ```text
  分享一个自研开源工具 AstPack：用 AST 语法树剪枝，帮 Coding Agent 省下 80% Token 账单
  ```
* **内容提要**:
  - 当前 Repomix / gitingest 粗暴拼接代码的硬伤（大模型注意力稀释、API 账单昂贵）。
  - AstPack 编译原理级解法：保留代码骨架（类型签名/Docstring/PEP 484 桩代码），只保留目标手术函数的真实实现。
  - 原生支持 MCP 协议，Cursor / Claude 开箱即用。
  - 项目主页：https://github.com/zxcompany311-svg/astpack
