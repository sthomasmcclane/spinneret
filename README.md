# 🕷️ Spinneret v2.1

**An AI-powered creative writing workflow manager that guides you from story idea to final draft.**

Spinneret leverages Google's Gemini AI to automate and streamline the creative writing process, breaking down story development into 15 manageable phases—from initial premise generation to final draft editing. With a human-in-the-loop review system, you maintain creative control while the AI handles the heavy lifting.

---

## ✨ Features

### Core Workflow
- **15-Phase Writing Pipeline:** Structured workflow from premise to final draft
- **Iterative Scene Generation:** Writes scenes one at a time based on your blocking outlines
- **Project Management:** Multi-project support with state-aware workflow tracking
- **Smart Menu System:** Visual indicators show project status at a glance

### AI Integration
- **Latest Gemini Models:** Uses `gemini-2.5-flash` (fast) and `gemini-3-pro-preview` (smart)
- **Automatic Model Selection:** Chooses the right model for each task type
- **Model Fallback:** Gracefully falls back to `gemini-2.5-pro` if preview model hits quota limits
- **Streaming Output:** Real-time text generation with typewriter-style display

### Human-in-the-Loop
- **Interactive Review System:** Approve, edit, retry, or quit after each generation
- **Approve All:** Auto-approve remaining items for uninterrupted workflow
- **Edit Integration:** Pause to edit files in your external editor, then resume
- **State Management:** Non-destructive folder-based approval system

### Customization
- **Style Matching:** Provide writing samples to match your preferred prose style
- **Project-Specific Instructions:** Custom `GEMINI.md` files for project-level AI guidance
- **Template Generation:** Auto-creates `GEMINI.md` template when starting new projects
- **Configurable Settings:** Centralized configuration with easy-to-access settings menu

### User Experience
- **Rich Terminal UI:** Beautiful colored output with markdown rendering
- **Project Name Formatting:** Clean, readable project titles (title case with spaces)
- **Progress Tracking:** Visual status indicators for each phase
- **Auto-Dependency Installation:** Automatically installs required packages

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone or download this repository:**
   ```bash
   git clone <repository-url>
   cd spin
   ```

2. **Set your API key:**
   ```bash
   export GEMINI_API_KEY='your_api_key_here'
   ```
   
   Or add it to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) for persistence.

3. **Run Spinneret:**
   ```bash
   python3 spinneret.py
   ```
   
   The script will automatically install required dependencies (`google-generativeai` and `rich`) on first run.

---

## 📖 Usage

### Creating a New Project

1. Run `spinneret.py`
2. Select `[N] New Project` from the main menu
3. Enter a one-sentence story idea
4. Enter a project title
5. The script will:
   - Create a project directory
   - Generate a `GEMINI.md` template for project-specific instructions
   - Start with brainstorming and premise generation

### Working Through Phases

The workflow consists of 15 phases:

1. **Premise** - Generate multiple premise options from your story idea
2. **Story Skeleton** - Create the basic story structure
3. **Character Introductions** - Develop initial character profiles
4. **Short Synopsis** - Write a brief story summary
5. **Extended Synopsis** - Expand into a detailed synopsis
6. **Goal to Decision Cycle** - Map character goals and decisions
7. **Character Development** - Deep dive into character details
8. **Locations** - Define story settings and locations
9. **Advanced Plotting** - Develop complex plot elements
10. **Character Viewpoints** - Establish narrative perspectives
11. **Blocking Outline** - Create scene-by-scene blocking
12. **First Draft** - Generate full prose scenes iteratively
13. **Theme and Variations** - Analyze and refine themes
14. **Second Draft** - Rewrite with theme integration
15. **Final Draft** - Polish and finalize

### Review Options

After each generation, you'll see:
- `[A]pprove` - Save and move to approved folder
- `[X] Approve All Remaining` - Approve this and auto-approve all remaining items
- `[E]dit` - Pause to edit in your external editor
- `[R]etry` - Regenerate the output
- `[Q]uit` - Save draft and exit

### Project Structure

```
YourProject/
├── GEMINI.md                    # Project-specific AI instructions (customize this!)
├── Phase_01_Premise/
│   ├── drafts/
│   └── approved/
├── Phase_02_Story_Skeleton/
│   ├── draft/
│   └── approved/
├── ...
└── Phase_15_Final_Draft/
    ├── draft/
    └── approved/
```

---

## ⚙️ Configuration

### Settings Menu

Access the settings menu from the main menu by pressing `[S]`. This displays:
- API key status
- Current model configuration
- Phase-specific AI settings
- Style matching status
- Token management limits

### Customizing AI Behavior

**Project-Level Instructions:**
Edit `GEMINI.md` in your project directory to add custom instructions that apply to all AI generations for that project.

**Style Matching:**
- **Global:** Add `Tools/Writing_Samples.md` with your writing samples
- **Project-Specific:** Add `STYLE.md` in your project directory

**Model Configuration:**
Edit the `MODELS` dictionary at the top of `spinneret.py`:
```python
MODELS = {
    "fast": "gemini-2.5-flash",
    "smart": "gemini-3-pro-preview",
}
```

---

## 🛠️ Project Structure

```
spin/
├── spinneret.py          # Main script
├── roadmap.md            # Development roadmap
├── README.md             # This file
└── Tools/                # AI instruction files
    ├── 01 - Premise.md
    ├── 02 - The Story Skeleton.md
    ├── ...
    ├── Brainstormer.md
    ├── StoryGrid_AI_Instructions.md
    └── Writing_Samples.md
```

---

## 🗺️ Roadmap

### ✅ v2.1 (Current)
- Full 15-phase workflow
- Style matching
- Approve All feature
- Model fallback system
- Rich terminal UI
- Project management

### 🔜 v2.2 (Planned)
- **Parallel Processing:** Generate multiple independent items simultaneously

### 🔜 v2.3 (Planned)
- **Critique & Refine Loop:** Automated draft → critique → rewrite cycle

### 🔜 v2.4 (Planned)
- **Dynamic Context Injection:** Sliding window context management for better continuity

See [roadmap.md](roadmap.md) for detailed feature descriptions.

---

## 💡 Tips & Best Practices

1. **Start Small:** Test with a short story idea first to understand the workflow
2. **Review Regularly:** Don't skip the review step—it's where you maintain creative control
3. **Customize GEMINI.md:** Add project-specific rules, world-building details, or style preferences
4. **Use Style Samples:** Provide examples of writing you admire to guide the AI's prose style
5. **Approve All Sparingly:** Use "Approve All" when you're confident in the AI's output quality
6. **Edit When Needed:** The Edit feature lets you refine AI output before approval

---

## 🐛 Troubleshooting

**"Model Not Found" Error:**
- Check that you're using valid Gemini model names
- Run the script to see available models listed

**API Key Issues:**
- Ensure `GEMINI_API_KEY` is set in your environment
- The script will prompt you if the key is missing

**Quota Exceeded:**
- The script automatically falls back to `gemini-2.5-pro` if the preview model hits limits
- Wait 60 seconds and retry, or check your API quota

**Missing Dependencies:**
- The script auto-installs required packages on first run
- If issues persist, manually install: `pip install google-generativeai rich`

---

## 📝 License

### Software License

**Spinneret is free for personal and non-profit use. Commercial use requires a paid license.**

**Free Use (Personal & Non-Profit):**
- ✅ Individuals may use Spinneret for personal projects
- ✅ Non-profit organizations may use Spinneret for their activities
- ✅ Educational institutions may use Spinneret for teaching and research
- ✅ You can modify the source code for personal/non-profit use
- ⚠️ You must retain copyright notices

**Commercial Use:**
- 💼 Commercial use requires a paid license
- 💼 This includes: businesses, for-profit organizations, commercial writing services, paid content creation
- 📧 Contact the project maintainer to discuss commercial licensing terms

**Content Created with Spinneret:**
- The licensing of stories, content, or creative works generated using Spinneret is entirely up to you
- Spinneret does not claim any rights to content you create with the tool
- You retain full ownership and control over your creative works

**For Commercial Licensing Inquiries:**
Please contact the project maintainer to discuss licensing terms for commercial use.

---

## 🙏 Acknowledgments

- Built with [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- Terminal UI powered by [Rich](https://github.com/Textualize/rich)
- Writing methodology inspired by Story Grid principles

---

## 🤝 Contributing

[Add contribution guidelines if applicable]

---

**Happy Writing! 🕷️🕸️**

