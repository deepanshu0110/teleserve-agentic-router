"""
resumegap_mcp_server.py
=======================
Day 204 — FastMCP server wrapping the locked resumegap_engine.analyze_resume_gap
as a callable tool ("resumegap_analyze"). Rebuilt as a standalone script from the
Day204 notebook's Tasks 1-3, with a stdio run entrypoint added so Day214's
LangGraph node can spawn this as a subprocess via StdioTransport.

Requires resumegap_engine.py to be present in the same directory (or on PYTHONPATH).
"""

from pydantic import BaseModel, Field, ConfigDict
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from resumegap_engine import analyze_resume_gap


# ── Task 1: Validated input model ──────────────────────────────────────────
class ResumeGapInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    resume_text: str = Field(
        ...,
        min_length=20,
        description="The full text of the candidate's resume or CV."
    )
    jd_text: str = Field(
        ...,
        min_length=20,
        description="The full text of the job description to compare against."
    )
    top_n: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Number of top gap words to return (between 1 and 20)."
    )


# ── Tasks 2 & 3: Tool registration + boundary error handling ───────────────
mcp = FastMCP("resumegap_mcp")


@mcp.tool(
    name="resumegap_analyze",
    annotations={
        "readOnlyHint": True,       # does not modify state
        "destructiveHint": False,   # does not delete or alter data
        "idempotentHint": True,     # calling repeatedly has same effect
        "openWorldHint": False      # no external side effects
    }
)
def resumegap_analyze(params: ResumeGapInput) -> dict:
    """
    Analyze gaps between a resume and a job description using TF-IDF similarity.

    Returns a similarity score (0-100), a match band (Strong/Moderate/Weak),
    and a list of top gap words that appear in the JD but not in the resume.
    """
    try:
        return analyze_resume_gap(
            resume=params.resume_text,
            jd=params.jd_text,
            top_n=params.top_n
        )
    except Exception as e:
        # Any unexpected error from the engine is wrapped as a ToolError
        raise ToolError(f"Engine error during analysis: {str(e)}")


# ── Stdio entrypoint (added for Day214) ────────────────────────────────────
# Day204's notebook only ever exercised this via an in-memory Client(mcp).
# Day214 spawns this file as a real subprocess (StdioTransport), so it needs
# an actual run() call when executed as a script.
if __name__ == "__main__":
    mcp.run()  # defaults to stdio transport
