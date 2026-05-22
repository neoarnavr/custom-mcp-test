from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import PlainTextResponse
from datetime import datetime
import uvicorn
import uuid
import os

mcp = FastMCP(
    name="QA Test Management MCP",
    stateless_http=True,
)

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------
test_cases = {
    "TC-001": {
        "id": "TC-001",
        "title": "Verify user login with valid credentials",
        "module": "Authentication",
        "priority": "High",
        "status": "Active",
        "steps": ["Navigate to login page", "Enter valid username and password", "Click Login button", "Verify dashboard is displayed"],
        "expected_result": "User is redirected to dashboard",
        "created_by": "arnav",
        "created_at": "2025-01-10"
    },
    "TC-002": {
        "id": "TC-002",
        "title": "Verify user login with invalid credentials",
        "module": "Authentication",
        "priority": "High",
        "status": "Active",
        "steps": ["Navigate to login page", "Enter invalid username and password", "Click Login button", "Verify error message is displayed"],
        "expected_result": "Error message 'Invalid credentials' is shown",
        "created_by": "arnav",
        "created_at": "2025-01-10"
    },
    "TC-003": {
        "id": "TC-003",
        "title": "Verify password reset flow",
        "module": "Authentication",
        "priority": "Medium",
        "status": "Active",
        "steps": ["Click Forgot Password on login page", "Enter registered email", "Check email for reset link", "Set new password", "Login with new password"],
        "expected_result": "User can login with new password",
        "created_by": "arnav",
        "created_at": "2025-01-11"
    },
    "TC-004": {
        "id": "TC-004",
        "title": "Verify checkout with valid payment",
        "module": "Payments",
        "priority": "Critical",
        "status": "Active",
        "steps": ["Add item to cart", "Proceed to checkout", "Enter valid card details", "Confirm order", "Verify order confirmation page"],
        "expected_result": "Order is placed and confirmation email is sent",
        "created_by": "arnav",
        "created_at": "2025-01-12"
    },
    "TC-005": {
        "id": "TC-005",
        "title": "Verify API response time under load",
        "module": "Performance",
        "priority": "Medium",
        "status": "Draft",
        "steps": ["Simulate 100 concurrent users", "Hit /api/products endpoint", "Measure response times", "Check for errors"],
        "expected_result": "Response time < 2s for 95th percentile",
        "created_by": "arnav",
        "created_at": "2025-01-13"
    },
}

test_runs = {}

defects = {
    "DEF-001": {
        "id": "DEF-001",
        "title": "Login button unresponsive on Safari",
        "severity": "High",
        "status": "Open",
        "module": "Authentication",
        "linked_tc": "TC-001",
        "reported_by": "arnav",
        "reported_at": "2025-01-15",
        "description": "Login button does not respond to click events on Safari 16.x"
    },
    "DEF-002": {
        "id": "DEF-002",
        "title": "Payment fails for Amex cards",
        "severity": "Critical",
        "status": "In Progress",
        "module": "Payments",
        "linked_tc": "TC-004",
        "reported_by": "arnav",
        "reported_at": "2025-01-16",
        "description": "Amex card payments throw a 500 error at the payment gateway"
    },
    "DEF-003": {
        "id": "DEF-003",
        "title": "Password reset email not received on Gmail",
        "severity": "Medium",
        "status": "Open",
        "module": "Authentication",
        "linked_tc": "TC-003",
        "reported_by": "arnav",
        "reported_at": "2025-01-17",
        "description": "Reset email is sent but lands in spam on Gmail accounts"
    },
}


# ---------------------------------------------------------------------------
# TEST CASE TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def get_test_case(test_case_id: str) -> str:
    """Get full details of a test case by its ID. Example: TC-001"""
    tc = test_cases.get(test_case_id.upper())
    if not tc:
        return f"Test case '{test_case_id}' not found."
    steps_formatted = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(tc["steps"])])
    return (
        f"ID: {tc['id']}\n"
        f"Title: {tc['title']}\n"
        f"Module: {tc['module']}\n"
        f"Priority: {tc['priority']}\n"
        f"Status: {tc['status']}\n"
        f"Steps:\n{steps_formatted}\n"
        f"Expected Result: {tc['expected_result']}\n"
        f"Created By: {tc['created_by']} on {tc['created_at']}"
    )


@mcp.tool()
def list_test_cases(module: str = "", priority: str = "", status: str = "") -> str:
    """
    List test cases with optional filters.
    module: Authentication, Payments, Performance (leave empty for all)
    priority: Critical, High, Medium, Low (leave empty for all)
    status: Active, Draft (leave empty for all)
    """
    filtered = list(test_cases.values())
    if module:
        filtered = [tc for tc in filtered if tc["module"].lower() == module.lower()]
    if priority:
        filtered = [tc for tc in filtered if tc["priority"].lower() == priority.lower()]
    if status:
        filtered = [tc for tc in filtered if tc["status"].lower() == status.lower()]
    if not filtered:
        return "No test cases found matching the given filters."
    lines = [f"Found {len(filtered)} test case(s):\n"]
    for tc in filtered:
        lines.append(f"  {tc['id']} | [{tc['priority']}] {tc['title']} | Module: {tc['module']} | Status: {tc['status']}")
    return "\n".join(lines)


@mcp.tool()
def create_test_case(title: str, module: str, priority: str, steps: str, expected_result: str) -> str:
    """
    Create a new test case.
    priority: Critical, High, Medium, Low
    steps: comma separated list of steps
    module: the feature module being tested
    """
    new_id = f"TC-{str(len(test_cases) + 1).zfill(3)}"
    steps_list = [s.strip() for s in steps.split(",")]
    test_cases[new_id] = {
        "id": new_id,
        "title": title,
        "module": module,
        "priority": priority,
        "status": "Draft",
        "steps": steps_list,
        "expected_result": expected_result,
        "created_by": "copilot-agent",
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    return f"Test case created!\nID: {new_id}\nTitle: {title}\nModule: {module}\nPriority: {priority}\nStatus: Draft"


@mcp.tool()
def update_test_case_status(test_case_id: str, status: str) -> str:
    """
    Update the status of a test case.
    status: Active, Draft, Deprecated
    """
    tc = test_cases.get(test_case_id.upper())
    if not tc:
        return f"Test case '{test_case_id}' not found."
    old_status = tc["status"]
    tc["status"] = status
    return f"Test case {test_case_id} status updated: {old_status} → {status}"


# ---------------------------------------------------------------------------
# TEST RUN TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def create_test_run(name: str, test_case_ids: str) -> str:
    """
    Create a new test run with a set of test cases.
    test_case_ids: comma separated list e.g. TC-001,TC-002,TC-003
    """
    run_id = f"RUN-{str(uuid.uuid4())[:8].upper()}"
    tc_ids = [t.strip().upper() for t in test_case_ids.split(",")]
    invalid = [t for t in tc_ids if t not in test_cases]
    if invalid:
        return f"Invalid test case IDs: {', '.join(invalid)}"
    test_runs[run_id] = {
        "id": run_id,
        "name": name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "In Progress",
        "results": {tc_id: "Pending" for tc_id in tc_ids}
    }
    return (
        f"Test run created!\n"
        f"Run ID: {run_id}\n"
        f"Name: {name}\n"
        f"Test Cases: {', '.join(tc_ids)}\n"
        f"Status: In Progress"
    )


@mcp.tool()
def update_test_run_result(run_id: str, test_case_id: str, result: str) -> str:
    """
    Update the result of a test case within a test run.
    result: Pass, Fail, Blocked, Skipped
    """
    run = test_runs.get(run_id.upper())
    if not run:
        return f"Test run '{run_id}' not found."
    tc_id = test_case_id.upper()
    if tc_id not in run["results"]:
        return f"Test case '{tc_id}' not part of run '{run_id}'."
    run["results"][tc_id] = result
    if all(v != "Pending" for v in run["results"].values()):
        run["status"] = "Completed"
    return f"Updated {tc_id} in {run_id}: result set to '{result}'"


@mcp.tool()
def get_test_run_summary(run_id: str) -> str:
    """Get a summary of a test run including pass/fail counts."""
    run = test_runs.get(run_id.upper())
    if not run:
        return f"Test run '{run_id}' not found."
    results = run["results"]
    counts = {"Pass": 0, "Fail": 0, "Blocked": 0, "Skipped": 0, "Pending": 0}
    for r in results.values():
        counts[r] = counts.get(r, 0) + 1
    total = len(results)
    pass_rate = round((counts["Pass"] / total) * 100) if total > 0 else 0
    return (
        f"Run ID: {run['id']}\n"
        f"Name: {run['name']}\n"
        f"Status: {run['status']}\n"
        f"Created: {run['created_at']}\n\n"
        f"Results ({total} total):\n"
        f"  Pass:    {counts['Pass']}\n"
        f"  Fail:    {counts['Fail']}\n"
        f"  Blocked: {counts['Blocked']}\n"
        f"  Skipped: {counts['Skipped']}\n"
        f"  Pending: {counts['Pending']}\n\n"
        f"Pass Rate: {pass_rate}%"
    )


# ---------------------------------------------------------------------------
# DEFECT TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def list_defects(severity: str = "", status: str = "", module: str = "") -> str:
    """
    List defects with optional filters.
    severity: Critical, High, Medium, Low
    status: Open, In Progress, Resolved, Closed
    module: Authentication, Payments, Performance
    """
    filtered = list(defects.values())
    if severity:
        filtered = [d for d in filtered if d["severity"].lower() == severity.lower()]
    if status:
        filtered = [d for d in filtered if d["status"].lower() == status.lower()]
    if module:
        filtered = [d for d in filtered if d["module"].lower() == module.lower()]
    if not filtered:
        return "No defects found matching the given filters."
    lines = [f"Found {len(filtered)} defect(s):\n"]
    for d in filtered:
        lines.append(f"  {d['id']} | [{d['severity']}] {d['title']} | Status: {d['status']} | Module: {d['module']}")
    return "\n".join(lines)


@mcp.tool()
def create_defect(title: str, severity: str, module: str, description: str, linked_tc: str = "") -> str:
    """
    Log a new defect.
    severity: Critical, High, Medium, Low
    linked_tc: optional test case ID that uncovered this defect e.g. TC-001
    """
    new_id = f"DEF-{str(len(defects) + 1).zfill(3)}"
    defects[new_id] = {
        "id": new_id,
        "title": title,
        "severity": severity,
        "status": "Open",
        "module": module,
        "linked_tc": linked_tc,
        "reported_by": "copilot-agent",
        "reported_at": datetime.now().strftime("%Y-%m-%d"),
        "description": description
    }
    return (
        f"Defect logged!\n"
        f"ID: {new_id}\n"
        f"Title: {title}\n"
        f"Severity: {severity}\n"
        f"Module: {module}\n"
        f"Status: Open\n"
        f"Linked TC: {linked_tc if linked_tc else 'None'}"
    )


@mcp.tool()
def update_defect_status(defect_id: str, status: str) -> str:
    """
    Update the status of a defect.
    status: Open, In Progress, Resolved, Closed
    """
    defect = defects.get(defect_id.upper())
    if not defect:
        return f"Defect '{defect_id}' not found."
    old_status = defect["status"]
    defect["status"] = status
    return f"Defect {defect_id} status updated: {old_status} → {status}"


@mcp.tool()
def get_qa_summary() -> str:
    """Get an overall QA health summary — test cases, defects, and open issues."""
    total_tc = len(test_cases)
    active_tc = sum(1 for tc in test_cases.values() if tc["status"] == "Active")
    draft_tc = sum(1 for tc in test_cases.values() if tc["status"] == "Draft")
    total_defects = len(defects)
    open_defects = sum(1 for d in defects.values() if d["status"] == "Open")
    critical_defects = sum(1 for d in defects.values() if d["severity"] == "Critical" and d["status"] != "Closed")
    in_progress = sum(1 for d in defects.values() if d["status"] == "In Progress")
    total_runs = len(test_runs)
    return (
        f"======= QA Health Summary =======\n"
        f"\nTest Cases ({total_tc} total):\n"
        f"  Active:  {active_tc}\n"
        f"  Draft:   {draft_tc}\n"
        f"\nDefects ({total_defects} total):\n"
        f"  Open:        {open_defects}\n"
        f"  In Progress: {in_progress}\n"
        f"  Critical:    {critical_defects}\n"
        f"\nTest Runs: {total_runs}\n"
        f"================================="
    )


# ---------------------------------------------------------------------------
# Health check + Starlette app
# ---------------------------------------------------------------------------
import contextlib

async def health(request):
    return PlainTextResponse("healthy")


@contextlib.asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/health", health),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ],
    redirect_slashes=False,  # ← add this
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# run
