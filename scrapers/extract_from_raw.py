import os
import json
import asyncio
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import anthropic

load_dotenv()

@dataclass
class LinkedInPersonProfile:
    """Data class for LinkedIn-relevant professional parameters only"""
    name: str
    occupation: str
    background: Dict[str, str]  # education, location
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinkedInPersonProfile':
        return cls(**data)

async def call_claude_for_extraction(raw_linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call Claude API to extract professional parameters from raw LinkedIn data"""
    
    # Get Claude API key from environment
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    if not claude_api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")
    
    client = anthropic.Anthropic(api_key=claude_api_key)
    
    # Create prompt for Claude
    prompt = f"""
You are a professional data extraction assistant. Given the raw LinkedIn profile data below, extract and structure the information into a clean professional profile format.

Raw LinkedIn Data:
{json.dumps(raw_linkedin_data, indent=2)}

Please extract ONLY the following LinkedIn-relevant information and return it as a JSON object:

1. name: Full name of the person
2. occupation: Current job title/role (from headline or most recent experience)
3. background: Object with:
   - education: Highest degree and field (e.g., "Computer Science PhD", "MBA")
   - location: Current location

Rules:
- Only include information that can be reasonably inferred from LinkedIn data
- If information is missing or unclear, use reasonable professional defaults
- Do not include personal hobbies, family details, personality traits, or non-professional information

Return ONLY the JSON object, no additional text.
"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse Claude's response
        response_text = response.content[0].text.strip()
        
        # Extract JSON from response (in case Claude adds extra text)
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        extracted_data = json.loads(response_text)
        return extracted_data
        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Fallback: basic extraction from raw data
        return extract_basic_info(raw_linkedin_data)

def extract_basic_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback function for basic information extraction without AI"""
    
    # Extract basic info
    name = raw_data.get('name', 'Unknown')
    headline = raw_data.get('headline', '')
    
    # Get occupation from headline or first experience
    occupation = headline
    if not occupation and raw_data.get('experiences'):
        first_exp = raw_data['experiences'][0]
        occupation = first_exp.get('title', 'Professional')
    
    # Extract education
    education = "N/A"
    if raw_data.get('education'):
        edu = raw_data['education'][0]
        degree = edu.get('degree', '')
        school = edu.get('school', '')
        if degree and school:
            education = f"{degree} from {school}"
        elif degree:
            education = degree
        elif school:
            education = f"Education from {school}"
    
    return {
        'name': name,
        'occupation': occupation,
        'background': {
            'education': education,
            'location': raw_data.get('location', 'N/A')
        }
    }

async def process_raw(filename: str) -> LinkedInPersonProfile:
    """
    Main function to process raw LinkedIn JSON data and extract professional parameters
    
    Args:
        filename: Path to the raw LinkedIn JSON file
        
    Returns:
        LinkedInPersonProfile object with extracted professional data
    """
    
    # Load raw LinkedIn data
    with open(filename, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print(f"Processing LinkedIn data for: {raw_data.get('name', 'Unknown')}")
    
    # Extract professional parameters using Claude
    try:
        extracted_data = await call_claude_for_extraction(raw_data)
        print("Successfully extracted data using Claude API")
    except Exception as e:
        print(f"Claude extraction failed, using fallback: {e}")
        extracted_data = extract_basic_info(raw_data)
    
    # Create and return profile object
    profile = LinkedInPersonProfile.from_dict(extracted_data)
    
    # Save extracted profile to file
    output_filename = filename.replace('.json', '_processed.json')
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
    
    print(f"Saved processed profile to: {output_filename}")
    
    return profile

# Example usage
async def main():
    """Example usage of the extraction function"""
    import sys
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        profile = await process_raw(filename)
        print("\nExtracted Profile:")
        print(json.dumps(profile.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("Usage: python extract_from_raw.py <linkedin_json_file>")

if __name__ == "__main__":
    asyncio.run(main())
