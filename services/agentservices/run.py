import asyncio
from agents import Runner
from agents.stream_events import RunItemStreamEvent
from services.agentservices.orchestrator import orchestrator, OrchestratorOutput
from services.agentservices.retention import modifier, ModifierOutput
from services.agentservices.acquisition import initiation, InitiatorOutput
from services.postgremanager.new_order import add_new_order


orch_agent = orchestrator()
mod_agent  = modifier()
init_agent = initiation()

AGENT_MAP = {
    "orchestrator": orch_agent,
    "modifier":     mod_agent,
    "acquisition":  init_agent,
}

OUTPUT_MAP = {
    "orchestrator": OrchestratorOutput,
    "modifier":     ModifierOutput,
    "acquisition":  InitiatorOutput,
}

async def handle_turn(current_agent: str, history: list, user_input: str):

    if not user_input and not history:
        user_input = "start"


    if user_input:
        history.append({"role": "user", "content": user_input})

    agent  = AGENT_MAP[current_agent]
    result = Runner.run_streamed(agent, input=history)

    print("\n")

    async for event in result.stream_events():
        if isinstance(event, RunItemStreamEvent):
            if event.item.type == "tool_call_item":
                print(f"[Tool Call]   → {event.item.raw_item.name}({event.item.raw_item.arguments})")
            elif event.item.type == "tool_call_output_item":
                print(f"[Tool Result] → {event.item.output[:200]}...")

    final = result.final_output_as(OUTPUT_MAP[current_agent])

    history = result.to_input_list()

    # print(f"\n[DEBUG] Agent: {current_agent}")
    # print(f"[DEBUG] Final output: {final}")
    # print(f"[DEBUG] History length: {len(history)}")

    if current_agent == "orchestrator" and final.stop_flag:
        next_agent = "modifier" if final.type == "renewal" else "acquisition"
        return await handle_turn(next_agent, [], "")

    if current_agent == "modifier" and final.stop_flag and final.handoff_to_new:
        return await handle_turn("acquisition", [], "")

        if current_agent == "acquisition" and final.stop_flag:
            new_order = add_new_order(
            item_name=final.item_name,
            category=final.category,
            quantity=final.quantity,
        )

        reply = (
            f"{final.reply}\n\n"
            f"New order saved:\n"
            f"Transaction ID: {new_order['TransactionID']}\n"
            f"Item Name: {new_order['ItemName']}\n"
            f"Category: {new_order['Category']}\n"
            f"Quantity: {new_order['Quantity']}\n"
            f"Unit Price: {new_order['UnitPrice']}\n"
            f"Total Cost: {new_order['TotalCost']}\n"
            f"Purchase Date: {new_order['PurchaseDate']}\n"
            f"Supplier: {new_order['Supplier']}\n"
            f"Buyer: {new_order['Buyer']}"
        )

        return reply, "orchestrator", []
    
    return final.reply, current_agent, history
