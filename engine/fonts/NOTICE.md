# Bundled fonts

Two typefaces are embedded in every generated HTML file as base64 woff2, so a
book renders identically on a machine that has neither installed.

| File | Family | Copyright | Licence |
|---|---|---|---|
| `Caveat-SemiBold.woff2` | Caveat | The Caveat Project Authors | SIL Open Font License 1.1 |
| `PatrickHand-Regular.woff2` | Patrick Hand | Patrick Wagesreiter | SIL Open Font License 1.1 |

Both are from Google Fonts and both are free to use, embed and redistribute,
including commercially. The full licence text is at
`scripts.sil.org/OFL` and in each font's entry at `fonts.google.com`.

If you redistribute this pipeline publicly, include a copy of the full OFL 1.1
text alongside these files. The licence requires it, and this NOTICE is a
pointer rather than a substitute.

## Not bundled

The monospace and serif faces are **not** embedded. `engine/theme.css` names
them with fallbacks:

```text
--mono   JetBrains Mono, SF Mono, Menlo, monospace
--serif  Charter, Georgia, serif
```

On a machine without JetBrains Mono or Charter installed, the fallbacks are
used and the books still build and read correctly. Code blocks are measured at
build time using JetBrains Mono's advance width, so a substituted monospace
face with different metrics can make a wide ASCII diagram slightly narrower or
wider than intended. Nothing clips. Install both if you want an exact match.
