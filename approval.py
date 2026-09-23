from typing import Any, Dict


class ApprovalManager:

    HIGH_IMPACT_ACTIONS = {
        "send_email",
        "delete_data",
        "modify_data",
        "make_transaction",
    }

    def check_approval(
        self,
        action: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not action:
            return {
                "status": "rejected",
                "action": action,
                "approval_required": False,
                "message": "Action is required."
            }

        if action in self.HIGH_IMPACT_ACTIONS:
            return {
                "status": "approval_required",
                "action": action,
                "approval_required": True,
                "input": input_data,
                "message": "Human approval is required before this action."
            }

        return {
            "status": "approved",
            "action": action,
            "approval_required": False,
            "input": input_data,
            "message": "Action does not require human approval."
        }
