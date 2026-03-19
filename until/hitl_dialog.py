import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional


class HitlDialog:
    """
    Human-in-the-loop approval dialog driven by Interrupt payload.
    """

    def __init__(self, interrupt: Any):
        """
        interrupt: Interrupt object extracted from __interrupt__[0]
        """

        self.interrupt = interrupt
        self.hitl_payload = self._parse_interrupt(interrupt)

        self.result: Optional[List[Dict[str, Any]]] = None
        self.sections: List[Dict[str, Any]] = []

        self.root = tk.Tk()
        self.root.title("Agent Approval Required")
        self.root.geometry("640x560")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    # -----------------------------
    # Interrupt parsing
    # -----------------------------

    def _parse_interrupt(self, interrupt: Any) -> Dict[str, Any]:
        """
        Normalize Interrupt payload into UI-friendly structure.
        """

        if not hasattr(interrupt, "value"):
            raise ValueError("Invalid Interrupt object")

        value = interrupt.value

        action_requests = value.get("action_requests", [])
        review_configs = value.get("review_configs", [])

        review_map = {
            cfg["action_name"]: cfg.get(
                "allowed_decisions",
                ["approve", "reject", "edit"],
            )
            for cfg in review_configs
        }

        for req in action_requests:
            req["allowed_decisions"] = review_map.get(
                req["name"],
                ["approve", "reject", "edit"],
            )

        return {"action_requests": action_requests}

    # -----------------------------
    # UI construction
    # -----------------------------

    def _build_ui(self):

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Agent requires approval",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        for req in self.hitl_payload["action_requests"]:
            section = self._build_action_section(container, req)
            self.sections.append(section)

        ttk.Button(
            container,
            text="Submit Decision",
            command=self._submit,
        ).pack(pady=12)

    def _build_action_section(self, parent: ttk.Frame, req: dict):

        wrapper = ttk.LabelFrame(parent, text=req["name"])
        wrapper.pack(fill="x", pady=10)

        ttk.Label(wrapper, text="Arguments:").pack(anchor="w")

        ttk.Label(
            wrapper,
            text=str(req.get("args", {})),
            foreground="#555",
            wraplength=600,
        ).pack(anchor="w", pady=(0, 8))

        allowed = req.get("allowed_decisions", ["approve", "reject", "edit"])
        decision_var = tk.StringVar(value=allowed[0])

        radios = ttk.Frame(wrapper)
        radios.pack(anchor="w")

        for v in allowed:
            ttk.Radiobutton(
                radios,
                text=v.capitalize(),
                variable=decision_var,
                value=v,
            ).pack(side="left", padx=8)

        dynamic_frame = ttk.Frame(wrapper)
        dynamic_frame.pack(fill="x", pady=6)

        reject_label = ttk.Label(dynamic_frame, text="Reject reason:")
        reject_var = tk.StringVar()
        reject_entry = ttk.Entry(dynamic_frame, textvariable=reject_var)

        edit_rows: Dict[str, ttk.Frame] = {}
        edit_vars: Dict[str, tk.StringVar] = {}

        for key, val in req.get("args", {}).items():
            row = ttk.Frame(dynamic_frame)

            ttk.Label(row, text=key, width=18).pack(side="left")

            v = tk.StringVar(value=str(val))
            ttk.Entry(row, textvariable=v).pack(
                side="left", fill="x", expand=True
            )

            edit_rows[key] = row
            edit_vars[key] = v

        def hide_all():
            reject_label.pack_forget()
            reject_entry.pack_forget()
            for row in edit_rows.values():
                row.pack_forget()

        def on_change(*_):
            hide_all()

            if decision_var.get() == "reject":
                reject_label.pack(anchor="w")
                reject_entry.pack(fill="x")

            elif decision_var.get() == "edit":
                for row in edit_rows.values():
                    row.pack(fill="x", pady=2)

        decision_var.trace_add("write", on_change)

        hide_all()

        return {
            "req": req,
            "decision_var": decision_var,
            "reject_var": reject_var,
            "edit_vars": edit_vars,
        }

    # -----------------------------
    # Submission
    # -----------------------------

    def _submit(self):

        decisions: List[Dict[str, Any]] = []

        for section in self.sections:

            req = section["req"]
            decision = section["decision_var"].get()

            if decision == "approve":
                decisions.append({"type": "approve"})

            elif decision == "reject":

                reason = section["reject_var"].get().strip()

                if not reason:
                    messagebox.showerror(
                        "Validation error",
                        f"Reject reason required for {req['name']}",
                    )
                    return

                decisions.append(
                    {"type": "reject", "message": reason}
                )

            elif decision == "edit":

                args = {
                    k: v.get()
                    for k, v in section["edit_vars"].items()
                }

                decisions.append(
                    {
                        "type": "edit",
                        "edited_action": {
                            "name": req["name"],
                            "args": args,
                        },
                    }
                )

        self.result = decisions
        self.root.destroy()

    # -----------------------------
    # Window control
    # -----------------------------

    def _on_close(self):
        messagebox.showwarning(
            "Approval required",
            "Submit a decision before closing.",
        )

    # -----------------------------
    # Public API
    # -----------------------------

    def show(self) -> List[Dict[str, Any]]:
        self.root.mainloop()
        return self.result or []
