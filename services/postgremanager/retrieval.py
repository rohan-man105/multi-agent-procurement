from services.postgremanager.utils import get_connection



def run_sql_query(sql_query):
    conn = get_connection()
    curr = conn.cursor()
    curr.execute(sql_query)
    rows = curr.fetchall()
    columns = [desc[0] for desc in curr.description]
    curr.close()
    conn.close()
    return rows, columns

def format_answer(rows, columns):
    if not rows:
        return "No records found."

    records = [dict(zip(columns, row)) for row in rows]

    formatted = []
    for i, record in enumerate(records, start=1):
        lines = [f"Record {i}:"]
        for col, val in record.items():
            lines.append(f"  - {col}: {val}")
        formatted.append("\n".join(lines))

    return "\n\n".join(formatted)
