#!/bin/bash

# Spinneret: An interactive project manager to spin story drafts from outlines.

# --- Main Menu Function ---
main_menu() {
    clear
    echo "SPINNERET PROJECT MANAGER 🕷️🕸️"
    echo "-------------------------"

    echo "IN PROGRESS:"
    found_in_progress=0
    for item in *; do
        if [ -d "$item" ] && [ "$item" != "Tools" ]; then
            found_in_progress=1
            # --- State Detection Logic ---
            synopsis_draft_dir="$item/synopses/drafts"
            synopsis_approved_dir="$item/synopses/approved"
            scene_draft_dir="$item/scenes/drafts" # Corrected Path
            scene_approved_dir="$item/scenes/approved" # Corrected Path
            final_draft_file="$item/$(basename "$item")_Draft_v1.md" # Corrected Path

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
    # (Logic is correct, omitted for brevity)
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

    echo "--- INITIALIZING: $story_name ---"
    mkdir -p "$story_dir/synopses/drafts" "$story_dir/synopses/approved" "$story_dir/scenes/drafts" "$story_dir/scenes/approved"
    mv "$outline_file" "$story_dir/${story_name} outline.txt"
    echo "Workspace created. Outline moved."

    # (Synopsis generation logic is correct, omitted for brevity)
}

manage_existing_project() {
    local project_dir=$1
    while true; do
        clear
        echo "MANAGING PROJECT: $project_dir"
        # --- State Detection Logic (omitted for brevity, same as main_menu) ---

        # --- Dynamic Menu Options ---
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
        action="${project_menu_actions[$project_choice]}"

        case $action in
            "back") break ;;
            "approve_synopses") echo "Please move files from synopses/drafts to synopses/approved." ;;
            "generate_scenes") generate_drafts "$project_dir" ;;
            "approve_scenes") echo "Please move files from scenes/drafts to scenes/approved." ;;
            "compile_draft") compile_final_draft "$project_dir" ;;
            *) echo "Invalid option." ;;
        esac
        read -p "Press Enter to continue..."
    done
}

generate_drafts() {
    local project_dir=$1
    local story_name=$(basename "$project_dir")
    local synopsis_dir="$project_dir/synopses/approved"
    local drafts_dir="$project_dir/scenes/drafts" # Corrected Path

    # (AI generation logic is correct, omitted for brevity)
}

compile_final_draft() {
    local project_dir=$1
    local story_name=$(basename "$project_dir")
    local approved_drafts_dir="$project_dir/scenes/approved" # Corrected Path
    local final_draft_file="$project_dir/${story_name}_Draft_v1.md" # Corrected Path

    # (Compilation logic is correct, omitted for brevity)
}

# --- Main Loop ---
# (Main loop is correct, omitted for brevity)
