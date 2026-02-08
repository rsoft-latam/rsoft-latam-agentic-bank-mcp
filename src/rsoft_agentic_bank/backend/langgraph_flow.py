"""LangGraph workflow for loan risk evaluation."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


# ── State schema ─────────────────────────────────────────────────────────────

class LoanState(TypedDict):
    agent_id: str
    monto: float
    score: int
    deuda_actual: float
    aprobado: bool
    motivo: str


# ── Node functions ───────────────────────────────────────────────────────────

def analizar_riesgo(state: LoanState) -> dict[str, Any]:
    """Heuristic risk gate — rejects high-risk requests early."""
    score = state["score"]
    monto = state["monto"]
    deuda = state["deuda_actual"]

    if score < 400:
        return {"aprobado": False, "motivo": "Score crediticio insuficiente (< 400)."}

    ratio_deuda = deuda / max(monto, 1)
    if ratio_deuda > 0.8:
        return {
            "aprobado": False,
            "motivo": f"Ratio deuda/monto demasiado alto ({ratio_deuda:.2f}).",
        }

    return {"aprobado": True, "motivo": "Riesgo aceptable — aprobado."}


def decidir(state: LoanState) -> str:
    """Routing edge: approved → end, rejected → end."""
    return "aprobado" if state["aprobado"] else "rechazado"


# ── Graph construction ───────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    graph = StateGraph(LoanState)
    graph.add_node("analizar_riesgo", analizar_riesgo)
    graph.set_entry_point("analizar_riesgo")
    graph.add_conditional_edges(
        "analizar_riesgo",
        decidir,
        {"aprobado": END, "rechazado": END},
    )
    return graph.compile()


_compiled_graph = _build_graph()


# ── Public API ───────────────────────────────────────────────────────────────

async def evaluar_solicitud_prestamo(
    agent_id: str,
    monto: float,
    score: int,
    deuda_actual: float,
) -> dict[str, Any]:
    """Run the LangGraph loan-evaluation workflow and return the verdict."""
    initial_state: LoanState = {
        "agent_id": agent_id,
        "monto": monto,
        "score": score,
        "deuda_actual": deuda_actual,
        "aprobado": False,
        "motivo": "",
    }

    result = await _compiled_graph.ainvoke(initial_state)

    return {
        "agent_id": agent_id,
        "monto": monto,
        "aprobado": result["aprobado"],
        "motivo": result["motivo"],
        "score_utilizado": score,
    }
