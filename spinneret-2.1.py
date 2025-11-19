#!/usr/bin/env python3
import os
import sys
import subprocess
import re
import time
import shutil
import warnings
# Filter out the specific Google API warning about Python 3.9
warnings.filterwarnings("ignore", message="You are using a Python version")
from pathlib import Path
from typing import Union, Optional, List

# --- DEPENDENCY CHECK & AUTO-INSTALL ---
def ensure_dependencies():
    """
    Checks for required libraries and installs them if missing.
    Restarts the script after installation to load new modules.
    """
    required_packages = {
        "google-generativeai": "google.generativeai",
        "rich": "rich"
    }
    
    missing_packages = []
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️  Missing dependencies detected: {', '.join(missing_packages)}")
        print("⏳ Installing packages... (This may take a moment)")
        
        try:
            # Install packages silently
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing_packages,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ Dependencies installed successfully.")
            print("🔄 Restarting script to load new libraries...")
            print("-" * 40)
            # Restart the script
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            print("Please manually run: pip install google-generativeai rich")
            sys.exit(1)

# Run the check immediately
ensure_dependencies()

# --- IMPORTS (Now safe to load) ---
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.status import Status
from rich.live import Live

# Initialize Rich Console
console = Console()

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY")

# Model selection
# Note: Using 'flash' for speed/cost and 'pro' for quality
MODELS = {
    "fast": "gemini-2.0-flash",
    "smart": "gemini-2.5-pro", # Adjust based on current availability
}

# Phase Configuration
PHASE_CONFIG = {
    "brainstorming": {"model": "fast", "thinking": "deep"},
    "premise":       {"model": "fast", "thinking": "standard"},
    "planning":      {"model": "fast", "thinking": "standard"},
    "analysis":      {"model": "fast", "thinking": "deep"},
    "draft":         {"model": "smart", "thinking": "ultra"},
    "editing":       {"model": "smart", "thinking": "deep"},
}

# Thinking Instructions
THINKING_LEVELS = {
    "standard": "",
    "deep": "Take a deep breath and think step-by-step about the nuances of this request.",
    "ultra": "Think deeply and comprehensively. Consider multiple angles, subtext, and implications before generating the final output."
}

MAX_CONTEXT_TOKENS = 800000
CHARS_PER_TOKEN = 4

def check_api_key():
    """Checks for API key and guides user if missing."""
    global API_KEY
    if not API_KEY:
        console.clear()
        console.print(Panel.fit("[bold red]MISSING API KEY[/bold red]", style="red"))
        console.print("To use Spinneret, you need a Google Gemini API Key.")
        console.print("1. Get one here: [link]https://aistudio.google.com/app/apikey[/link]")
        console.print("2. Set it in your terminal:")
        console.print("   [italic]export GEMINI_API_KEY='your_key_here'[/italic]")
        console.print("\nOr paste it below for this session only:")
        
        key = Prompt.ask("Enter API Key", password=True)
        if key:
            os.environ["GEMINI_API_KEY"] = key
            API_KEY = key
            genai.configure(api_key=API_KEY)
        else:
            console.print("[red]Exiting.[/red]")
            sys.exit(1)
    else:
        genai.configure(api_key=API_KEY)

# --- UTILITIES ---

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN

def manage_token_limit(prompt: str) -> str:
    """Truncates prompt if it exceeds safety limits."""
    tokens = estimate_tokens(prompt)
    if tokens > MAX_CONTEXT_TOKENS:
        chars_to_keep = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN
        keep_part = chars_to_keep // 2
        truncated = prompt[:keep_part] + "\n\n[... CONTEXT TRUNCATED ...]\n\n" + prompt[-keep_part:]
        console.print(f"[yellow]⚠️  Prompt truncated from {tokens:,} to {estimate_tokens(truncated):,} tokens.[/yellow]")
        return truncated
    return prompt

def load_project_instructions(project_dir: Path) -> str:
    gemini_file = project_dir / "GEMINI.md"
    if gemini_file.exists():
        return f"\n\n--- PROJECT SPECIFIC INSTRUCTIONS ---\n{gemini_file.read_text(encoding='utf-8')}\n"
    return ""

def get_tool_content(filename: str) -> str:
    try:
        return (Path("Tools") / filename).read_text(encoding='utf-8')
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] Missing tool file: Tools/{filename}")
        return ""

# --- AI INTERACTION ---

def call_gemini(prompt: str, task_type: str = "draft", project_dir: Optional[Path] = None) -> Optional[str]:
    """Calls Gemini via SDK with streaming and simple text output."""
    check_api_key()
    
    config = PHASE_CONFIG.get(task_type, PHASE_CONFIG["draft"])
    model_name = MODELS[config["model"]]
    thinking_prompt = THINKING_LEVELS[config["thinking"]]
    
    project_instructions = load_project_instructions(project_dir) if project_dir else ""
    full_prompt = f"{thinking_prompt}{project_instructions}\n\n{prompt}"
    full_prompt = manage_token_limit(full_prompt)

    try:
        model = genai.GenerativeModel(model_name)
        
        console.print(f"[bold cyan]🤖 AI Processing:[/bold cyan] {model_name} ({task_type})")
        full_response_text = ""

        # Stream the response
        response_stream = model.generate_content(full_prompt, stream=True)
        
        # Standard streaming loop (No 'Live' context manager)
        # This prevents the "multiple copies" artifact on long texts
        for chunk in response_stream:
            if chunk.text:
                print(chunk.text, end="", flush=True) # Native print for safety
                full_response_text += chunk.text
        
        console.print("\n\n[bold green]✔ Generation Complete[/bold green]\n")
        return full_response_text

    except google_exceptions.ResourceExhausted:
        console.print("[bold red]❌ Error: Quota exceeded (Rate Limit). Waiting 60 seconds...[/bold red]")
        time.sleep(60)
        return call_gemini(prompt, task_type, project_dir) # Retry
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        return None

# --- GENERATORS ---

def generic_generator(project_dir: Path, phase_info: dict):
    """Generic generator for standard phases."""
    phase_name = phase_info["name"]
    tool_file = phase_info["tool"]
    input_dirs = phase_info["inputs"] 
    task_type = phase_info.get("task_type", "planning")
    output_filename = phase_info.get("output_file", "draft.txt")
    
    console.rule(f"[bold]{phase_name}[/bold]")
    
    current_phase_dir = project_dir / phase_name
    draft_dir = current_phase_dir / "draft"
    draft_dir.mkdir(parents=True, exist_ok=True)
    (current_phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    # Gather Context
    context_str = ""
    for prev_phase, pattern, is_compilation in input_dirs:
        src_dir = project_dir / prev_phase / "approved"
        files = list(src_dir.glob(pattern))
        
        if not files:
            console.print(f"[red]Missing approved files in {prev_phase}[/red]")
            # Assuming non-critical if some previous phases optional, but for now strict
            return

        content = ""
        if is_compilation:
            content = "\n\n---\n\n".join([f.read_text(encoding='utf-8') for f in sorted(files)])
        else:
            content = files[0].read_text(encoding='utf-8')
        
        context_str += f"\n\n--- APPROVED {prev_phase} ---\n{content}\n"

    instructions = get_tool_content(tool_file)
    if not instructions: return

    prompt = f"""
    You are an expert story architect.
    {instructions}
    {context_str}
    Output the requested content only.
    """

    while True:
        output = call_gemini(prompt, task_type=task_type, project_dir=project_dir)
        if output:
            save_path = draft_dir / output_filename
            if review_and_save(output, save_path, project_dir):
                break
        else:
            break

def create_new_premise():
    story_idea = Prompt.ask("Enter a one-sentence story idea")
    story_title = Prompt.ask("Enter a title for this project")
    
    safe_title = re.sub(r'[^a-zA-Z0-9 ]', '', story_title).replace(' ', '_')
    project_dir = Path(safe_title)

    if project_dir.exists():
        console.print("[red]Project already exists.[/red]")
        return

    phase_dir = project_dir / "Phase_01_Premise"
    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)
    
    # 1. Brainstorming
    brainstorm_instr = get_tool_content("Brainstormer.md")
    if not brainstorm_instr: return

    prompt = f"{brainstorm_instr}\n\n--- USER IDEA ---\n{story_idea}\n\nOutput comprehensive brainstorming."
    
    while True:
        output = call_gemini(prompt, task_type="brainstorming", project_dir=project_dir)
        if output:
            save_path = phase_dir / "drafts" / "00-brainstorming.txt"
            if review_and_save(output, save_path, project_dir):
                break
        else:
            break

    # 2. Premise Generation
    premise_instr = get_tool_content("01 - Premise.md")
    brainstorming_txt = (phase_dir / "drafts" / "00-brainstorming.txt").read_text(encoding='utf-8')
    
    prompt = f"""
    {premise_instr}
    --- CONTEXT ---
    Idea: {story_idea}
    Brainstorming: {brainstorming_txt}
    --- TASK ---
    Generate 5 premise options. Separate each with '---PREMISE-BREAK---'.
    """
    
    output = call_gemini(prompt, task_type="premise", project_dir=project_dir)
    if output:
        premises = output.split("---PREMISE-BREAK---")
        for i, premise in enumerate(premises):
            if len(premise.strip()) > 10:
                fname = phase_dir / "drafts" / f"premise-{i+1:02d}.txt"
                fname.write_text(premise.strip(), encoding='utf-8')
        console.print(f"[green]Generated {len(premises)} premises in drafts folder.[/green]")

# --- SPECIFIC GENERATORS ---

def generate_story_skeleton(project_dir: Path):
    generic_generator(project_dir, {
        "name": "Phase_02_Story_Skeleton",
        "tool": "02 - The Story Skeleton.md",
        "inputs": [("Phase_01_Premise", "*.txt", False)],
        "output_file": "02-story-skeleton.txt"
    })

def generate_character_introductions(project_dir: Path):
    phase_dir = project_dir / "Phase_03_Character_Introductions"
    src_dir = project_dir / "Phase_02_Story_Skeleton" / "approved"
    files = list(src_dir.glob("*.txt"))
    if not files: 
        console.print("[red]No approved story skeleton found.[/red]")
        return
    skeleton = files[0].read_text(encoding='utf-8')
    instr = get_tool_content("03 - Character Introductions.md")
    
    prompt = f"{instr}\n\n--- SKELETON ---\n{skeleton}\n\nGenerate characters. Separate with '---CHARACTER-BREAK---'. Start names with 'CHARACTER_NAME: '"
    
    output = call_gemini(prompt, task_type="planning", project_dir=project_dir)
    if output:
        chars = output.split("---CHARACTER-BREAK---")
        (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
        count = 0
        for char in chars:
            if len(char.strip()) > 10:
                lines = char.strip().split('\n')
                name = "unnamed"
                for line in lines:
                    if "CHARACTER_NAME:" in line:
                        name = line.split(":")[1].strip()
                        name = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(' ', '_'))
                        break
                
                path = phase_dir / "drafts" / f"{name}.txt"
                path.write_text(char.strip(), encoding='utf-8')
                count += 1
        console.print(f"[green]Saved {count} character drafts.[/green]")

# --- SPECIFIC GENERATORS (PHASES 5-15) ---

def generate_extended_synopsis(project_dir: Path):
    generic_generator(project_dir, {
        "name": "Phase_05_Extended_Synopsis",
        "tool": "05 - The Extended Synopsis.md",
        "inputs": [
            ("Phase_01_Premise", "*.txt", False),
            ("Phase_02_Story_Skeleton", "*.txt", False),
            ("Phase_03_Character_Introductions", "*.txt", True),
            ("Phase_04_Short_Synopsis", "*.txt", False)
        ],
        "output_file": "05-extended-synopsis.txt"
    })

def generate_goal_to_decision(project_dir: Path):
    generic_generator(project_dir, {
        "name": "Phase_06_Goal_to_Decision_Cycle",
        "tool": "06 - Goal to Decision Cycle.md",
        "inputs": [("Phase_05_Extended_Synopsis", "*.txt", False)],
        "output_file": "06-goal-to-decision.txt",
        "task_type": "analysis"
    })

def generate_character_development(project_dir: Path):
    # Splits output into individual character files
    phase_name = "Phase_07_Character_Development"
    console.rule(f"[bold]{phase_name}[/bold]")
    
    # Inputs
    synopsis = (project_dir / "Phase_05_Extended_Synopsis" / "approved" / "05-extended-synopsis.txt").read_text(encoding='utf-8')
    g2d = (project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved" / "06-goal-to-decision.txt").read_text(encoding='utf-8')
    instr = get_tool_content("07 - Character Development.md")

    prompt = f"""
    {instr}
    --- EXTENDED SYNOPSIS ---
    {synopsis}
    --- GOAL TO DECISION CYCLE ---
    {g2d}
    
    Start each character with 'CHARACTER_NAME: [Name]'.
    Separate characters with '---CHARACTER-DEVELOPMENT-BREAK---'.
    """

    output = call_gemini(prompt, task_type="planning", project_dir=project_dir)
    if output:
        save_dir = project_dir / phase_name / "drafts"
        save_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

        items = output.split("---CHARACTER-DEVELOPMENT-BREAK---")
        count = 0
        for item in items:
            if len(item.strip()) > 50:
                name_match = re.search(r"CHARACTER_NAME:\s*(.*)", item)
                name = name_match.group(1).strip() if name_match else f"char_{count+1}"
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))
                
                (save_dir / f"{safe_name}.txt").write_text(item.strip(), encoding='utf-8')
                count += 1
        console.print(f"[green]Saved {count} character development profiles.[/green]")

def generate_locations(project_dir: Path):
    phase_name = "Phase_08_Locations"
    console.rule(f"[bold]{phase_name}[/bold]")

    synopsis = (project_dir / "Phase_05_Extended_Synopsis" / "approved" / "05-extended-synopsis.txt").read_text(encoding='utf-8')
    instr = get_tool_content("08 - Locations.md")

    prompt = f"""
    {instr}
    --- EXTENDED SYNOPSIS ---
    {synopsis}
    
    Start each location with 'LOCATION_NAME: [Name]'.
    Separate locations with '---LOCATION-BREAK---'.
    """

    output = call_gemini(prompt, task_type="planning", project_dir=project_dir)
    if output:
        save_dir = project_dir / phase_name / "drafts"
        save_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

        items = output.split("---LOCATION-BREAK---")
        count = 0
        for item in items:
            if len(item.strip()) > 20:
                name_match = re.search(r"LOCATION_NAME:\s*(.*)", item)
                name = name_match.group(1).strip() if name_match else f"loc_{count+1}"
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))
                
                (save_dir / f"{safe_name}.txt").write_text(item.strip(), encoding='utf-8')
                count += 1
        console.print(f"[green]Saved {count} location drafts.[/green]")

def generate_advanced_plotting(project_dir: Path):
    generic_generator(project_dir, {
        "name": "Phase_09_Advanced_Plotting",
        "tool": "09 - Advanced Plotting.md",
        "inputs": [
            ("Phase_05_Extended_Synopsis", "*.txt", False),
            ("Phase_06_Goal_to_Decision_Cycle", "*.txt", False),
            ("Phase_07_Character_Development", "*.txt", True),
            ("Phase_08_Locations", "*.txt", True)
        ],
        "output_file": "09-advanced-plotting.txt"
    })

def generate_character_viewpoints(project_dir: Path):
    phase_name = "Phase_10_Character_Viewpoints"
    console.rule(f"[bold]{phase_name}[/bold]")
    
    # Inputs from previous phases
    synopsis = (project_dir / "Phase_05_Extended_Synopsis" / "approved" / "05-extended-synopsis.txt").read_text(encoding='utf-8')
    chars = "\n".join([f.read_text(encoding='utf-8') for f in (project_dir / "Phase_07_Character_Development" / "approved").glob("*.txt")])
    plotting = (project_dir / "Phase_09_Advanced_Plotting" / "approved" / "09-advanced-plotting.txt").read_text(encoding='utf-8')
    instr = get_tool_content("10 - Character Viewpoints.md")

    prompt = f"""
    {instr}
    --- SYNOPSIS ---
    {synopsis}
    --- CHARACTERS ---
    {chars}
    --- PLOTTING ---
    {plotting}
    
    Start each viewpoint with 'CHARACTER_VIEWPOINT_NAME: [Name]'.
    Separate with '---CHARACTER-VIEWPOINT-BREAK---'.
    """
    
    output = call_gemini(prompt, task_type="planning", project_dir=project_dir)
    if output:
        save_dir = project_dir / phase_name / "drafts"
        save_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

        items = output.split("---CHARACTER-VIEWPOINT-BREAK---")
        count = 0
        for item in items:
            if len(item.strip()) > 50:
                name_match = re.search(r"CHARACTER_VIEWPOINT_NAME:\s*(.*)", item)
                name = name_match.group(1).strip() if name_match else f"view_{count+1}"
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))
                
                (save_dir / f"{safe_name}.txt").write_text(item.strip(), encoding='utf-8')
                count += 1
        console.print(f"[green]Saved {count} viewpoint drafts.[/green]")

def generate_blocking_outline(project_dir: Path):
    phase_name = "Phase_11_Blocking_a_Rough_Outline"
    console.rule(f"[bold]{phase_name}[/bold]")

    # Compile heavy context
    synopsis = (project_dir / "Phase_05_Extended_Synopsis" / "approved" / "05-extended-synopsis.txt").read_text(encoding='utf-8')
    plotting = (project_dir / "Phase_09_Advanced_Plotting" / "approved" / "09-advanced-plotting.txt").read_text(encoding='utf-8')
    viewpoints = "\n".join([f.read_text(encoding='utf-8') for f in (project_dir / "Phase_10_Character_Viewpoints" / "approved").glob("*.txt")])
    
    instr = get_tool_content("11 - Blocking a Rough Outline.md")

    prompt = f"""
    {instr}
    --- SYNOPSIS ---
    {synopsis}
    --- PLOTTING ---
    {plotting}
    --- VIEWPOINTS ---
    {viewpoints}
    
    Start each scene with 'SCENE_NAME: [Name]'.
    Separate scenes with '---SCENE-BLOCKING-BREAK---'.
    """

    output = call_gemini(prompt, task_type="planning", project_dir=project_dir)
    if output:
        save_dir = project_dir / phase_name / "drafts"
        save_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

        items = output.split("---SCENE-BLOCKING-BREAK---")
        count = 0
        for i, item in enumerate(items):
            if len(item.strip()) > 20:
                name_match = re.search(r"SCENE_NAME:\s*(.*)", item)
                name = name_match.group(1).strip() if name_match else "Scene"
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_'))
                
                # Numbered files for ordering
                (save_dir / f"{i+1:02d}-{safe_name}.txt").write_text(item.strip(), encoding='utf-8')
                count += 1
        console.print(f"[green]Saved {count} scene blocking outlines.[/green]")

def generate_first_draft(project_dir: Path):
    phase_name = "Phase_12_First_Draft"
    console.rule(f"[bold]{phase_name}[/bold]")

    # Check for blocking outlines
    blocking_dir = project_dir / "Phase_11_Blocking_a_Rough_Outline" / "approved"
    # Sort strictly by filename to ensure order
    blocking_files = sorted(blocking_dir.glob("*.txt"))
    
    if not blocking_files:
        console.print("[red]No approved blocking outlines found in Phase 11.[/red]")
        return

    # Compile Static Context (Stuff that doesn't change between scenes)
    synopsis = (project_dir / "Phase_05_Extended_Synopsis" / "approved" / "05-extended-synopsis.txt").read_text(encoding='utf-8')
    chars = "\n".join([f.read_text(encoding='utf-8') for f in (project_dir / "Phase_07_Character_Development" / "approved").glob("*.txt")])
    locations = "\n".join([f.read_text(encoding='utf-8') for f in (project_dir / "Phase_08_Locations" / "approved").glob("*.txt")])
    
    instr = get_tool_content("12 - First Draft.md")
    sg_instr = get_tool_content("StoryGrid_AI_Instructions.md")

    save_dir = project_dir / phase_name / "draft"
    save_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

    console.print(f"[green]Found {len(blocking_files)} scenes to generate.[/green]\n")

    # ITERATIVE GENERATION LOOP
    for i, blocking_file in enumerate(blocking_files):
        scene_title = blocking_file.stem # e.g. "01-The_Inciting_Incident"
        blocking_content = blocking_file.read_text(encoding='utf-8')
        
        console.print(f"[bold cyan]Generating Scene {i+1}/{len(blocking_files)}: {scene_title}[/bold cyan]")

        prompt = f"""
        {instr}
        {sg_instr}
        
        --- GLOBAL CONTEXT ---
        SYNOPSIS: {synopsis}
        CHARACTERS: {chars}
        LOCATIONS: {locations}
        
        --- CURRENT SCENE BLOCKING ---
        SCENE TITLE: {scene_title}
        BLOCKING:
        {blocking_content}
        
        TASK: Write the first draft of THIS SPECIFIC SCENE based on the blocking above.
        Do not write summaries. Write the full prose.
        Start with a Markdown header: "## {scene_title}"
        """

        # Auto-retry loop for this specific scene
        while True:
            output = call_gemini(prompt, task_type="draft", project_dir=project_dir)
            
            if output:
                # Clean up potential markdown fencing
                clean_output = output.replace("```markdown", "").replace("```", "").strip()
                
                # Construct output filename matching the blocking filename but .md
                output_filename = f"{blocking_file.stem}.md"
                save_path = save_dir / output_filename
                
                # Enter Review Loop
                if review_and_save(clean_output, save_path, project_dir):
                    break # Move to next scene
                # If review_and_save returns False (Retry), the loop restarts for this scene
            else:
                console.print("[red]Generation failed.[/red]")
                if not Confirm.ask("Retry this scene?"):
                    break

def generate_theme_analysis(project_dir: Path):
    generic_generator(project_dir, {
        "name": "Phase_13_Theme_and_Variations",
        "tool": "13 - Theme and Variations.md",
        "inputs": [("Phase_12_First_Draft", "*.md", True)], # Compiles all draft scenes
        "output_file": "13-theme-analysis.txt",
        "task_type": "analysis"
    })

def generate_second_draft(project_dir: Path):
    # Logic: Iterate through First Draft scenes and rewrite them
    phase_name = "Phase_14_Second_Draft"
    console.rule(f"[bold]{phase_name}[/bold]")
    
    draft_dir = project_dir / "Phase_12_First_Draft" / "approved"
    theme_file = project_dir / "Phase_13_Theme_and_Variations" / "approved" / "13-theme-analysis.txt"
    
    if not draft_dir.exists():
        console.print("[red]No First Draft scenes found.[/red]")
        return

    # Context
    theme_notes = theme_file.read_text(encoding='utf-8') if theme_file.exists() else "No theme notes."
    instr = get_tool_content("14 - Second Draft.md")
    
    save_dir = project_dir / phase_name / "draft"
    save_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

    files = sorted(draft_dir.glob("*.md"))
    
    for i, scene_file in enumerate(files):
        scene_text = scene_file.read_text(encoding='utf-8')
        console.print(f"[cyan]Rewriting {scene_file.name}...[/cyan]")
        
        prompt = f"""
        {instr}
        --- THEME NOTES ---
        {theme_notes}
        --- DRAFT SCENE ---
        {scene_text}
        
        Rewrite this scene. Retain the filename/title structure.
        """
        
        # Auto-retry loop for individual scenes
        while True:
            output = call_gemini(prompt, task_type="editing", project_dir=project_dir)
            if output:
                # Clean up output if it includes markdown code blocks
                clean_output = output.replace("```markdown", "").replace("```", "")
                
                # Review Loop
                if review_and_save(clean_output, save_dir / scene_file.name, project_dir):
                    break
            else:
                if not Confirm.ask("Generation failed. Retry?"):
                    break

def generate_final_draft(project_dir: Path):
    phase_name = "Phase_15_Final_Draft"
    console.rule(f"[bold]{phase_name}[/bold]")
    
    draft_dir = project_dir / "Phase_14_Second_Draft" / "approved"
    if not draft_dir.exists():
        console.print("[red]No Second Draft scenes found.[/red]")
        return

    instr = get_tool_content("15 - Final Draft & Editing.md")
    
    save_dir = project_dir / phase_name / "draft"
    save_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / phase_name / "approved").mkdir(parents=True, exist_ok=True)

    files = sorted(draft_dir.glob("*.md"))
    
    for i, scene_file in enumerate(files):
        scene_text = scene_file.read_text(encoding='utf-8')
        console.print(f"[cyan]Polishing {scene_file.name}...[/cyan]")
        
        prompt = f"""
        {instr}
        --- SECOND DRAFT SCENE ---
        {scene_text}
        
        Produce the Final Polish.
        """
        
        while True:
            output = call_gemini(prompt, task_type="editing", project_dir=project_dir)
            if output:
                clean_output = output.replace("```markdown", "").replace("```", "")
                if review_and_save(clean_output, save_dir / scene_file.name, project_dir):
                    break
            else:
                if not Confirm.ask("Generation failed. Retry?"):
                    break
                    
# --- DYNAMIC MENU SYSTEM ---

def check_phase_status(project_dir: Path, phase_folder: str) -> str:
    """
    Determines the status of a phase.
    Returns: 'completed', 'draft', or 'empty'
    """
    approved_dir = project_dir / phase_folder / "approved"
    draft_dir = project_dir / phase_folder / "draft"
    drafts_dir = project_dir / phase_folder / "drafts" # Some phases use plural

    if approved_dir.exists() and any(approved_dir.iterdir()):
        return "completed"
    
    # Check for drafts (singular or plural folder)
    has_draft = (draft_dir.exists() and any(draft_dir.iterdir())) or \
                (drafts_dir.exists() and any(drafts_dir.iterdir()))
    
    if has_draft:
        return "draft"
        
    return "empty"

def manage_existing_project(project_dir: Path):
    while True:
        clear_screen()
        console.print(Panel(f"[bold cyan]Project: {project_dir.name}[/bold cyan]", subtitle="Workflow Manager"))
        
        # Define the workflow order and functions
        workflow = [
            ("Phase_01_Premise", "Premise", None),
            ("Phase_02_Story_Skeleton", "Story Skeleton", lambda: generate_story_skeleton(project_dir)),
            ("Phase_03_Character_Introductions", "Character Introductions", lambda: generate_character_introductions(project_dir)),
            ("Phase_04_Short_Synopsis", "Short Synopsis", lambda: generate_short_synopsis(project_dir)),
            ("Phase_05_Extended_Synopsis", "Extended Synopsis", lambda: generate_extended_synopsis(project_dir)),
            ("Phase_06_Goal_to_Decision_Cycle", "Goal to Decision Cycle", lambda: generate_goal_to_decision(project_dir)),
            ("Phase_07_Character_Development", "Character Development", lambda: generate_character_development(project_dir)),
            ("Phase_08_Locations", "Locations", lambda: generate_locations(project_dir)),
            ("Phase_09_Advanced_Plotting", "Advanced Plotting", lambda: generate_advanced_plotting(project_dir)),
            ("Phase_10_Character_Viewpoints", "Character Viewpoints", lambda: generate_character_viewpoints(project_dir)),
            ("Phase_11_Blocking_a_Rough_Outline", "Blocking Outline", lambda: generate_blocking_outline(project_dir)),
            ("Phase_12_First_Draft", "First Draft", lambda: generate_first_draft(project_dir)),
            ("Phase_13_Theme_and_Variations", "Theme Analysis", lambda: generate_theme_analysis(project_dir)),
            ("Phase_14_Second_Draft", "Second Draft", lambda: generate_second_draft(project_dir)),
            ("Phase_15_Final_Draft", "Final Draft", lambda: generate_final_draft(project_dir)),
        ]

        menu_options = []
        previous_phase_status = "completed" # Assume Phase 0 is done to start the chain
        
        # Iterate through workflow to build menu
        for i, (phase_folder, label, func) in enumerate(workflow):
            status = check_phase_status(project_dir, phase_folder)
            
            # Only show Phase 1 if it's missing (unlikely here) or for status context
            if i == 0: 
                previous_phase_status = status
                continue

            # Logic: We can only interact with a phase if the PREVIOUS phase is complete
            # OR if we already have a draft/completion of the current phase.
            if previous_phase_status == "completed":
                
                # Determine Visual Label
                if status == "completed":
                    status_label = "[dim green]✔ Completed[/dim green]"
                elif status == "draft":
                    status_label = "[yellow]✎ Draft Waiting[/yellow]"
                else:
                    status_label = "[bold cyan]⭐ READY TO GENERATE[/bold cyan]"
                
                # Add to menu list
                display_text = f"Phase {i+1}: {label}"
                menu_options.append((display_text, status_label, func))
            
            # Update tracker for next iteration
            previous_phase_status = status

        # Render Menu
        if not menu_options:
            console.print("[yellow]Phase 1 (Premise) appears incomplete. Please check your files.[/yellow]")
        else:
            for idx, (text, label, func) in enumerate(menu_options):
                console.print(f"[{idx+1}] {text.ljust(40)} {label}")

        console.print("\n[Q] Back to Main Menu")
        
        choice = Prompt.ask("Select", default="q")
        
        if choice.lower() == 'q':
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(menu_options):
                _, _, selected_func = menu_options[idx]
                if selected_func:
                    selected_func()
                    Prompt.ask("\nPress Enter to continue...")
        except ValueError:
            pass

def main_menu():
    check_api_key()
    
    while True:
        clear_screen()
        console.print(Panel.fit("🕷️ SPINNERET v2.1 🕸️", style="bold magenta"))
        
        projects = [d for d in Path('.').iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != "Tools"]
        
        if not projects:
            console.print("[italic dim]No projects found.[/italic dim]")
        else:
            for i, p in enumerate(projects):
                console.print(f"[{i+1}] {p.name}")
            
        console.print(f"\n[{len(projects)+1}] New Project")
        console.print("[Q] Quit")
        
        choice = Prompt.ask("Select")
        
        if choice.lower() == 'q': break
        try:
            idx = int(choice) - 1
            if idx < len(projects):
                manage_existing_project(projects[idx])
            elif idx == len(projects):
                create_new_premise()
        except ValueError:
            pass

if __name__ == "__main__":
    main_menu()
