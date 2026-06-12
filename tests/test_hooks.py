import json, subprocess, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HALT = REPO / "hooks" / "halt-reminder.py"
AUDIT = REPO / "hooks" / "turn-audit.py"

def run_hook(script, payload):
    p = subprocess.run(["python3", str(script)], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=10)
    return p.returncode, p.stdout

def write_transcript(tmpdir, events):
    path = Path(tmpdir) / "t.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events))
    return str(path)

def assistant(blocks):
    return {"type": "assistant", "message": {"content": blocks}}

def user_text(text):
    return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}

def user_string(text, meta=False):
    evt = {"type": "user", "message": {"content": text}}
    if meta:
        evt["isMeta"] = True
    return evt

GOOD_VERIFY = "⟦verify claims=1 cited=1 pw=0⟧"
GATE = "⟦gate tools=edit scope=\"x\" excluded=none risk=routine⟧"

class HaltReminderTest(unittest.TestCase):
    def test_error_response_injects_context(self):
        rc, out = run_hook(HALT, {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                  "tool_input": {}, "tool_response": {"is_error": True}})
        self.assertEqual(rc, 0)
        body = json.loads(out)
        self.assertIn("errors.md", body["hookSpecificOutput"]["additionalContext"])

    def test_success_response_silent(self):
        rc, out = run_hook(HALT, {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                  "tool_input": {}, "tool_response": {"type": "text", "text": "ok"}})
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_iserror_flag_injects(self):
        rc, out = run_hook(HALT, {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                  "tool_input": {}, "tool_response": {"isError": True}})
        self.assertEqual(rc, 0)
        body = json.loads(out)
        self.assertIn("errors.md", body["hookSpecificOutput"]["additionalContext"])

    def test_type_error_injects(self):
        rc, out = run_hook(HALT, {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                                  "tool_input": {}, "tool_response": {"type": "error"}})
        self.assertEqual(rc, 0)
        body = json.loads(out)
        self.assertIn("errors.md", body["hookSpecificOutput"]["additionalContext"])

class TurnAuditTest(unittest.TestCase):
    def _run(self, events, active=False):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            payload = {"hook_event_name": "Stop", "stop_hook_active": active,
                       "transcript_path": write_transcript(d, events)}
            return run_hook(AUDIT, payload)

    def test_clean_turn_passes(self):
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": "answer " + GOOD_VERIFY}])])
        self.assertEqual(out.strip(), "")

    def test_missing_verify_blocks(self):
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": "answer, no marker"}])])
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_zero_claims_long_prose_blocks(self):
        long_text = "x" * 700 + " ⟦verify claims=0 cited=0 pw=0⟧"
        rc, out = self._run([user_text("q"), assistant([{"type": "text", "text": long_text}])])
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_zero_claims_code_block_passes(self):
        code_text = ("see below ```python\n" + "x = 1\n" * 120 + "```"
                     " ⟦verify claims=0 cited=0 pw=0⟧")
        rc, out = self._run([user_text("q"), assistant([{"type": "text", "text": code_text}])])
        self.assertEqual(out.strip(), "")

    def test_arithmetic_violation_blocks(self):
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": "a ⟦verify claims=3 cited=1 pw=0⟧"}])])
        self.assertEqual(json.loads(out)["decision"], "block")

    def test_state_tool_without_gate_advises(self):
        # gate findings are advisory (transcript prose can lag/branch); no block
        rc, out = self._run([user_text("q"),
            assistant([{"type": "tool_use", "name": "Edit", "input": {}},
                       {"type": "text", "text": "done " + GOOD_VERIFY}])])
        body = json.loads(out)
        self.assertNotIn("decision", body)
        self.assertIn("no preceding ⟦gate⟧",
                      body["hookSpecificOutput"]["additionalContext"])

    def test_tool_only_span_silent(self):
        # no text blocks landed: nothing auditable — stay silent
        rc, out = self._run([user_text("q"),
            assistant([{"type": "tool_use", "name": "Edit", "input": {}}])])
        self.assertEqual(out.strip(), "")

    def test_missing_verify_trailing_tool_silent(self):
        # final message not landed (last block is tool_use): no missing-verify block
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": "working on it"},
                       {"type": "tool_use", "name": "Bash", "input": {}}])])
        self.assertEqual(out.strip(), "")

    def test_state_tool_with_gate_passes(self):
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": GATE},
                       {"type": "tool_use", "name": "Edit", "input": {}},
                       {"type": "text", "text": "done " + GOOD_VERIFY}])])
        self.assertEqual(out.strip(), "")

    def test_meta_event_does_not_fragment_turn(self):
        # gate emitted, then an injected meta event (hook feedback / reminder),
        # then the Edit: the meta event must not break the span — gate still counts
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": GATE}]),
            user_string("PostToolUse hook blocking error: ...", meta=True),
            assistant([{"type": "tool_use", "name": "Edit", "input": {}},
                       {"type": "text", "text": "done " + GOOD_VERIFY}])])
        self.assertEqual(out.strip(), "")

    def test_string_content_user_message_is_boundary(self):
        # a real user message stored as a plain string ends the turn: the gate
        # before it is out of scope, so the Edit after it draws the advisory
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": GATE}]),
            user_string("a real user instruction"),
            assistant([{"type": "tool_use", "name": "Edit", "input": {}},
                       {"type": "text", "text": "done " + GOOD_VERIFY}])])
        body = json.loads(out)
        self.assertNotIn("decision", body)
        self.assertIn("no preceding ⟦gate⟧",
                      body["hookSpecificOutput"]["additionalContext"])

    def test_stop_hook_active_exits_silently(self):
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": "no marker"}])], active=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_quoted_verify_in_fence_ignored(self):
        # Real marker before fence; broken example inside fence must not be picked as last
        text = ("real answer ⟦verify claims=1 cited=1 pw=0⟧ and an example:\n"
                "```\n⟦verify claims=5 cited=1 pw=0⟧\n```")
        rc, out = self._run([user_text("q"), assistant([{"type": "text", "text": text}])])
        self.assertEqual(out.strip(), "")

    def test_quoted_gate_in_fence_not_a_gate(self):
        # Gate marker only inside fence — must not satisfy gate requirement for Edit
        gate_in_fence = ("example:\n"
                         "```\n⟦gate tools=edit scope=\"x\" excluded=none risk=routine⟧\n```")
        rc, out = self._run([user_text("q"),
            assistant([{"type": "text", "text": gate_in_fence},
                       {"type": "tool_use", "name": "Edit", "input": {}},
                       {"type": "text", "text": "done ⟦verify claims=1 cited=1 pw=0⟧"}])])
        body = json.loads(out)
        self.assertNotIn("decision", body)
        self.assertIn("no preceding ⟦gate⟧",
                      body["hookSpecificOutput"]["additionalContext"])

if __name__ == "__main__":
    unittest.main()
