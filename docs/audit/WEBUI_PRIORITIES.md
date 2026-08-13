# ETHAN WebUI Implementation Priorities

This document defines the execution order for the WebUI transformation, based on architectural criticality and user experience.

## P0: Fundamental Architecture & Blocking Issues
*Critical items that prevent the system from functioning or block the entire architecture.*

- **API Proxy Configuration**: Fix the `next.config.js` rewrites to enable frontend $\rightarrow$ API communication.
- **Authentication Bridge**: Ensure the existing ETHAN Login is fully integrated and the session is correctly passed to the API.
- **Minimal Connectivity Shim**: Implement a basic "Backend Shim" in the Open-WebUI backend to allow the frontend to perform a basic chat turn.
- **Statelessness Verification**: Ensure no business logic from ETHAN Core is leaked into the WebUI.

## P1: Functional Core
*Necessary features for a usable ETHAN WebUI.*

- **API Surface Expansion**: Create the missing routers in `interfaces/api/routers/` to expose the implemented Core logic (Automations, Analytics, Audio, etc.).
- **Open-WebUI $\rightarrow$ ETHAN API Mapping**: Complete the full translation of Open-WebUI backend endpoints to ETHAN API calls.
- **Chat History & Persistence**: Implement the full flow from UI $\rightarrow$ Shim $\rightarrow$ ETHAN Core for chat history.
- **Model Selector**: Integrate the ETHAN Provider/Model list into the Open-WebUI selector.

## P2: Advanced Capabilities
*Important improvements that enhance the "AI OS" experience.*

- **Advanced RAG Integration**: Connect the "Knowledge" and "Documents" UI to the ETHAN RAG engine.
- **Memory Management**: Integrate the user memory system into the interface.
- **Skills & Tools**: Expose ETHAN Skills and MCP tools within the chat interface.
- **System Status**: Implement real-time monitoring of the ETHAN Runtime/Core.

## P3: UX & Polish
*Visual and interaction refinements.*

- **ETHAN Branding**: Apply the ETHAN visual identity to the Open-WebUI base.
- **Navigation Optimization**: Adapt the sidebar and menus to ETHAN's specific capabilities.
- **Cleanup**: Remove unused Open-WebUI components and legacy React frontend code.
- **Performance Tuning**: Optimize API calls and streaming latency.
