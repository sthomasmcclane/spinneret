#!/bin/bash

# Spinneret: An interactive project manager to spin story drafts from outlines.

# --- Configuration ---
# Set the Gemini model to use for all API calls.
# Examples: "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro"
GEMINI_MODEL="gemini-2.5-flash"


# --- Main Menu Function ---
main_menu() {
    clear
    echo "SPINNERET PROJECT MANAGER 🕷️🕸️"
    echo "-------------------------"
    echo "Using Model: $GEMINI_MODEL"
    echo ""

    echo "PROJECTS:"
    found_in_progress=0
    # menu_item_count is initialized in the main loop
    for item in *; do
        if [ -d "$item" ] && [ "$item" != "Tools" ]; then
            found_in_progress=1
            # Simplified status for now, will be expanded later
            echo "  [$menu_item_count] Manage: $item"
            menu_actions[$menu_item_count]="$item"
            menu_item_count=$((menu_item_count + 1))
        fi
    done
    if [ "$found_in_progress" -eq 0 ]; then echo "  (No projects found)"; fi
    echo ""

    echo "OPTIONS:"
    echo "  [$menu_item_count] Create New Story Premise"
    menu_actions[$menu_item_count]="create_premise"
    menu_item_count=$((menu_item_count + 1))
    echo "  [q] Quit"
    echo ""
}

# --- Action Functions ---
create_new_premise() {
    read -p "Enter a one-sentence story idea: " story_idea
    read -p "Enter a title for this project: " story_title

    # Sanitize story_title to create a valid directory name
    story_dir=$(echo "$story_title" | sed 's/[^a-zA-Z0-9 ]//g' | tr ' ' '_')

    if [ -d "$story_dir" ]; then
        echo "A project with that title already exists. Please choose another."
        return
    fi

    echo "--- INITIALIZING: $story_title ---"
    mkdir -p "$story_dir/Phase_01_Premise/drafts" "$story_dir/Phase_01_Premise/approved"
    echo "Workspace created."

    echo "--- GENERATING PREMISE OPTIONS (AI) ---"
    # Read the instructions from the Premise file
    premise_instructions=$(cat "Tools/01 - Premise.md")

    ai_prompt="You are a master story coach. Your task is to take a user's simple story idea and brainstorm five compelling story premises based on it.

    Follow these instructions precisely:
    1.  Read the user's story idea carefully.
    2.  Use the following framework to structure your thinking for each premise:
        $premise_instructions
    3.  Generate five distinct premise options. Each premise must be a single sentence and follow the structure: Situation > Character > Goal > Opponent > Disaster.
    4.  Present the five premises clearly.
    5.  IMPORTANT: Separate each premise with the exact string '---PREMISE-BREAK---' on its own line.

    --- USER'S STORY IDEA ---
    $story_idea
    --- END OF IDEA ---

    Begin generation now."

    # Write the prompt to a temporary file
    tmp_prompt_file=$(mktemp)
    echo -e "$ai_prompt" > "$tmp_prompt_file"

    # Call the Gemini CLI and pipe the output to awk to split into separate files
    cat "$tmp_prompt_file" | gemini -m "$GEMINI_MODEL" -p - | awk -v dir="$story_dir/Phase_01_Premise/drafts" 'BEGIN {RS="---PREMISE-BREAK---"; premise_num=1} {gsub(/^\s+|\s+$/, ""); if (length($0) > 10) { filename = sprintf("%s/premise-%02d.txt", dir, premise_num++); print $0 > filename}}'

    # Clean up the temporary file
    rm "$tmp_prompt_file"

    echo "--- PREMISE GENERATION COMPLETE ---"
    echo "Five premise options have been generated as separate files in:"
    echo "  $story_dir/Phase_01_Premise/drafts/"
    echo ""
    echo "NEXT STEP: Please review the options, choose the one you like best, and move it to:"
    echo "  $story_dir/Phase_01_Premise/approved/"
    echo "You can rename the file if you wish, but it is not necessary."
}


manage_existing_project() {
    local project_dir=$1
    while true; do
        clear
        echo "MANAGING PROJECT: $project_dir"
        echo "-------------------------"

        # --- State Detection ---
        current_phase="Premise"
        premise_approved=false
        if [ -n "$(find "$project_dir/Phase_01_Premise/approved" -type f 2>/dev/null)" ]; then
            premise_approved=true
        fi

        skeleton_approved=false
        if [ -n "$(find "$project_dir/Phase_02_Story_Skeleton/approved" -type f 2>/dev/null)" ]; then
            skeleton_approved=true
        fi

        character_introductions_approved=false
        if [ -n "$(find "$project_dir/Phase_03_Character_Introductions/approved" -type f 2>/dev/null)" ]; then
            character_introductions_approved=true
        fi

        total_char_count=$(find "$project_dir/Phase_03_Character_Introductions/drafts" -type f 2>/dev/null | wc -l)
        approved_char_count=$(find "$project_dir/Phase_03_Character_Introductions/approved" -type f 2>/dev/null | wc -l)
        pending_char_count=$((total_char_count - approved_char_count))

        short_synopsis_draft_exists=false
        if [ -n "$(find "$project_dir/Phase_04_Short_Synopsis/draft" -type f 2>/dev/null)" ]; then
            short_synopsis_draft_exists=true
        fi
        
        # This will be expanded as we add more phases
        if $premise_approved && ! $skeleton_approved; then
            current_phase="Story Skeleton"
        elif $skeleton_approved && [ "$total_char_count" -eq 0 ]; then
            current_phase="Character Introductions"
        elif $skeleton_approved && [ "$pending_char_count" -gt 0 ]; then
            current_phase="Characters Pending Approval ($pending_char_count pending)"
        elif $character_introductions_approved && ! $short_synopsis_draft_exists; then
            current_phase="Short Synopsis"
        fi

        echo "CURRENT PHASE: $current_phase"
        echo ""

        declare -A project_menu_actions
        project_menu_item_count=1

        # --- Dynamic Menu Generation ---
        if $premise_approved && ! $skeleton_approved; then
            echo "  [$project_menu_item_count] Generate Story Skeleton (Phase 2)"
            project_menu_actions[$project_menu_item_count]="generate_skeleton"
            project_menu_item_count=$((project_menu_item_count + 1))
        elif $skeleton_approved && [ "$total_char_count" -eq 0 ]; then
            echo "  [$project_menu_item_count] Generate Character Introductions (Phase 3)"
            project_menu_actions[$project_menu_item_count]="generate_character_introductions"
            project_menu_item_count=$((project_menu_item_count + 1))
        elif $skeleton_approved && [ "$pending_char_count" -gt 0 ]; then
            echo "  [$project_menu_item_count] Approve Characters ($pending_char_count pending)"
            project_menu_actions[$project_menu_item_count]="approve_characters"
            project_menu_item_count=$((project_menu_item_count + 1))
        elif $character_introductions_approved && ! $short_synopsis_draft_exists; then
            echo "  [$project_menu_item_count] Generate Short Synopsis (Phase 4)"
            project_menu_actions[$project_menu_item_count]="generate_short_synopsis"
            project_menu_item_count=$((project_menu_item_count + 1))
        fi

        echo "  [$project_menu_item_count] Back to Main Menu"
        project_menu_actions[$project_menu_item_count]="back"

        read -p "Choose an option: " project_choice

        if [ -z "$project_choice" ]; then
            action=""
        else
            action="${project_menu_actions[$project_choice]}"
        fi

        case $action in
            "back") break ;;
            "generate_skeleton")
                generate_story_skeleton "$project_dir"
                ;;
            "generate_character_introductions")
                generate_character_introductions "$project_dir"
                ;;
            "approve_characters")
                echo "Please review the generated character files in $project_dir/Phase_03_Character_Introductions/drafts/"
                echo "Edit them as needed, and then move the approved files to $project_dir/Phase_03_Character_Introductions/approved/"
                ;;
            "generate_short_synopsis")
                generate_short_synopsis "$project_dir"
                ;;
            "generate_extended_synopsis")
                generate_extended_synopsis "$project_dir"
                ;;
            *) echo "Invalid option." ;;
        esac
        read -p "Press Enter to continue..."
    done
}

generate_extended_synopsis() {
    local project_dir=$1
    echo "--- GENERATING EXTENDED SYNOPSIS (AI) ---"

    # --- Gather all approved materials ---
    approved_premise=$(cat "$project_dir/Phase_01_Premise/approved"/*)
    approved_skeleton=$(cat "$project_dir/Phase_02_Story_Skeleton/approved"/*)
    approved_short_synopsis=$(cat "$project_dir/Phase_04_Short_Synopsis/approved"/*)
    
    approved_characters=""
    for char_file in "$project_dir/Phase_03_Character_Introductions/approved"/*; do
        approved_characters+=$(cat "$char_file")
        approved_characters+=$'\n\n---\n\n'
    done

    # Create the directory for the new phase
    mkdir -p "$project_dir/Phase_05_Extended_Synopsis/draft" "$project_dir/Phase_05_Extended_Synopsis/approved"

    # Read the instructions for this phase
    extended_synopsis_instructions=$(cat "Tools/05 - The Extended Synopsis.md")

    ai_prompt="You are a master story expander. Your task is to take the provided short synopsis and expand it into a detailed extended synopsis, incorporating all previously approved story elements.

    Follow these instructions precisely:
    1.  Read and internalize all the provided materials: the premise, the story skeleton, character introductions, and especially the short synopsis.
    2.  Use the following framework to guide the structure and content of the extended synopsis:
        $extended_synopsis_instructions
    3.  Expand the short synopsis to approximately 4-5 pages (around 150 words per scene, if applicable, or roughly 2000-2500 words total).
    4.  Weave in greater detail regarding key events, character motivations, subplots, and world-building, ensuring consistency with all approved prior materials.
    5.  The output should be a single, flowing narrative, without any dialogue or conversational filler.

    --- APPROVED PREMISE ---
    $approved_premise

    --- APPROVED STORY SKELETON ---
    $approved_skeleton

    --- APPROVED CHARACTERS ---
    $approved_characters

    --- APPROVED SHORT SYNOPSIS ---
    $approved_short_synopsis
    --- END MATERIALS ---

    Begin generation now. Output only the extended synopsis."

    # Write the prompt to a temporary file
    tmp_prompt_file=$(mktemp)
    echo -e "$ai_prompt" > "$tmp_prompt_file"

    # Call the Gemini CLI
    cat "$tmp_prompt_file" | gemini -m "$GEMINI_MODEL" -p - > "$project_dir/Phase_05_Extended_Synopsis/draft/05-extended-synopsis.txt"

    # Clean up the temporary file
    rm "$tmp_prompt_file"

    echo "--- EXTENDED SYNOPSIS GENERATION COMPLETE ---"
    echo "A draft of the extended synopsis has been generated in:"
    echo "  $project_dir/Phase_05_Extended_Synopsis/draft/05-extended-synopsis.txt"
    echo ""
    echo "NEXT STEP: Please review the draft. If you are happy with it, move it to:"
    echo "  $project_dir/Phase_05_Extended_Synopsis/approved/"
}

generate_short_synopsis() {
    local project_dir=$1
    echo "--- GENERATING SHORT SYNOPSIS (AI) ---"

    # --- Gather all approved materials ---
    approved_premise=$(cat "$project_dir/Phase_01_Premise/approved"/*)
    approved_skeleton=$(cat "$project_dir/Phase_02_Story_Skeleton/approved"/*)
    
    approved_characters=""
    for char_file in "$project_dir/Phase_03_Character_Introductions/approved"/*; do
        approved_characters+=$(cat "$char_file")
        approved_characters+=$'\n\n---\n\n'
    done

    # Create the directory for the new phase
    mkdir -p "$project_dir/Phase_04_Short_Synopsis/draft" "$project_dir/Phase_04_Short_Synopsis/approved"

    # Read the instructions for this phase
    synopsis_instructions=$(cat "Tools/04 - The Short Synopsis.md")

    ai_prompt="You are a master story editor. Your task is to synthesize the provided premise, story skeleton, and character introductions into a single, cohesive short synopsis.

    Follow these instructions precisely:
    1.  Read and internalize all the provided materials: the premise, the story skeleton, and the character introductions.
    2.  Use the following framework to guide the structure and content of the synopsis:
        $synopsis_instructions
    3.  The synopsis must be approximately 500 words.
    4.  Weave the key characters and plot points from the source materials into a compelling narrative summary.
    5.  The output should be a single block of text, without any dialogue or conversational filler.

    --- APPROVED PREMISE ---
    $approved_premise

    --- APPROVED STORY SKELETON ---
    $approved_skeleton

    --- APPROVED CHARACTERS ---
    $approved_characters
    --- END MATERIALS ---

    Begin generation now. Output only the short synopsis."

    # Write the prompt to a temporary file
    tmp_prompt_file=$(mktemp)
    echo -e "$ai_prompt" > "$tmp_prompt_file"

    # Call the Gemini CLI
    cat "$tmp_prompt_file" | gemini -m "$GEMINI_MODEL" -p - > "$project_dir/Phase_04_Short_Synopsis/draft/04-short-synopsis.txt"

    # Clean up the temporary file
    rm "$tmp_prompt_file"

    echo "--- SHORT SYNOPSIS GENERATION COMPLETE ---"
    echo "A draft of the short synopsis has been generated in:"
    echo "  $project_dir/Phase_04_Short_Synopsis/draft/04-short-synopsis.txt"
    echo ""
    echo "NEXT STEP: Please review the draft. If you are happy with it, move it to:"
    echo "  $project_dir/Phase_04_Short_Synopsis/approved/"
}

generate_character_introductions() {
    local project_dir=$1
    echo "--- GENERATING CHARACTER INTRODUCTIONS (AI) ---"

    # Find the approved story skeleton file
    approved_skeleton_file=$(find "$project_dir/Phase_02_Story_Skeleton/approved" -type f -print -quit)
    if [ -z "$approved_skeleton_file" ]; then
        echo "Error: No approved story skeleton found."
        return
    fi
    approved_skeleton=$(cat "$approved_skeleton_file")

    # Create the directory for the new phase
    mkdir -p "$project_dir/Phase_03_Character_Introductions/drafts" "$project_dir/Phase_03_Character_Introductions/approved"

    # Read the instructions for this phase
    character_instructions=$(cat "Tools/03 - Character Introductions.md")

    ai_prompt="You are a master character developer. Your task is to create detailed character introductions based on the provided story skeleton.

    Follow these instructions precisely:
    1.  Read the user's approved story skeleton to identify key characters (protagonist, antagonist, mentor, etc.).
    2.  For each identified key character, apply the three layers of introduction as described in the following framework:
        $character_instructions
    3.  CRITICAL: Start each character's introduction with the exact string 'CHARACTER_NAME: ' followed by the character's full name on a single line. This is essential for file naming.
    4.  Present each character's introduction clearly, with a distinct heading for each character.
    5.  IMPORTANT: Separate each character's complete introduction with the exact string '---CHARACTER-BREAK---' on its own line.

    --- APPROVED STORY SKELETON ---
    $approved_skeleton
    --- END SKELETON ---

    Begin generation now. Output only the character introductions."

    # Write the prompt to a temporary file
    tmp_prompt_file=$(mktemp)
    echo -e "$ai_prompt" > "$tmp_prompt_file"

    # Call the Gemini CLI and pipe the output to awk to split into separate, named files
    cat "$tmp_prompt_file" | gemini -m "$GEMINI_MODEL" -p - | awk -v dir="$project_dir/Phase_03_Character_Introductions/drafts" '
        BEGIN { RS="---CHARACTER-BREAK---" }
        {
            # Trim leading and trailing whitespace portably
            gsub(/^[ \t\n]+/, "");
            gsub(/[ \t\n]+$/, "");

            if (length($0) > 10) {
                # Extract the first line to find the character name
                first_line = $0;
                sub(/\n.*/, "", first_line);

                if (sub(/^CHARACTER_NAME: /, "", first_line)) {
                    char_name = first_line;
                    gsub(/[^a-zA-Z0-9_ -]/, "", char_name); # Sanitize
                    gsub(/ /, "_", char_name); # Replace spaces
                    filename = sprintf("%s/%s.txt", dir, char_name);
                } else {
                    # Fallback if the name line is missing
                    filename = sprintf("%s/character-unnamed-%02d.txt", dir, NR);
                }
                print $0 > filename;
            }
        }
    '

    # Clean up the temporary file
    rm "$tmp_prompt_file"

    echo "--- CHARACTER INTRODUCTIONS GENERATION COMPLETE ---"
    echo "Character introductions have been generated as named files in:"
    echo "  $project_dir/Phase_03_Character_Introductions/drafts/"
    echo ""
    echo "NEXT STEP: Please review the characters. Move the files for the characters you want to keep into:"
    echo "  $project_dir/Phase_03_Character_Introductions/approved/"
}

generate_story_skeleton() {
    local project_dir=$1
    echo "--- GENERATING STORY SKELETON (AI) ---"

    # Find the approved premise file
    approved_premise_file=$(find "$project_dir/Phase_01_Premise/approved" -type f -print -quit)
    if [ -z "$approved_premise_file" ]; then
        echo "Error: No approved premise found."
        return
    fi
    approved_premise=$(cat "$approved_premise_file")

    # Create the directory for the new phase
    mkdir -p "$project_dir/Phase_02_Story_Skeleton/draft" "$project_dir/Phase_02_Story_Skeleton/approved"

    # Read the instructions for this phase
    skeleton_instructions=$(cat "Tools/02 - The Story Skeleton.md")

    ai_prompt="You are a master story planner. Your task is to expand a single-sentence story premise into a complete story skeleton using the three-act structure.

    Follow these instructions precisely:
    1.  Read the user's approved story premise.
    2.  Use the following framework to structure the story skeleton:
        $skeleton_instructions
    3.  For each stage of the three acts, write a detailed paragraph describing the key events, character actions, and plot developments.
    4.  Ensure the generated skeleton is a cohesive and logical expansion of the original premise.

    --- APPROVED PREMISE ---
    $approved_premise
    --- END PREMISE ---

    Begin generation now. Output only the story skeleton."

    # Write the prompt to a temporary file
    tmp_prompt_file=$(mktemp)
    echo -e "$ai_prompt" > "$tmp_prompt_file"

    # Call the Gemini CLI
    cat "$tmp_prompt_file" | gemini -m "$GEMINI_MODEL" -p - > "$project_dir/Phase_02_Story_Skeleton/draft/02-story-skeleton.txt"

    # Clean up the temporary file
    rm "$tmp_prompt_file"

    echo "--- SKELETON GENERATION COMPLETE ---"
    echo "A draft of the story skeleton has been generated in:"
    echo "  $project_dir/Phase_02_Story_Skeleton/draft/02-story-skeleton.txt"
    echo ""
    echo "NEXT STEP: Please review the draft. If you are happy with it, move it to:"
    echo "  $project_dir/Phase_02_Story_Skeleton/approved/"
}

generate_drafts() {
    local project_dir=$1
    local story_name=$(basename "$project_dir")
    local synopsis_dir="$project_dir/synopses/approved"
    local drafts_dir="$project_dir/scenes/drafts"

    echo "--- GENERATING SCENES (AI) ---"
    find "$synopsis_dir" -name "scene-*.txt" -print0 | sort -z | while IFS= read -r -d '' synopsis_file; do
        scene_name=$(basename "$synopsis_file")
        echo "Generating scene for $scene_name..."
        
        # This prompt incorporates the Story Grid methodology for better scene structure.
        ai_prompt="You are a master novelist who expertly applies the Story Grid methodology to craft compelling scenes. Your task is to expand the provided synopsis into a full, engaging scene. The scene must be a minimum of 750 words.

Adhere strictly to the following principles:

1.  **Core Structure (The 5 Commandments):** The scene MUST be built around this structure:
    *   **Inciting Incident:** Start the scene as close as possible to an event that destabilizes the protagonist.
    *   **Object of Desire:** The protagonist must have a clear, immediate, and conscious goal they are trying to achieve in this scene.
    *   **Progressive Complications & Turning Point:** As the protagonist pursues their goal, introduce a series of escalating obstacles. Show the protagonist changing tactics to overcome them. The final complication must be an irreversible Turning Point that forces the protagonist to act.
    *   **Crisis:** The Turning Point must lead to a clear Crisis: a difficult choice between two compelling options (a best bad choice or the lesser of two evils). The stakes of this choice must be clear.
    *   **Climax:** The protagonist makes their choice and acts on it. This action is the climax of the scene.
    *   **Resolution:** Show the immediate result of the climax, revealing a clear shift in value for the protagonist (e.g., from safe to in danger, from ignorant to knowledgeable).

2.  **Active Protagonist:** The protagonist must be the primary driver of the action (an \"outputter\"). They make decisions and take actions to achieve their goal. They are not passive observers.

3.  **Show, Don't Tell:** Convey all information through character action, dialogue, sensory details, and conflict. Do not state emotions or character traits directly. Avoid exposition and infodumping; weave in necessary details naturally.

4.  **Purposeful Dialogue:** Every line of dialogue should be a strategic action a character takes to get what they want. Dialogue reveals character and advances the conflict.

5.  **Economical Language:** Use strong, specific nouns and verbs. Avoid weak adverbs and adjectives. Ensure the word choice reflects the scene's tone.

--- SYNOPSIS TO EXPAND ---
$(cat "$synopsis_file")
--- END SYNOPSIS ---

Begin the scene now. Output only the text of the scene itself. Do not write any introduction, summary, or conversational text."
        
        tmp_prompt_file=$(mktemp)
        echo -e "$ai_prompt" > "$tmp_prompt_file"

        # Call the Gemini CLI with the prompt file, referencing the model variable
        cat "$tmp_prompt_file" | gemini -m "$GEMINI_MODEL" -p - > "$drafts_dir/$scene_name"

        rm "$tmp_prompt_file"
        sleep 10
    done
    echo "Scene generation complete."
}

compile_final_draft() {
    local project_dir=$1
    local story_name=$(basename "$project_dir")
    local approved_drafts_dir="$project_dir/scenes/approved"
    local final_draft_file="$project_dir/${story_name}_Draft_v1.md"

    echo "--- COMPILING FINAL DRAFT ---"
    echo "# $story_name" > "$final_draft_file"
    find "$approved_drafts_dir" -name "scene-*.txt" -print0 | sort -z | while IFS= read -r -d '' draft_file; do
        cat "$draft_file" >> "$final_draft_file"
        echo -e "\n\n---\\n\n" >> "$final_draft_file"
    done
    echo "Final draft compiled: $final_draft_file"
}

# --- Main Loop ---
while true; do
    declare -A menu_actions
    menu_item_count=1
    main_menu
    read -p "Choose an option: " choice

    if [ "$choice" == "q" ]; then break; fi

    if [ -z "$choice" ]; then
        action=""
    else
        action="${menu_actions[$choice]}"
    fi

    if [ -z "$action" ]; then
        echo "Invalid option."
    elif [ "$action" == "create_premise" ]; then
        create_new_premise
    else # It must be a project directory
        manage_existing_project "$action"
    fi

    echo ""
    read -p "Press Enter to return to the main menu..."
done

echo "Exiting Spinneret."
