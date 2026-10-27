from agents import Runner
from agents.stream_events import RunItemStreamEvent

from services.agentservices.acquisition import InitiatorOutput, initiation
from services.agentservices.orchestrator import OrchestratorOutput, orchestrator
from services.agentservices.retention import ModifierOutput, modifier
from services.postgremanager.new_order import (
    add_new_order,
    create_renewal_from_order,
)


orch_agent = orchestrator()
mod_agent = modifier()
init_agent = initiation()

AGENT_MAP = {
    "orchestrator": orch_agent,
    "modifier": mod_agent,
    "acquisition": init_agent,
}

OUTPUT_MAP = {
    "orchestrator": OrchestratorOutput,
    "modifier": ModifierOutput,
    "acquisition": InitiatorOutput,
}


async def _stream_result(result) -> None:
    async for event in result.stream_events():
        if isinstance(event, RunItemStreamEvent):
            if event.item.type == "tool_call_item":
                print(f"[Tool Call] -> {event.item.raw_item.name}({event.item.raw_item.arguments})")
            elif event.item.type == "tool_call_output_item":
                print(f"[Tool Result] -> {event.item.output[:200]}...")


def _order_summary(prefix: str, order: dict) -> str:
    return (
        f"{prefix}\n\n"
        f"Transaction ID: {order['TransactionID']}\n"
        f"Order Type: {order['OrderType']}\n"
        f"Status: {order['Status']}\n"
        f"Item Name: {order['ItemName']}\n"
        f"Category: {order['Category']}\n"
        f"Quantity: {order['Quantity']}\n"
        f"Unit Price: {order['UnitPrice'] or 'Pending quote'}\n"
        f"Total Cost: {order['TotalCost'] or 'Pending quote'}\n"
        f"Purchase Date: {order['PurchaseDate']}\n"
        f"Supplier: {order['Supplier'] or 'Unassigned'}\n"
        f"Buyer: {order['Buyer'] or 'Unassigned'}"
    )


async def handle_turn(current_agent: str, history: list, user_input: str):
    if current_agent not in AGENT_MAP:
        raise ValueError(f"Unknown agent: {current_agent}")

    if not user_input and not history:
        user_input = "start"
    if user_input:
        history.append({"role": "user", "content": user_input})

    result = Runner.run_streamed(AGENT_MAP[current_agent], input=history)
    await _stream_result(result)
    final = result.final_output_as(OUTPUT_MAP[current_agent])
    updated_history = result.to_input_list()

    if current_agent == "orchestrator" and final.stop_flag:
        next_agent = "modifier" if final.type == "renewal" else "acquisition"
        return await handle_turn(next_agent, [], "")

    if current_agent == "modifier":
        if final.stop_flag and final.handoff_to_new:
            return await handle_turn("acquisition", [], "")

        if final.stop_flag and final.user_approved == "yes":
            if not final.matched_transaction_id:
                raise ValueError("Renewal completed without a matched transaction ID")
            renewal = create_renewal_from_order(
                parent_transaction_id=final.matched_transaction_id,
                edit_field=final.edit_field,
                edit_value=final.edit_value,
                actor="procurement-user",
            )
            return _order_summary("Renewal saved successfully:", renewal), "orchestrator", []

        return final.reply, current_agent, updated_history

    if current_agent == "acquisition" and final.stop_flag:
        new_order = add_new_order(
            item_name=final.item_name,
            category=final.category,
            quantity=final.quantity,
            unit_price=final.unit_price or None,
            supplier=final.supplier or None,
            buyer=final.buyer or None,
            status="pending_approval" if final.unit_price else "draft",
            order_type="new",
        )
        return _order_summary("New order saved successfully:", new_order), "orchestrator", []

    return final.reply, current_agent, updated_history
