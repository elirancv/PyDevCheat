import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional, List

class CheatShSource:
    """A source that fetches cheat sheets from cheat.sh."""
    
    def __init__(self):
        """Initialize the CheatShSource."""
        self.base_url = "https://cheat.sh"
    
    def search(self, query: str) -> Optional[str]:
        """
        Search cheat.sh for a given query and return formatted results.
        Returns None if no results found or error occurs.
        """
        try:
            headers = {
                "User-Agent": "curl/7.64.1",
                "Accept": "text/plain",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            # Handle git commands specially
            if query.startswith("git "):
                url = f"{self.base_url}/git/{query[4:].replace(' ', '/')}"
            else:
                url = f"{self.base_url}/{query.replace(' ', '/')}"
                
            response = httpx.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                return None

            content = response.text
            if "<!DOCTYPE html>" in content or "<html>" in content:
                soup = BeautifulSoup(content, 'html.parser')
                pre = soup.find('pre')
                if pre:
                    content = pre.get_text()
                else:
                    return None

            return self.clean_content(content)

        except Exception as e:
            print(f"Error fetching from cheat.sh: {e}")
            return None

    def clean_content(self, content: str) -> str:
        """
        Clean and format the content from cheat.sh
        """
        if not content:
            return ""

        # Remove ANSI color codes
        content = re.sub(r'\x1b\[[0-9;]*m', '', content)
        
        # Remove attribution and navigation lines
        lines = content.split('\n')
        cleaned_lines = []
        description_lines = []
        command_lines = []
        
        for line in lines:
            # Skip empty lines and navigation/attribution
            if not line.strip():
                continue
            if '[↑1]' in line or '[←]' in line or '[→]' in line:
                continue
            if line.startswith('# [') and '] [' in line:
                continue
            if line.startswith('  # [') and ']' in line:
                continue
                
            # Clean markdown artifacts
            line = re.sub(r'\[(\d+)\]:', '', line)  # Remove reference numbers
            line = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', line)  # Convert links to text
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Remove bold
            line = re.sub(r'\*(.*?)\*', r'\1', line)  # Remove italics
            
            # Format command lines
            if line.strip().startswith('$'):
                line = line.replace('$', '').strip()
            
            # Categorize lines
            if line.strip().startswith('#'):
                description_lines.append(line.strip())
            else:
                command_lines.append('  ' + line.strip())

        # Combine the results
        result = []
        if description_lines:
            result.append("Description:")
            result.extend(description_lines)
            result.append("")
        if command_lines:
            result.append("Commands:")
            result.extend(command_lines)

        return '\n'.join(result)

    def _parse_response(self, content: str) -> str:
        """Parse cheat.sh response into a formatted string."""
        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the pre element containing the cheat sheet content
        pre_element = soup.find('pre')
        if not pre_element:
            return "# Error: Could not parse cheat sheet content"
        
        # Extract and clean the content
        lines = pre_element.get_text().split('\n')
        result = []
        
        for line in lines:
            # Skip empty lines and navigation elements
            if not line.strip() or line.startswith('http'):
                continue
                
            # Remove ANSI color codes
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            
            if clean_line.strip():
                result.append(clean_line)
        
        return '\n'.join(result) 