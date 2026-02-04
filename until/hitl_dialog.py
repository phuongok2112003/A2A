import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any


class HitlDialog:
    def __init__(self, hitl_request: dict):
        self.hitl_request = hitl_request
        self.result: List[Dict[str, Any]] | None = None

        self.root = tk.Tk()
        self.root.title("Agent Approval Required")
        self.root.geometry("600x540")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    # -----------------------------
    # UI Construction
    # -----------------------------

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Agent requests approval for actions",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        self.sections: List[Dict[str, Any]] = []

        for req in self.hitl_request["action_requests"]:
            section = self._build_action_section(container, req)
            self.sections.append(section)

        ttk.Button(container, text="Submit", command=self._submit).pack(pady=12)

    def _build_action_section(self, parent: ttk.Frame, req: dict):

        wrapper = ttk.LabelFrame(parent, text=req["name"])
        wrapper.pack(fill="x", pady=10)

        ttk.Label(wrapper, text="Arguments:").pack(anchor="w")

        ttk.Label(
            wrapper,
            text=str(req["args"]),
            foreground="#555",
            wraplength=560,
        ).pack(anchor="w", pady=(0, 8))

        # -----------------------------
        # Radio group
        # -----------------------------
        decision_var = tk.StringVar(value="approve")

        radios = ttk.Frame(wrapper)
        radios.pack(anchor="w")

        for v in ("approve", "reject", "edit"):
            ttk.Radiobutton(
                radios,
                text=v.capitalize(),
                variable=decision_var,
                value=v,
            ).pack(side="left", padx=8)

        # -----------------------------
        # Dynamic area
        # -----------------------------
        dynamic_frame = ttk.Frame(wrapper)
        dynamic_frame.pack(fill="x", pady=6)

        # Reject widgets
        reject_label = ttk.Label(dynamic_frame, text="Reject reason:")
        reject_var = tk.StringVar()
        reject_entry = ttk.Entry(dynamic_frame, textvariable=reject_var)

        # Edit widgets
        edit_rows: Dict[str, ttk.Frame] = {}
        edit_vars: Dict[str, tk.StringVar] = {}

        for key, val in req["args"].items():
            row = ttk.Frame(dynamic_frame)

            ttk.Label(row, text=key, width=18).pack(side="left")

            v = tk.StringVar(value=str(val))
            ent = ttk.Entry(row, textvariable=v)
            ent.pack(side="left", fill="x", expand=True)

            edit_rows[key] = row
            edit_vars[key] = v

        # Hide all initially
        reject_label.pack_forget()
        reject_entry.pack_forget()

        for row in edit_rows.values():
            row.pack_forget()

        # -----------------------------
        # Radio handler
        # -----------------------------

        def on_change(*_):

            # Hide everything
            reject_label.pack_forget()
            reject_entry.pack_forget()

            for row in edit_rows.values():
                row.pack_forget()

            if decision_var.get() == "reject":
                reject_label.pack(anchor="w")
                reject_entry.pack(fill="x")

            elif decision_var.get() == "edit":
                for row in edit_rows.values():
                    row.pack(fill="x", pady=2)

        decision_var.trace_add("write", on_change)

        return {
            "req": req,
            "decision_var": decision_var,
            "reject_var": reject_var,
            "edit_vars": edit_vars,
        }

    # -----------------------------
    # Submit
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
                    {
                        "type": "reject",
                        "message": reason,
                    }
                )

            elif decision == "edit":
                args: Dict[str, Any] = {}

                for k, v in section["edit_vars"].items():
                    args[k] = v.get()

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

    def _on_close(self):
        messagebox.showwarning(
            "Approval required",
            "You must submit a decision before closing.",
        )

    # -----------------------------
    # Public API
    # -----------------------------

    def show(self) -> List[Dict[str, Any]]:
        self.root.mainloop()
        return self.result or []
