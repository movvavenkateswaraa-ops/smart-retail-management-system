"""Tiny helper for printing aligned text tables."""


def table(headers, rows) -> str:
    rows = [[str(cell) for cell in row] for row in rows]
    if not rows:
        return "  (nothing to show)"
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    sep = "  ".join("-" * w for w in widths)
    body = ["  ".join(c.ljust(w) for c, w in zip(r, widths)) for r in rows]
    return "\n".join([line, sep, *body])
