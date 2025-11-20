### ✅ Completed Features (Live in v2.1)

**1. Core Architecture Overhaul**
*   **SDK Integration:** Replaced `subprocess` calls with the official `google-generativeai` Python library. This enabled streaming and better error handling.
*   **Auto-Dependency Check:** The script now self-checks for required libraries (`rich`, `google-generativeai`) and installs them automatically if missing.
*   **Project-Specific Instructions:** Implemented the `GEMINI.md` loader, allowing custom "System Prompts" per project.
*   **GEMINI.md Template Generation:** Automatically creates a template `GEMINI.md` file when new projects are created.

**2. User Experience (UX) & UI**
*   **Rich Terminal UI:** Integrated the `rich` library for colored output, markdown rendering, and panels.
*   **Streaming Output:** Text now streams to the console like a typewriter, preventing the "wait 2 minutes for a wall of text" friction.
*   **Smart Workflow Menu:** The menu now visually indicates project state:
    *   `⭐ READY TO GENERATE` (Next logical step)
    *   `✔ Completed` (Files approved)
    *   `✎ Draft Waiting` (Generated but not approved)
    *   `↻ In Progress (2/8)` (Specific tracking for multi-scene phases)
*   **Project Name Formatting:** Project names display in title case with spaces (e.g., "My Awesome Story" instead of "My_Awesome_Story").
*   **Menu Numbering Alignment:** Menu option numbers now match phase numbers (e.g., `[2] Phase 2: Story Skeleton`).

**3. The "Human-in-the-Loop" Workflow**
*   **Interactive Review System:** Instead of dumping files blindly, the script asks you to:
    *   **[A]pprove:** Automatically moves the file to the `approved` folder.
    *   **[X] Approve All Remaining:** Approves current item and auto-approves all remaining items in the generation phase.
    *   **[R]etry:** Immediately regenerates the output.
    *   **[E]dit:** Pauses the script, allowing you to edit the draft in your external text editor, then resumes to approve your custom changes.
*   **Approve All Feature:** Available in First Draft, Second Draft, and Final Draft generation phases for uninterrupted workflow.

**4. Logic & Content Improvements**
*   **Full 15-Phase Support:** Implemented generators for every stage from "Premise" to "Final Draft."
*   **Iterative Scene Generation:** Phase 12 (First Draft) was converted from a bulk "write the whole book" command to a loop that writes one scene at a time based on your Blocking Outlines.
*   **Model Fallback System:** Automatic fallback to `gemini-2.5-pro` if `gemini-3-pro-preview` hits quota limits, with user notification.

**5. Style Matching** ✅
*   **Goal:** Allow the user to provide a sample of their writing (or an author they admire) to enforce a specific prose style.
*   **Implementation:** Supports both global (`Tools/Writing_Samples.md`) and project-specific (`STYLE.md`) style samples. Automatically included in draft and editing phases.

**6. Global Configuration** ✅
*   **Goal:** Centralized configuration management for easy access and updates.
*   **Implementation:** All settings consolidated at the top of `spinneret.py` with inline documentation. Settings menu (`[S]`) displays current configuration. Supports latest models: `gemini-2.5-flash` and `gemini-3-pro-preview`.

---

### 🔜 Planned Features (Roadmap for v2.2+)

**v2.2: Parallel Processing (Speed)**
*   **Goal:** Generate non-linear assets simultaneously.
*   **Use Case:** Generate all 10 Character Profiles or 5 Locations at the same time, rather than one by one.
*   **Impact:** Significantly reduces generation time for phases with multiple independent items (Character Development, Locations, Character Viewpoints).

**v2.3: The "Critique & Refine" Loop (Quality)**
*   **Goal:** Automate the editing process within the generation phase.
*   **Mechanism:** Instead of just generating the text, the script would:
    1.  Generate Draft (Flash model).
    2.  Ask Pro Model: "Critique this."
    3.  Ask Flash Model: "Rewrite based on critique."
    4.  Present final result to user.
*   **Impact:** Higher quality first-pass output, reducing need for manual editing.

**v2.4: Dynamic Context Injection (Coherence)**
*   **Goal:** Prevent token limit issues and confusion in later chapters.
*   **Mechanism:** For Scene 20, automatically inject the text of Scene 19 (for continuity) but *drop* Scene 1 to save space. Currently, we load broad context, but a "Sliding Window" is more precise.
*   **Impact:** Better scene-to-scene continuity in longer works while staying within token limits.

### Current Status
You have a **fully functional, stable v2.1** that covers the entire writing lifecycle with a robust review loop, style matching, and improved UX.

**Recommendation:** Continue testing v2.1 with real projects to identify any subtle UX bugs or workflow improvements before moving to v2.2 features.