"""**Tools** are classes that an Agent uses to interact with the world.

Each tool has a **description**. Agent uses the description to choose the right
tool for the job.

**Class hierarchy:**

.. code-block::

    ToolMetaclass --> BaseTool --> <name>Tool  # Examples: AIPluginTool, BaseGraphQLTool
                                   <name>      # Examples: BraveSearch, HumanInputRun

**Main helpers:**

.. code-block::

    CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
"""

from langchain_core.tools import (
    StructuredTool as StructuredTool,
)
from langchain_core.tools import (
    Tool as Tool,
)
from langchain_core.tools.convert import tool as tool


__all__ = [
    "StructuredTool",
    "Tool",
    "tool",
]
