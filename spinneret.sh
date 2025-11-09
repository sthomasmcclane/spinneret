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

    echo "IN PROGRESS:"
    found_in_progress=0
    for item in *; do
        if [ -d "$item" ] && [ "$item" != "Tools" ]; then
            found_in_progress=1
            synopsis_draft_dir="$item/synopses/drafts"
            synopsis_approved_dir="$item/synopses/approved"
            scene_draft_dir="$item/scenes/drafts"
            scene_approved_dir="$item/scenes/approved"
            final_draft_file="$item/$(basename "$item")_Draft_v1.md"

            total_syn_count=$(find "$synopsis_draft_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
            approved_syn_count=$(find "$synopsis_approved_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
            pending_syn_count=$((total_syn_count - approved_syn_count))

            total_draft_count=$(find "$scene_draft_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
            approved_draft_count=$(find "$scene_approved_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
            pending_draft_count=$((total_draft_count - approved_draft_count))

            state="Unknown"
            if [ -f "$final_draft_file" ]; then state="Completed"
elif [ "$total_draft_count" -gt 0 ] && [ "$pending_draft_count" -le 0 ]; then state="Ready to Compile"
elif [ "$total_draft_count" -gt 0 ]; then state="Scenes Pending Approval ($pending_draft_count pending)"
elif [ "$total_syn_count" -gt 0 ] && [ "$pending_syn_count" -le 0 ]; then state="Ready to Generate Scenes"
elif [ "$total_syn_count" -gt 0 ]; then state="Synopses Pending Approval ($pending_syn_count pending)"
else state="Initialized"; fi
            
            echo "  [$menu_item_count] Manage: $item ($state)"
            menu_actions[$menu_item_count]="$item"
            menu_item_count=$((menu_item_count + 1))
        fi
    done
    if [ "$found_in_progress" -eq 0 ]; then echo "  (No projects found)"; fi
    echo ""

    echo "NEW OUTLINES:"
    found_new_outlines=0
    for item in *; do
        if [[ -f "$item" && ("$item" == *.txt || "$item" == *.md) && "$item" != "spinneret.sh" ]]; then
            found_new_outlines=1
            echo "  [$menu_item_count] Create Project from: $item"
            menu_actions[$menu_item_count]="$item"
            menu_item_count=$((menu_item_count + 1))
        fi
    done
    if [ "$found_new_outlines" -eq 0 ]; then echo "  (No new outlines found)"; fi
    echo ""
    echo "[q] Quit"
    echo ""
}

# --- Action Functions ---
create_new_project() {
    local outline_file=$1
    filename=$(basename "$outline_file")
    story_name=${filename%.*}
    story_name=${story_name//_/ }
    story_name=$(echo "$story_name" | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2); print}')
    story_dir="$story_name"
    local moved_outline_file="$story_dir/${story_name} outline.txt"

    echo "--- INITIALIZING: $story_name ---"
    mkdir -p "$story_dir/synopses/drafts" "$story_dir/synopses/approved" "$story_dir/scenes/drafts" "$story_dir/scenes/approved"
    mv "$outline_file" "$moved_outline_file"
    echo "Workspace created. Outline moved."

    echo "--- GENERATING SYNOPSES (AI) ---"
    ai_prompt="You are a story processor. Your task is to read the following outline and break it down into distinct scene synopses. Each synopsis should be a concise paragraph describing the key events, characters, and setting.

IMPORTANT: Do not include any introductory text, conversation, or summaries. Separate each synopsis with the exact string '---SCENE-BREAK---' on its own line.

--- OUTLINE ---
"
    # Write the prompt to a temporary file
    tmp_prompt_file=$(mktemp)
    echo -e "$ai_prompt" > "$tmp_prompt_file"

    # Concatenate the prompt and the outline file, then pipe to the Gemini CLI
    (cat "$tmp_prompt_file"; cat "$moved_outline_file") | gemini -m "$GEMINI_MODEL" -p - | awk -v dir="$story_dir/synopses/drafts" 'BEGIN {RS="---SCENE-BREAK---"; scene_num=1} {gsub(/^\s+|\s+$/, ""); if (length($0) > 10) { filename = sprintf("%s/scene-%02d.txt", dir, scene_num++); print $0 > filename}}'

    # Clean up the temporary file
    rm "$tmp_prompt_file"
    echo "Project '$story_name' created successfully."
}

manage_existing_project() {
    local project_dir=$1
    while true; do
        clear
        echo "MANAGING PROJECT: $project_dir"
        
        synopsis_draft_dir="$project_dir/synopses/drafts"
        synopsis_approved_dir="$project_dir/synopses/approved"
        scene_draft_dir="$project_dir/scenes/drafts"
        scene_approved_dir="$project_dir/scenes/approved"
        final_draft_file="$project_dir/$(basename "$project_dir")_Draft_v1.md"

        total_syn_count=$(find "$synopsis_draft_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
        approved_syn_count=$(find "$synopsis_approved_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
        pending_syn_count=$((total_syn_count - approved_syn_count))

        total_draft_count=$(find "$scene_draft_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
        approved_draft_count=$(find "$scene_approved_dir" -type f -name 'scene-*.txt' 2>/dev/null | wc -l)
        pending_draft_count=$((total_draft_count - approved_draft_count))

        declare -A project_menu_actions
        project_menu_item_count=1

        if [ "$total_syn_count" -gt 0 ] && [ "$pending_syn_count" -gt 0 ]; then
            echo "  [$project_menu_item_count] Approve Synopses ($pending_syn_count pending)"
            project_menu_actions[$project_menu_item_count]="approve_synopses"
            project_menu_item_count=$((project_menu_item_count + 1))
        fi

        if [ "$pending_syn_count" -le 0 ] && [ "$total_syn_count" -gt 0 ] && [ "$total_draft_count" -eq 0 ]; then
            echo "  [$project_menu_item_count] Generate Scenes from Synopses"
            project_menu_actions[$project_menu_item_count]="generate_scenes"
            project_menu_item_count=$((project_menu_item_count + 1))
        fi

        if [ "$total_draft_count" -gt 0 ] && [ "$pending_draft_count" -gt 0 ]; then
            echo "  [$project_menu_item_count] Approve Scenes ($pending_draft_count pending)"
            project_menu_actions[$project_menu_item_count]="approve_scenes"
            project_menu_item_count=$((project_menu_item_count + 1))
        fi
        
        if [ "$pending_draft_count" -le 0 ] && [ "$total_draft_count" -gt 0 ] && ! [ -f "$final_draft_file" ]; then
            echo "  [$project_menu_item_count] Compile Final Draft"
            project_menu_actions[$project_menu_item_count]="compile_draft"
            project_menu_item_count=$((project_menu_item_count + 1))
        fi

        echo "  [$project_menu_item_count] Back to Main Menu"
        project_menu_actions[$project_menu_item_count]="back"

        read -p "Choose an option: " project_choice

        # === BUG FIX START ===
        # Check for empty input before using it as an array key.
        if [ -z "$project_choice" ]; then
            action=""
        else
            action="${project_menu_actions[$project_choice]}"
        fi
        # === BUG FIX END ===

        case $action in
            "back") break ;; 
            "approve_synopses") echo "Please move files from synopses/drafts to synopses/approved."
            ;;
            "generate_scenes") generate_drafts "$project_dir"
            ;;
            "approve_scenes") echo "Please move files from scenes/drafts to scenes/approved."
            ;;
            "compile_draft") compile_final_draft "$project_dir"
            ;;
            *) echo "Invalid option."
            ;;
        esac
        read -p "Press Enter to continue..."
    done
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
        
        # This prompt is more direct to prevent conversational replies.
        ai_prompt="You are a story writing AI. Your task is to write a full scene based on the provided synopsis. The scene should be compelling, well-paced, and engaging.

IMPORTANT: Do not write any introduction, summary, or conversational text. Begin writing the scene immediately and output only the text of the scene itself.

--- CONTEXT ---
Story Title: $story_name
Scene Synopsis to Expand:
$(cat "$synopsis_file")
--- END CONTEXT ---

Begin the scene now:"
        
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

    # === BUG FIX START ===
    # Check for empty input before using it as an array key.
    if [ -z "$choice" ]; then
        action_target=""
    else
        action_target="${menu_actions[$choice]}"
    fi
    # === BUG FIX END ===

    if [ -z "$action_target" ]; then echo "Invalid option."
elif [ -f "$action_target" ]; then create_new_project "$action_target"
elif [ -d "$action_target" ]; then manage_existing_project "$action_target"
else echo "Error: Target not found."; fi
    echo ""
    read -p "Press Enter to return to the main menu..."
done

echo "Exiting Spinneret."
