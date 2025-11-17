#!/usr/bin/env python3
import os
import subprocess
import re
from pathlib import Path
from typing import Union

# --- Configuration ---
# Set the Gemini model to use for all API calls.
# Examples: "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro"
GEMINI_MODEL = "gemini-2.5-flash"

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def call_gemini(prompt: str) -> Union[str, None]:
    """
    Calls the Gemini CLI with a given prompt via stdin.
    Returns the output or None if an error occurs.
    """
    print("--- Calling Gemini AI... ---")
    try:
        process = subprocess.run(
            ['gemini', '-m', GEMINI_MODEL, '-p', '-'],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        print("--- AI generation complete. ---")
        return process.stdout
    except FileNotFoundError:
        print("\nError: 'gemini' command not found.")
        print("Please ensure the Gemini CLI is installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"\nError: Gemini API call failed with exit code {e.returncode}.")
        print("--- Gemini Stderr ---")
        print(e.stderr)
        print("--------------------")
        return None

def create_new_premise():
    """Guides the user to create a new story premise and workspace."""
    story_idea = input("Enter a one-sentence story idea: ")
    story_title = input("Enter a title for this project: ")

    # Sanitize story_title to create a valid directory name
    safe_title = re.sub(r'[^a-zA-Z0-9 ]', '', story_title).replace(' ', '_')
    project_dir = Path(safe_title)

    if project_dir.exists():
        print("A project with that title already exists. Please choose another.")
        return

    print(f"--- INITIALIZING: {story_title} ---")
    phase_dir = project_dir / "Phase_01_Premise"
    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)
    print("Workspace created.")

    try:
        premise_instructions = (Path("Tools") / "01 - Premise.md").read_text()
    except FileNotFoundError:
        print("Error: Could not find 'Tools/01 - Premise.md'. Make sure it exists.")
        return

    prompt = f"""
You are a master story coach. Your task is to take a user's simple story idea and brainstorm five compelling story premises based on it.

Follow these instructions precisely:
1.  Read the user's story idea carefully.
2.  Use the following framework to structure your thinking for each premise:
{premise_instructions}
3.  Generate five distinct premise options. Each premise must be a single sentence and follow the structure: Situation > Character > Goal > Opponent > Disaster.
4.  Present the five premises clearly.
5.  IMPORTANT: Separate each premise with the exact string '---PREMISE-BREAK---' on its own line.

--- USER'S STORY IDEA ---
{story_idea}
--- END OF IDEA ---

Begin generation now.
"""

    output = call_gemini(prompt)
    if not output:
        return

    premises = output.split("---PREMISE-BREAK---")
    for i, premise in enumerate(premises):
        premise = premise.strip()
        if len(premise) > 10:
            file_path = phase_dir / "drafts" / f"premise-{i+1:02d}.txt"
            file_path.write_text(premise)

    print("\n--- PREMISE GENERATION COMPLETE ---")
    print("Five premise options have been generated in:")
    print(f"  {phase_dir / 'drafts'}/")
    print("""
NEXT STEP: Please review the options, choose one, and move it to:""")
    print(f"  {phase_dir / 'approved'}/")

# --- All other generate_* functions would follow a similar pattern ---
# Example:
def generate_story_skeleton(project_dir: Path):
    """Generates the story skeleton for the project."""
    print("--- GENERATING STORY SKELETON (AI) ---")
    phase_dir = project_dir / "Phase_02_Story_Skeleton"
    premise_dir = project_dir / "Phase_01_Premise" / "approved"

    try:
        approved_premise_files = list(premise_dir.glob('*.txt'))
        if not approved_premise_files:
            print("Error: No approved premise found.")
            return
        approved_premise = approved_premise_files[0].read_text()
        skeleton_instructions = (Path("Tools") / "02 - The Story Skeleton.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "draft").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master story planner. Your task is to expand a single-sentence story premise into a complete story skeleton using the three-act structure.

Follow these instructions precisely:
1.  Read the user's approved story premise.
2.  Use the following framework to structure the story skeleton:
{skeleton_instructions}
3.  For each stage of the three acts, write a detailed paragraph describing the key events, character actions, and plot developments.
4.  Ensure the generated skeleton is a cohesive and logical expansion of the original premise.

--- APPROVED PREMISE ---
{approved_premise}
--- END PREMISE ---

Begin generation now. Output only the story skeleton.
"""
    output = call_gemini(prompt)
    if output:
        draft_file = phase_dir / "draft" / "02-story-skeleton.txt"
        draft_file.write_text(output.strip())
        print("\n--- SKELETON GENERATION COMPLETE ---")
        print("A draft of the story skeleton has been generated in:")
    print(f"  {draft_file}")
        print("""
NEXT STEP: Please review the draft. If you are happy with it, move it to:""")
    print(f"  {phase_dir / 'approved'}/")

# ... other generate functions would go here ...

def generate_character_introductions(project_dir: Path):
    """Generates character introductions for the project."""
    print("--- GENERATING CHARACTER INTRODUCTIONS (AI) ---")
    phase_dir = project_dir / "Phase_03_Character_Introductions"
    skeleton_approved_dir = project_dir / "Phase_02_Story_Skeleton" / "approved"

    try:
        approved_skeleton_files = list(skeleton_approved_dir.glob('*.txt'))
        if not approved_skeleton_files:
            print("Error: No approved story skeleton found.")
            return
        approved_skeleton = approved_skeleton_files[0].read_text()
        character_instructions = (Path("Tools") / "03 - Character Introductions.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master character developer. Your task is to create detailed character introductions based on the provided story skeleton.

Follow these instructions precisely:
1.  Read the user's approved story skeleton to identify key characters (protagonist, antagonist, mentor, etc.).
2.  For each identified key character, apply the three layers of introduction as described in the following framework:
{character_instructions}
3.  CRITICAL: Start each character's introduction with the exact string 'CHARACTER_NAME: ' followed by the character's full name on a single line. This is essential for file naming.
4.  Present each character's introduction clearly, with a distinct heading for each character.
5.  IMPORTANT: Separate each character's complete introduction with the exact string '---CHARACTER-BREAK---' on its own line.

--- APPROVED STORY SKELETON ---
{approved_skeleton}
--- END SKELETON ---

Begin generation now. Output only the character introductions.
"""
    output = call_gemini(prompt)
    if not output:
        return

    characters = output.split("---CHARACTER-BREAK---")
    for i, char_content in enumerate(characters):
        char_content = char_content.strip()
        if len(char_content) > 10:
            # Attempt to extract character name from the first line
            first_line = char_content.split('\n', 1)[0]
            char_name_match = re.match(r'CHARACTER_NAME: (.*)', first_line)
            
            if char_name_match:
                char_name = char_name_match.group(1).strip()
                # Sanitize for filename
                safe_char_name = re.sub(r'[^a-zA-Z0-9_ -]', '', char_name).replace(' ', '_')
                file_path = phase_dir / "drafts" / f"{safe_char_name}.txt"
            else:
                # Fallback if name not found
                file_path = phase_dir / "drafts" / f"character-unnamed-{i+1:02d}.txt"
            
            file_path.write_text(char_content)

    print("""
--- CHARACTER INTRODUCTIONS GENERATION COMPLETE ---""")
    print("Character introductions have been generated as named files in:")
    print(f"  {phase_dir / 'drafts'}/")
    print("""
NEXT STEP: Please review the profiles. Move the files for the characters you want to keep into:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_short_synopsis(project_dir: Path):
    """Generates the short synopsis for the project."""
    print("--- GENERATING SHORT SYNOPSIS (AI) ---")
    phase_dir = project_dir / "Phase_04_Short_Synopsis"
    premise_approved_dir = project_dir / "Phase_01_Premise" / "approved"
    skeleton_approved_dir = project_dir / "Phase_02_Story_Skeleton" / "approved"
    char_intro_approved_dir = project_dir / "Phase_03_Character_Introductions" / "approved"

    try:
        approved_premise_files = list(premise_approved_dir.glob('*.txt'))
        if not approved_premise_files:
            print("Error: No approved premise found.")
            return
        approved_premise = approved_premise_files[0].read_text()

        approved_skeleton_files = list(skeleton_approved_dir.glob('*.txt'))
        if not approved_skeleton_files:
            print("Error: No approved story skeleton found.")
            return
        approved_skeleton = approved_skeleton_files[0].read_text()

        approved_characters_content = []
        for char_file in char_intro_approved_dir.glob('*.txt'):
            approved_characters_content.append(char_file.read_text())
        approved_characters = "\n\n---\n\n".join(approved_characters_content)

        synopsis_instructions = (Path("Tools") / "04 - The Short Synopsis.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "draft").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master story editor. Your task is to synthesize the provided premise, story skeleton, and character introductions into a single, cohesive short synopsis.

Follow these instructions precisely:
1.  Read and internalize all the provided materials: the premise, the story skeleton, and the character introductions.
2.  Use the following framework to guide the structure and content of the synopsis:
{synopsis_instructions}
3.  The synopsis must be approximately 500 words.
4.  Weave the key characters and plot points from the source materials into a compelling narrative summary.
5.  The output should be a single block of text, without any dialogue or conversational filler.

--- APPROVED PREMISE ---
{approved_premise}

--- APPROVED STORY SKELETON ---
{approved_skeleton}

--- APPROVED CHARACTERS ---
{approved_characters}
--- END MATERIALS ---

Begin generation now. Output only the short synopsis.
"""
    output = call_gemini(prompt)
    if output:
        draft_file = phase_dir / "draft" / "04-short-synopsis.txt"
        draft_file.write_text(output.strip())
        print("""
--- SHORT SYNOPSIS GENERATION COMPLETE ---""")
        print("A draft of the short synopsis has been generated in:")
    print(f"  {draft_file}")
        print("""
NEXT STEP: Review the draft. If you are happy with it, move it to:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_extended_synopsis(project_dir: Path):
    """Generates the extended synopsis for the project."""
    print("--- GENERATING EXTENDED SYNOPSIS (AI) ---")
    phase_dir = project_dir / "Phase_05_Extended_Synopsis"
    premise_approved_dir = project_dir / "Phase_01_Premise" / "approved"
    skeleton_approved_dir = project_dir / "Phase_02_Story_Skeleton" / "approved"
    char_intro_approved_dir = project_dir / "Phase_03_Character_Introductions" / "approved"
    short_synopsis_approved_dir = project_dir / "Phase_04_Short_Synopsis" / "approved"

    try:
        approved_premise_files = list(premise_approved_dir.glob('*.txt'))
        if not approved_premise_files:
            print("Error: No approved premise found.")
            return
        approved_premise = approved_premise_files[0].read_text()

        approved_skeleton_files = list(skeleton_approved_dir.glob('*.txt'))
        if not approved_skeleton_files:
            print("Error: No approved story skeleton found.")
            return
        approved_skeleton = approved_skeleton_files[0].read_text()

        approved_characters_content = []
        for char_file in char_intro_approved_dir.glob('*.txt'):
            approved_characters_content.append(char_file.read_text())
        approved_characters = "\n\n---\n\n".join(approved_characters_content)

        approved_short_synopsis_files = list(short_synopsis_approved_dir.glob('*.txt'))
        if not approved_short_synopsis_files:
            print("Error: No approved short synopsis found.")
            return
        approved_short_synopsis = approved_short_synopsis_files[0].read_text()

        extended_synopsis_instructions = (Path("Tools") / "05 - The Extended Synopsis.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "draft").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master story expander. Your task is to take the provided short synopsis and expand it into a detailed extended synopsis, incorporating all previously approved story elements.

Follow these instructions precisely:
1.  Read and internalize all the provided materials: the premise, the story skeleton, character introductions, and especially the short synopsis.
2.  Use the following framework to guide the structure and content of the extended synopsis:
{extended_synopsis_instructions}
3.  Expand the short synopsis to approximately 4-5 pages (around 150 words per scene, if applicable, or roughly 2000-2500 words total).
4.  Weave in greater detail regarding key events, character motivations, subplots, and world-building, ensuring consistency with all approved prior materials.
5.  The output should be a single, flowing narrative, without any dialogue or conversational filler.

--- APPROVED PREMISE ---
{approved_premise}

--- APPROVED STORY SKELETON ---
{approved_skeleton}

--- APPROVED CHARACTERS ---
{approved_characters}

--- APPROVED SHORT SYNOPSIS ---
{approved_short_synopsis}
--- END MATERIALS ---

Begin generation now. Output only the extended synopsis.
"""
    output = call_gemini(prompt)
    if output:
        draft_file = phase_dir / "draft" / "05-extended-synopsis.txt"
        draft_file.write_text(output.strip())
    print("""
--- EXTENDED SYNOPSIS GENERATION COMPLETE ---""")
    print("A draft of the extended synopsis has been generated in:")
    print(f"  {draft_file}")
        print("""
NEXT STEP: Please review the draft. If you are happy with it, move it to:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_goal_to_decision_cycle(project_dir: Path):
    """Generates the Goal to Decision Cycle for the project."""
    print("--- GENERATING GOAL TO DECISION CYCLE (AI) ---")
    phase_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        goal_to_decision_cycle_instructions = (Path("Tools") / "06 - Goal to Decision Cycle.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "draft").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master story analyst. Your task is to break down the provided Extended Synopsis into a series of 'Goal to Decision Cycles' for each major scene or sequence, as described in the instructions.

Follow these instructions precisely:
1.  Read and internalize the provided Extended Synopsis.
2.  Apply the 'Action Scenes Breakdown' and 'Reaction Scenes Breakdown' framework from the following instructions to each significant scene or sequence in the Extended Synopsis:
{goal_to_decision_cycle_instructions}
3.  For each scene, clearly identify:
    *   Whether it's an Action Scene or a Reaction Scene.
    *   For Action Scenes: Goal, Conflict, Disaster.
    *   For Reaction Scenes: Reaction, Dilemma, Decision.
4.  Present the breakdown for each scene clearly, using headings for each scene and subheadings for Goal, Conflict, etc.
5.  The output should be a structured list of scenes with their respective Goal to Decision Cycle elements.

--- APPROVED EXTENDED SYNOPSIS ---
{approved_extended_synopsis}
--- END MATERIALS ---

Begin generation now. Output only the Goal to Decision Cycle breakdown.
"""
    output = call_gemini(prompt)
    if output:
        draft_file = phase_dir / "draft" / "06-goal-to-decision-cycle.txt"
        draft_file.write_text(output.strip())
    print("""
--- GOAL TO DECISION CYCLE GENERATION COMPLETE ---""")
        print("A draft of the Goal to Decision Cycle has been generated in:")
    print(f"  {draft_file}")
        print("""
NEXT STEP: Please review the draft. If you are happy with it, move it to:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_character_development(project_dir: Path):
    """Generates character development profiles for the project."""
    print("--- GENERATING CHARACTER DEVELOPMENT (AI) ---")
    phase_dir = project_dir / "Phase_07_Character_Development"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"
    goal_to_decision_cycle_approved_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        approved_goal_to_decision_cycle_files = list(goal_to_decision_cycle_approved_dir.glob('*.txt'))
        if not approved_goal_to_decision_cycle_files:
            print("Error: No approved Goal to Decision Cycle found.")
            return
        approved_goal_to_decision_cycle = approved_goal_to_decision_cycle_files[0].read_text()

        character_development_instructions = (Path("Tools") / "07 - Character Development.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master character developer. Your task is to create detailed character development profiles for the main characters identified in the provided story materials, following the given instructions.

Follow these instructions precisely:
1.  Read and internalize all the provided materials: the approved Extended Synopsis and the approved Goal to Decision Cycle.
2.  Identify the main characters from these materials.
3.  For each main character, generate a detailed character development profile covering the following aspects as described in the framework:
{character_development_instructions}
    *   Voice
    *   Characterisation
    *   Questionnaire (answer relevant questions to deepen the character)
    *   History (key points from their past)
4.  CRITICAL: Start each character's development profile with the exact string 'CHARACTER_NAME: ' followed by the character's full name on a single line. This is essential for file naming.
5.  Present each character's development profile clearly, with a distinct heading for each character.
6.  IMPORTANT: Separate each complete character development profile with the exact string '---CHARACTER-DEVELOPMENT-BREAK---' on its own line.

--- APPROVED EXTENDED SYNOPSIS ---
{approved_extended_synopsis}

--- APPROVED GOAL TO DECISION CYCLE ---
{approved_goal_to_decision_cycle}
--- END MATERIALS ---

Begin generation now. Output only the character development profiles.
"""
    output = call_gemini(prompt)
    if not output:
        return

    characters = output.split("---CHARACTER-DEVELOPMENT-BREAK---")
    for i, char_content in enumerate(characters):
        char_content = char_content.strip()
        if len(char_content) > 10:
            first_line = char_content.split('\n', 1)[0]
            char_name_match = re.match(r'CHARACTER_NAME: (.*)', first_line)
            
            if char_name_match:
                char_name = char_name_match.group(1).strip()
                safe_char_name = re.sub(r'[^a-zA-Z0-9_ -]', '', char_name).replace(' ', '_')
                file_path = phase_dir / "drafts" / f"{safe_char_name}.txt"
            else:
                file_path = phase_dir / "drafts" / f"character-development-unnamed-{i+1:02d}.txt"
            
            file_path.write_text(char_content)

    print("""
--- CHARACTER DEVELOPMENT GENERATION COMPLETE ---""")
    print("Character development profiles have been generated as named files in:")
    print(f"  {phase_dir / 'drafts'}/")
    print("""
NEXT STEP: Please review the profiles. Move the files for the characters you want to keep into:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_locations(project_dir: Path):
    """Generates location descriptions for the project."""
    print("--- GENERATING LOCATIONS (AI) ---")
    phase_dir = project_dir / "Phase_08_Locations"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"
    goal_to_decision_cycle_approved_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        approved_goal_to_decision_cycle_files = list(goal_to_decision_cycle_approved_dir.glob('*.txt'))
        if not approved_goal_to_decision_cycle_files:
            print("Error: No approved Goal to Decision Cycle found.")
            return
        approved_goal_to_decision_cycle = approved_goal_to_decision_cycle_files[0].read_text()

        locations_instructions = (Path("Tools") / "08 - Locations.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master world-builder. Your task is to create detailed descriptions for key locations identified in the provided story materials, following the given instructions.

Follow these instructions precisely:
1.  Read and internalize all the provided materials: the approved Extended Synopsis and the approved Goal to Decision Cycle.
2.  Identify the main locations from these materials that are crucial to the story.
3.  For each main location, generate a detailed description covering the following aspects as described in the framework:
{locations_instructions}
    *   Mood and Atmosphere
    *   Character Development opportunities within the location
    *   Foreshadowing plot points related to the location
    *   Sensory details (sight, smell, taste, feel, hear)
4.  CRITICAL: Start each location description with the exact string 'LOCATION_NAME: ' followed by the location's full name on a single line. This is essential for file naming.
5.  Present each location description clearly, with a distinct heading for each location.
6.  IMPORTANT: Separate each complete location description with the exact string '---LOCATION-BREAK---' on its own line.

--- APPROVED EXTENDED SYNOPSIS ---
{approved_extended_synopsis}

--- APPROVED GOAL TO DECISION CYCLE ---
{approved_goal_to_decision_cycle}
--- END MATERIALS ---

Begin generation now. Output only the location descriptions.
"""
    output = call_gemini(prompt)
    if not output:
        return

    locations = output.split("---LOCATION-BREAK---")
    for i, location_content in enumerate(locations):
        location_content = location_content.strip()
        if len(location_content) > 10:
            first_line = location_content.split('\n', 1)[0]
            location_name_match = re.match(r'LOCATION_NAME: (.*)', first_line)
            
            if location_name_match:
                location_name = location_name_match.group(1).strip()
                safe_location_name = re.sub(r'[^a-zA-Z0-9_ -]', '', location_name).replace(' ', '_')
                file_path = phase_dir / "drafts" / f"{safe_location_name}.txt"
            else:
                file_path = phase_dir / "drafts" / f"location-unnamed-{i+1:02d}.txt"
            
            file_path.write_text(location_content)

    print("""
--- LOCATIONS GENERATION COMPLETE ---""")
    print("Location descriptions have been generated as named files in:")
    print(f"  {phase_dir / 'drafts'}/")
    print("""
NEXT STEP: Please review the descriptions. Move the files for the locations you want to keep into:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_advanced_plotting(project_dir: Path):
    """Generates advanced plotting details for the project."""
    print("--- GENERATING ADVANCED PLOTTING (AI) ---")
    phase_dir = project_dir / "Phase_09_Advanced_Plotting"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"
    goal_to_decision_cycle_approved_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved"
    char_dev_approved_dir = project_dir / "Phase_07_Character_Development" / "approved"
    locations_approved_dir = project_dir / "Phase_08_Locations" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        approved_goal_to_decision_cycle_files = list(goal_to_decision_cycle_approved_dir.glob('*.txt'))
        if not approved_goal_to_decision_cycle_files:
            print("Error: No approved Goal to Decision Cycle found.")
            return
        approved_goal_to_decision_cycle = approved_goal_to_decision_cycle_files[0].read_text()

        approved_char_development_content = []
        for char_file in char_dev_approved_dir.glob('*.txt'):
            approved_char_development_content.append(char_file.read_text())
        approved_char_development = "\n\n---\n\n".join(approved_char_development_content)

        approved_locations_content = []
        for loc_file in locations_approved_dir.glob('*.txt'):
            approved_locations_content.append(loc_file.read_text())
        approved_locations = "\n\n---\n\n".join(approved_locations_content)

        advanced_plotting_instructions = (Path("Tools") / "09 - Advanced Plotting.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "draft").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master plot weaver. Your task is to identify and weave in advanced plot points and threads based on the provided story materials, following the given instructions.

Follow these instructions precisely:
1.  Read and internalize all the provided materials: the approved Extended Synopsis, Goal to Decision Cycle, Character Development, and Locations.
2.  Identify opportunities to introduce:
    *   Character Background reveals (slowly throughout the story)
    *   Significant Items (tracking their appearance and context)
    *   Clues (especially for mystery/thriller elements)
    *   Off-screen events that impact the plot
3.  Use the following framework to guide the advanced plotting:
{advanced_plotting_instructions}
4.  Present the advanced plotting as a structured list of plot points and threads, indicating how they connect to existing scenes or characters.
5.  The output should be a single, cohesive document outlining these advanced plotting elements.

--- APPROVED EXTENDED SYNOPSIS ---
{approved_extended_synopsis}

--- APPROVED GOAL TO DECISION CYCLE ---
{approved_goal_to_decision_cycle}

--- APPROVED CHARACTER DEVELOPMENT ---
{approved_char_development}

--- APPROVED LOCATIONS ---
{approved_locations}
--- END MATERIALS ---

Begin generation now. Output only the advanced plotting details.
"""
    output = call_gemini(prompt)
    if output:
        draft_file = phase_dir / "draft" / "09-advanced-plotting.txt"
        draft_file.write_text(output.strip())
        print("""
--- ADVANCED PLOTTING GENERATION COMPLETE ---""")
        print("A draft of the advanced plotting has been generated in:")
    print(f"  {draft_file}")
        print("""
NEXT STEP: Please review the draft. If you are happy with it, move it to:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_character_viewpoints(project_dir: Path):
    """Generates character viewpoint synopses for the project."""
    print("--- GENERATING CHARACTER VIEWPOINTS (AI) ---")
    phase_dir = project_dir / "Phase_10_Character_Viewpoints"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"
    goal_to_decision_cycle_approved_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved"
    char_dev_approved_dir = project_dir / "Phase_07_Character_Development" / "approved"
    locations_approved_dir = project_dir / "Phase_08_Locations" / "approved"
    advanced_plotting_approved_dir = project_dir / "Phase_09_Advanced_Plotting" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        approved_goal_to_decision_cycle_files = list(goal_to_decision_cycle_approved_dir.glob('*.txt'))
        if not approved_goal_to_decision_cycle_files:
            print("Error: No approved Goal to Decision Cycle found.")
            return
        approved_goal_to_decision_cycle = approved_goal_to_decision_cycle_files[0].read_text()

        approved_char_development_content = []
        for char_file in char_dev_approved_dir.glob('*.txt'):
            approved_char_development_content.append(char_file.read_text())
        approved_char_development = "\n\n---\n\n".join(approved_char_development_content)

        approved_locations_content = []
        for loc_file in locations_approved_dir.glob('*.txt'):
            approved_locations_content.append(loc_file.read_text())
        approved_locations = "\n\n---\n\n".join(approved_locations_content)

        approved_advanced_plotting_files = list(advanced_plotting_approved_dir.glob('*.txt'))
        if not approved_advanced_plotting_files:
            print("Error: No approved advanced plotting found.")
            return
        approved_advanced_plotting = approved_advanced_plotting_files[0].read_text()

        character_viewpoints_instructions = (Path("Tools") / "10 - Character Viewpoints.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master storyteller, capable of inhabiting the minds of diverse characters. Your task is to write a concise synopsis of the story from the point of view of each of the major characters, based on the previously approved story materials and the following instructions.

Follow these instructions precisely:
1.  Refer to the previously approved Extended Synopsis, Goal to Decision Cycle, Character Development, Locations, Advanced Plotting, and Character Viewpoints for context.
2.  Identify the major characters for whom a viewpoint synopsis would be beneficial (excluding the primary lead character if the story is primarily from their POV).
3.  For each identified character, write a concise synopsis of the story (approximately 200-300 words) from their unique perspective, as described in the following framework:
{character_viewpoints_instructions}
    *   Inhabit their voice, vocabulary, and metaphors.
    *   Notice what they would notice, and ignore what they would ignore.
    *   Include what they are doing in-between encounters with other characters or appearances in the main story.
    *   Start at the first relevant point to their story, which may be before the main story begins.
4.  CRITICAL: Start each character viewpoint synopsis with the exact string 'CHARACTER_VIEWPOINT_NAME: ' followed by the character's full name on a single line. This is essential for file naming.
5.  Present each character viewpoint synopsis clearly, with a distinct heading for each character.
6.  IMPORTANT: Separate each complete character viewpoint synopsis with the exact string '---CHARACTER-VIEWPOINT-BREAK---' on its own line.

--- END INSTRUCTIONS ---

Begin generation now. Output only the character viewpoint synopses.
"""
    output = call_gemini(prompt)
    if not output:
        return

    characters = output.split("---CHARACTER-VIEWPOINT-BREAK---")
    for i, char_content in enumerate(characters):
        char_content = char_content.strip()
        if len(char_content) > 10:
            first_line = char_content.split('\n', 1)[0]
            char_name_match = re.match(r'CHARACTER_VIEWPOINT_NAME: (.*)', first_line)
            
            if char_name_match:
                char_name = char_name_match.group(1).strip()
                safe_char_name = re.sub(r'[^a-zA-Z0-9_ -]', '', char_name).replace(' ', '_')
                file_path = phase_dir / "drafts" / f"{safe_char_name}.txt"
            else:
                file_path = phase_dir / "drafts" / f"character-viewpoint-unnamed-{i+1:02d}.txt"
            
            file_path.write_text(char_content)

    print("""
--- CHARACTER VIEWPOINTS GENERATION COMPLETE ---""")
    print("Character viewpoint synopses have been generated as named files in:")
    print(f"  {phase_dir / 'drafts'}/")
    print("""
NEXT STEP: Please review the synopses. Move the files for the characters you want to keep into:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_blocking_outline(project_dir: Path):
    """Generates scene blocking outlines for the project."""
    print("--- GENERATING BLOCKING OUTLINE (AI) ---")
    phase_dir = project_dir / "Phase_11_Blocking_a_Rough_Outline"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"
    goal_to_decision_cycle_approved_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved"
    char_dev_approved_dir = project_dir / "Phase_07_Character_Development" / "approved"
    locations_approved_dir = project_dir / "Phase_08_Locations" / "approved"
    advanced_plotting_approved_dir = project_dir / "Phase_09_Advanced_Plotting" / "approved"
    char_viewpoints_approved_dir = project_dir / "Phase_10_Character_Viewpoints" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        approved_goal_to_decision_cycle_files = list(goal_to_decision_cycle_approved_dir.glob('*.txt'))
        if not approved_goal_to_decision_cycle_files:
            print("Error: No approved Goal to Decision Cycle found.")
            return
        approved_goal_to_decision_cycle = approved_goal_to_decision_cycle_files[0].read_text()

        approved_char_development_content = []
        for char_file in char_dev_approved_dir.glob('*.txt'):
            approved_char_development_content.append(char_file.read_text())
        approved_char_development = "\n\n---\n\n".join(approved_char_development_content)

        approved_locations_content = []
        for loc_file in locations_approved_dir.glob('*.txt'):
            approved_locations_content.append(loc_file.read_text())
        approved_locations = "\n\n---\n\n".join(approved_locations_content)

        approved_advanced_plotting_files = list(advanced_plotting_approved_dir.glob('*.txt'))
        if not approved_advanced_plotting_files:
            print("Error: No approved advanced plotting found.")
            return
        approved_advanced_plotting = approved_advanced_plotting_files[0].read_text()

        approved_char_viewpoints_content = []
        for char_file in char_viewpoints_approved_dir.glob('*.txt'):
            approved_char_viewpoints_content.append(char_file.read_text())
        approved_char_viewpoints = "\n\n---\n\n".join(approved_char_viewpoints_content)

        blocking_outline_instructions = (Path("Tools") / "11 - Blocking a Rough Outline.md").read_text()
    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master scene blocker. Your task is to create a rough outline (scene blocking) for each major scene in the story, based on the previously approved story materials and the following instructions.

Follow these instructions precisely:
1.  Refer to the previously approved Extended Synopsis, Goal to Decision Cycle, Character Development, Locations, Advanced Plotting, and Character Viewpoints for context.
2.  For each major scene, write a rough outline describing everything that happens from beginning to end. This should include:
    *   Every action.
    *   Rough descriptions of what characters say (no speech marks).
    *   Where characters are and where they go.
3.  The blocking should not be in prose form or include detailed descriptions. It should be simple, succinct, and written in the present tense, like stage directions.
4.  Keep referring to notes on characters, locations, and plot points to ensure everything is woven in.
5.  The blocking for each scene should be approximately 100-500 words.
6.  CRITICAL: Start each scene blocking with the exact string 'SCENE_NAME: ' followed by a descriptive scene title on a single line. This is essential for file naming.
7.  Present each scene blocking clearly, with a distinct heading for each scene.
8.  IMPORTANT: Separate each complete scene blocking with the exact string '---SCENE-BLOCKING-BREAK---' on its own line.

--- END INSTRUCTIONS ---

Begin generation now. Output only the scene blocking outlines.
"""
    output = call_gemini(prompt)
    if not output:
        return

    scenes = output.split("---SCENE-BLOCKING-BREAK---")
    for i, scene_content in enumerate(scenes):
        scene_content = scene_content.strip()
        if len(scene_content) > 10:
            first_line = scene_content.split('\n', 1)[0]
            scene_name_match = re.match(r'SCENE_NAME: (.*)', first_line)
            
            if scene_name_match:
                scene_name = scene_name_match.group(1).strip()
                safe_scene_name = re.sub(r'[^a-zA-Z0-9_ -]', '', scene_name).replace(' ', '_')
                file_path = phase_dir / "drafts" / f"{i+1:02d}-{safe_scene_name}.txt"
            else:
                file_path = phase_dir / "drafts" / f"scene-unnamed-{i+1:02d}.txt"
            
            file_path.write_text(scene_content)

    print("""
--- BLOCKING OUTLINE GENERATION COMPLETE ---""")
    print("Scene blocking outlines have been generated as named files in:")
    print(f"  {phase_dir / 'drafts'}/")
    print("""
NEXT STEP: Please review the outlines. Move the files for the scenes you want to keep into:""")
    print(f"  {phase_dir / 'approved'}/")

def generate_first_draft(project_dir: Path):
    """Generates the first draft scenes for the project."""
    print("--- GENERATING FIRST DRAFT (AI) ---")
    phase_dir = project_dir / "Phase_12_First_Draft"
    extended_synopsis_approved_dir = project_dir / "Phase_05_Extended_Synopsis" / "approved"
    goal_to_decision_cycle_approved_dir = project_dir / "Phase_06_Goal_to_Decision_Cycle" / "approved"
    char_dev_approved_dir = project_dir / "Phase_07_Character_Development" / "approved"
    locations_approved_dir = project_dir / "Phase_08_Locations" / "approved"
    advanced_plotting_approved_dir = project_dir / "Phase_09_Advanced_Plotting" / "approved"
    char_viewpoints_approved_dir = project_dir / "Phase_10_Character_Viewpoints" / "approved"
    blocking_outline_approved_dir = project_dir / "Phase_11_Blocking_a_Rough_Outline" / "approved"

    try:
        approved_extended_synopsis_files = list(extended_synopsis_approved_dir.glob('*.txt'))
        if not approved_extended_synopsis_files:
            print("Error: No approved extended synopsis found.")
            return
        approved_extended_synopsis = approved_extended_synopsis_files[0].read_text()

        approved_goal_to_decision_cycle_files = list(goal_to_decision_cycle_approved_dir.glob('*.txt'))
        if not approved_goal_to_decision_cycle_files:
            print("Error: No approved Goal to Decision Cycle found.")
            return
        approved_goal_to_decision_cycle = approved_goal_to_decision_cycle_files[0].read_text()

        approved_char_development_content = []
        for char_file in char_dev_approved_dir.glob('*.txt'):
            approved_char_development_content.append(char_file.read_text())
        approved_char_development = "\n\n---\n\n".join(approved_char_development_content)

        approved_locations_content = []
        for loc_file in locations_approved_dir.glob('*.txt'):
            approved_locations_content.append(loc_file.read_text())
        approved_locations = "\n\n---\n\n".join(approved_locations_content)

        approved_advanced_plotting_files = list(advanced_plotting_approved_dir.glob('*.txt'))
        if not approved_advanced_plotting_files:
            print("Error: No approved advanced plotting found.")
            return
        approved_advanced_plotting = approved_advanced_plotting_files[0].read_text()

        approved_char_viewpoints_content = []
        for char_file in char_viewpoints_approved_dir.glob('*.txt'):
            approved_char_viewpoints_content.append(char_file.read_text())
        approved_char_viewpoints = "\n\n---\n\n".join(approved_char_viewpoints_content)

        approved_blocking_outlines_content = []
        # Sort blocking outlines by filename to maintain order (e.g., 01-Scene_Name.txt)
        for blocking_file in sorted(blocking_outline_approved_dir.glob('*-*.txt')):
            approved_blocking_outlines_content.append(f"--- SCENE BLOCKING: {blocking_file.stem} ---\n{blocking_file.read_text()}")
        approved_blocking_outlines = "\n\n".join(approved_blocking_outlines_content)

        first_draft_instructions = (Path("Tools") / "12 - First Draft.md").read_text()
        story_grid_instructions = (Path("Tools") / "StoryGrid_AI_Instructions.md").read_text()

    except FileNotFoundError as e:
        print(f"Error: Could not find a required file: {e.filename}")
        return

    (phase_dir / "draft").mkdir(parents=True, exist_ok=True)
    (phase_dir / "approved").mkdir(parents=True, exist_ok=True)

    prompt = f"""
You are a master novelist. Your task is to write the first draft of a novel, scene by scene, based on the provided scene blocking outlines and all previously approved story materials. Focus on converting the blocking into rich, descriptive prose, incorporating dialogue, sensory details, and character actions.

Follow these instructions precisely:
1.  Refer to the previously approved Extended Synopsis, Goal to Decision Cycle, Character Development, Locations, Advanced Plotting, and Character Viewpoints for comprehensive context.
2.  Go through each provided 'SCENE BLOCKING' section in order.
3.  For each scene blocking, write a full, engaging prose scene. This is your first draft, so focus on getting the story down, but make it as good as possible.
    *   Convert actions and rough dialogue into vivid prose and natural-sounding dialogue (with speech marks).
    *   Weave in sensual descriptions, adjectives, and metaphors.
    *   Utilize details about characters, locations, and plot points from the approved materials.
    *   Ensure the scene flows logically from the blocking and connects to the overall narrative.
4.  Adhere strictly to the following Story Grid principles for crafting compelling scenes:
{story_grid_instructions}
5.  Do not agonize over perfection; push through to complete each scene.
6.  CRITICAL: Start each generated scene with a clear, descriptive title (e.g., '## Scene 1: The Dark Alley Encounter').
7.  IMPORTANT: Separate each complete scene with the exact string '---SCENE-BREAK---' on its own line.

--- END INSTRUCTIONS ---

--- APPROVED EXTENDED SYNOPSIS ---
{approved_extended_synopsis}

--- APPROVED GOAL TO DECISION CYCLE ---
{approved_goal_to_decision_cycle}

--- APPROVED CHARACTER DEVELOPMENT ---
{approved_char_development}

--- APPROVED LOCATIONS ---
{approved_locations}

--- APPROVED ADVANCED PLOTTING ---
{approved_advanced_plotting}

--- APPROVED CHARACTER VIEWPOINTS ---
{approved_char_viewpoints}

--- FIRST DRAFT INSTRUCTIONS ---
{first_draft_instructions}

--- APPROVED SCENE BLOCKING ---
{approved_blocking_outlines}
--- END MATERIALS ---

Begin generation now. Output only the first draft scenes.
"""
    output = call_gemini(prompt)
    if not output:
        return

    scenes = output.split("---SCENE-BREAK---")
    for i, scene_content in enumerate(scenes):
        scene_content = scene_content.strip()
        if len(scene_content) > 10:
            first_line = scene_content.split('\n', 1)[0]
            # Attempt to extract scene title from the first line (e.g., ## Scene 1: Title)
            scene_title_match = re.match(r'## Scene [0-9]+: (.*)', first_line)
            
            if scene_title_match:
                scene_title = scene_title_match.group(1).strip()
                safe_scene_title = re.sub(r'[^a-zA-Z0-9_ -]', '', scene_title).replace(' ', '_')
                file_path = phase_dir / "draft" / f"{i+1:02d}-{safe_scene_title}.md"
            else:
                file_path = phase_dir / "draft" / f"scene-unnamed-{i+1:02d}.md"
            
            file_path.write_text(scene_content)

    print("""
--- FIRST DRAFT GENERATION COMPLETE ---""")
    print("First draft scenes have been generated as named files in:")
    print(f"  {phase_dir / 'draft'}/")
    print("""
NEXT STEP: Please review the scenes. Move the files for the scenes you want to keep into:""")
    print(f"  {phase_dir / 'approved'}/")

def compile_final_draft(project_dir: Path):
    """Compiles all approved first draft scenes into a single final Markdown file."""
    print("--- COMPILING FINAL DRAFT ---")
    approved_drafts_dir = project_dir / "Phase_12_First_Draft" / "approved"
    story_name = project_dir.name
    final_draft_file = project_dir / f"{story_name}_Draft_v1.md"

    if not approved_drafts_dir.exists() or not any(approved_drafts_dir.glob('*.md')):
        print("Error: No approved first draft scenes found to compile.")
        return

    with open(final_draft_file, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# {story_name}\n\n")
        # Sort files to ensure correct scene order
        for draft_file in sorted(approved_drafts_dir.glob('*.md')):
            outfile.write(draft_file.read_text())
            outfile.write("\n\n---\n\n") # Separator between scenes
    
    print("--- FINAL DRAFT COMPILED ---")
    print(f"Final draft compiled to: {final_draft_file}")

# The full implementation would have a Python function for each Bash function.









# The full implementation would have a Python function for each Bash function.

def get_project_state(project_dir: Path) -> dict:
    """Detects the current state of the project by checking for approved files."""
    state = {}
    phases = [
        "01_Premise", "02_Story_Skeleton", "03_Character_Introductions",
        "04_Short_Synopsis", "05_Extended_Synopsis", "06_Goal_to_Decision_Cycle",
        "07_Character_Development", "08_Locations", "09_Advanced_Plotting",
        "07_Character_Development", "08_Locations", "09_Advanced_Plotting",
        "10_Character_Viewpoints", "11_Blocking_a_Rough_Outline", "12_First_Draft"
    ]
    for phase in phases:
        phase_name = phase.split('_', 1)[1]
        approved_dir = project_dir / f"Phase_{phase}" / "approved"
        state[f"{phase_name}_approved"] = any(approved_dir.glob('*'))
    
    story_name = project_dir.name
    final_draft_file = project_dir / f"{story_name}_Draft_v1.md"
    state["final_draft_compiled"] = final_draft_file.exists()

    return state

def manage_existing_project(project_dir: Path):
    """Manages the lifecycle of an existing story project."""
    while True:
        clear_screen()
        print(f"MANAGING PROJECT: {project_dir.name}")
        print("-------------------------")

        state = get_project_state(project_dir)
        current_phase = "Initial Premise"

        # Determine the current phase based on approved files
        if not state["Premise_approved"]:
            current_phase = "Premise Pending Approval"
        elif not state["Story_Skeleton_approved"]:
            current_phase = "Ready to Generate Story Skeleton (Phase 2)"
        elif state["Story_Skeleton_approved"] and not state["Character_Introductions_approved"]:
            current_phase = "Ready to Generate Character Introductions (Phase 3)"
        elif state["Character_Introductions_approved"] and not state["Short_Synopsis_approved"]:
            current_phase = "Ready to Generate Short Synopsis (Phase 4)"
        elif state["Short_Synopsis_approved"] and not state["Extended_Synopsis_approved"]:
            current_phase = "Ready to Generate Extended Synopsis (Phase 5)"
        elif state["Extended_Synopsis_approved"] and not state["Goal_to_Decision_Cycle_approved"]:
            current_phase = "Ready to Generate Goal to Decision Cycle (Phase 6)"
        elif state["Goal_to_Decision_Cycle_approved"] and not state["Character_Development_approved"]:
            current_phase = "Ready to Generate Character Development (Phase 7)"
        elif state["Character_Development_approved"] and not state["Locations_approved"]:
            current_phase = "Ready to Generate Locations (Phase 8)"
        elif state["Locations_approved"] and not state["Advanced_Plotting_approved"]:
            current_phase = "Ready to Generate Advanced Plotting (Phase 9)"
        elif state["Advanced_Plotting_approved"] and not state["Character_Viewpoints_approved"]:
            current_phase = "Ready to Generate Character Viewpoints (Phase 10)"
        elif state["Character_Viewpoints_approved"] and not state["Blocking_a_Rough_Outline_approved"]:
            current_phase = "Ready to Generate Blocking Outline (Phase 11)"
        elif state["Blocking_a_Rough_Outline_approved"] and not state["First_Draft_approved"]:
            current_phase = "Ready to Generate First Draft (Phase 12)"
        elif state["First_Draft_approved"] and not state["final_draft_compiled"]:
            current_phase = "Ready to Compile Final Draft"
        # ... more state logic would go here, checking each phase in order
        else:
            current_phase = "First Draft Complete!"

        print(f"CURRENT PHASE: {current_phase}\n")

        menu_actions = {}
        item_count = 1

        # --- Dynamic Menu Generation ---
        if state["Premise_approved"] and not state["Story_Skeleton_approved"]:
            print(f"  [{item_count}] Generate Story Skeleton (Phase 2)")
            menu_actions[str(item_count)] = lambda: generate_story_skeleton(project_dir)
            item_count += 1
        elif state["Story_Skeleton_approved"] and not state["Character_Introductions_approved"]:
            print(f"  [{item_count}] Generate Character Introductions (Phase 3)")
            menu_actions[str(item_count)] = lambda: generate_character_introductions(project_dir)
            item_count += 1
        elif state["Character_Introductions_approved"] and not state["Short_Synopsis_approved"]:
            print(f"  [{item_count}] Generate Short Synopsis (Phase 4)")
            menu_actions[str(item_count)] = lambda: generate_short_synopsis(project_dir)
            item_count += 1
        elif state["Short_Synopsis_approved"] and not state["Extended_Synopsis_approved"]:
            print(f"  [{item_count}] Generate Extended Synopsis (Phase 5)")
            menu_actions[str(item_count)] = lambda: generate_extended_synopsis(project_dir)
            item_count += 1
        elif state["Extended_Synopsis_approved"] and not state["Goal_to_Decision_Cycle_approved"]:
            print(f"  [{item_count}] Generate Goal to Decision Cycle (Phase 6)")
            menu_actions[str(item_count)] = lambda: generate_goal_to_decision_cycle(project_dir)
            item_count += 1
        elif state["Goal_to_Decision_Cycle_approved"] and not state["Character_Development_approved"]:
            print(f"  [{item_count}] Generate Character Development (Phase 7)")
            menu_actions[str(item_count)] = lambda: generate_character_development(project_dir)
            item_count += 1
        elif state["Character_Development_approved"] and not state["Locations_approved"]:
            print(f"  [{item_count}] Generate Locations (Phase 8)")
            menu_actions[str(item_count)] = lambda: generate_locations(project_dir)
            item_count += 1
        elif state["Locations_approved"] and not state["Advanced_Plotting_approved"]:
            print(f"  [{item_count}] Generate Advanced Plotting (Phase 9)")
            menu_actions[str(item_count)] = lambda: generate_advanced_plotting(project_dir)
            item_count += 1
        elif state["Advanced_Plotting_approved"] and not state["Character_Viewpoints_approved"]:
            print(f"  [{item_count}] Generate Character Viewpoints (Phase 10)")
            menu_actions[str(item_count)] = lambda: generate_character_viewpoints(project_dir)
            item_count += 1
        elif state["Character_Viewpoints_approved"] and not state["Blocking_a_Rough_Outline_approved"]:
            print(f"  [{item_count}] Generate Blocking Outline (Phase 11)")
            menu_actions[str(item_count)] = lambda: generate_blocking_outline(project_dir)
            item_count += 1
        elif state["Blocking_a_Rough_Outline_approved"] and not state["First_Draft_approved"]:
            print(f"  [{item_count}] Generate First Draft (Phase 12)")
            menu_actions[str(item_count)] = lambda: generate_first_draft(project_dir)
            item_count += 1
        elif state["First_Draft_approved"] and not state["final_draft_compiled"]:
            print(f"  [{item_count}] Compile Final Draft")
            menu_actions[str(item_count)] = lambda: compile_final_draft(project_dir)
            item_count += 1
        # ... other menu items would be dynamically added here based on state

        print("  [b] Back to Main Menu")
        menu_actions['b'] = "back"

        choice = input("\nChoose an option: ").lower()
        action = menu_actions.get(choice)

        if action == "back":
            break
        elif callable(action):
            action()
            input("\nPress Enter to continue...")
        else:
            print("Invalid option.")
            input("\nPress Enter to continue...")


def main_menu():
    """Displays the main menu and handles user input."""
    while True:
        clear_screen()
        print("SPINNERET PROJECT MANAGER 🕷️🕸️")
        print("-------------------------")
        print(f"Using Model: {GEMINI_MODEL}\n")

        print("PROJECTS:")
        project_dirs = [d for d in Path('.').iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != "Tools"]
        
        menu_actions = {}
        
        if not project_dirs:
            print("  (No projects found)")
        else:
            for i, p_dir in enumerate(project_dirs):
                print(f"  [{i+1}] Manage: {p_dir.name}")
                menu_actions[str(i+1)] = p_dir

        print("\nOPTIONS:")
        create_key = str(len(project_dirs) + 1)
        print(f"  [{create_key}] Create New Story Premise")
        print("  [q] Quit\n")

        choice = input("Choose an option: ").lower()

        if choice == 'q':
            print("Exiting Spinneret.")
            break
        elif choice == create_key:
            create_new_premise()
            input("\nPress Enter to return to the main menu...")
        elif choice in menu_actions:
            manage_existing_project(menu_actions[choice])
        else:
            print("Invalid option.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main_menu()
