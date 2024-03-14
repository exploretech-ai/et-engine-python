

class Tool:

    def __init__(self, tool_id, session) -> None:
        self.session = session
        self.url = session.API_ENDPOINT + f"tools/{tool_id}"