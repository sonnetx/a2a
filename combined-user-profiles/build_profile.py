import json
import os
from typing import Dict, Any

def extract_name_from_filename(filename: str) -> str:
    """Extract user name from filename, handling different formats"""
    # Remove file extension
    name = filename.replace('.json', '')
    
    # Handle LinkedIn processed files
    if '_linkedin_processed' in name:
        name = name.replace('_linkedin_processed', '')
    
    # Convert underscores to spaces and title case
    name = name.replace('_', ' ').title()
    return name

def normalize_name_for_matching(name: str) -> str:
    """Normalize name for matching (lowercase, underscores)"""
    return name.lower().replace(' ', '_').replace('-', '_')

def merge_profiles(linkedin_data: Dict[Any, Any], conversational_data: Dict[Any, Any], name: str) -> Dict[Any, Any]:
    """Merge LinkedIn and conversational profile data"""
    
    # Start with LinkedIn professional data as base
    combined = {
        "name": name,
        "occupation": linkedin_data.get("occupation", ""),
        "background": {
            "education": linkedin_data.get("background", {}).get("education", ""),
            "location": linkedin_data.get("background", {}).get("location", ""),
            "family": conversational_data.get("background", {}).get("family", "")
        }
    }
    
    # Add age from conversational data
    combined["age"] = conversational_data.get("age", 25)
    
    # Add hobbies from conversational data
    combined["hobbies"] = conversational_data.get("hobbies", [])
    
    # Merge personality data (LinkedIn professional + conversational personal)
    linkedin_personality = linkedin_data.get("personality", {})
    conversational_personality = conversational_data.get("personality", {})
    
    combined["personality"] = {
        "traits": list(set(
            linkedin_personality.get("traits", []) + 
            conversational_personality.get("traits", [])
        )),
        "interests": list(set(
            linkedin_personality.get("interests", []) + 
            conversational_personality.get("interests", [])
        )),
        "goals": list(set(
            linkedin_personality.get("goals", []) + 
            conversational_personality.get("goals", [])
        ))
    }
    
    # Combine additional_info from both sources
    combined["additional_info"] = {}
    combined["additional_info"].update(conversational_data.get("additional_info", {}))
    
    return combined

def main():
    """Main function to combine matching profiles"""
    
    # Define directories
    linkedin_dir = "../scrapers/linkedin_processed_profiles"
    conversational_dir = "../profiling-agents/user-profiles"
    output_dir = "."
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all files from both directories
    try:
        linkedin_files = [f for f in os.listdir(linkedin_dir) if f.endswith('.json')]
        conversational_files = [f for f in os.listdir(conversational_dir) if f.endswith('.json')]
    except FileNotFoundError as e:
        print(f"Directory not found: {e}")
        return
    
    print(f"Found {len(linkedin_files)} LinkedIn profiles and {len(conversational_files)} conversational profiles")
    
    # Create name mappings
    linkedin_mapping = {}
    for filename in linkedin_files:
        name = extract_name_from_filename(filename)
        normalized = normalize_name_for_matching(name)
        linkedin_mapping[normalized] = (filename, name)
    
    conversational_mapping = {}
    for filename in conversational_files:
        name = extract_name_from_filename(filename)
        normalized = normalize_name_for_matching(name)
        conversational_mapping[normalized] = (filename, name)
    
    # Find matching profiles
    matches = []
    for normalized_name in linkedin_mapping:
        if normalized_name in conversational_mapping:
            linkedin_file, linkedin_name = linkedin_mapping[normalized_name]
            conversational_file, conversational_name = conversational_mapping[normalized_name]
            matches.append((normalized_name, linkedin_file, conversational_file, linkedin_name))
    
    print(f"Found {len(matches)} matching profiles")
    
    # Process each match
    for normalized_name, linkedin_file, conversational_file, display_name in matches:
        print(f"Processing: {display_name}")
        
        try:
            # Load LinkedIn data
            with open(os.path.join(linkedin_dir, linkedin_file), 'r', encoding='utf-8') as f:
                linkedin_data = json.load(f)
            
            # Load conversational data
            with open(os.path.join(conversational_dir, conversational_file), 'r', encoding='utf-8') as f:
                conversational_data = json.load(f)
            
            # Merge profiles
            combined_profile = merge_profiles(linkedin_data, conversational_data, display_name)
            
            # Save combined profile
            output_filename = f"../profiles/person_{normalized_name}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(combined_profile, f, indent=2, ensure_ascii=False)
            
            print(f"Created: {output_filename}")
            
        except Exception as e:
            print(f"Error processing {display_name}: {e}")
    
    print(f"\nCompleted! {len(matches)} combined profiles created in {output_dir}")

if __name__ == "__main__":
    main()