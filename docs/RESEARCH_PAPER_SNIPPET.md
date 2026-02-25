# Research Paper Snippet — Validated Gemini 2.5 Results

Copy the LaTeX below into your paper's RQ2/RQ3 sections.

---

## Validated results (Gemini 2.5 Flash)

```latex
\textbf{Validated results (Gemini 2.5 Flash):}
\begin{itemize}
  \item Full-repo context: 375{,}216 characters, 11{,}259 lines, 31{,}661 prompt tokens, $\sim$32{,}000 total tokens.
  \item Rabt minimal subgraph: 136 characters (subgraph), 7 lines, \textbf{85 prompt tokens} (from API \texttt{usage\_metadata}).
  \item Token reduction: 99.7\% (31{,}661 $\rightarrow$ 85 tokens).
  \item Both answers correctly identify \texttt{get}, \texttt{options}, \texttt{head}, \texttt{post}, \texttt{put}, \texttt{patch}, and \texttt{delete} as callers of \texttt{request}.
\end{itemize}
```

---

## RQ3 cost table (use 85 tokens for Rabt)

```latex
On the \texttt{requests} repository:
\begin{itemize}
  \item Full-repo context: 31{,}661 prompt tokens per query (375{,}216 characters, 11{,}259 lines).
  \item Rabt minimal subgraph: 85 tokens per query (validated via Gemini API).
\end{itemize}
```

---

## Validation note (for methods section)

```latex
Token counts are validated by (a) reading \texttt{usage\_metadata} from the Gemini API response for both full-repo and Rabt calls, and (b) running the \texttt{validate\_tokens} script which prints raw \texttt{usage\_metadata} for reproducibility.
```
